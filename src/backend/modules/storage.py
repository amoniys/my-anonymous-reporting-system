import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from ..models.client import ClientEntity

logger = logging.getLogger(__name__)

class StorageModule:
    def __init__(self):
        self.reports_db: List[Dict] = []
        self.clients_db: List[ClientEntity] = []

    async def store_report(self, report_data: dict, verification_result: dict):
        stored_report = {
            "id": f"report_{len(self.reports_db) + 1}",
            "timestamp": datetime.now().isoformat(),
            "raw_report_data": report_data,
            "verification_result": verification_result,
            "status": "PENDING_AI_REVIEW" if verification_result["is_valid"] else "REJECTED_INVALID_FRANKING",
        }
        self.reports_db.append(stored_report)
        logger.info(f"Stored report {stored_report['id']} in database.")
        return stored_report

    async def get_all_reports(self) -> List[Dict]:
        await asyncio.sleep(0.1) # Simulate I/O
        return self.reports_db

    def add_client_to_db(self, client: ClientEntity):
        self.clients_db.append(client)