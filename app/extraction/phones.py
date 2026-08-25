import re


PHONE_REGEX = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{1,4}\)?[\s.-]?){2,5}\d{2,4}"
)

YEAR_PAIR_REGEX = re.compile(
    r"^(?:19|20)\d{2}[\s.-]+(?:19|20)\d{2}$"
)

REPEATED_DIGIT_REGEX = re.compile(r"(\d)\1{7,}")


def _looks_like_phone_noise(raw: str, digits: str) -> bool:
    """Rejects free-text regex matches that are almost certainly not a
    phone number: copyright year ranges, implausible digit counts, and
    long runs of the same repeated digit. This is a deterministic
    length/shape filter, not a country/format guess - it never decides
    a number IS valid, only that a match clearly ISN'T one."""
    if not (8 <= len(digits) <= 15):
        return True

    if YEAR_PAIR_REGEX.match(raw):
        return True

    if REPEATED_DIGIT_REGEX.search(digits):
        return True

    return False


def extract_phones(text: str) -> list[str]:
    matches = PHONE_REGEX.findall(text)

    phones = set()

    for phone in matches:
        normalized_spacing = " ".join(phone.split())
        digits = re.sub(r"\D", "", phone)

        if _looks_like_phone_noise(normalized_spacing, digits):
            continue

        phones.add(normalized_spacing)

    return sorted(phones)
