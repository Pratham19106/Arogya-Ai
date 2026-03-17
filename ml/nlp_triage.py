import pandas as pd
import numpy as np
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os
import random

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

MODEL_PATH = "ml/triage_model.pkl"

def generate_training_data():
    data = [
        ("severe chest pain and shortness of breath", "Urgent", 15),
        ("bleeding heavily from a deep cut", "Urgent", 10),
        ("unconscious patient", "Urgent", 5),
        ("suspected heart attack breathing difficulty", "Urgent", 20),
        ("stroke drooping face", "Urgent", 10),
        
        ("high fever and vomiting", "Moderate", 40),
        ("broken arm bone fracture", "Moderate", 60),
        ("severe stomach ache nausea", "Moderate", 45),
        ("dizzy and lightheaded", "Moderate", 50),
        ("bad migraine cannot see", "Moderate", 35),
        
        ("routine checkup for blood pressure", "Low", 45),
        ("mild headache since yesterday", "Low", 35),
        ("need a prescription refill", "Low", 60),
        ("minor scrape on knee", "Low", 30),
        ("sore throat cough", "Low", 40),
    ]
    expanded_data = []
    for _ in range(10):
        for text, label, wt in data:
            wait_time = max(0, int(np.random.normal(wt, wt*0.2)))
            expanded_data.append((text, label, wait_time))
            
    df = pd.DataFrame(expanded_data, columns=["complaint", "priority", "wait_time_mins"])
    return df

def train_triage_model():
    print("Training NLP Triage Model...")
    df = generate_training_data()
    
    def preprocess(text):
        doc = nlp(text.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        return " ".join(tokens)
        
    df['processed'] = df['complaint'].apply(preprocess)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=1000)),
        ('clf', LogisticRegression(class_weight='balanced'))
    ])
    
    pipeline.fit(df['processed'], df['priority'])
    
    wait_time_map = df.groupby('priority')['wait_time_mins'].mean().to_dict()
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"pipeline": pipeline, "wait_time_map": wait_time_map}, MODEL_PATH)
    print("Model saved to", MODEL_PATH)
    return pipeline, wait_time_map

model_data = None

def get_triage_model():
    global model_data
    if model_data is None:
        if not os.path.exists(MODEL_PATH):
            model_data = train_triage_model()
        else:
            model_data_dict = joblib.load(MODEL_PATH)
            model_data = (model_data_dict["pipeline"], model_data_dict["wait_time_map"])
    return model_data

def analyze_complaint(complaint: str) -> dict:
    pipeline, wait_time_map = get_triage_model()
    
    doc = nlp(complaint.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    processed_text = " ".join(tokens)
    
    preds = pipeline.predict_proba([processed_text])[0]
    classes = pipeline.classes_
    best_idx = np.argmax(preds)
    priority = classes[best_idx]
    
    score = float(preds[best_idx] * 100)
    base_wait = wait_time_map.get(priority, 60)
    wait_minutes = max(0, int(np.random.normal(base_wait, base_wait*0.1)))
    
    return {
        "priority": priority,
        "estimated_wait_time": f"{wait_minutes} mins",
        "wait_minutes": wait_minutes,
        "score": score
    }
