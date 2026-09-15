from dataclasses import dataclass
from typing import Any


@dataclass
class TokenUsageReport:
    requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    remaining_tokens: int
    usage_percent: float
    cached_tokens: int = 0
    reasoning_tokens: int = 0


def get_token_usage(
    result: Any,
    token_budget: int | None = None,
) -> TokenUsageReport:

    usage = result.context_wrapper.usage

    cached_tokens = 0
    reasoning_tokens = 0

    if getattr(usage, "input_tokens_details", None):
        cached_tokens = (
            getattr(
                usage.input_tokens_details,
                "cached_tokens",
                0,
            )
            or 0
        )

    if getattr(usage, "output_tokens_details", None):
        reasoning_tokens = (
            getattr(
                usage.output_tokens_details,
                "reasoning_tokens",
                0,
            )
            or 0
        )

    total = usage.total_tokens

    if token_budget is not None:
        remaining = max(token_budget - total, 0)

        percentage = (
            (total / token_budget) * 100
            if token_budget > 0
            else 0
        )
    else:
        remaining = 0
        percentage = 0

    return TokenUsageReport(
        requests=usage.requests,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=total,
        remaining_tokens=remaining,
        usage_percent=round(percentage, 2),
        cached_tokens=cached_tokens,
        reasoning_tokens=reasoning_tokens,
    )