from bs4 import BeautifulSoup


def extract_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    if not soup.title:
        return None

    return soup.title.get_text(
        " ",
        strip=True,
    )


def extract_meta_description(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    tag = soup.find("meta", attrs={"name": "description"})

    if not tag:
        tag = soup.find("meta", attrs={"property": "og:description"})

    if not tag:
        return None

    content = tag.get("content")

    if not content:
        return None

    content = content.strip()

    return content or None


def extract_language(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    html_tag = soup.find("html")

    if not html_tag:
        return None

    lang = html_tag.get("lang")

    if not lang:
        return None

    return lang.strip().split("-")[0].lower() or None
