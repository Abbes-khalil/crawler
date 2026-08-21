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


JSON_LD_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@type": "Organization",
  "name": "Acme Industrial",
  "email": "info@acme-industrial.example",
  "telephone": "+33607386963",
  "address": {"addressLocality": "Paris", "addressCountry": "FR"},
  "sameAs": ["https://www.linkedin.com/company/acme-industrial"]
}
</script>
</head><body>
<a href="https://www.linkedin.com/company/acme-industrial">LinkedIn</a>
</body></html>
"""


def test_json_ld_organization_produces_high_confidence_observations():
    observations = build_page_observations(
        JSON_LD_HTML, "https://acme-industrial.example"
    )

    by_field = {o.field: o for o in observations if o.source_type == "json_ld"}

    assert by_field["organization_name"].raw_value == "Acme Industrial"
    assert by_field["email"].normalized_value == "info@acme-industrial.example"
    assert by_field["phone"].normalized_value == "+33607386963"
    assert by_field["city"].raw_value == "Paris"
    assert by_field["email"].confidence >= 0.9
    assert by_field["phone"].confidence >= 0.9


def test_social_links_are_captured_as_observations():
    observations = build_page_observations(
        JSON_LD_HTML, "https://acme-industrial.example"
    )

    linkedin_obs = [o for o in observations if o.field == "linkedin_url"]

    assert linkedin_obs
    assert linkedin_obs[0].source_type == "social_link"
    assert linkedin_obs[0].confidence == 1.0


def test_json_ld_email_not_duplicated_with_link_extraction():
    html = JSON_LD_HTML.replace(
        '<a href="https://www.linkedin.com/company/acme-industrial">LinkedIn</a>',
        '<a href="https://www.linkedin.com/company/acme-industrial">LinkedIn</a>'
        '<a href="mailto:info@acme-industrial.example">Email</a>',
    )

    observations = build_page_observations(html, "https://acme-industrial.example")

    email_values = [
        o.normalized_value
        for o in observations
        if o.field == "email"
        and o.normalized_value == "info@acme-industrial.example"
    ]

    assert len(email_values) == 1
