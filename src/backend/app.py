from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .config import settings
from .core.report_manager import ReportManager
from .modules.verification import VerificationModule
import asyncio
import json

app = FastAPI(title=settings.PROJECT_NAME)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

report_manager = ReportManager()
verification_module = VerificationModule()

# --- Demo Setup ---
server_public_keys_demo = [f"pubkey_server_{i}".encode() for i in range(settings.SERVER_COUNT)]
demo_clients = {}
for name in ["Alice", "Bob"]:
    client = report_manager.register_client(name)
    demo_clients[name] = client

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "clients": list(demo_clients.values())})

class SubmitReportRequest(BaseModel):
    reporter_id: str
    reported_message: str
    context: str

@app.post("/api/v1/report")
async def submit_report_endpoint(request: SubmitReportRequest):
    receiver_key = demo_clients["Bob"].shared_key_with_receiver
    report = await report_manager.handle_full_report_flow(
        reporter_id=request.reporter_id,
        reported_message=request.reported_message,
        context=request.context,
        server_public_keys=server_public_keys_demo,
        receiver_shared_key=receiver_key
    )
    return report

@app.get("/api/v1/reports")
async def get_reports():
    return report_manager.get_all_reports()

# WebSocket for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast new reports to all connected clients
            reports = report_manager.get_all_reports()
            await manager.broadcast(json.dumps({"type": "update_reports", "data": reports}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Placeholder for AI Model Integration
@app.post("/api/v1/ai_review")
async def ai_review_endpoint(payload: dict):
    """
    This endpoint is designed to receive data from the storage module.
    It simulates the integration point for your trained ML model.
    """
    message_content = payload.get("message_content", "")
    
    # --- SIMULATE YOUR ML MODEL HERE ---
    # For example: prediction = my_ml_model.predict(message_content)
    # For demo, we'll hardcode a result.
    is_content_violation = "violation" in message_content.lower() or "badword" in message_content.lower()
    severity_score = 0.9 if is_content_violation else 0.1

    return {
        "ai_prediction": "VIOLATION_FOUND" if is_content_violation else "CONTENT_OK",
        "severity_score": severity_score,
        "review_timestamp": asyncio.get_event_loop().time()
    }