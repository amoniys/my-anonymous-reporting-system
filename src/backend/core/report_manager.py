import asyncio
import logging
from ..modules.submission import SubmissionModule
from ..modules.verification import VerificationModule
from ..modules.storage import StorageModule
from ..modules.abuse_control import AbuseControlModule

logger = logging.getLogger(__name__)

class ReportManager:
    def __init__(self):
        self.abuse_control = AbuseControlModule()
        self.submission_module = SubmissionModule(self.abuse_control)
        self.verification_module = VerificationModule()
        self.storage_module = StorageModule()

    async def handle_full_report_flow(self, reporter_id: str, reported_message: str, context: str, server_public_keys: list, receiver_shared_key: str):
        try:
            # 1. Submit
            report_data = self.submission_module.submit_report(reporter_id, reported_message, context, server_public_keys)

            # 2. Verify (现在是异步的，会推送结果)
            verification_result = await self.verification_module.verify_report(report_data, receiver_shared_key)

            # 3. Store
            stored_report = await self.storage_module.store_report(report_data, verification_result)

            # 4. If verified, trigger AI review (placeholder)
            if verification_result["is_valid"]:
                stored_report["status"] = "SUBMITTED_TO_AI"
                logger.info(f"Report {stored_report['id']} submitted to AI for content analysis.")
                # Here you would call your ML model
                # ai_result = await self.run_ai_model(report_data["raw_report_data"], verification_result["message_content"])
                # stored_report.update(ai_result)
                # stored_report["status"] = "AI_REVIEWED"

            return stored_report
        except Exception as e:
            logger.error(f"Full report flow failed: {e}")
            return {"error": str(e)}

    def get_all_reports(self):
        return self.storage_module.reports_db

    def register_client(self, name: str):
        client = self.submission_module.register_client(name)
        self.storage_module.add_client_to_db(client)
        return client