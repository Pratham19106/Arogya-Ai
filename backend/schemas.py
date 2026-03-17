from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PatientCreate(BaseModel):
    name: str
    phone: str
    complaint: str

class PatientResponse(BaseModel):
    id: int
    name: str
    phone: str
    complaint: str
    priority: str
    wait_time_mins: int
    time_registered: datetime
    status: str
    queue_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class FollowUpResponse(BaseModel):
    id: int
    patient_name: str
    patient_phone: str
    status: str
    time_sent: datetime
    time_replied: Optional[datetime] = None

class StaffForecastResponse(BaseModel):
    department: str
    expected_patients: int
    recommended_doctors: int
    recommended_nurses: int
    current_docs: int = 0
    current_nurses: int = 0
    understaffed: bool = False
