"""Coarse question-language detection for template refusals."""

from __future__ import annotations

import re

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
UZ_RE = re.compile(
    r"oʻ|gʻ|o'|g'|ʻ|\b(qanday|qancha|nima|uchun|bo'yicha|shartlari|qoldig'i|stavkasi|hujjat)\b",
    re.IGNORECASE,
)

REFUSALS = {
    "en": "The synthetic sample corpus does not contain this.",
    "ru": "В синтетическом корпусе образцов этого нет.",
    "uz": "Sun'iy namunaviy hujjatlarda bu ma'lumot yo'q.",
}


def detect_language(text: str) -> str:
    if CYRILLIC_RE.search(text):
        return "ru"
    if UZ_RE.search(text):
        return "uz"
    return "en"


def refusal_for(question: str) -> str:
    return REFUSALS[detect_language(question)]
