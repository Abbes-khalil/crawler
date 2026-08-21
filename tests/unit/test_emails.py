from app.extraction.emails import extract_emails


def test_extracts_simple_email():
    text = "Contact us at info@example.com for more details."
    assert extract_emails(text) == ["info@example.com"]


def test_deduplicates_and_sorts():
    text = "b@example.com then a@example.com then b@example.com again"
    assert extract_emails(text) == ["a@example.com", "b@example.com"]


def test_no_email_returns_empty_list():
    assert extract_emails("No contact info here.") == []
