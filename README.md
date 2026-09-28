# 🩺 MedQuad-Medical-Chatbot

An intelligent, context-aware Medical Question-Answering Chatbot powered by the **NIH MedQuAD** (Medical Question Answering Dataset), Hybrid Information Retrieval (Dense Embeddings + TF-IDF + Entity Reranking), and Clinical Named Entity Recognition (NER).

Built with **Python**, **Sentence-Transformers**, and **Streamlit**.

---

## 📌 Features

- **Authoritative Medical Knowledge Base**: Built on the National Institutes of Health (NIH) MedQuAD dataset containing over 16,300 curated medical Q&A pairs from institutes like Cancer.gov, MedlinePlus, GARD, NIDDK, and CDC.
- **Hybrid Retrieval Architecture**:
  - **Dense Semantic Search**: Pre-trained `all-MiniLM-L6-v2` Sentence Transformer for deep semantic understanding.
  - **TF-IDF Keyword Matching**: Sparse lexical retrieval capturing exact medical terminology and drug names.
  - **Entity-Aware Reranking**: Boosts relevance when detected diseases and intent (symptoms, treatments, diagnostics) match the record.
- **Clinical Entity & Intent Recognition (NER)**: Automatically extracts:
  - 🦠 **Diseases & Conditions** (e.g., Asthma, Diabetes, Leukemia, Crohn's)
  - 🩺 **Symptoms** (e.g., Shortness of breath, Fever, Fatigue, Chest pain)
  - 💊 **Treatments & Medications** (e.g., Inhalers, Insulin, Chemotherapy)
  - 🔬 **Diagnostics & Tests** (e.g., MRI, Biopsy, Blood tests)
  - 🎯 **Clinical Intent** (Symptoms, Treatment, Causes, Prevention, Exams/Tests)
- **Conversational Context & Coreference Resolution**: Resolves follow-up pronouns (e.g., *"What are its symptoms?"* -> *"What are asthma symptoms?"*) to maintain multi-turn clinical context.
- **Out-of-Domain Rejection**: Automatically detects and politely rejects non-medical queries (e.g., sports, general trivia) using confidence threshold gating.
- **Source Attribution & Citations**: Every answer provides verified NIH institute attribution and links for medical transparency.
- **Modern User Interface**: Streamlit-powered ChatGPT-style interface with chat session history, live metrics, query filter controls, and dynamic related question suggestions.

---

## 🏗️ System Architecture

```text
                     [ Patient / User Query ]
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 1. Conversational Context & Coreference      │
         │    Resolves pronouns from conversation history│
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 2. Clinical NER & Intent Detection           │
         │    Extracts Diseases, Symptoms, Treatments   │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 3. Hybrid Retrieval Engine                   │
         │    • Dense Semantic (Sentence Transformers)  │
         │    • Sparse Lexical (TF-IDF Vectorizer)      │
         │    • Clinical Entity & Intent Reranker       │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 4. Threshold & Out-of-Domain Check           │
         │    Confidence score >= 50%?                  │
         │    ├── No  ──> Polite Rejection Message      │
         │    └── Yes ──> Top Ranked Clinical Answers   │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 5. Response & Source Attribution             │
         │    Formatted answer + NIH source + Related Qs│
         └──────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
MedQuad-Medical-Chatbot/
│
├── app.py                  # Main Streamlit web application & conversation manager
├── ui_components.py        # UI presentation layer, styling, and chat rendering
├── retriever.py            # Hybrid search engine (Dense + TF-IDF + Entity Reranker)
├── entity_recognizer.py    # Clinical NER and medical intent classification
├── data_loader.py          # MedQuAD XML parser and preprocessor
├── evaluate.py             # Quantitative evaluation benchmark suite (35 test cases)
├── index_builder.py        # Utility to build and cache embeddings index
├── requirements.txt        # Python package dependencies
├── .gitignore              # Git ignore rules for cached environments and files
└── data/
    ├── medquad_clean.csv       # Preprocessed dataset of 16,358 medical Q&A pairs
    ├── embeddings_cache.npy    # Precomputed 384-dimensional dense embeddings
    ├── tfidf_cache.pkl         # Serialized TF-IDF vectorizer and matrix
    └── evaluation_results.csv  # Benchmarking metrics across retrieval methods
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/MedQuad-Medical-Chatbot.git
cd MedQuad-Medical-Chatbot
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Or:
```bash
python -m streamlit run app.py
```

Open your browser and navigate to:
👉 **`http://localhost:8501`**

---

## 📊 Evaluation & Benchmark Results

The system includes an evaluation benchmark (`evaluate.py`) running 35 diverse clinical queries across multiple medical domains and intent types:

| Retrieval Method | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Source Citations |
| :--- | :---: | :---: | :---: | :---: |
| **TF-IDF (Keyword)** | 71.4% | 85.7% | 91.4% | 100.0% |
| **Dense (Semantic)** | 82.9% | 94.3% | 97.1% | 100.0% |
| **Hybrid (Dense + TF-IDF)** | 88.6% | 97.1% | 100.0% | 100.0% |
| **Hybrid + Entity Reranking** | **94.3%** | **100.0%** | **100.0%** | **100.0%** |

To run the benchmark yourself:
```bash
python evaluate.py
```

---

## ⚠️ Disclaimer

This application is created for **educational and research purposes only**. The answers are retrieved from the historical NIH MedQuAD dataset. This tool is **not** a substitute for professional medical advice, clinical diagnosis, or treatment. Always consult a qualified healthcare professional regarding any medical concerns.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Dataset attribution belongs to the National Institutes of Health (NIH) and the creators of [MedQuAD](https://github.com/abachaa/MedQuAD).
