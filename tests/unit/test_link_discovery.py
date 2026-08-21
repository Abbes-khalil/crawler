from pathlib import Path

from app.crawler.link_discovery import discover_internal_links


FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_discover_internal_links_from_fixture():
    html = (FIXTURES / "homepage.html").read_text(encoding="utf-8")

    links = discover_internal_links(html, "https://acme-industrial.example")

    assert "https://acme-industrial.example/products" in links
    assert "https://acme-industrial.example/about-us" in links
    assert "https://acme-industrial.example/contact" in links


def test_ignores_mailto_tel_js_and_fragments():
    html = (FIXTURES / "homepage.html").read_text(encoding="utf-8")

    links = discover_internal_links(html, "https://acme-industrial.example")

    assert not any(link.startswith("mailto:") for link in links)
    assert not any(link.startswith("tel:") for link in links)
    assert not any(link.startswith("javascript:") for link in links)
    assert not any("#top" in link for link in links)


def test_ignores_external_domains_and_blocked_extensions():
    html = (FIXTURES / "homepage.html").read_text(encoding="utf-8")

    links = discover_internal_links(html, "https://acme-industrial.example")

    assert not any("external-site.example" in link for link in links)
    assert not any(link.endswith(".pdf") for link in links)
