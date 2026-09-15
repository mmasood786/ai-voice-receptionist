class ReviewEscalationService:

    async def escalate(
        self,
        *,
        review_id: int,
        rating: int,
        feedback: str | None,
    ) -> None:

        print("\n========== REVIEW ESCALATION ==========")
        print(f"REVIEW ID: {review_id}")
        print(f"RATING: {rating}")
        print(f"FEEDBACK: {feedback}")
        print("ACTION: Human follow-up required")
        print("=======================================\n")