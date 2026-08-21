from app.extraction.addresses import extract_address_candidates


def test_extracts_postal_code_and_city():
    text = "Our office is located at 75002 Paris, France."
    candidates = extract_address_candidates(text)

    assert ("75002", "Paris") in candidates


def test_no_match_returns_empty_list():
    assert extract_address_candidates("No address mentioned here.") == []
