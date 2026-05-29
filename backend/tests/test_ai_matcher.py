from app.ai.matcher import compute_match


def test_compute_match_intersection() -> None:
    result = compute_match(
        ["Python", "SQL", "Docker"],
        ["Python", "SQL", "React"],
    )
    assert set(result.matched_skills) == {"python", "sql"}
    assert "docker" in result.missing_skills
    assert 0 <= result.score <= 100


def test_compute_match_deterministic() -> None:
    job = ["Python", "FastAPI", "PostgreSQL"]
    candidate = ["Python", "FastAPI", "Docker"]
    first = compute_match(job, candidate)
    second = compute_match(job, candidate)
    assert first.score == second.score
    assert first.matched_skills == second.matched_skills


def test_compute_match_empty_job_uses_candidate() -> None:
    result = compute_match([], ["Python"])
    assert result.score >= 0
