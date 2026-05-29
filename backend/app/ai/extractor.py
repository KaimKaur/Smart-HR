from __future__ import annotations

import re

from app.ai.skills_vocabulary import SKILLS_VOCABULARY, _CANONICAL_BY_LOWER

_NLP: object | None = None
_NLP_LOAD_FAILED = False


def _get_nlp():
    global _NLP, _NLP_LOAD_FAILED
    if _NLP_LOAD_FAILED:
        return None
    if _NLP is not None:
        return _NLP
    try:
        import spacy

        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP_LOAD_FAILED = True
        _NLP = None
    return _NLP


def extract_skills(text: str) -> list[str]:
    """Extract normalized skill names from resume text."""
    if not text or not text.strip():
        return []

    found: set[str] = set()
    lower_text = text.lower()

    for skill in SKILLS_VOCABULARY:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, lower_text):
            found.add(skill)

    nlp = _get_nlp()
    if nlp is not None:
        doc = nlp(text[:100000])
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "SKILL"):
                normalized = _normalize_token(ent.text)
                if normalized:
                    found.add(normalized)

    return sorted(found)


def _normalize_token(token: str) -> str | None:
    cleaned = token.strip()
    if not cleaned:
        return None
    canonical = _CANONICAL_BY_LOWER.get(cleaned.lower())
    if canonical:
        return canonical
    if cleaned in SKILLS_VOCABULARY:
        return cleaned
    return None
