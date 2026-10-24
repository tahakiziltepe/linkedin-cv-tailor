"""Opt-in canli testler: gercek Gemini API cagrisi yapar.

Calistirma: make test-live   (RUN_LIVE_TESTS=1 gerekir)
Varsayilan `make test` bu dosyayi calistirmaz.
"""
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.live

RUN = os.environ.get("RUN_LIVE_TESTS") == "1"


@pytest.mark.skipif(not RUN, reason="RUN_LIVE_TESTS=1 gerekli")
def test_live_suitability_tailor_and_compile(tmp_path):
    import src.cv_tailor as ct

    if not ct.client:
        pytest.skip("GEMINI_API_KEY yok")

    description = (
        "Data Engineer. SQL, ETL, BigQuery, Python ve veri modelleme deneyimi "
        "beklenir. Veri ambari ve raporlama sureclerinde calisacak."
    )
    assert ct.check_job_suitability(description) is True

    base = (ROOT / "templates" / "base_cv.example.typ").read_text(encoding="utf-8")
    tailored = ct.tailor_cv(base, description)
    assert tailored and tailored.strip()
    assert "{{" not in tailored

    from src.pdf_generator import render_pdf

    pdf = tmp_path / "live.pdf"
    render_pdf(tailored, str(pdf))
    assert pdf.exists() and pdf.stat().st_size > 0
