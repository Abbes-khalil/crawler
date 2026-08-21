import phonenumbers
from bs4 import BeautifulSoup

from app.extraction.addresses import extract_address_candidates
from app.extraction.contact_links import extract_contact_links
from app.extraction.emails import extract_emails
from app.extraction.jsonld import extract_organization_facts
from app.extraction.metadata import extract_opengraph
from app.extraction.phones import extract_phones
from app.extraction.social_links import extract_social_links
from app.models.observation import Observation


EMAIL_LINK_CONFIDENCE = 1.0
EMAIL_JSON_LD_CONFIDENCE = 0.95
EMAIL_TEXT_CONFIDENCE = 0.7

PHONE_LINK_CONFIDENCE = 1.0
PHONE_JSON_LD_CONFIDENCE = 0.95
PHONE_TEXT_CONFIDENCE = 0.4

NAME_JSON_LD_CONFIDENCE = 0.9
NAME_OPENGRAPH_CONFIDENCE = 0.6
ADDRESS_JSON_LD_CONFIDENCE = 0.9
ADDRESS_TEXT_CONFIDENCE = 0.4

SOCIAL_LINK_CONFIDENCE = 1.0


# Deterministic ccTLD -> ISO region hints, used only to VALIDATE a
# phone number already declared by the site itself (tel: link or
# JSON-LD telephone). Never used to normalize an ambiguous free-text
# match, and never treated as proof - if validation fails, the raw
# value is preserved and normalized_value stays null.
TLD_REGION_HINTS = {
    "fr": "FR", "ma": "MA", "tn": "TN", "dz": "DZ", "eg": "EG",
    "ae": "AE", "sa": "SA", "qa": "QA", "kw": "KW", "bh": "BH",
    "jo": "JO", "ci": "CI", "sn": "SN", "be": "BE", "ch": "CH",
    "de": "DE", "es": "ES", "it": "IT", "nl": "NL", "us": "US",
    "ca": "CA", "uk": "GB",
}


def _guess_region(source_url: str) -> str | None:
    host = source_url.split("//")[-1].split("/")[0].lower()
    tld = host.rsplit(".", 1)[-1] if "." in host else ""

    return TLD_REGION_HINTS.get(tld)


def _normalize_email(raw: str) -> str:
    return raw.strip().lower()


def _normalize_authoritative_phone(
    raw: str,
    source_url: str,
) -> str | None:
    """For phone numbers the site itself declared (tel: link, JSON-LD).
    Only returns a normalized value when phonenumbers can confidently
    validate it - either because the raw value already carries an
    explicit country code, or a TLD-derived region hint lets it parse
    to a genuinely valid number. Otherwise returns None; the raw value
    is never discarded, just left unnormalized."""
    region_hint = _guess_region(source_url)

    try:
        number = phonenumbers.parse(raw, region_hint)
    except phonenumbers.NumberParseException:
        return None

    if not phonenumbers.is_valid_number(number):
        return None

    return phonenumbers.format_number(
        number, phonenumbers.PhoneNumberFormat.E164
    )


