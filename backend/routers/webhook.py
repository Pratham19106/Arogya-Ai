from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from .. import database, models_db
from datetime import datetime

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(database.get_db)):
    form_data = await request.form()
    
    from_number = form_data.get("From", "")
    body = form_data.get("Body", "").strip().lower()
    
    phone_clean = from_number.replace("whatsapp:", "")
    
    patient = db.query(models_db.Patient).filter(models_db.Patient.phone == phone_clean).first()
    
    if patient:
        followup = db.query(models_db.FollowUpRecord).filter(models_db.FollowUpRecord.patient_id == patient.id).first()
        if followup:
            if "1" in body or "better" in body:
                followup.status = "Better"
            elif "2" in body or "same" in body:
                followup.status = "Same"
            elif "3" in body or "worse" in body:
                followup.status = "Worse"
                
            followup.time_replied = datetime.utcnow()
            db.commit()
            
            from ..services import twilio_client
            twilio_client.send_whatsapp_message(phone_clean, "Thank you for the update. Our medical team has been notified.")
            
            if followup.status == "Worse":
                alert_msg = f"🚨 URGENT: Patient {patient.name} ({patient.phone}) just reported their condition is WORSE after being discharged. Please follow up immediately."
                twilio_client.send_whatsapp_message(twilio_client.DOCTOR_PHONE_NUMBER, alert_msg)
            
    return {"status": "received"}

# Internal API to simulate a whatsapp webhook call for Demo/Simulator page
from pydantic import BaseModel
class SimulateReplyRequest(BaseModel):
    phone: str
    reply_code: str # 1, 2, 3

@router.post("/simulate")
def simulate_whatsapp(req: SimulateReplyRequest, db: Session = Depends(database.get_db)):
    patient = db.query(models_db.Patient).filter(models_db.Patient.phone == req.phone).first()
    if patient:
        followup = db.query(models_db.FollowUpRecord).filter(models_db.FollowUpRecord.patient_id == patient.id).first()
        if followup:
            mapping = {"1": "Better", "2": "Same", "3": "Worse"}
            followup.status = mapping.get(req.reply_code, "Pending Reply")
            followup.time_replied = datetime.utcnow()
            db.commit()
            
            if followup.status == "Worse":
                from ..services import twilio_client
                alert_msg = f"🚨 URGENT: Patient {patient.name} ({patient.phone}) just reported their condition is WORSE after being discharged. Please follow up immediately."
                twilio_client.send_whatsapp_message(twilio_client.DOCTOR_PHONE_NUMBER, alert_msg)
                
            return {"status": "success"}
    return {"status": "failed", "detail": "Patient or Followup record not found"}
