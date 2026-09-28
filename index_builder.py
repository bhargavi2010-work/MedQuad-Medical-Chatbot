import sys
import time
from pathlib import Path
import pandas as pd
from data_loader import MedQuADLoader
from retriever import MedicalRetriever

def build_index(limit=None):
    print("==================================================")
    print("      MEDQUAD KNOWLEDGE BASE INDEX BUILDER        ")
    print("==================================================")
    start_time = time.time()
    
    loader = MedQuADLoader()
    df = loader.process_and_cache(limit=limit)
    print(f"[Info] Loaded {len(df)} QA pairs for indexing.")
    
    print("\n[Step 1/2] Initializing MedicalRetriever & Embeddings...")
    retriever = MedicalRetriever(df=df)
    
    elapsed = time.time() - start_time
    print(f"\n[Success] Index built and saved in {elapsed:.1f} seconds.")
    print("==================================================")
    return retriever

if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    build_index(limit=limit_arg)
