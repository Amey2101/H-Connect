from fastapi import APIRouter
from app.storage import hospitals,tickets
from app.utils import calculate_distance

router = APIRouter()


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
            "distance_km": round(distance,2)
        })

    results.sort(key=lambda x: x["distance_km"])

    return results

@router.post("/hospital/accept_ticket")
def accept_ticket(data: dict):

    ticket_id = data["ticket_id"]

    if ticket_id not in tickets:
        return {"error": "ticket not found"}

    ticket = tickets[ticket_id]
    
    ticket.hospital_id = data["hospital_id"]
    ticket.status = "HOSPITAL_ACCEPTED"

    return {"message": "hospital accepted case"}

@router.post("/hospital/reject_ticket")
def reject_ticket(data: dict):

    ticket_id = data["ticket_id"]
    reason = data["reason"]

    if ticket_id not in tickets:
        return {"error": "ticket not found"}

    ticket = tickets[ticket_id]

    ticket.status = "HOSPITAL_REJECTED"
    ticket.rejection_reason = reason

    return {"message": "hospital rejected case"}