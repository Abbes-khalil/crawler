import hashlib

import trafilatura


def extract_clean_text(html: str) -> str:
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
    )

    return text or ""


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
