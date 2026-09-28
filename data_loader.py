import os
import glob
import subprocess
import zipfile
import urllib.request
import xml.etree.ElementTree as ET
import pandas as pd

# List of folders in MedQuAD that contain actual medical answers
# (Folders 10, 11, and 12 only contain URLs due to copyright, so we skip them)
DATA_FOLDERS = [
    "1_CancerGov_QA",
    "2_GARD_QA",
    "3_GHR_QA",
    "4_MPlus_Health_Topics_QA",
    "5_NIDDK_QA",
    "6_NINDS_QA",
    "7_SeniorHealth_QA",
    "8_NHLBI_QA_XML",
    "9_CDC_QA"
]

def download_medquad_dataset(target_folder="data/MedQuAD_raw"):
    """
    Downloads the MedQuAD dataset from GitHub if not already present.
    First tries git clone, otherwise downloads the zip archive.
    """
    if os.path.exists(target_folder) and len(os.listdir(target_folder)) > 0:
        print("[+] MedQuAD raw data already exists.")
        return target_folder

    os.makedirs("data", exist_ok=True)
    repo_url = "https://github.com/abachaa/MedQuAD.git"
    
    print("[*] Downloading MedQuAD dataset from GitHub...")
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, target_folder], check=True)
        print("[+] Download complete via git clone.")
    except Exception as e:
        print(f"[-] Git clone failed ({e}), downloading zip instead...")
        zip_url = "https://github.com/abachaa/MedQuAD/archive/refs/heads/master.zip"
        zip_file = "data/medquad.zip"
        urllib.request.urlretrieve(zip_url, zip_file)
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall("data")
        
        if os.path.exists("data/MedQuAD-master"):
            os.rename("data/MedQuAD-master", target_folder)
        if os.path.exists(zip_file):
            os.remove(zip_file)
        print("[+] Download and extraction complete.")

    return target_folder

def parse_xml_file(file_path):
    """
    Parses a single XML file from MedQuAD and extracts Q&A pairs.
    """
    records = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Document-level information
        source = root.attrib.get("source", "NIH")
        url = root.attrib.get("url", "")
        
        focus_tag = root.find("Focus")
        focus = focus_tag.text.strip() if focus_tag is not None and focus_tag.text else "General"

        # Loop through all Question-Answer pairs in the file
        for qa in root.findall(".//QAPair"):
            q_tag = qa.find("Question")
            a_tag = qa.find("Answer")

            if q_tag is not None and a_tag is not None:
                question = q_tag.text.strip() if q_tag.text else ""
                answer = a_tag.text.strip() if a_tag.text else ""
                qtype = q_tag.attrib.get("qtype", "general").lower()

                # Keep only valid answers with reasonable length
                if len(answer) > 20 and len(question) > 5:
                    records.append({
                        "focus": focus,
                        "question": question,
                        "answer": answer,
                        "qtype": qtype,
                        "source": source,
                        "url": url
                    })
    except Exception:
        pass  # Skip if an individual file is unreadable

    return records

def load_medquad_data(save_path="data/medquad_clean.csv", sample_limit=None):
    """
    Main function to parse all XML files and save them to a clean CSV.
    If the CSV already exists, it simply loads and returns it.
    """
    # If already parsed, load from CSV to save time
    if os.path.exists(save_path):
        print(f"[+] Loading processed dataset from: {save_path}")
        df = pd.read_csv(save_path)
        if sample_limit:
            df = df.head(sample_limit)
        print(f"[+] Loaded {len(df)} Q&A pairs.")
        return df

    # Download dataset if needed
    raw_dir = download_medquad_dataset()

    print("[*] Parsing MedQuAD XML files...")
    all_data = []

    for folder in DATA_FOLDERS:
        folder_path = os.path.join(raw_dir, folder)
        if not os.path.exists(folder_path):
            continue

        xml_files = glob.glob(os.path.join(folder_path, "*.xml"))
        print(f"    -> Reading {folder}: {len(xml_files)} files")

        for f in xml_files:
            pairs = parse_xml_file(f)
            all_data.extend(pairs)
            if sample_limit and len(all_data) >= sample_limit:
                break
        if sample_limit and len(all_data) >= sample_limit:
            break

    df = pd.DataFrame(all_data)
    # Remove any duplicate questions
    df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)

    # Save to CSV for fast future loading
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"[+] Successfully saved {len(df)} medical Q&A pairs to {save_path}")

    return df

class MedQuADLoader:
    """Class wrapper for backward compatibility with test suites."""
    def __init__(self, base_dir=None):
        pass

    def process_and_cache(self, limit=None):
        return load_medquad_data(sample_limit=limit)

if __name__ == "__main__":
    # Test script standalone
    df = load_medquad_data()
    print("\nDataset Preview:")
    print(df.head(3))

