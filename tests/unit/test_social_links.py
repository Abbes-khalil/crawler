from app.extraction.social_links import extract_social_links


HTML = """
<html><body>
<a href="https://www.linkedin.com/company/acme-industrial">LinkedIn</a>
<a href="https://facebook.com/acmeindustrial">Facebook</a>
<a href="https://instagram.com/acme">Instagram</a>
<a href="https://www.youtube.com/@acme">YouTube</a>
<a href="https://example.com/not-social">Other</a>
</body></html>
"""


def test_extracts_known_platforms():
    links = extract_social_links(HTML)

    assert links["linkedin_url"] == "https://www.linkedin.com/company/acme-industrial"
    assert links["facebook_url"] == "https://facebook.com/acmeindustrial"
    assert links["instagram_url"] == "https://instagram.com/acme"
    assert links["youtube_url"] == "https://www.youtube.com/@acme"


def test_ignores_unrelated_links():
    links = extract_social_links(HTML)
    assert "twitter_url" not in links


def test_no_social_links_returns_empty_dict():
    assert extract_social_links("<html><body>none</body></html>") == {}
