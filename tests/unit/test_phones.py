from app.extraction.phones import extract_phones


def test_extracts_phone_like_sequence():
    text = "Call us at +33 6 07 38 69 63 for support."
    phones = extract_phones(text)
    assert len(phones) == 1
    assert "07 38 69 63" in phones[0]


def test_ignores_short_numeric_noise():
    text = "Founded in 1998, we serve 42 countries."
    assert extract_phones(text) == []


def test_ignores_copyright_year_ranges():
    text = "Copyright 2001-2026. All rights reserved. 2026 2026."
    assert extract_phones(text) == []


def test_ignores_long_repeated_digit_runs():
    text = "Fibonacci sample: 666666666666667 is not a phone number."
    assert extract_phones(text) == []


def test_keeps_plausible_international_number():
    text = "Reach the office at 233 377 610 987 during business hours."
    assert extract_phones(text) == ["233 377 610 987"]


def test_keeps_full_number_with_dropped_zero_trunk_prefix():
    text = "Our fax: +33 (0)1 23 45 67 89."
    phones = extract_phones(text)
    assert len(phones) == 1
    assert phones[0].startswith("+33 (0)1")
