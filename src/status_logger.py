import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StatusLogger:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.log_file = data_dir / "status_logs.json"
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Creates the log file if it doesn't exist."""
        if not self.log_file.exists():
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"Failed to create status log file: {e}")

    def load_logs(self) -> List[Dict]:
        """Loads existing logs."""
        try:
            if not self.log_file.exists():
                return []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load status logs: {e}")
            return []

    def save_logs(self, logs: List[Dict]):
        """Saves logs to file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save status logs: {e}")

    def log_status_change(self, job_url: str, old_status: str, new_status: str):
        """
        Logs a status change event.
        
        Args:
            job_url: The URL of the job application.
            old_status: The previous status.
            new_status: The new status.
        """
        if old_status == new_status:
            return

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'job_url': job_url,
            'old_status': old_status,
            'new_status': new_status
        }
        
        logs = self.load_logs()
        logs.append(log_entry)
        self.save_logs(logs)
        logger.info(f"Logged status change for {job_url}: {old_status} -> {new_status}")
