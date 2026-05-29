from __future__ import annotations

from app.ai.schemas import MatchResult


def compute_match(job_skills: list[str], candidate_skills: list[str]) -> MatchResult:
    """Compute skill overlap and TF-IDF cosine similarity score (0–100)."""
    job_set = {_normalize(s) for s in job_skills if s.strip()}
    candidate_set = {_normalize(s) for s in candidate_skills if s.strip()}

    if not job_set:
        job_set = candidate_set.copy()

    matched = sorted(job_set & candidate_set)
    missing = sorted(job_set - candidate_set)

    score = _cosine_score(job_skills, candidate_skills)
    return MatchResult(
        matched_skills=matched,
        missing_skills=missing,
        score=score,
    )


def _normalize(skill: str) -> str:
    return skill.strip().lower()


def _cosine_score(job_skills: list[str], candidate_skills: list[str]) -> float:
    job_text = " ".join(job_skills).strip()
    candidate_text = " ".join(candidate_skills).strip()

    if not job_text and not candidate_text:
        return 0.0
    if not job_text or not candidate_text:
        return 0.0

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([job_text, candidate_text])
    similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    return round(max(0.0, min(100.0, similarity * 100)), 2)
