from __future__ import annotations

import re


def _replace_literal_escape_markers(text: str) -> str:
    text = text.replace("\\r\\n", "\n")
    text = text.replace("\\n", "\n").replace("\\r", "\n")
    text = text.replace("\\t", " ")
    text = text.replace("\\u00a0", " ").replace("\\xa0", " ")
    text = re.sub(r"(?i)(?:(?<=\s)|^)/n(?=(?:\s|[.,;:!?)]|$))", "\n", text)
    text = re.sub(r"(?i)(?:(?<=\s)|^)/r(?=(?:\s|[.,;:!?)]|$))", "\n", text)
    text = re.sub(r"(?i)(?:(?<=\s)|^)/t(?=(?:\s|[.,;:!?)]|$))", " ", text)
    return text


def normalize_whitespace(text: str) -> str:
    text = _replace_literal_escape_markers(text)
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
