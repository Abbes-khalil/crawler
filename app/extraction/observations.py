from bs4 import BeautifulSoup

from app.extraction.contact_links import extract_contact_links
from app.extraction.emails import extract_emails
from app.extraction.phones import extract_phones
from app.models.observation import Observation


EMAIL_LINK_CONFIDENCE = 1.0
PHONE_LINK_CONFIDENCE = 1.0
EMAIL_TEXT_CONFIDENCE = 0.7
PHONE_TEXT_CONFIDENCE = 0.4


def _normalize_email(raw: str) -> str:
    return raw.strip().lower()


def _normalize_link_phone(raw: str) -> str | None:
    """Normalize only when unambiguous: a tel: link with an explicit
    leading '+' can be safely stripped of formatting. Anything else is
    left as raw text rather than guessing a country code."""
    stripped = raw.strip()

    if not stripped.startswith("+"):
        return None

    digits = "".join(ch for ch in stripped if ch.isdigit())

    if len(digits) < 8:
        return None

    return f"+{digits}"


def build_page_observations(
    html: str,
    source_url: str,
) -> list[Observation]:
    observations: list[Observation] = []

    link_emails, link_phones = extract_contact_links(html)

    seen_emails: set[str] = set()
    seen_phones: set[str] = set()

    for raw_email in link_emails:
        normalized = _normalize_email(raw_email)
        seen_emails.add(normalized)

        observations.append(
            Observation(
                field="email",
                raw_value=raw_email,
                normalized_value=normalized,
                source_url=source_url,
                source_type="mailto_link",
                confidence=EMAIL_LINK_CONFIDENCE,
            )
        )

    for raw_phone in link_phones:
        seen_phones.add(raw_phone.strip())

        observations.append(
            Observation(
                field="phone",
                raw_value=raw_phone,
                normalized_value=_normalize_link_phone(raw_phone),
                source_url=source_url,
                source_type="tel_link",
                confidence=PHONE_LINK_CONFIDENCE,
            )
        )

    soup = BeautifulSoup(html, "lxml")
    visible_text = soup.get_text(" ", strip=True)

    for raw_email in extract_emails(visible_text):
        normalized = _normalize_email(raw_email)

        if normalized in seen_emails:
            continue

        seen_emails.add(normalized)

        observations.append(
            Observation(
                field="email",
                raw_value=raw_email,
                normalized_value=normalized,
                source_url=source_url,
                source_type="visible_text",
                confidence=EMAIL_TEXT_CONFIDENCE,
            )
        )

    for raw_phone in extract_phones(visible_text):
        if raw_phone.strip() in seen_phones:
            continue

        seen_phones.add(raw_phone.strip())

        observations.append(
            Observation(
                field="phone",
                raw_value=raw_phone,
                # Regex matches on free text can truncate a larger
                # international number, so never invent a normalized
                # value here - preserve raw only.
                normalized_value=None,
                source_url=source_url,
                source_type="visible_text",
                confidence=PHONE_TEXT_CONFIDENCE,
            )
        )

    return observations
