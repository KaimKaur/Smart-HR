SHORTLIST = "Shortlist"
REVIEW = "Review"
REJECT = "Reject"

THRESHOLD_SHORTLIST = 70.0
THRESHOLD_REVIEW = 40.0


def generate_recommendation(score: float) -> str:
    """Map numeric score to Shortlist / Review / Reject."""
    if score >= THRESHOLD_SHORTLIST:
        return SHORTLIST
    if score >= THRESHOLD_REVIEW:
        return REVIEW
    return REJECT


def map_llm_recommendation(recommendation: str) -> str:
    """Map LLM proceed/reject/review to application recommendation labels."""
    mapping = {
        "proceed": SHORTLIST,
        "review": REVIEW,
        "reject": REJECT,
    }
    return mapping.get(recommendation.lower(), REVIEW)
