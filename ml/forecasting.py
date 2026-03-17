import pandas as pd
import numpy as np
from prophet import Prophet
import os
import joblib
import json

MODEL_DIR = "ml/forecast_models"
DEPARTMENTS = ["Emergency", "General Ward", "ICU", "Pediatrics", "Orthopedics"]

HISTORICAL_DATA_FILE = "ml/historical_patients.csv"
FEEDBACK_LOG_FILE = "ml/feedback_log.json"

def process_admin_feedback(dept: str, predicted_docs: int, actual_docs_needed: int, predicted_patients: int) -> dict:
    """
    Called when an admin flags the model's prediction was wrong.
    
    Logic: If the model predicted 4 doctors were sufficient but 6 were actually needed,
    the real patient count was higher. We use the doctor-to-patient ratio (1:10) to
    calculate the implied actual patient count and fine-tune the training data.
    """
    # Back-calculate implied actual patient volume from the actual staff needed
    # Using the same ratio as the forecasting formula: 1 doc per 10 patients
    actual_implied_patients = actual_docs_needed * 10
    
    # Calculate a correction multiplier for smarter context
    correction_ratio = actual_implied_patients / max(1, predicted_patients)
    
    # Log the feedback event for audit and analysis
    feedback_entry = {
        "date": pd.Timestamp.today().normalize().isoformat(),
        "department": dept,
        "predicted_doctors": predicted_docs,
        "actual_doctors_needed": actual_docs_needed,
        "predicted_patients": predicted_patients,
        "actual_implied_patients": actual_implied_patients,
        "correction_ratio": round(correction_ratio, 3)
    }
    
    log = []
    if os.path.exists(FEEDBACK_LOG_FILE):
        with open(FEEDBACK_LOG_FILE, "r") as f:
            try:
                log = json.load(f)
            except:
                log = []
    log.append(feedback_entry)
    with open(FEEDBACK_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
    
    # Override historical CSV with the corrected patient count for today
    today = pd.Timestamp.today().normalize()
    retrain_prophet({dept: actual_implied_patients})
    
    return feedback_entry

def get_or_create_historical_data() -> pd.DataFrame:
    if os.path.exists(HISTORICAL_DATA_FILE):
        df = pd.read_csv(HISTORICAL_DATA_FILE)
        df['ds'] = pd.to_datetime(df['ds'])
        return df
        
    print("Generating initial historical dataset...")
    # 1 year of daily data
    dates = pd.date_range(start="2024-01-01", end=pd.Timestamp.today().normalize())
    all_data = []
    
    for dept in DEPARTMENTS:
        base = 20 if dept == "Emergency" else 10
        np.random.seed(len(dept))
        weekly_seasonality = np.sin(dates.dayofweek * (2 * np.pi / 7)) * 5
        noise = np.random.normal(0, 3, len(dates))
        
        y = base + weekly_seasonality + noise
        y = [max(1, int(val)) for val in y]
        
        dept_df = pd.DataFrame({"ds": dates, "y": y, "department": dept})
        all_data.append(dept_df)
        
    master_df = pd.concat(all_data, ignore_index=True)
    master_df.to_csv(HISTORICAL_DATA_FILE, index=False)
    return master_df

def train_forecast_models():
    print("Training Prophet forecast models...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    models = {}
    master_df = get_or_create_historical_data()
    
    for dept in DEPARTMENTS:
        df = master_df[master_df['department'] == dept][['ds', 'y']]
        m = Prophet(yearly_seasonality=False, daily_seasonality=False)
        m.fit(df)
        
        path = os.path.join(MODEL_DIR, f"{dept.replace(' ', '_')}.pkl")
        joblib.dump(m, path)
        models[dept] = m
    return models

def retrain_prophet(new_counts: dict):
    """
    Takes a dictionary mapping Department -> Actual Patient Count for today.
    Appends to CSV and retrains models.
    """
    today = pd.Timestamp.today().normalize()
    master_df = get_or_create_historical_data()
    
    new_rows = []
    for dept, count in new_counts.items():
        if dept in DEPARTMENTS:
            new_rows.append({"ds": today, "y": count, "department": dept})
            
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        # Drop existing record for today if it exists to avoid duplicates
        master_df = master_df[~((master_df['ds'] == today) & (master_df['department'].isin(new_counts.keys())))]
        master_df = pd.concat([master_df, new_df], ignore_index=True)
        master_df.to_csv(HISTORICAL_DATA_FILE, index=False)
        
        # Retrain models
        train_forecast_models()
        return True
    return False

def get_forecast_models():
    models = {}
    if not os.path.exists(MODEL_DIR) or len(os.listdir(MODEL_DIR)) == 0:
        models = train_forecast_models()
    else:
        for dept in DEPARTMENTS:
            path = os.path.join(MODEL_DIR, f"{dept.replace(' ', '_')}.pkl")
            if os.path.exists(path):
                models[dept] = joblib.load(path)
            else:
                return train_forecast_models()
    return models

def get_staffing_forecast(days_ahead=1) -> pd.DataFrame:
    models = get_forecast_models()
    data = []
    
    for dept, m in models.items():
        future = m.make_future_dataframe(periods=days_ahead)
        forecast = m.predict(future)
        
        expected_patients = int(forecast.iloc[-1]['yhat'])
        expected_patients = max(1, expected_patients)
        
        recommended_docs = max(1, expected_patients // 10)
        recommended_nurses = max(2, expected_patients // 5)
        
        # Load from JSON
        current_docs, current_nurses = 0, 0
        try:
            with open("ml/current_staffing.json", "r") as f:
                staff_data = json.load(f)
                if dept in staff_data:
                    current_docs = staff_data[dept].get("doctors", 0)
                    current_nurses = staff_data[dept].get("nurses", 0)
        except Exception:
            current_docs = max(1, recommended_docs + np.random.randint(-1, 2))
            current_nurses = max(1, recommended_nurses + np.random.randint(-2, 3))
        
        data.append({
            "Department": dept,
            "Expected Patients": expected_patients,
            "Recommended Staff (Doc/Nurse)": f"{recommended_docs} / {recommended_nurses}",
            "Current Staff (Doc/Nurse)": f"{current_docs} / {current_nurses}",
            "Understaffed": current_docs < recommended_docs or current_nurses < recommended_nurses
        })

    return pd.DataFrame(data)
