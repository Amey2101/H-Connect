from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from app.routes import tickets, ambulances, hospitals
from app.websocket_manager import clients

app = FastAPI()

app.include_router(hospitals.router)
app.include_router(tickets.router)
app.include_router(ambulances.router)

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