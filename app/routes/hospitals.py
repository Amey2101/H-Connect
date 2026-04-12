from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TicketDB
from app.models import AmbulanceDB

from app.storage import hospitals
from app.utils import calculate_distance

router = APIRouter()


# -------------------------
# ACCEPT TICKET (FIXED 🔥)
# -------------------------
@router.post("/hospital/accept_ticket")
def accept_ticket(data: dict, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(
        ticket_id=data["ticket_id"]
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    if not ticket.ambulance_id:
        raise HTTPException(status_code=400, detail="no ambulance assigned")

    ambulance = db.query(AmbulanceDB).filter_by(
        ambulance_id=ticket.ambulance_id
    ).first()

    if not ambulance:
        raise HTTPException(status_code=404, detail="ambulance not found")

    # ✅ UPDATE BOTH
    ticket.hospital_id = data["hospital_id"]
    ticket.status = "HOSPITAL_ACCEPTED"

    # 🔥 CRITICAL LINE
    ambulance.current_ticket = ticket.ticket_id
    ambulance.status = "BUSY"

    db.commit()

    return {"message": "hospital accepted case"}


# -------------------------
# REJECT TICKET (FIXED 🔥)
# -------------------------
@router.post("/hospital/reject_ticket")
def reject_ticket(data: dict, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(
        ticket_id=data["ticket_id"]
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    ticket.status = "HOSPITAL_REJECTED"
    ticket.rejection_reason = data["reason"]

    db.commit()

    return {"message": "hospital rejected case"}


@router.get("/hospitals/nearby")
def nearby_hospitals(latitude: float, longitude: float):

    results = []

    for h in hospitals:

        distance = calculate_distance(
            latitude,
            longitude,
            h["latitude"],
            h["longitude"]
        )

        results.append({
            "hospital_id": h["hospital_id"],
            "name": h["name"],
            "latitude": h["latitude"],
            "longitude": h["longitude"],
            "distance_km": round(distance, 2)
        })

    results.sort(key=lambda x: x["distance_km"])

    return results