import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AbuseControlModule:
    def __init__(self, max_reports_per_window: int = 5, window_seconds: int = 60):
        self.max_reports = max_reports_per_window
        self.window = window_seconds
        self.submission_times = defaultdict(list)

    def can_submit(self, client_id: str) -> bool:
        now = time.time()
        times = self.submission_times[client_id]
        # Remove old submissions outside the window
        self.submission_times[client_id] = [t for t in times if now - t < self.window]
        current_count = len(self.submission_times[client_id])
        
        if current_count >= self.max_reports:
            logger.warning(f"Abuse detected: {client_id} exceeded limit ({current_count}/{self.max_reports}).")
            return False
        return True

    def record_submission(self, client_id: str):
        self.submission_times[client_id].append(time.time())