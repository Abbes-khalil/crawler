from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


IGNORED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".zip",
    ".rar",
    ".mp4",
    ".mp3",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
)


def clean_url(url: str) -> str:
    parsed = urlparse(url)

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            "",
            "",
            "",
        )
    )


def discover_internal_links(
    html: str,
    base_url: str,
) -> list[str]:

    soup = BeautifulSoup(html, "lxml")

    base_domain = urlparse(base_url).netloc.lower()

    urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if not href:
            continue

        if href.startswith(
            (
                "#",
                "mailto:",
                "tel:",
                "javascript:",
            )
        ):
            continue

        absolute_url = urljoin(base_url, href)

        parsed = urlparse(absolute_url)

        if parsed.scheme not in ("http", "https"):
            continue

        if parsed.netloc.lower() != base_domain:
            continue

        if parsed.path.lower().endswith(IGNORED_EXTENSIONS):
            continue

        clean = clean_url(absolute_url)

        if clean:
            urls.add(clean)

    return sorted(urls)