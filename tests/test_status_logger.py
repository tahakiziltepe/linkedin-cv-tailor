"""src/status_logger.py: durum degisikligi jurnali."""
def test_init_creates_file(tmp_path):
    from src.status_logger import StatusLogger

    logger = StatusLogger(tmp_path)
    assert logger.log_file.exists()
    assert logger.load_logs() == []


def test_log_status_change_appends(tmp_path):
    from src.status_logger import StatusLogger

    logger = StatusLogger(tmp_path)
    logger.log_status_change("u1", "Pending", "Applied")
    logs = logger.load_logs()
    assert len(logs) == 1
    assert logs[0]["job_url"] == "u1"
    assert logs[0]["old_status"] == "Pending"
    assert logs[0]["new_status"] == "Applied"
    assert "T" in logs[0]["timestamp"]


def test_same_status_not_logged(tmp_path):
    from src.status_logger import StatusLogger

    logger = StatusLogger(tmp_path)
    logger.log_status_change("u1", "Applied", "Applied")
    assert logger.load_logs() == []


def test_corrupt_log_returns_empty(tmp_path):
    from src.status_logger import StatusLogger

    logger = StatusLogger(tmp_path)
    logger.log_file.write_text("bozuk", encoding="utf-8")
    assert logger.load_logs() == []
