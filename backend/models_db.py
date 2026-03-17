from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, index=True)
    complaint = Column(String)
    
    # NLP Triage outcomes
    priority = Column(String) # Urgent, Moderate, Low
    wait_time_mins = Column(Integer)
    base_score = Column(Float)
    
    # Dynamic queue system
    time_registered = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="Waiting") # Waiting, Treating, Discharged
    
    # Relationships
    follow_up = relationship("FollowUpRecord", back_populates="patient", uselist=False)

class FollowUpRecord(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    message_sid = Column(String, index=True, nullable=True) # Twilio SID
    status = Column(String, default="Pending Reply") # Pending Reply, Better, Same, Worse
    time_sent = Column(DateTime(timezone=True), server_default=func.now())
    time_replied = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="follow_up")

class StaffForecastItem(Base):
    __tablename__ = "staff_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String, index=True)
    forecast_date = Column(DateTime(timezone=True), index=True)
    expected_patients = Column(Integer)
    recommended_doctors = Column(Integer)
    recommended_nurses = Column(Integer)
