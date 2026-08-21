import re


# Loose FR-style "5-digit postal code + city name" pattern. This is a
# weak heuristic fallback, not a real address parser - it is only used
# at low confidence when no structured (JSON-LD) address is available.
POSTAL_CODE_CITY_REGEX = re.compile(
    r"\b(\d{5})\s+([A-ZÀ-Ý][A-Za-zà-ÿ\-'’]+(?:[\s\-][A-ZÀ-Ý][A-Za-zà-ÿ\-'’]+)*)\b"
)


def extract_address_candidates(text: str) -> list[tuple[str, str]]:
    """Returns (postal_code, city) pairs found via a loose regex. This
    is intentionally conservative: it does not attempt to capture the
    full street address, and callers should treat matches as low
    confidence, unverified evidence."""
    matches = POSTAL_CODE_CITY_REGEX.findall(text)

    return [(code, city.strip()) for code, city in matches]
