from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
from .core.report_manager import ReportManager
from .core.ws_manager import manager # 导入管理器
from .core.onion_franking import generate_server_keys

# --- Application Setup ---
print("Starting Anonymous Reporting System...")
print("- Open your browser to http://127.0.0.1:8000")
print("- The system includes 4 modules: Submission, Verification, Storage, Abuse Control.")
print("- A WebSocket endpoint at /ws provides live updates.")
print("- An AI review endpoint is available at /api/v1/ai_review for model integration.")

app = FastAPI(title="Anonymous Reporting System API")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# --- System Initialization ---
server_public_keys, _ = generate_server_keys()
report_manager = ReportManager()

# Register initial clients (Alice and Bob)
alice = report_manager.register_client("Alice")
bob = report_manager.register_client("Bob")
clients = [alice, bob]

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 等待消息，如果客户端没有发送任何消息，此循环会一直阻塞
            data = await websocket.receive_text()
            # 如果需要处理客户端发来的命令，可以在这里添加逻辑
            # 例如: await manager.send_personal_message({"msg": "Command received"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- API Endpoints ---
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "clients": clients,
        "server_public_keys": server_public_keys
    })

@app.post("/api/v1/report")
async def submit_report(report_data: dict):
    # 使用 .get(key, "") 为缺失的键提供一个空字符串作为默认值
    reporter_id = report_data.get("reporter_id") or ""
    reported_message = report_data.get("reported_message") or ""
    context = report_data.get("context") or ""

    if not all([reporter_id, reported_message, context]):
        return {"error": "Missing required fields"}

    # 此时，reporter_id, reported_message, context 的类型都是 str
    receiver_shared_key = alice.shared_key_with_receiver # 假设消息是发给Alice的

    result = await report_manager.handle_full_report_flow(
        reporter_id, reported_message, context, server_public_keys, receiver_shared_key
    )
    return result

@app.get("/api/v1/reports")
async def get_reports():
    reports = report_manager.get_all_reports()
    return {"reports": reports}

# --- Run the Server ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)