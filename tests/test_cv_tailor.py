"""src/cv_tailor.py: Gemini cagrilari mock'lanarak davranis testleri."""
import pytest


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return FakeResponse(self.text)


class FakeClient:
    def __init__(self, text=None, error=None):
        self.models = FakeModels(text, error)


@pytest.fixture
def ct(monkeypatch):
    import src.cv_tailor as module

    monkeypatch.setattr(module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(module, "client", None)
    return module


def test_no_client_failsafe(ct):
    assert ct.check_job_suitability("ilan") is True
    assert ct.tailor_cv("cv", "ilan") == "cv"
    assert ct.fix_typst_code("kod", "hata") == "kod"


@pytest.mark.parametrize(
    ("answer", "expected"),
    [("YES", True), ("yes", True), ("NO", False), ("no", False), ("YES ekstra", True)],
)
def test_suitability_parsing(ct, monkeypatch, answer, expected):
    monkeypatch.setattr(ct, "client", FakeClient(answer))
    assert ct.check_job_suitability("ilan") is expected


def test_suitability_prompt_comes_from_file(ct, monkeypatch):
    fake = FakeClient("YES")
    monkeypatch.setattr(ct, "client", fake)
    ct.check_job_suitability("BENZERSIZ ILAN METNI")
    contents = fake.models.calls[0]["contents"]
    assert "BENZERSIZ ILAN METNI" in contents
    assert "{{" not in contents


def test_suitability_error_returns_true(ct, monkeypatch):
    monkeypatch.setattr(ct, "client", FakeClient(error=RuntimeError("boom")))
    assert ct.check_job_suitability("ilan") is True


def test_tailor_returns_model_text(ct, monkeypatch):
    monkeypatch.setattr(ct, "client", FakeClient("uyarlanmis cv"))
    assert ct.tailor_cv("base cv", "ilan") == "uyarlanmis cv"


def test_tailor_prompt_contains_inputs(ct, monkeypatch):
    fake = FakeClient("x")
    monkeypatch.setattr(ct, "client", fake)
    ct.tailor_cv("BASE-CV-METNI", "ILAN-METNI")
    contents = fake.models.calls[0]["contents"]
    assert "BASE-CV-METNI" in contents and "ILAN-METNI" in contents
    assert "{{" not in contents


def test_tailor_strips_markdown_fence(ct, monkeypatch):
    monkeypatch.setattr(ct, "client", FakeClient("```typst\n#set page()\n```"))
    assert ct.tailor_cv("base", "ilan") == "#set page()"


def test_tailor_error_returns_base(ct, monkeypatch):
    monkeypatch.setattr(ct, "client", FakeClient(error=RuntimeError("boom")))
    assert ct.tailor_cv("base cv", "ilan") == "base cv"


def test_fix_typst_returns_fixed_code(ct, monkeypatch):
    monkeypatch.setattr(ct, "client", FakeClient("duzeltilmis kod"))
    assert ct.fix_typst_code("bozuk", "hata") == "duzeltilmis kod"


def test_fix_typst_prompt_contains_error(ct, monkeypatch):
    fake = FakeClient("x")
    monkeypatch.setattr(ct, "client", fake)
    ct.fix_typst_code("BOZUK-KOD", "HATA-MESAJI")
    contents = fake.models.calls[0]["contents"]
    assert "BOZUK-KOD" in contents and "HATA-MESAJI" in contents
    assert "{{" not in contents


def test_fix_typst_error_returns_none(ct, monkeypatch):
    monkeypatch.setattr(ct, "client", FakeClient(error=RuntimeError("boom")))
    assert ct.fix_typst_code("bozuk", "hata") is None
