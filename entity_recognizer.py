import re

# Curated lists of common medical terms for Entity Recognition (NER)
# In clinical NLP, dictionary matching is a reliable, fast baseline for medical concepts.

DISEASES = [
    "acute lymphoblastic leukemia", "chronic lymphocytic leukemia",
    "type 1 diabetes", "type 2 diabetes", "diabetes",
    "coronary artery disease", "heart disease", "hypertension",
    "crohn's disease", "crohn disease", "celiac disease",
    "alzheimer's disease", "parkinson's disease", "multiple sclerosis",
    "rheumatoid arthritis", "osteoarthritis", "arthritis",
    "breast cancer", "lung cancer", "prostate cancer", "skin cancer", "leukemia", "cancer",
    "asthma", "bronchitis", "pneumonia", "copd", "tuberculosis",
    "glaucoma", "cataract", "migraine", "epilepsy", "stroke",
    "hepatitis", "cirrhosis", "depression", "anxiety", "malaria"
]

SYMPTOMS = [
    "shortness of breath", "chest pain", "abdominal pain", "joint pain", "headache",
    "fever", "chills", "cough", "dry cough", "fatigue", "tiredness", "weakness",
    "nausea", "vomiting", "diarrhea", "constipation", "dizziness", "rash",
    "itching", "swelling", "weight loss", "weight gain", "loss of appetite",
    "night sweats", "numbness", "tingling", "insomnia", "blurred vision", "bruising"
]

TREATMENTS = [
    "chemotherapy", "radiation therapy", "radiation", "surgery", "transplant",
    "dialysis", "physical therapy", "lifestyle changes", "diet changes",
    "insulin", "metformin", "antibiotics", "antiviral", "painkillers",
    "aspirin", "ibuprofen", "paracetamol", "steroids", "inhaler",
    "vaccine", "vaccination", "immunotherapy"
]

DIAGNOSTICS = [
    "biopsy", "blood test", "complete blood count", "cbc", "urine test",
    "mri scan", "mri", "ct scan", "x-ray", "ultrasound",
    "echocardiogram", "ecg", "ekg", "endoscopy", "colonoscopy",
    "mammogram", "pap smear", "pet scan", "genetic testing",
    "lumbar puncture", "lung function test", "eye exam"
]

class MedicalEntityRecognizer:
    """
    Medical Entity Recognizer (NER).
    Extracts Diseases, Symptoms, Treatments, and Diagnostic Tests from text.
    """
    def __init__(self):
        # Sort terms by length in descending order to match multi-word phrases first
        # e.g., match 'type 2 diabetes' before matching 'diabetes'
        self.diseases = sorted(DISEASES, key=len, reverse=True)
        self.symptoms = sorted(SYMPTOMS, key=len, reverse=True)
        self.treatments = sorted(TREATMENTS, key=len, reverse=True)
        self.diagnostics = sorted(DIAGNOSTICS, key=len, reverse=True)

    def extract_entities(self, text):
        """
        Scans the user query and returns a dictionary of found medical entities.
        """
        text_lower = text.lower()
        found_diseases = []
        found_symptoms = []
        found_treatments = []
        found_diagnostics = []

        # Find diseases
        for disease in self.diseases:
            # \b ensures we match complete words, not substrings inside other words
            pattern = r"\b" + re.escape(disease) + r"\b"
            if re.search(pattern, text_lower):
                found_diseases.append(disease.title())

        # Find symptoms
        for symptom in self.symptoms:
            pattern = r"\b" + re.escape(symptom) + r"\b"
            if re.search(pattern, text_lower):
                found_symptoms.append(symptom.title())

        # Find treatments
        for treatment in self.treatments:
            pattern = r"\b" + re.escape(treatment) + r"\b"
            if re.search(pattern, text_lower):
                found_treatments.append(treatment.title())

        # Find diagnostic tests
        for diag in self.diagnostics:
            pattern = r"\b" + re.escape(diag) + r"\b"
            if re.search(pattern, text_lower):
                found_diagnostics.append(diag.upper() if len(diag) <= 4 else diag.title())

        return {
            "diseases": list(set(found_diseases)),
            "symptoms": list(set(found_symptoms)),
            "treatments": list(set(found_treatments)),
            "diagnostics": list(set(found_diagnostics))
        }

    def detect_question_type(self, question):
        """
        Identifies what the user is asking about (e.g., Symptoms, Treatment, Causes).
        """
        q = question.lower()
        if any(word in q for word in ["symptom", "signs", "warning sign", "how do i know"]):
            return "symptoms"
        elif any(word in q for word in ["treat", "cure", "therapy", "medicine", "drug", "manage"]):
            return "treatment"
        elif any(word in q for word in ["cause", "why", "risk factor", "reason"]):
            return "causes"
        elif any(word in q for word in ["diagnos", "test", "screening", "detect", "exam"]):
            return "exams and tests"
        elif any(word in q for word in ["prevent", "avoid", "protect"]):
            return "prevention"
        else:
            return "information"

    def analyze_query(self, query):
        """
        Clinical analysis method returning intent and extracted entities.
        """
        entities = self.extract_entities(query)
        intent = self.detect_question_type(query)
        return {
            "query": query,
            "intent": intent,
            "entities": entities,
            "diseases": entities.get("diseases", []),
            "symptoms": entities.get("symptoms", []),
            "treatments": entities.get("treatments", []),
            "tests": entities.get("diagnostics", [])
        }

if __name__ == "__main__":
    # Test the entity recognizer
    ner = MedicalEntityRecognizer()
    sample = "What are the common symptoms of Type 2 Diabetes and can insulin treat it?"
    
    print("User Question:", sample)
    entities = ner.extract_entities(sample)
    qtype = ner.detect_question_type(sample)
    
    print("Detected Intent:", qtype)
    print("Extracted Entities:", entities)
