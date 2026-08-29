from datetime import datetime, timezone

from app.formatting import to_markdown
from app.models.observation import Observation
from app.models.page import CrawledPage
from app.models.response import CrawlCompanyResponse, CrawlMetrics


def _obs(field: str, raw: str, *, url: str, conf: float = 1.0) -> Observation:
    return Observation(
        field=field,
        raw_value=raw,
        source_url=url,
        source_type="test",
        confidence=conf,
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _full_response() -> CrawlCompanyResponse:
    return CrawlCompanyResponse(
        status="SUCCESS",
        canonical_url="https://acme.example",
        pages_discovered=6,
        pages_selected=2,
        pages_crawled=2,
        pages_failed=0,
        pages=[
            CrawledPage(
                url="https://acme.example",
                title="Acme Industrial",
                text="We build industrial widgets since 1974.",
            ),
            CrawledPage(
                url="https://acme.example/contact",
                title="Contact Us",
                text="Reach the Acme team at our head office.",
            ),
        ],
        page_errors=[],
        observations=[
            _obs("email", "info@acme.example", url="https://acme.example/contact"),
            _obs(
                "email",
                "sales@acme.example",
                url="https://acme.example",
                conf=0.8,
            ),
            _obs("phone", "+1 555 0100", url="https://acme.example/contact"),
            _obs(
                "social",
                "https://linkedin.com/company/acme",
                url="https://acme.example",
            ),
        ],
        metrics=CrawlMetrics(duration_ms=4200, http_pages=2),
    )


def test_includes_header_with_url_and_status():
    md = to_markdown(_full_response())
    assert "https://acme.example" in md
    assert "SUCCESS" in md
    assert "2" in md  # pages crawled


def test_groups_observations_by_field():
    md = to_markdown(_full_response())
    assert "info@acme.example" in md
    assert "sales@acme.example" in md
    assert "+1 555 0100" in md
    assert "https://linkedin.com/company/acme" in md
    # each distinct field gets its own section heading
    for heading in ("Email", "Phone", "Social"):
        assert heading in md


def test_includes_page_text_and_titles():
    md = to_markdown(_full_response())
    assert "Acme Industrial" in md
    assert "industrial widgets since 1974" in md
    assert "Contact Us" in md


def test_observation_provenance_is_shown():
    md = to_markdown(_full_response())
    assert "https://acme.example/contact" in md


def test_empty_response_is_still_readable():
    empty = CrawlCompanyResponse(
        status="INVALID_URL",
        canonical_url="https://bad.example",
        pages_discovered=0,
        pages_selected=0,
        pages_crawled=0,
        pages_failed=0,
        pages=[],
        page_errors=[],
        observations=[],
        metrics=CrawlMetrics(duration_ms=12, http_pages=0),
    )
    md = to_markdown(empty)
    assert "https://bad.example" in md
    assert "INVALID_URL" in md
    # no crash, produces a non-trivial string
    assert len(md.strip()) > 20
