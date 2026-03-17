from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from .. import schemas, models_db, database
from ml.forecasting import get_staffing_forecast, retrain_prophet, process_admin_feedback
import math
import json
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def calculate_dynamic_queue_score(base_score, time_registered):
    now = datetime.now()
    # Handle both timezone aware/unaware
    time_reg = time_registered.replace(tzinfo=None)
    wait_time_mins = (now - time_reg).total_seconds() / 60
    return base_score + math.floor(wait_time_mins / 10)

@router.get("/queue", response_model=list[schemas.PatientResponse])
def get_live_queue(db: Session = Depends(database.get_db)):
    patients = db.query(models_db.Patient).filter(
        models_db.Patient.status.in_(["Waiting", "Treating"])
    ).all()
    
    PRIORITY_ORDER = {"Urgent": 0, "Moderate": 1, "Low": 2}
    
    for p in patients:
        p.queue_score = calculate_dynamic_queue_score(p.base_score, p.time_registered)
        
    # Sort: Priority tier first (Urgent > Moderate > Low), then by dynamic score descending
    sorted_patients = sorted(
        patients,
        key=lambda x: (PRIORITY_ORDER.get(x.priority, 9), -x.queue_score)
    )
    return sorted_patients

@router.get("/metrics")
def get_metrics(db: Session = Depends(database.get_db)):
    waiting_count = db.query(models_db.Patient).filter(models_db.Patient.status == "Waiting").count()
    worse_count = db.query(models_db.FollowUpRecord).filter(models_db.FollowUpRecord.status == "Worse").count()
    
    forecast_df = get_staffing_forecast()
    
    return {
        "waiting_patients": waiting_count,
        "critical_cases": worse_count,
        "forecast": forecast_df.to_dict(orient="records"),
        "understaffed_departments": int(forecast_df["Understaffed"].sum())
    }

@router.get("/recoveries", response_model=list[schemas.FollowUpResponse])
def get_recoveries(db: Session = Depends(database.get_db)):
    records = db.query(models_db.FollowUpRecord).join(models_db.Patient).filter(
        models_db.Patient.status == "Discharged"
    ).all()
    
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "patient_name": r.patient.name,
            "patient_phone": r.patient.phone,
            "status": r.status,
            "time_sent": r.time_sent,
            "time_replied": r.time_replied
        })
    return result

@router.post("/retrain")
def retrain_forecast_model(counts: dict = Body(...)):
    """
    Accepts a dictionary of actual patient counts per department.
    { "Emergency": 150, "OPD General": 120, ... }
    """
    success = retrain_prophet(counts)
    if success:
        return {"message": "Prophet models retrained successfully with actual counts."}
    return {"message": "No valid departments provided for retraining."}, 400

@router.get("/staff")
def get_current_staff():
    try:
        with open("ml/current_staffing.json", "r") as f:
            return json.load(f)
    except:
        return {}

@router.post("/staff")
def update_current_staff(staff_data: dict = Body(...)):
    with open("ml/current_staffing.json", "w") as f:
        json.dump(staff_data, f, indent=4)
    return {"message": "Staffing configuration updated."}

@router.post("/feedback")
def submit_feedback(payload: dict = Body(...)):
    """
    Admin feedback to improve Prophet predictions.
    Expects: { dept, predicted_docs, actual_docs_needed, predicted_patients }
    """
    result = process_admin_feedback(
        dept=payload["dept"],
        predicted_docs=payload["predicted_docs"],
        actual_docs_needed=payload["actual_docs_needed"],
        predicted_patients=payload["predicted_patients"]
    )
    return {"message": "Feedback recorded. Model retrained.", "entry": result}

@router.get("/feedback-log")
def get_feedback_log():
    import os
    log_file = "ml/feedback_log.json"
    if not os.path.exists(log_file):
        return []
    with open(log_file, "r") as f:
        try:
            return json.load(f)
        except:
            return []
