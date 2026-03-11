from dataclasses import dataclass


@dataclass
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    is_estimated: bool = False


@dataclass
class PricingConfig:
    input_unit_price: float
    cached_input_unit_price: float
    output_unit_price: float
    unit_tokens: int = 1_000_000


def calculate_cost(usage: TokenUsage, pricing: PricingConfig) -> float:
    divisor = max(pricing.unit_tokens, 1)
    return (
        usage.input_tokens * pricing.input_unit_price
        + usage.cached_input_tokens * pricing.cached_input_unit_price
        + usage.output_tokens * pricing.output_unit_price
    ) / divisor
