from pathlib import Path

from app.extraction.observations import build_page_observations


FIXTURES = Path(__file__).parent.parent / "fixtures"


def _contact_html() -> str:
    return (FIXTURES / "contact.html").read_text(encoding="utf-8")


def test_mailto_link_produces_high_confidence_email_observation():
    observations = build_page_observations(
        _contact_html(), "https://acme-industrial.example/contact"
    )

    email_obs = [o for o in observations if o.field == "email"]
    mailto_obs = [o for o in email_obs if o.source_type == "mailto_link"]

    assert mailto_obs
    assert mailto_obs[0].confidence == 1.0
    assert mailto_obs[0].normalized_value == "sales@acme-industrial.example"


def test_tel_link_preserves_raw_value_and_does_not_invent_country_code():
    observations = build_page_observations(
        _contact_html(), "https://acme-industrial.example/contact"
    )

    tel_obs = [o for o in observations if o.source_type == "tel_link"]

    assert tel_obs
    assert tel_obs[0].raw_value == "+33607386963"
    assert tel_obs[0].normalized_value == "+33607386963"


def test_visible_text_phone_fallback_has_no_normalized_value():
    observations = build_page_observations(
        _contact_html(), "https://acme-industrial.example/contact"
    )

    text_phone_obs = [
        o
        for o in observations
        if o.field == "phone" and o.source_type == "visible_text"
    ]

    for obs in text_phone_obs:
        assert obs.normalized_value is None
        assert obs.confidence < 1.0


def test_same_value_not_duplicated_within_page():
    observations = build_page_observations(
        _contact_html(), "https://acme-industrial.example/contact"
    )

    values = [
        (o.field, o.normalized_value or o.raw_value) for o in observations
    ]

    assert len(values) == len(set(values))
