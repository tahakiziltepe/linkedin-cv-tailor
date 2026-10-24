import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class JobTracker:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.history_file = data_dir / "job_history.json"
        self._ensure_history_file()

    def _ensure_history_file(self):
        if not self.history_file.exists():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def load_history(self) -> List[Dict]:
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load job history: {e}")
            return []

    def save_history(self, history: List[Dict]):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save job history: {e}")

    def job_exists(self, url: str) -> bool:
        """Checks if a job URL is already in the history."""
        history = self.load_history()
        return any(j.get('url') == url for j in history)

    def add_job(self, job_data: Dict):
        """
        Adds a job to the history.
        job_data should contain: company, title, url, pdf_path, timestamp
        """
        history = self.load_history()
        # check for duplicates based on URL
        if not any(j.get('url') == job_data.get('url') for j in history):
            job_data['status'] = job_data.get('status', 'Pending') # Default status
            job_data['notes'] = job_data.get('notes', '') # Default empty notes
            history.insert(0, job_data) # Add new jobs to the top
            self.save_history(history)
            logger.info(f"Job added to history: {job_data.get('url')}")
        else:
            logger.info(f"Job already tracked: {job_data.get('url')}")

    def delete_job(self, url: str) -> bool:
        """Removes a job from history based on URL."""
        history = self.load_history()
        initial_len = len(history)
        history = [j for j in history if j.get('url') != url]
        
        if len(history) < initial_len:
            self.save_history(history)
            logger.info(f"Deleted job from history: {url}")
            return True
        return False
