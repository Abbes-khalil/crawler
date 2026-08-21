from app.extraction.jsonld import extract_organization_facts


ORG_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Industrial",
  "email": "info@acme-industrial.example",
  "telephone": "+33607386963",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "12 rue de la Paix",
    "addressLocality": "Paris",
    "postalCode": "75002",
    "addressCountry": "FR"
  },
  "sameAs": ["https://www.linkedin.com/company/acme-industrial"]
}
</script>
</head><body></body></html>
"""

GRAPH_HTML = """
<html><head>
<script type="application/ld+json">
{"@graph": [
  {"@type": "WebSite", "name": "Should be ignored"},
  {"@type": "LocalBusiness", "name": "Acme Local", "telephone": "+33100000000"}
]}
</script>
</head><body></body></html>
"""

INVALID_HTML = """
<html><head>
<script type="application/ld+json">{ not valid json </script>
</head><body></body></html>
"""


def test_extracts_organization_fields():
    facts = extract_organization_facts(ORG_HTML)

    assert facts["name"] == "Acme Industrial"
    assert facts["email"] == "info@acme-industrial.example"
    assert facts["telephone"] == "+33607386963"
    assert facts["address"]["city"] == "Paris"
    assert "https://www.linkedin.com/company/acme-industrial" in facts["same_as"]


def test_handles_graph_wrapper_and_ignores_non_organization_types():
    facts = extract_organization_facts(GRAPH_HTML)

    assert facts["name"] == "Acme Local"
    assert facts["telephone"] == "+33100000000"


def test_invalid_json_ld_does_not_raise():
    assert extract_organization_facts(INVALID_HTML) == {}


def test_no_json_ld_returns_empty_dict():
    assert extract_organization_facts("<html><body>none</body></html>") == {}
