from fastapi import APIRouter
from app.services.ai_service import generate_triage

router = APIRouter()

@router.post("/ai/triage")
def ai_triage(data: dict):

    return generate_triage(data)



