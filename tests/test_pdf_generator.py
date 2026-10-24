"""src/pdf_generator.py: Typst -> PDF derleme."""
import pytest

MINIMAL = "#set page(margin: 1cm)\n\nMerhaba *dunya*.\n"


def test_compiles_minimal_typst(tmp_path):
    from src.pdf_generator import render_pdf

    pdf = tmp_path / "out.pdf"
    render_pdf(MINIMAL, str(pdf))
    assert pdf.exists()
    assert pdf.stat().st_size > 0
    assert pdf.read_bytes().startswith(b"%PDF")
    # .typ kaynagi da yazilmis olmali
    typ = pdf.with_suffix(".typ")
    assert typ.exists() and typ.read_text(encoding="utf-8") == MINIMAL


def test_unicode_content_compiles(tmp_path):
    from src.pdf_generator import render_pdf

    pdf = tmp_path / "tr.pdf"
    render_pdf("#set page(margin: 1cm)\n\nİş Zekası ve Veri Mühendisliği\n", str(pdf))
    assert pdf.exists() and pdf.stat().st_size > 0


def test_invalid_typst_raises(tmp_path):
    from src.pdf_generator import render_pdf

    with pytest.raises(Exception):
        render_pdf("#work(title: \"x\"", str(tmp_path / "bad.pdf"))
