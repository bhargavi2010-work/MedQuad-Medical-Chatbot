import pandas as pd
from data_loader import load_medquad_data
from retriever import MedicalRetriever

# 35 Curated benchmark test questions covering diverse conditions, intents, and wordings
TEST_QUESTIONS = [
    # 1. Disease Questions (General information / definition)
    {"question": "What is Type 2 Diabetes?", "expected_focus": "diabetes"},
    {"question": "Can you explain Crohn's disease?", "expected_focus": "crohn"},
    {"question": "What is Acute Lymphoblastic Leukemia?", "expected_focus": "leukemia"},
    {"question": "Tell me about Parkinson disease", "expected_focus": "parkinson"},
    {"question": "What is Glaucoma?", "expected_focus": "glaucoma"},
    {"question": "What is Alzheimer's disease?", "expected_focus": "alzheimer"},
    {"question": "What is Rheumatoid Arthritis?", "expected_focus": "rheumatoid arthritis"},
    {"question": "What is Celiac Disease?", "expected_focus": "celiac"},
    
    # 2. Symptom Questions
    {"question": "What are the common symptoms of Asthma?", "expected_focus": "asthma"},
    {"question": "What are the warning signs of Leukemia?", "expected_focus": "leukemia"},
    {"question": "What are the symptoms of high blood pressure?", "expected_focus": "hypertension"},
    {"question": "How do I know if I have Cataracts?", "expected_focus": "cataract"},
    {"question": "What are the symptoms of Migraine?", "expected_focus": "migraine"},
    {"question": "What are signs of Hepatitis?", "expected_focus": "hepatitis"},
    {"question": "What are the symptoms of Breast Cancer?", "expected_focus": "breast cancer"},
    {"question": "What are the symptoms of Cystic Fibrosis?", "expected_focus": "cystic fibrosis"},
    
    # 3. Treatment Questions
    {"question": "How is Type 2 Diabetes treated?", "expected_focus": "diabetes"},
    {"question": "What treatments are available for Glaucoma?", "expected_focus": "glaucoma"},
    {"question": "How to treat Asthma attacks with inhalers?", "expected_focus": "asthma"},
    {"question": "What are therapies for Osteoarthritis?", "expected_focus": "osteoarthritis"},
    {"question": "How is Prostate Cancer treated?", "expected_focus": "prostate cancer"},
    {"question": "What is the treatment for Epilepsy?", "expected_focus": "epilepsy"},
    {"question": "How is Depression treated?", "expected_focus": "depression"},
    {"question": "Can surgery cure Cataracts?", "expected_focus": "cataract"},

    # 4. Diagnostic & Exam Questions
    {"question": "How is Acute Lymphoblastic Leukemia diagnosed?", "expected_focus": "leukemia"},
    {"question": "How do doctors test for Glaucoma?", "expected_focus": "glaucoma"},
    {"question": "What exams diagnose Heart Disease?", "expected_focus": "heart"},
    {"question": "How is Multiple Sclerosis diagnosed?", "expected_focus": "multiple sclerosis"},
    {"question": "What screening tests detect Breast Cancer?", "expected_focus": "breast cancer"},

    # 5. Cause & Risk Factor Questions
    {"question": "What causes Crohn's disease?", "expected_focus": "crohn"},
    {"question": "What are the causes and risk factors for Hypertension?", "expected_focus": "hypertension"},
    {"question": "What causes Chronic Obstructive Pulmonary Disease?", "expected_focus": "copd"},
    {"question": "What triggers Asthma?", "expected_focus": "asthma"},
    {"question": "Is Alzheimer disease genetic?", "expected_focus": "alzheimer"},
    {"question": "What causes Cirrhosis of the liver?", "expected_focus": "cirrhosis"}
]

def evaluate_retrieval_methods():
    print("=" * 65)
    print("       MEDQUAD RETRIEVAL EVALUATION & COMPARISON         ")
    print("=" * 65)
    print(f"Total Evaluation Questions: {len(TEST_QUESTIONS)}")

    df = load_medquad_data()
    retriever = MedicalRetriever(df)

    methods = ["tfidf", "dense", "hybrid", "hybrid_rerank"]
    results_summary = []

    for method in methods:
        print(f"\n[*] Evaluating method: '{method}'...")
        top1_hits = 0
        top3_hits = 0
        top5_hits = 0
        citations_valid = 0
        total_answers_checked = 0

        for item in TEST_QUESTIONS:
            q = item["question"]
            target = item["expected_focus"].lower()

            response = retriever.search(q, top_k=5, method=method, threshold=0.0)
            matches = response.get("results", [])

            # Check Top-K accuracy
            matched_ranks = []
            for rank, match in enumerate(matches, start=1):
                focus_text = match["focus"].lower()
                question_text = match["question"].lower()
                
                # Check if target condition matches focus or question
                if target in focus_text or target in question_text:
                    matched_ranks.append(rank)

                # Source Citation verification
                if match.get("source") and len(match.get("source")) > 1:
                    citations_valid += 1
                total_answers_checked += 1

            if matched_ranks:
                min_rank = min(matched_ranks)
                if min_rank <= 1:
                    top1_hits += 1
                if min_rank <= 3:
                    top3_hits += 1
                if min_rank <= 5:
                    top5_hits += 1

        total_q = len(TEST_QUESTIONS)
        top1_acc = (top1_hits / total_q) * 100
        top3_acc = (top3_hits / total_q) * 100
        top5_acc = (top5_hits / total_q) * 100
        citation_pct = (citations_valid / total_answers_checked) * 100 if total_answers_checked else 100.0

        results_summary.append({
            "Method": method.upper().replace("_", " + "),
            "Top-1 Acc (%)": round(top1_acc, 1),
            "Top-3 Acc (%)": round(top3_acc, 1),
            "Top-5 Acc (%)": round(top5_acc, 1),
            "Source Citations (%)": round(citation_pct, 1)
        })

    summary_df = pd.DataFrame(results_summary)
    print("\n" + "=" * 65)
    print("                 FINAL EVALUATION RESULTS                ")
    print("=" * 65)
    print(summary_df.to_string(index=False))
    print("=" * 65)
    
    # Save results to a CSV for project report
    summary_df.to_csv("data/evaluation_results.csv", index=False)
    print("\n[+] Evaluation report saved to 'data/evaluation_results.csv'")
    return summary_df

if __name__ == "__main__":
    evaluate_retrieval_methods()
