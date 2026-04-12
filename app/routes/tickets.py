from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models import Ticket, TicketDB, AmbulanceDB
from app.database import get_db

router = APIRouter()


VALID_STATUSES = [
    "CREATED",
    "AMBULANCE_ASSIGNED",
    "HOSPITAL_PENDING",
    "HOSPITAL_ACCEPTED",
    "HOSPITAL_REJECTED",
    "COMPLETED"
]


# -------------------------
# CREATE TICKET
# -------------------------
@router.post("/tickets")
def create_ticket(ticket: Ticket, db: Session = Depends(get_db)):

    db_ticket = TicketDB(**ticket.dict())

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)

    return {
        "message": "ticket created",
        "ticket": db_ticket
    }


# -------------------------
# GET ALL TICKETS
# -------------------------
@router.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):
    return db.query(TicketDB).all()


# -------------------------
# GET SINGLE TICKET
# -------------------------
@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(ticket_id=ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    return ticket


# -------------------------
# UPDATE STATUS
# -------------------------
@router.post("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, data: dict, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(ticket_id=ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    if data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="invalid status")

    ticket.status = data["status"]

    # 🔥 FREE AMBULANCE WHEN COMPLETED
    if data["status"] == "COMPLETED":

        ambulance = db.query(AmbulanceDB).filter_by(
            ambulance_id=ticket.ambulance_id
        ).first()

        if ambulance:
            ambulance.status = "AVAILABLE"
            ambulance.current_ticket = None

    db.commit()

    return {
        "message": "status updated",
        "ticket": ticket
    }


# -------------------------
# GET STATUS
# -------------------------
@router.get("/tickets/{ticket_id}/status")
def get_ticket_status(ticket_id: str, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(ticket_id=ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    return {
        "ticket_id": ticket.ticket_id,
        "status": ticket.status,
        "ambulance_id": ticket.ambulance_id,
        "hospital_id": ticket.hospital_id,
        "rejection_reason": ticket.rejection_reason
    }

@router.post("/assign_ambulance")
def assign_ambulance(data: dict, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(
        ticket_id=data["ticket_id"]
    ).first()

    ambulance = db.query(AmbulanceDB).filter_by(
        ambulance_id=data["ambulance_id"]
    ).first()

    if not ticket or not ambulance:
        raise HTTPException(status_code=404, detail="not found")

    # 🔥 LINK BOTH
    ticket.ambulance_id = ambulance.ambulance_id
    ticket.status = "AMBULANCE_ASSIGNED"

    ambulance.current_ticket = ticket.ticket_id
    ambulance.status = "BUSY"

    db.commit()

    return {"message": "assigned"}