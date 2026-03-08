from fastapi import WebSocket
from typing import List, Dict, Any # 1. 确保导入了 Any
import logging

logger = logging.getLogger(__name__)

class WSManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # 这里可以扩展为一个字典，以用户ID为键，存储特定用户的连接
        # self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    # 2. 将类型注释中的 'any' 改为 'Any'
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)

    # 3. 将类型注释中的 'any' 改为 'Any'
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message to {connection}: {e}")
                self.disconnect(connection)

# 实例化一个全局管理器
manager = WSManager()