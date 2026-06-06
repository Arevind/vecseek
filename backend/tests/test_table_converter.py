from app.services.preprocessing.table_converter import table_to_records


def test_table_to_records_uses_fallback_headers_and_na() -> None:
    rows = [
        ["", "Fee", "Fee"],
        ["0-5 years", "Free", ""],
    ]
    records = table_to_records("Table 1", "aadhaar.docx", rows)
    assert "Column 1: 0-5 years" in records[0]
    assert "Column 3: N/A" in records[0]
