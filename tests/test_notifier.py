"""src/notifier.py: Telegram ve bildirim yoneticisi (ag mock'lu)."""
class FakeResponse:
    def __init__(self, ok=True):
        self.ok = ok

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError("http error")


class FakeNotifier:
    def __init__(self, result=True):
        self.result = result
        self.messages = []

    def send_notification(self, message):
        self.messages.append(message)
        return self.result


def test_telegram_missing_credentials(monkeypatch):
    import src.notifier as notifier

    monkeypatch.setenv("TELEGRAM_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "")
    tg = notifier.TelegramNotifier()
    assert tg.send_notification("mesaj") is False


def test_telegram_sends_successfully(monkeypatch):
    import src.notifier as notifier

    monkeypatch.setenv("TELEGRAM_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse(ok=True)

    monkeypatch.setattr(notifier.requests, "post", fake_post)
    tg = notifier.TelegramNotifier()
    assert tg.send_notification("merhaba") is True
    assert calls and calls[0][1]["text"] == "merhaba"
    assert "token" in calls[0][0]


def test_telegram_http_error_returns_false(monkeypatch):
    import src.notifier as notifier

    monkeypatch.setenv("TELEGRAM_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    monkeypatch.setattr(
        notifier.requests, "post", lambda *a, **k: FakeResponse(ok=False)
    )
    assert notifier.TelegramNotifier().send_notification("x") is False


def test_manager_formats_message_and_returns_true():
    from src.notifier import NotificationManager

    manager = NotificationManager()
    manager.notifiers = []
    fake = FakeNotifier(result=True)
    manager.add_notifier(fake)
    assert manager.notify_suitable_job("Data Engineer", "ACME", "https://x") is True
    message = fake.messages[0]
    assert "Data Engineer" in message and "ACME" in message and "https://x" in message


def test_manager_without_notifiers_returns_false():
    from src.notifier import NotificationManager

    manager = NotificationManager()
    manager.notifiers = []
    assert manager.notify_suitable_job("t", "c", "u") is False
