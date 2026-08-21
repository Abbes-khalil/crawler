import json

from bs4 import BeautifulSoup


ORGANIZATION_TYPES = {
    "organization",
    "localbusiness",
    "corporation",
    "ngo",
}


def _iter_nodes(data):
    if isinstance(data, list):
        for item in data:
            yield from _iter_nodes(item)
        return

    if not isinstance(data, dict):
        return

    yield data

    if "@graph" in data and isinstance(data["@graph"], list):
        for item in data["@graph"]:
            yield from _iter_nodes(item)


def _is_organization_node(node: dict) -> bool:
    node_type = node.get("@type")

    if node_type is None:
        return False

    if isinstance(node_type, str):
        types = [node_type]
    elif isinstance(node_type, list):
        types = node_type
    else:
        return False

    return any(str(t).lower() in ORGANIZATION_TYPES for t in types)


def extract_json_ld_blocks(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    blocks: list[dict] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()

        if not raw or not raw.strip():
            continue

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        blocks.extend(_iter_nodes(data))

    return blocks


def extract_organization_facts(html: str) -> dict:
    """Returns a flat dict of whatever an Organization/LocalBusiness
    JSON-LD node exposes directly: name, email, telephone, address,
    sameAs. Missing fields are simply absent - nothing is inferred."""
    facts: dict = {}

    for node in extract_json_ld_blocks(html):
        if not _is_organization_node(node):
            continue

        if "name" in node and isinstance(node["name"], str):
            facts.setdefault("name", node["name"].strip())

        if "email" in node and isinstance(node["email"], str):
            facts.setdefault("email", node["email"].strip())

        if "telephone" in node and isinstance(node["telephone"], str):
            facts.setdefault("telephone", node["telephone"].strip())

        address = node.get("address")

        if isinstance(address, dict):
            facts.setdefault(
                "address",
                {
                    "street": address.get("streetAddress"),
                    "city": address.get("addressLocality"),
                    "postal_code": address.get("postalCode"),
                    "country": address.get("addressCountry"),
                },
            )

        same_as = node.get("sameAs")

        if isinstance(same_as, list):
            facts.setdefault(
                "same_as", [s for s in same_as if isinstance(s, str)]
            )
        elif isinstance(same_as, str):
            facts.setdefault("same_as", [same_as])

    return facts
