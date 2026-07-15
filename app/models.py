from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, String, Float, Integer
from app.database import Base

class TicketDB(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True, index=True)
    patient_name = Column(String)
    patient_age = Column(Integer)
    emergency_contact = Column(String)
    case_type = Column(String)
    severity = Column(String)
    symptoms = Column(String)
    incident_latitude = Column(Float)
    incident_longitude = Column(Float)

    ambulance_id = Column(String, nullable=True)
    hospital_id = Column(String, nullable=True)
    doctor_id = Column(String, nullable=True)

    status = Column(String, default="CREATED")
    eta_minutes = Column(Integer, nullable=True)
    rejection_reason = Column(String, nullable=True)

class Ticket(BaseModel):
    ticket_id: str
    patient_name: str
    patient_age: int
    emergency_contact: str
    case_type: str
    severity: str
    symptoms: str
    incident_latitude: float
    incident_longitude: float

    ambulance_id: Optional[str] = None
    hospital_id: Optional[str] = None
    doctor_id: Optional[str] = None

    status: str = "CREATED"
    eta_minutes: Optional[int] = None

    rejection_reason: Optional[str] = None

class Ambulance(BaseModel):
    ambulance_id: str
    driver_name: Optional[str] = None
    latitude: float
    longitude: float
    status: str = "AVAILABLE"
    current_ticket: Optional[str] = None

class AmbulanceDB(Base):
    __tablename__ = "ambulances"

    ambulance_id = Column(String, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

    type = Column(String)
    status = Column(String, default="AVAILABLE")
    current_ticket = Column(String, nullable=True)
