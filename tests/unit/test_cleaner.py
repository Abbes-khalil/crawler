from app.extraction.cleaner import compute_content_hash


def test_same_text_same_hash():
    assert compute_content_hash("hello world") == compute_content_hash(
        "hello world"
    )


def test_different_text_different_hash():
    assert compute_content_hash("hello world") != compute_content_hash(
        "hello there"
    )


def test_hash_is_sha256_hex_length():
    assert len(compute_content_hash("anything")) == 64
