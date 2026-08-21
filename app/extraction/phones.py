import re


PHONE_REGEX = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,5}\d{2,4}"
)


def extract_phones(text: str) -> list[str]:
    matches = PHONE_REGEX.findall(text)

    phones = {
        " ".join(phone.split())
        for phone in matches
        if len(re.sub(r"\D", "", phone)) >= 8
    }

    return sorted(phones)