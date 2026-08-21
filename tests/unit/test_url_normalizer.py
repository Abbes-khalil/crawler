from app.crawler.url_normalizer import normalize_url


def test_adds_missing_scheme():
    assert normalize_url("company.com") == "https://company.com"


def test_lowercases_host():
    assert normalize_url("https://Company.COM") == "https://company.com"


def test_strips_trailing_slash():
    assert normalize_url("https://company.com/") == "https://company.com"


def test_keeps_path_without_trailing_slash():
    assert normalize_url("https://company.com/about/") == "https://company.com/about"


def test_drops_query_and_fragment():
    assert (
        normalize_url("https://company.com/?utm_source=x#section")
        == "https://company.com"
    )


def test_preserves_existing_scheme():
    assert normalize_url("http://company.com") == "http://company.com"
