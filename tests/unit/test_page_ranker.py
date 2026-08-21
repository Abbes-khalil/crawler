from app.crawler.page_ranker import (
    get_page_category,
    score_url,
    select_best_urls,
)


def test_homepage_scores_highest():
    assert score_url("https://company.com") > score_url(
        "https://company.com/products"
    )


def test_negative_keywords_score_low():
    assert score_url("https://company.com/privacy") < 0


def test_category_detection_english_and_french():
    assert get_page_category("https://company.com/products") == "products"
    assert get_page_category("https://company.com/produits") == "products"
    assert get_page_category("https://company.com/a-propos") == "about"
    assert get_page_category("https://company.com/contact") == "contact"


def test_select_best_urls_is_category_diverse():
    homepage = "https://company.com"
    urls = [
        homepage,
        "https://company.com/products",
        "https://company.com/products/solution-a",
        "https://company.com/products/solution-b",
        "https://company.com/about-us",
        "https://company.com/contact",
    ]

    selected = select_best_urls(urls, homepage=homepage, max_pages=4)

    assert homepage in selected
    assert len(selected) == 4

    categories = {get_page_category(u) for u in selected if u != homepage}
    # diversity: should not be only the "products" category repeated
    assert len(categories) > 1


def test_select_best_urls_respects_max_pages():
    homepage = "https://company.com"
    urls = [homepage] + [
        f"https://company.com/page-{i}" for i in range(10)
    ]

    selected = select_best_urls(urls, homepage=homepage, max_pages=3)

    assert len(selected) == 3
