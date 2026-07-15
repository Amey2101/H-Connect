from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routes import tickets, ambulances, hospitals, ai
from app.websocket_manager import clients

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(hospitals.router)
app.include_router(tickets.router)
app.include_router(ambulances.router)
app.include_router(ai.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("🔥 WS HIT")   # ADD THIS

    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        clients.remove(websocket)