import os
import logging
from abc import ABC, abstractmethod
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BaseNotifier(ABC):
    """Abstract base class for all notification providers."""
    
    @abstractmethod
    def send_notification(self, message: str) -> bool:
        """Send a notification message. Must be implemented by subclasses."""
        pass

class TelegramNotifier(BaseNotifier):
    """Telegram notification provider."""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not found in environment variables.")

    def send_notification(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            logger.error("Cannot send Telegram notification: Missing credentials.")
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

class NotificationManager:
    """Manages multiple notification providers and sends notifications to all of them."""
    
    def __init__(self):
        self.notifiers = []
        
        # Initialize default notifiers
        if os.getenv("TELEGRAM_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            self.add_notifier(TelegramNotifier())
            
    def add_notifier(self, notifier: BaseNotifier):
        self.notifiers.append(notifier)
        
    def notify_suitable_job(self, job_title: str, company: str, url: str):
        """Send a formatted notification for a suitable job."""
        message = (
            f"🎯 <b>Yeni Uygun İlan Bulundu!</b>\n\n"
            f"<b>Pozisyon:</b> {job_title}\n"
            f"<b>Şirket:</b> {company}\n"
            f"<b>İlan Linki:</b> {url}"
        )
        
        success_count = 0
        for notifier in self.notifiers:
            if notifier.send_notification(message):
                success_count += 1
                
        return success_count > 0

# Singleton instance for easy usage
notifier = NotificationManager()
