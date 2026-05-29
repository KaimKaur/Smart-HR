SCREENING_SYSTEM_PROMPT = """You are an expert technical recruiter. Evaluate how well a candidate's resume matches a job posting.
Respond with valid JSON only — no markdown fences or extra text.
The JSON must match this schema:
{
  "score": <integer 0-100>,
  "summary": "<brief overall assessment>",
  "strengths": ["<strength>", ...],
  "weaknesses": ["<weakness>", ...],
  "recommendation": "<proceed|reject|review>"
}
Scoring guide: 70+ strong fit, 40-69 partial fit, below 40 poor fit.
recommendation: proceed = strong fit, review = needs human review, reject = poor fit."""


def build_screening_user_prompt(
    *,
    job_title: str,
    job_description: str,
    job_skills: list[str],
    resume_text: str,
) -> str:
    skills_block = ", ".join(job_skills) if job_skills else "Not specified"
    return (
        f"Job title: {job_title}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Required/preferred skills: {skills_block}\n\n"
        f"Resume text:\n{resume_text[:12000]}"
    )