def build_page_observations(
    html: str,
    source_url: str,
) -> list[Observation]:
    observations: list[Observation] = []

    seen_emails: set[str] = set()
    seen_phones: set[str] = set()

    def add_email(raw: str, source_type: str, confidence: float):
        normalized = _normalize_email(raw)

        if normalized in seen_emails:
            return

        seen_emails.add(normalized)

        observations.append(
            Observation(
                field="email",
                raw_value=raw,
                normalized_value=normalized,
                source_url=source_url,
                source_type=source_type,
                confidence=confidence,
            )
        )

    def add_phone(
        raw: str,
        source_type: str,
        confidence: float,
        authoritative: bool,
    ):
        key = raw.strip()

        if key in seen_phones:
            return

        seen_phones.add(key)

        normalized = (
            _normalize_authoritative_phone(raw, source_url)
            if authoritative
            else None
        )

        observations.append(
            Observation(
                field="phone",
                raw_value=raw,
                normalized_value=normalized,
                source_url=source_url,
                source_type=source_type,
                confidence=confidence,
            )
        )

    # 1. mailto: / tel: links - highest confidence, direct site signal.
    link_emails, link_phones = extract_contact_links(html)

    for raw_email in link_emails:
        add_email(raw_email, "mailto_link", EMAIL_LINK_CONFIDENCE)

    for raw_phone in link_phones:
        add_phone(
            raw_phone, "tel_link", PHONE_LINK_CONFIDENCE, authoritative=True
        )

    # 2. JSON-LD Organization/LocalBusiness - structured, high confidence.
    org_facts = extract_organization_facts(html)

    if "name" in org_facts:
        observations.append(
            Observation(
                field="organization_name",
                raw_value=org_facts["name"],
                normalized_value=org_facts["name"],
                source_url=source_url,
                source_type="json_ld",
                confidence=NAME_JSON_LD_CONFIDENCE,
            )
        )
    else:
        site_name = extract_opengraph(html).get("site_name")

        if site_name:
            observations.append(
                Observation(
                    field="organization_name",
                    raw_value=site_name,
                    normalized_value=site_name,
                    source_url=source_url,
                    source_type="metadata",
                    confidence=NAME_OPENGRAPH_CONFIDENCE,
                )
            )

    if "email" in org_facts:
        add_email(org_facts["email"], "json_ld", EMAIL_JSON_LD_CONFIDENCE)

    if "telephone" in org_facts:
        add_phone(
            org_facts["telephone"],
            "json_ld",
            PHONE_JSON_LD_CONFIDENCE,
            authoritative=True,
        )

    address = org_facts.get("address")

    if address and any(address.values()):
        parts = [
            address.get("street"),
            address.get("postal_code"),
            address.get("city"),
        ]
        raw_address = ", ".join(p for p in parts if p)

        if raw_address:
            observations.append(
                Observation(
                    field="address",
                    raw_value=raw_address,
                    normalized_value=raw_address,
                    source_url=source_url,
                    source_type="json_ld",
                    confidence=ADDRESS_JSON_LD_CONFIDENCE,
                )
            )

        if address.get("city"):
            observations.append(
                Observation(
                    field="city",
                    raw_value=address["city"],
                    normalized_value=address["city"],
                    source_url=source_url,
                    source_type="json_ld",
                    confidence=ADDRESS_JSON_LD_CONFIDENCE,
                )
            )

        if address.get("country"):
            observations.append(
                Observation(
                    field="country",
                    raw_value=address["country"],
                    normalized_value=address["country"],
                    source_url=source_url,
                    source_type="json_ld",
                    confidence=ADDRESS_JSON_LD_CONFIDENCE,
                )
            )

    # 3. Social profile links.
    for field, url in extract_social_links(html).items():
        observations.append(
            Observation(
                field=field,
                raw_value=url,
                normalized_value=url,
                source_url=source_url,
                source_type="social_link",
                confidence=SOCIAL_LINK_CONFIDENCE,
            )
        )

    # 4. Visible text - regex fallback, lowest confidence.
    soup = BeautifulSoup(html, "lxml")
    visible_text = soup.get_text(" ", strip=True)

    for raw_email in extract_emails(visible_text):
        add_email(raw_email, "visible_text", EMAIL_TEXT_CONFIDENCE)

    for raw_phone in extract_phones(visible_text):
        add_phone(
            raw_phone,
            "visible_text",
            PHONE_TEXT_CONFIDENCE,
            authoritative=False,
        )

    if not address:
        for postal_code, city in extract_address_candidates(visible_text):
            raw_address = f"{postal_code} {city}"

            observations.append(
                Observation(
                    field="address",
                    raw_value=raw_address,
                    normalized_value=None,
                    source_url=source_url,
                    source_type="visible_text",
                    confidence=ADDRESS_TEXT_CONFIDENCE,
                )
            )

    return observations
