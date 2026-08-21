from app.extraction.phones import extract_phones


def test_extracts_phone_like_sequence():
    text = "Call us at +33 6 07 38 69 63 for support."
    phones = extract_phones(text)
    assert len(phones) == 1
    assert "07 38 69 63" in phones[0]


def test_ignores_short_numeric_noise():
    text = "Founded in 1998, we serve 42 countries."
    assert extract_phones(text) == []
