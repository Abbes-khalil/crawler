import re


EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def extract_emails(text: str) -> list[str]:
    emails = EMAIL_REGEX.findall(text)

    return sorted(set(emails))