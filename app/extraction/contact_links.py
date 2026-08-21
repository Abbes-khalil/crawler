from bs4 import BeautifulSoup


def extract_contact_links(
    html: str,
) -> tuple[list[str], list[str]]:

    soup = BeautifulSoup(html, "lxml")

    emails = set()
    phones = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if href.startswith("mailto:"):
            email = (
                href
                .replace("mailto:", "", 1)
                .split("?")[0]
                .strip()
            )

            if email:
                emails.add(email)

        elif href.startswith("tel:"):
            phone = (
                href
                .replace("tel:", "", 1)
                .strip()
            )

            if phone:
                phones.add(phone)

    return (
        sorted(emails),
        sorted(phones),
    )