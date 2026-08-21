from pathlib import Path

from app.extraction.metadata import (
    extract_language,
    extract_meta_description,
    extract_title,
)


FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_extract_title():
    html = (FIXTURES / "homepage.html").read_text(encoding="utf-8")
    assert extract_title(html) == "Acme Industrial - Homepage"


def test_extract_meta_description():
    html = (FIXTURES / "homepage.html").read_text(encoding="utf-8")
    description = extract_meta_description(html)
    assert description is not None
    assert "precision components" in description


def test_extract_language():
    html = (FIXTURES / "homepage.html").read_text(encoding="utf-8")
    assert extract_language(html) == "en"


def test_missing_title_returns_none():
    assert extract_title("<html><body>No title</body></html>") is None


def test_missing_description_returns_none():
    assert extract_meta_description("<html><body>No meta</body></html>") is None
