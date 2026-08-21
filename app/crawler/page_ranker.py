from urllib.parse import urlparse


PAGE_CATEGORIES = {
    "products": {
        "keywords": [
            "products",
            "produits",
            "product",
            "solutions",
            "services",
            "offer",
            "offre",
        ],
        "score": 100,
    },

    "capabilities": {
        "keywords": [
            "capabilities",
            "competences",
            "expertise",
            "savoir-faire",
            "technology",
            "technologies",
        ],
        "score": 95,
    },

    "markets": {
        "keywords": [
            "industries",
            "industry",
            "sectors",
            "secteurs",
            "applications",
            "markets",
            "marches",
        ],
        "score": 90,
    },

    "about": {
        "keywords": [
            "about",
            "about-us",
            "company",
            "who-we-are",
            "qui-sommes-nous",
            "a-propos",
            "notre-entreprise",
        ],
        "score": 85,
    },

    "references": {
        "keywords": [
            "references",
            "clients",
            "projects",
            "realisations",
            "partners",
            "partenaires",
        ],
        "score": 80,
    },

    "contact": {
        "keywords": [
            "contact",
            "contact-us",
            "nous-contacter",
        ],
        "score": 75,
    },
}


NEGATIVE_KEYWORDS = [
    "privacy",
    "cookies",
    "terms",
    "legal",
    "mentions-legales",
    "login",
    "signin",
    "signup",
    "cart",
    "checkout",
]


def get_page_category(url: str) -> str | None:
    path = urlparse(url).path.lower()

    for category, config in PAGE_CATEGORIES.items():
        if any(keyword in path for keyword in config["keywords"]):
            return category

    return None


def score_url(url: str) -> int:
    path = urlparse(url).path.lower().strip("/")

    if not path:
        return 110

    if any(keyword in path for keyword in NEGATIVE_KEYWORDS):
        return -100

    category = get_page_category(url)

    score = 0

    if category:
        score = PAGE_CATEGORIES[category]["score"]

    depth = len(
        [part for part in path.split("/") if part]
    )

    score -= depth * 3

    return score


def select_best_urls(
    urls: list[str],
    homepage: str,
    max_pages: int,
) -> list[str]:

    ranked = sorted(
        urls,
        key=score_url,
        reverse=True,
    )

    selected = [homepage]
    selected_categories = set()

    # First pass:
    # maximize category diversity.
    for url in ranked:
        if len(selected) >= max_pages:
            break

        if url == homepage:
            continue

        category = get_page_category(url)

        if category and category not in selected_categories:
            selected.append(url)
            selected_categories.add(category)

    # Second pass:
    # fill remaining slots with highest scoring pages.
    for url in ranked:
        if len(selected) >= max_pages:
            break

        if url not in selected:
            selected.append(url)

    return selected