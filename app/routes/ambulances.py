from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AmbulanceDB, TicketDB
from app.websocket_manager import clients
from app.utils import calculate_distance

router = APIRouter()


# -------------------------
# REGISTER AMBULANCE
# -------------------------
@router.post("/ambulances/register")
def register_ambulance(data: dict, db: Session = Depends(get_db)):

    ambulance_id = data["ambulance_id"]

    existing = db.query(AmbulanceDB).filter_by(
        ambulance_id=ambulance_id
    ).first()

    if existing:
        return {"message": "ambulance already exists"}

    new_ambulance = AmbulanceDB(
        ambulance_id=ambulance_id,
        latitude=data["latitude"],
        longitude=data["longitude"],
        type=data.get("type", "government"),
        status="AVAILABLE",
        current_ticket=None
    )

    db.add(new_ambulance)
    db.commit()

    return {"message": "ambulance registered"}


# -------------------------
# UPDATE LOCATION (FIXED 🔥)
# -------------------------
@router.post("/ambulances/location")
async def update_location(data: dict, db: Session = Depends(get_db)):

    ambulance = db.query(AmbulanceDB).filter_by(
        ambulance_id=data["ambulance_id"]
    ).first()

    if not ambulance:
        raise HTTPException(status_code=404, detail="ambulance not registered")

    # ✅ Update location
    ambulance.latitude = data["latitude"]
    ambulance.longitude = data["longitude"]
    db.commit()

    # -------------------------
    # INIT SAFE VARIABLES 🔥
    # -------------------------
    eta = None
    ticket = None
    hospital = None   # 🔥 CRITICAL FIX

    # -------------------------
    # FIND TICKET
    # -------------------------
    if ambulance.current_ticket:
        ticket = db.query(TicketDB).filter_by(
            ticket_id=ambulance.current_ticket
        ).first()

    if not ticket:
        ticket = db.query(TicketDB).filter(
            TicketDB.ambulance_id == ambulance.ambulance_id,
            TicketDB.status.in_(["HOSPITAL_ACCEPTED", "HOSPITAL_PENDING"])
        ).first()

    # -------------------------
    # FIND HOSPITAL + ETA
    # -------------------------
    if ticket and ticket.hospital_id:

        from app.storage import hospitals

        hospital = next(
            (h for h in hospitals if h["hospital_id"] == ticket.hospital_id),
            None
        )

        if hospital:
            distance = calculate_distance(
                ambulance.latitude,
                ambulance.longitude,
                hospital["latitude"],
                hospital["longitude"]
            )

            speed = 0.005
            eta = max(1, int(distance / speed))

    # -------------------------
    # SEND WEBSOCKET 🔥
    # -------------------------
    for client in clients:
        await client.send_json({
            "type": "ambulance_update",
            "ambulance_id": ambulance.ambulance_id,
            "latitude": ambulance.latitude,
            "longitude": ambulance.longitude,
            "eta": eta,
            "has_active_ticket": True if ticket and ticket.hospital_id else False,
            "hospital_id": ticket.hospital_id if ticket else None,
            "hospital_lat": hospital["latitude"] if hospital else None,
            "hospital_lon": hospital["longitude"] if hospital else None
        })

    # -------------------------
    # DEBUG
    # -------------------------
    print("---- DEBUG START ----")
    print("AMB:", ambulance.ambulance_id)
    print("CURRENT_TICKET:", ambulance.current_ticket)

    if ticket:
        print("TICKET FOUND:", ticket.ticket_id)
        print("HOSPITAL_ID:", ticket.hospital_id)
    else:
        print("NO TICKET FOUND")

    print("ETA:", eta)
    print("---- DEBUG END ----")

    return {"message": "location updated"}


# -------------------------
# ACCEPT TICKET
# -------------------------
@router.post("/ambulances/accept_ticket")
def accept_ticket(data: dict, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(
        ticket_id=data["ticket_id"]
    ).first()

    ambulance = db.query(AmbulanceDB).filter_by(
        ambulance_id=data["ambulance_id"]
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    if not ambulance:
        raise HTTPException(status_code=404, detail="ambulance not found")

    if ambulance.current_ticket:
        raise HTTPException(status_code=400, detail="ambulance already busy")

    ticket.ambulance_id = ambulance.ambulance_id
    ticket.status = "AMBULANCE_ASSIGNED"

    ambulance.status = "BUSY"
    ambulance.current_ticket = ticket.ticket_id

    db.commit()

    return {"message": "ticket assigned"}


# -------------------------
# SELECT HOSPITAL
# -------------------------
@router.post("/ambulances/select_hospital")
def select_hospital(data: dict, db: Session = Depends(get_db)):

    ticket = db.query(TicketDB).filter_by(
        ticket_id=data["ticket_id"]
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    ambulance = db.query(AmbulanceDB).filter_by(
        ambulance_id=ticket.ambulance_id
    ).first()

    if not ambulance:
        raise HTTPException(status_code=404, detail="ambulance not assigned")

    from app.storage import hospitals

    hospital = next(
        (h for h in hospitals if h["hospital_id"] == data["hospital_id"]),
        None
    )

    if not hospital:
        raise HTTPException(status_code=404, detail="hospital not found")

    distance = calculate_distance(
        ambulance.latitude,
        ambulance.longitude,
        hospital["latitude"],
        hospital["longitude"]
    )

    speed = 0.005
    eta = int(distance / speed)

    ticket.hospital_id = hospital["hospital_id"]
    ticket.status = "HOSPITAL_PENDING"
    ticket.eta_minutes = eta

    db.commit()

    return {
        "message": "hospital selected",
        "eta_minutes": eta
    }


# -------------------------
# GET ALL AMBULANCES
# -------------------------
@router.get("/ambulances")
def get_ambulances(db: Session = Depends(get_db)):
    return db.query(AmbulanceDB).all()