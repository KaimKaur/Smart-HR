from app.ai.extractor import extract_skills


def test_extract_skills_empty() -> None:
    assert extract_skills("") == []
    assert extract_skills("   ") == []


def test_extract_skills_from_text() -> None:
    text = "Experienced Python and SQL developer. Built React dashboards on AWS."
    skills = extract_skills(text)
    assert "Python" in skills
    assert "SQL" in skills
    assert "React" in skills
    assert "AWS" in skills


def test_extract_skills_case_normalized() -> None:
    text = "python, PYTHON, and sql experience"
    skills = extract_skills(text)
    assert "Python" in skills
    assert "SQL" in skills
    assert "python" not in skills
