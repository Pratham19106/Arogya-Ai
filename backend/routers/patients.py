from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models_db, database
from ..services import twilio_client
from ml.nlp_triage import analyze_complaint

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.post("/intake", response_model=schemas.PatientResponse)
def patient_intake(patient: schemas.PatientCreate, db: Session = Depends(database.get_db)):
    # 1. Analyze via ML model
    assessment = analyze_complaint(patient.complaint)
    
    # 2. Add to DB
    db_patient = models_db.Patient(
        name=patient.name,
        phone=patient.phone,
        complaint=patient.complaint,
        priority=assessment["priority"],
        wait_time_mins=assessment["wait_minutes"],
        base_score=assessment["score"]
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    # 3. Generate and send WhatsApp message
    msg = twilio_client.generate_triage_message(patient.name, assessment["priority"], assessment["estimated_wait_time"])
    twilio_client.send_whatsapp_message(patient.phone, msg)
    
    # 4. Create FollowUp record template
    db_followup = models_db.FollowUpRecord(patient_id=db_patient.id)
    db.add(db_followup)
    db.commit()
    
    return db_patient

@router.post("/{patient_id}/discharge")
def discharge_patient(patient_id: int, db: Session = Depends(database.get_db)):
    patient = db.query(models_db.Patient).filter(models_db.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    patient.status = "Discharged"
    db.commit()
    
    # Trigger Follow-Up Message (uses button template if FOLLOWUP_TEMPLATE_SID is set)
    sid = twilio_client.send_followup_whatsapp(patient.name, patient.phone)
    
    followup = db.query(models_db.FollowUpRecord).filter(models_db.FollowUpRecord.patient_id == patient_id).first()
    if followup:
        followup.message_sid = sid
        db.commit()
        
    return {"message": "Patient discharged and follow-up sent"}

@router.get("/{patient_id}", response_model=schemas.PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(database.get_db)):
    patient = db.query(models_db.Patient).filter(models_db.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.post("/{patient_id}/induct")
def induct_patient(patient_id: int, db: Session = Depends(database.get_db)):
    """Move a waiting patient into active treatment (Treating status)."""
    patient = db.query(models_db.Patient).filter(models_db.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.status != "Waiting":
        raise HTTPException(status_code=400, detail=f"Patient is already {patient.status}")
    
    patient.status = "Treating"
    db.commit()
    db.refresh(patient)
    return {"message": f"Patient {patient.name} inducted into treatment.", "patient": {
        "id": patient.id,
        "name": patient.name,
        "phone": patient.phone,
        "complaint": patient.complaint,
        "priority": patient.priority,
        "wait_time_mins": patient.wait_time_mins,
        "status": patient.status
    }}
