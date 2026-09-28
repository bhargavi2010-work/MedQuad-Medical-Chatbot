import os
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from entity_recognizer import MedicalEntityRecognizer

def normalize_retrieval_score(raw_score, method="hybrid_rerank"):
    """
    Normalizes raw retrieval similarity into a clean percentage (0 - 100%).
    Guarantees that the score never exceeds 100%.
    """
    if method == "hybrid_rerank":
        # Max possible raw score with boosts (0.15 disease + 0.10 intent) is 1.25
        norm = raw_score / 1.25
    else:
        norm = raw_score
    # Clamp strictly between 0% and 100%
    norm = max(0.0, min(1.0, float(norm)))
    return int(round(norm * 100))

class MedicalRetriever:
    """
    Medical Information Retrieval system.
    Supports 4 retrieval methods:
    1. TF-IDF (Keyword search)
    2. Dense (Sentence Transformer semantic search)
    3. Hybrid (Dense + TF-IDF combined)
    4. Hybrid + Entity Reranking (Combines hybrid search with medical entity/intent boosting)
    
    Includes threshold-based irrelevant question rejection.
    """
    def __init__(
        self,
        df,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embed_cache="data/embeddings_cache.npy",
        tfidf_cache="data/tfidf_cache.pkl",
        entity_recognizer=None
    ):
        self.df = df.reset_index(drop=True)
        self.embed_cache = embed_cache
        self.tfidf_cache = tfidf_cache
        self.ner = entity_recognizer or MedicalEntityRecognizer()
        
        # Precompute lowercase lists for fast reranking
        self.focus_list = self.df["focus"].fillna("").astype(str).str.lower().tolist()
        self.qtype_list = self.df["qtype"].fillna("").astype(str).str.lower().tolist()

        # Dense embedding model
        print(f"[*] Loading SentenceTransformer model: {model_name}...")
        self.dense_model = SentenceTransformer(model_name)
        self.embeddings = self._get_dense_embeddings()

        # TF-IDF vectorizer
        self.tfidf_vectorizer, self.tfidf_matrix = self._get_tfidf_index()

    def _get_search_texts(self):
        """Combines disease focus and question for rich representation."""
        return [
            f"Disease: {row['focus']} | Question: {row['question']}"
            for _, row in self.df.iterrows()
        ]

    def _get_dense_embeddings(self):
        """Loads dense embeddings from cache or computes them once."""
        cache_file = self.embed_cache
        if len(self.df) != 16358 and cache_file == "data/embeddings_cache.npy":
            cache_file = f"data/embeddings_cache_{len(self.df)}.npy"

        if os.path.exists(cache_file):
            cached = np.load(cache_file)
            if len(cached) == len(self.df):
                print(f"[+] Loaded {len(cached)} dense embeddings from {cache_file}")
                return cached

        print(f"[*] Computing embeddings for {len(self.df)} questions...")
        search_texts = self._get_search_texts()
        embeddings = self.dense_model.encode(
            search_texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True
        )
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        np.save(cache_file, embeddings)
        print(f"[+] Dense embeddings saved to {cache_file}")
        return embeddings

    def _get_tfidf_index(self):
        """Loads or fits TF-IDF matrix."""
        cache_file = self.tfidf_cache
        if len(self.df) != 16358 and cache_file == "data/tfidf_cache.pkl":
            cache_file = f"data/tfidf_cache_{len(self.df)}.pkl"

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    if data["matrix"].shape[0] == len(self.df):
                        print(f"[+] Loaded TF-IDF matrix from {cache_file}")
                        return data["vectorizer"], data["matrix"]
            except Exception:
                pass

        print(f"[*] Fitting TF-IDF vectorizer for {len(self.df)} documents...")
        search_texts = self._get_search_texts()
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=30000)
        matrix = vectorizer.fit_transform(search_texts)

        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "wb") as f:
            pickle.dump({"vectorizer": vectorizer, "matrix": matrix}, f)
        print(f"[+] TF-IDF index saved to {cache_file}")
        return vectorizer, matrix

    def search(
        self,
        user_query,
        top_k=3,
        method="hybrid_rerank",
        threshold=50.0,
        source_filter=None
    ):
        """
        Retrieves the best matching answers.
        
        Parameters:
        - user_query (str): The patient's question
        - top_k (int): Number of answers to return
        - method (str): 'dense', 'tfidf', 'hybrid', or 'hybrid_rerank'
        - threshold (float): Minimum confidence % to accept. Below this = rejected.
        - source_filter (str): Filter by NIH Institute (optional)
        
        Returns:
        dict: {"is_relevant": bool, "message": str, "results": list}
        """
        query_clean = user_query.strip()
        if not query_clean or len(query_clean) < 2:
            return {
                "is_relevant": False,
                "message": "Please enter a valid medical question.",
                "results": []
            }

        # Compute Dense Similarity
        query_vec = self.dense_model.encode([query_clean], normalize_embeddings=True)
        dense_scores = np.dot(self.embeddings, query_vec.T).flatten()
        dense_scores = np.clip(dense_scores, 0.0, 1.0)

        # Compute TF-IDF Similarity
        query_tfidf = self.tfidf_vectorizer.transform([query_clean])
        tfidf_scores = (self.tfidf_matrix * query_tfidf.T).toarray().flatten()
        max_tfidf = np.max(tfidf_scores) if np.max(tfidf_scores) > 0 else 1.0
        tfidf_scores = tfidf_scores / max_tfidf

        # Select scoring method
        if method == "dense":
            final_scores = dense_scores.copy()
        elif method == "tfidf":
            final_scores = tfidf_scores.copy()
        elif method == "hybrid":
            final_scores = (0.70 * dense_scores) + (0.30 * tfidf_scores)
        elif method == "hybrid_rerank":
            final_scores = (0.70 * dense_scores) + (0.30 * tfidf_scores)

            # Extract entities and intent to rerank
            analysis = self.ner.extract_entities(query_clean)
            intent = self.ner.detect_question_type(query_clean)
            detected_diseases = [d.lower() for d in analysis["diseases"]]

            # Boost scores for disease match & intent match
            if detected_diseases or intent != "information":
                for i, (row_focus, row_qtype) in enumerate(zip(self.focus_list, self.qtype_list)):
                    if any(d in row_focus or row_focus in d for d in detected_diseases):
                        final_scores[i] += 0.15
                    if intent != "information" and intent in row_qtype:
                        final_scores[i] += 0.10
        else:
            raise ValueError(f"Unknown retrieval method: {method}")

        # Filter by source if requested
        valid_indices = np.arange(len(self.df))
        if source_filter and source_filter != "All":
            mask = (self.df["source"] == source_filter).values
            valid_indices = valid_indices[mask]
            if len(valid_indices) == 0:
                return {
                    "is_relevant": False,
                    "message": f"No records found for source '{source_filter}'.",
                    "results": []
                }
            final_scores = final_scores[valid_indices]

        # Rank results
        top_local_idx = np.argsort(final_scores)[::-1][:top_k]
        top_scores_pct = [normalize_retrieval_score(final_scores[idx], method) for idx in top_local_idx]

        # Irrelevant question rejection check
        best_score = top_scores_pct[0] if len(top_scores_pct) > 0 else 0

        if best_score < threshold:
            return {
                "is_relevant": False,
                "best_score": best_score,
                "message": "No relevant medical answer found. Please ask a specific medical question about symptoms, diseases, or treatments.",
                "analysis": self.ner.analyze_query(query_clean),
                "results": []
            }

        # Collect ranked results with source citations
        results = []
        for rank, local_i in enumerate(top_local_idx, start=1):
            global_i = valid_indices[local_i]
            row = self.df.iloc[global_i]
            score_pct = top_scores_pct[rank - 1]

            # Source citation verification
            source_name = str(row.get("source", "")).strip()
            if not source_name or source_name.lower() == "nan":
                source_name = "National Institutes of Health (NIH)"

            url_link = str(row.get("url", "")).strip()
            if url_link.lower() == "nan":
                url_link = ""

            results.append({
                "rank": rank,
                "score": score_pct,
                "focus": str(row.get("focus", "General")),
                "qtype": str(row.get("qtype", "general")),
                "question": str(row.get("question", "")),
                "answer": str(row.get("answer", "")),
                "source": source_name,
                "url": url_link
            })

        return {
            "is_relevant": True,
            "best_score": best_score,
            "message": "Relevant answer found successfully.",
            "analysis": self.ner.analyze_query(query_clean),
            "results": results
        }

    def get_related_suggestions(self, focus_topic, current_question, max_suggestions=4):
        """
        Dynamically suggests related questions from MedQuAD for the detected medical condition.
        Ensures suggestions are relevant to the specific disease (e.g. Asthma, Diabetes).
        """
        if not focus_topic or focus_topic == "General":
            return []
            
        focus_lower = str(focus_topic).lower().strip()
        suggestions = []
        seen_questions = {current_question.lower().strip()}

        # Find questions from MedQuAD that share the same focus topic
        for _, row in self.df.iterrows():
            row_focus = str(row.get("focus", "")).lower().strip()
            row_q = str(row.get("question", "")).strip()
            
            if (focus_lower in row_focus or row_focus in focus_lower) and row_q.lower() not in seen_questions:
                suggestions.append(row_q)
                seen_questions.add(row_q.lower())
                if len(suggestions) >= max_suggestions:
                    break

        return suggestions

if __name__ == "__main__":
    from data_loader import load_medquad_data
    df = load_medquad_data()
    retriever = MedicalRetriever(df)

    # Test 1: Relevant question
    q_rel = "What are the symptoms of Asthma?"
    print(f"\n[Test 1] Question: '{q_rel}'")
    res_rel = retriever.search(q_rel, threshold=50.0)
    print("Is Relevant:", res_rel["is_relevant"])
    print("Best Score:", res_rel.get("best_score"))
    if res_rel["is_relevant"]:
        print("Top Answer Focus:", res_rel["results"][0]["focus"])

    # Test 2: Irrelevant / non-medical question
    q_irrel = "Who won the World Cup football match yesterday?"
    print(f"\n[Test 2] Question: '{q_irrel}'")
    res_irrel = retriever.search(q_irrel, threshold=50.0)
    print("Is Relevant:", res_irrel["is_relevant"])
    print("Best Score:", res_irrel.get("best_score"))
    print("Message:", res_irrel["message"])
