from bs4 import BeautifulSoup


SOCIAL_DOMAINS = {
    "linkedin.com": "linkedin_url",
    "facebook.com": "facebook_url",
    "instagram.com": "instagram_url",
    "youtube.com": "youtube_url",
    "youtu.be": "youtube_url",
    "twitter.com": "twitter_url",
    "x.com": "twitter_url",
}


def _match_field(url: str) -> str | None:
    lowered = url.lower()

    for domain, field in SOCIAL_DOMAINS.items():
        if domain in lowered:
            return field

    return None


def extract_social_links(html: str) -> dict[str, str]:
    """Returns at most one URL per platform (field -> url), taken from
    the first matching anchor found. Not a general link crawl - just
    the well-known public profile domains."""
    soup = BeautifulSoup(html, "lxml")

    found: dict[str, str] = {}

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if not href:
            continue

        field = _match_field(href)

        if field and field not in found:
            found[field] = href

    return found
