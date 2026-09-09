def calculate_lead_score(
    *,
    service_interest: str | None,
    urgency: str | None,
    budget: str | None,
    timeline: str | None,
) -> int:

    score = 0

    # --------------------------------
    # Service interest
    # --------------------------------

    if service_interest:
        score += 20

    # --------------------------------
    # Urgency
    # --------------------------------

    urgency_value = (urgency or "").lower()

    if urgency_value in {"high", "urgent", "immediate"}:
        score += 30

    elif urgency_value in {"medium", "soon"}:
        score += 20

    elif urgency_value in {"low", "later"}:
        score += 10

    # --------------------------------
    # Budget
    # --------------------------------

    if budget:
        score += 25

    # --------------------------------
    # Timeline
    # --------------------------------

    timeline_value = (timeline or "").lower()

    if timeline_value in {
        "today",
        "this week",
        "this month",
        "immediate",
        "asap",
    }:
        score += 25

    elif timeline:
        score += 10

    return min(score, 100)


def get_lead_status(score: int) -> str:

    if score >= 70:
        return "qualified"

    if score >= 40:
        return "contacted"

    return "new"