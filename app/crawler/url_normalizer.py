from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or "/"

    normalized = urlunparse(
        (
            scheme,
            netloc,
            path,
            "",
            "",
            "",
        )
    )

    return normalized.rstrip("/")