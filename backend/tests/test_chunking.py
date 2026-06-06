from app.services.chunking import merge_blocks, split_text


def test_merge_blocks_combines_small_adjacent_text_blocks() -> None:
    blocks = [
        {"text": "What is Pay10?", "content_type": "text", "page_number": -1, "table_index": -1, "row_index": -1},
        {"text": "With Pay10, you can collect payments easily.", "content_type": "text", "page_number": -1, "table_index": -1, "row_index": -1},
        {"text": "Select Pay via Pay10 Wallet.", "content_type": "text", "page_number": -1, "table_index": -1, "row_index": -1},
    ]
    merged = merge_blocks(blocks, 400)
    assert len(merged) == 1
    assert "What is Pay10?" in merged[0]["text"]
    assert "collect payments easily" in merged[0]["text"]


def test_split_text_prefers_paragraph_boundaries() -> None:
    text = "Intro paragraph.\n\nSecond paragraph with more detail.\n\nThird paragraph wraps up."
    chunks = split_text(text, 50, 10)
    assert len(chunks) >= 2
    assert any("Second paragraph" in chunk for chunk in chunks)
