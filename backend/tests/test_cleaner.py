from app.services.preprocessing.cleaner import normalize_whitespace


def test_normalize_whitespace_removes_literal_escape_markers() -> None:
    raw = "What is Pay10?\\nIt is a payments platform. /n Supports merchants.\\tFast onboarding."
    cleaned = normalize_whitespace(raw)
    assert "\\n" not in cleaned
    assert "/n" not in cleaned
    assert "\\t" not in cleaned
    assert cleaned == "What is Pay10?\nIt is a payments platform.\nSupports merchants. Fast onboarding."


def test_normalize_whitespace_keeps_regular_slashes_intact() -> None:
    raw = "Visit https://example.com/pay10 and compare A/B tests without stripping the slash."
    cleaned = normalize_whitespace(raw)
    assert "https://example.com/pay10" in cleaned
    assert "A/B tests" in cleaned
