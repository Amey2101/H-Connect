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
# UPDATE LOCATION + MOVEMENT ENGINE
# -------------------------
@router.post("/ambulances/location")
async def update_location(data: dict, db: Session = Depends(get_db)):

    ambulance = db.query(AmbulanceDB).filter_by(
        ambulance_id=data["ambulance_id"]
    ).first()

    if not ambulance:
        raise HTTPException(status_code=404, detail="ambulance not registered")

    # -------------------------
    # FIND ACTIVE TICKET
    # -------------------------
    ticket = None

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
    # FIND HOSPITAL
    # -------------------------
    hospital = None

    if ticket and ticket.hospital_id:
        from app.storage import hospitals

        hospital = next(
            (h for h in hospitals if h["hospital_id"] == ticket.hospital_id),
            None
        )
    print("==== MOVEMENT DEBUG ====")
    print("ticket:", ticket.ticket_id if ticket else None)
    print("ticket status:", ticket.status if ticket else None)
    print("hospital:", hospital)
    print("ambulance:", ambulance.ambulance_id)
    print("========================")
    # -------------------------
    # MOVEMENT + ARRIVAL LOGIC
    # -------------------------
    if hospital and ticket and ticket.status == "HOSPITAL_ACCEPTED":

        print("MOVEMENT BLOCK ENTERED")

        distance = calculate_distance(
            ambulance.latitude,
            ambulance.longitude,
            hospital["latitude"],
            hospital["longitude"]
        )

        print("========== DISTANCE DEBUG ==========")
        print("Ambulance:", ambulance.ambulance_id)
        print("Current :", ambulance.latitude, ambulance.longitude)
        print("Hospital:", hospital["hospital_id"])
        print("Target  :", hospital["latitude"], hospital["longitude"])
        print("Distance:", distance)
        print("====================================")

        print(
        ambulance.latitude,
        ambulance.longitude,
        "->",
        hospital["latitude"],
        hospital["longitude"]
        )

        # 🚨 ARRIVAL CONDITION
        if distance < 0.05:   # ~50 meters
            print("ARRIVED! Distance =", distance)
            ambulance.latitude = hospital["latitude"]
            ambulance.longitude = hospital["longitude"]

            ticket.status = "ARRIVED"
            ambulance.status = "AVAILABLE"
            ambulance.current_ticket = None

        else:
            # 🚑 MOVE TOWARDS HOSPITAL
            step = 0.05

            ambulance.latitude += (hospital["latitude"] - ambulance.latitude) * step
            ambulance.longitude += (hospital["longitude"] - ambulance.longitude) * step

            ambulance.status = "BUSY"

    else:
        # 🟢 Allow simulator updates only if NOT BUSY
        if ambulance.status != "BUSY":
            ambulance.latitude = data["latitude"]
            ambulance.longitude = data["longitude"]
    
    
    
    db.commit()

    # -------------------------
    # CALCULATE ETA
    # -------------------------
    eta = None

    if hospital:
        distance = calculate_distance(
            ambulance.latitude,
            ambulance.longitude,
            hospital["latitude"],
            hospital["longitude"]
        )

        speed = 0.01
        eta = max(1, int(distance / speed))

    # -------------------------
    # SEND WEBSOCKET UPDATE
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

    speed = 0.01
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

# -------------------------
# RESET SYSTEM
# -------------------------
@router.post("/system/reset")
def reset_system(db: Session = Depends(get_db)):

    ambulances = db.query(AmbulanceDB).all()
    for amb in ambulances:
        amb.status = "AVAILABLE"
        amb.current_ticket = None

    db.query(TicketDB).delete()

    db.commit()

    return {"message": "system reset complete"}


# -------------------------
# RESET ONLY AMBULANCES
# -------------------------
@router.post("/ambulances/reset")
def reset_ambulances(db: Session = Depends(get_db)):

    ambulances = db.query(AmbulanceDB).all()

    for amb in ambulances:
        amb.status = "AVAILABLE"
        amb.current_ticket = None

    db.commit()

    return {"message": "ambulances reset"}


# -------------------------
# RESET ONLY TICKETS
# -------------------------
@router.post("/tickets/reset")
def reset_tickets(db: Session = Depends(get_db)):

    db.query(TicketDB).delete()
    db.commit()

    return {"message": "all tickets cleared"}