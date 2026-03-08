from typing import Dict
from fastapi import HTTPException
import logging
from ..core.onion_franking import OnionFrankingClient
from ..models.client import ClientEntity
from ..modules.abuse_control import AbuseControlModule

logger = logging.getLogger(__name__)

class SubmissionModule:
    def __init__(self, abuse_control: AbuseControlModule):
        self.clients: Dict[str, ClientEntity] = {}
        self.abuse_control = abuse_control

    def register_client(self, client_name: str) -> ClientEntity:
        client_id = f"client_{len(self.clients) + 1}"
        # 创建客户端实例，shared_key_with_receiver 将自动由模型生成
        client = ClientEntity(id=client_id, name=client_name)
        self.clients[client.id] = client
        logger.info(f"Registered client: {client}")
        return client

    def submit_report(self, reporter_id: str, reported_message: str, context: str, server_public_keys: list) -> dict:
        if not self.abuse_control.can_submit(reporter_id):
            raise HTTPException(status_code=429, detail="Too many reports from this user.")

        client = self.clients.get(reporter_id)
        if not client:
            raise HTTPException(status_code=404, detail="Reporter not found.")

        # 此时 client.shared_key_with_receiver 必定是一个有效的字符串
        of_client = OnionFrankingClient(client.id, bytes.fromhex(client.shared_key_with_receiver), server_public_keys)
        
        s, rs, c3_encrypted_payload = of_client.send_preprocessing(len(server_public_keys))
        c1_encrypted_msg, c2_commitment = of_client.send_online(reported_message, s, rs)

        report_data = {
            "reporter_id": reporter_id,
            "c1_encrypted_msg": c1_encrypted_msg.hex(),
            "c2_commitment": c2_commitment.hex(),
            "c3_encrypted_payload": c3_encrypted_payload.hex(),
            "context": context,
            "s_seed": s.hex(),
            "rs_randomness": rs.hex()
        }
        
        self.abuse_control.record_submission(reporter_id)
        logger.info(f"Report submitted by {reporter_id}. Context: {context}")
        return report_data