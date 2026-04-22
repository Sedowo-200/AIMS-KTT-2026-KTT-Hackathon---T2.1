"""
Mathematical pricing engine for the Perishable Goods Dynamic Pricer.

This module implements a production-ready pricing helper for short-life retail
products. It combines:

1. A required freshness decay formula.
2. A required log-linear demand model.
3. Numerical price optimization over a feasible price corridor.
4. A business markdown policy that starts discounts before the last day.
5. A hard margin floor for live stock.
6. A waste-aware optimization score to avoid hoarding stock at high prices.

Main entry point:
    suggest_price(sku_data, now, competitor_snapshot, margin_floor=1.05)
"""

from __future__ import annotations

import math
from statistics import median
from typing import Any, Mapping, Sequence

import numpy as np


DEFAULT_REFERENCE_MARKUP = 1.35
DEFAULT_MARKET_BUFFER = 1.05
NUMERICAL_SEARCH_POINTS = 1024

MIN_EFFECTIVE_ALPHA = 2.5
LOW_FRESHNESS_THRESHOLD = 0.50
LOW_FRESHNESS_EXPONENT = 2.4
WASTE_PENALTY_BASE = 1.25


def compute_freshness_factor(age_hours: float, shelf_life_hours: float) -> float:
    """
    Compute the required freshness factor for a perishable item.

    Required formula:
        freshness_factor = max(0, 1 - (age / shelf_life) ** 1.5)

    Parameters
    ----------
    age_hours:
        Product age in hours.
    shelf_life_hours:
        Product shelf life in hours.

    Returns
    -------
    float
        Freshness value in the closed interval [0.0, 1.0].

    Raises
    ------
    ValueError
        If shelf_life_hours is not strictly positive.
    """
    if shelf_life_hours <= 0:
        raise ValueError("shelf_life_hours must be strictly positive.")

    safe_age = max(0.0, float(age_hours))
    safe_shelf_life = float(shelf_life_hours)

    return max(0.0, 1.0 - (safe_age / safe_shelf_life) ** 1.5)


def _effective_freshness(freshness_factor: float) -> float:
    """
    Penalize low freshness more aggressively inside the optimizer.

    Above 0.5:
        Keep freshness close to its raw value.

    Below 0.5:
        Make freshness decay much sharper so the optimizer accepts lower prices
        earlier and is more willing to move stock before expiry.
    """
    f = max(0.0, min(1.0, float(freshness_factor)))

    if f >= LOW_FRESHNESS_THRESHOLD:
        return f

    return f ** LOW_FRESHNESS_EXPONENT


def expected_demand(
    price: float,
    q0: float,
    alpha: float,
    p_ref: float,
    freshness_factor: float,
) -> float:
    """
    Compute expected demand using the required log-linear demand model.

    Required formula:
        Q(p) = Q0 * exp(-alpha * (p - p_ref) / p_ref) * f

    Practical adjustment:
    - alpha is floored at 2.5 so price cuts have enough impact on demand.
    - freshness is penalized more aggressively once freshness drops below 0.5.

    Parameters
    ----------
    price:
        Candidate selling price.
    q0:
        Baseline demand scale.
    alpha:
        Price elasticity coefficient.
    p_ref:
        Reference market price.
    freshness_factor:
        Freshness value in [0, 1].

    Returns
    -------
    float
        Expected demand, lower-bounded by zero.

    Raises
    ------
    ValueError
        If p_ref is not strictly positive.
    """
    if p_ref <= 0:
        raise ValueError("p_ref must be strictly positive.")

    effective_alpha = max(float(alpha), MIN_EFFECTIVE_ALPHA)
    safe_q0 = max(0.0, float(q0))
    adjusted_f = _effective_freshness(freshness_factor)

    demand = safe_q0 * math.exp(
        -effective_alpha * (float(price) - float(p_ref)) / float(p_ref)
    ) * adjusted_f

    return max(0.0, demand)


def expected_profit(
    price: float,
    unit_cost: float,
    q0: float,
    alpha: float,
    p_ref: float,
    freshness_factor: float,
) -> float:
    """
    Compute expected profit at a candidate price.

    Formula:
        profit = (price - unit_cost) * Q(price)
    """
    demand = expected_demand(
        price=price,
        q0=q0,
        alpha=alpha,
        p_ref=p_ref,
        freshness_factor=freshness_factor,
    )
    return (float(price) - float(unit_cost)) * demand


def suggest_price(sku_data, now, competitor_snapshot, margin_floor=1.05):
    """
    Suggest a selling price for one perishable SKU.

    Economic design
    ---------------
    The required mathematical model is:

        Q(p) = Q0 * exp(-alpha * (p - p_ref) / p_ref) * f
        pi(p) = (p - c) * Q(p)

    However, in that raw form, freshness enters profit multiplicatively. This
    means freshness changes the level of profit, but not necessarily the
    unconstrained optimal price. That behavior is dangerous for short-life
    grocery products because it can cause the optimizer to keep prices too high
    while inventory ages, leading to waste.

    To fix that, this function combines the mathematical model with a practical
    markdown policy and a waste-aware optimization loop:

    1. Compute the required freshness factor exactly.
    2. Build a competitor-anchored reference price.
    3. Build a monotone markdown corridor:
       - a continuous freshness cap,
       - a staged time-to-expiry discount schedule,
       - a market ceiling tied to local competitors.
    4. Enforce the hard business rule:
           price >= unit_cost * margin_floor
       for live stock. Once freshness reaches zero, the item is treated as dead
       stock and the function returns 0.0 gracefully.
    5. Strengthen demand sensitivity by using:
           effective_alpha = max(alpha, 2.5)
       so the optimizer sees that lower prices can materially increase sales.
    6. Optimize not only profit, but:
           optimization_score = expected_profit - expected_waste_penalty
       This pushes the engine to sell out before expiration instead of hoarding
       stock at high prices.

    Why this works
    --------------
    - As freshness falls below 0.5, both the effective freshness used in demand
      and the price cap become much harsher.
    - The allowed top price drops faster as expiry approaches.
    - Unsold stock is penalized directly in the optimization score.
    - The engine can hit the margin floor earlier, but it never prices below
      the live-stock floor unless the item is dead stock.

    Parameters
    ----------
    sku_data:
        Dictionary containing at least:
        - unit_cost
        - age_hours
        - shelf_life_hours
        - q0
        - alpha

        Optional fields:
        - on_hand_units
        - reference_price
    now:
        Current timestamp or marker from the caller. It is accepted to keep the
        orchestration interface stable. Pricing logic uses age_hours directly.
    competitor_snapshot:
        Sequence of competitor prices. Each entry may be:
        - a raw number, or
        - a mapping containing one of:
          price, price_xaf, unit_price, unit_price_xaf,
          current_price, competitor_price_xaf
    margin_floor:
        Minimum allowed markup multiplier above unit cost for live stock.
        Example:
            margin_floor = 1.05
        means the live-stock price cannot go below 105% of unit cost.

    Returns
    -------
    float
        Suggested selling price. Returns 0.0 for dead stock.

    Raises
    ------
    KeyError
        If a required field is missing.
    ValueError
        If inputs violate domain constraints.
    """
    _ = now  # Kept intentionally for interface stability and auditability.

    unit_cost = _require_positive_float(sku_data, "unit_cost")
    age_hours = max(0.0, float(sku_data["age_hours"]))
    shelf_life_hours = _require_positive_float(sku_data, "shelf_life_hours")
    q0 = max(0.0, float(sku_data["q0"]))
    alpha = _require_positive_float(sku_data, "alpha")

    if margin_floor <= 0:
        raise ValueError("margin_floor must be strictly positive.")

    freshness_factor = compute_freshness_factor(
        age_hours=age_hours,
        shelf_life_hours=shelf_life_hours,
    )

    # Graceful dead-stock handling.
    if freshness_factor <= 0.0:
        return 0.0

    min_price = unit_cost * float(margin_floor)

    # If baseline demand is zero or missing in a practical sense, fall back
    # to the minimum live-stock price to avoid overpricing.
    if q0 <= 0.0:
        return round(min_price, 2)

    p_ref = _resolve_reference_price(
        competitor_snapshot=competitor_snapshot,
        sku_data=sku_data,
        unit_cost=unit_cost,
        margin_floor=float(margin_floor),
    )

    max_price = _dynamic_price_cap(
        min_price=min_price,
        p_ref=p_ref,
        freshness_factor=freshness_factor,
        age_hours=age_hours,
        shelf_life_hours=shelf_life_hours,
    )

    if not math.isfinite(max_price):
        max_price = max(min_price, p_ref)

    if max_price <= min_price:
        return round(min_price, 2)

    candidate_prices = np.linspace(min_price, max_price, NUMERICAL_SEARCH_POINTS, dtype=float)

    effective_alpha = max(alpha, MIN_EFFECTIVE_ALPHA)
    inventory_units = max(0.0, float(sku_data.get("on_hand_units", q0)))
    remaining_life_ratio = max(0.0, 1.0 - (age_hours / shelf_life_hours))

    profits = np.array(
        [
            expected_profit(
                price=float(price),
                unit_cost=unit_cost,
                q0=q0,
                alpha=effective_alpha,
                p_ref=p_ref,
                freshness_factor=freshness_factor,
            )
            for price in candidate_prices
        ],
        dtype=float,
    )

    expected_sales = np.array(
        [
            min(
                inventory_units,
                expected_demand(
                    price=float(price),
                    q0=q0,
                    alpha=effective_alpha,
                    p_ref=p_ref,
                    freshness_factor=freshness_factor,
                ),
            )
            for price in candidate_prices
        ],
        dtype=float,
    )

    expected_unsold_units = np.maximum(inventory_units - expected_sales, 0.0)

    # Waste penalty becomes much stronger when freshness is low and remaining life
    # is short. This makes the optimizer actively prefer sell-through.
    freshness_urgency = 1.0 + 3.0 * max(0.0, LOW_FRESHNESS_THRESHOLD - freshness_factor)
    expiry_urgency = 1.0 + 2.5 * (1.0 - remaining_life_ratio)
    waste_penalty_per_unit = unit_cost * WASTE_PENALTY_BASE * freshness_urgency * expiry_urgency

    optimization_score = profits - (expected_unsold_units * waste_penalty_per_unit)

    best_index = int(np.argmax(optimization_score))
    suggested = float(candidate_prices[best_index])

    suggested = max(min_price, min(suggested, max_price))
    if not math.isfinite(suggested):
        suggested = min_price

    return round(suggested, 2)


def calculate_waste_reduction(baseline_waste: float, ai_waste: float) -> float:
    """
    Compute waste reduction percentage using the corrected formula:

        ((Baseline_Waste - AI_Waste) / Baseline_Waste) * 100

    Parameters
    ----------
    baseline_waste:
        Waste produced by the baseline pricing policy.
    ai_waste:
        Waste produced by the AI pricing policy.

    Returns
    -------
    float
        Waste reduction percentage. Positive is good. Negative means the AI
        produced more waste than the baseline.
    """
    baseline = float(baseline_waste)
    ai = float(ai_waste)

    if baseline <= 0:
        return 0.0

    return ((baseline - ai) / baseline) * 100.0


def _require_positive_float(data: Mapping[str, Any], key: str) -> float:
    """
    Read and validate a strictly positive float from a mapping.
    """
    value = float(data[key])
    if value <= 0:
        raise ValueError(f"{key} must be strictly positive.")
    return value


def _resolve_reference_price(
    competitor_snapshot: Sequence[Any],
    sku_data: Mapping[str, Any],
    unit_cost: float,
    margin_floor: float,
) -> float:
    """
    Build the local-market reference price.

    Priority:
    1. Median of valid competitor prices.
    2. Explicit reference_price from sku_data.
    3. Conservative fallback from unit cost.
    """
    market_price = _extract_reference_price(competitor_snapshot)
    if market_price is not None and market_price > 0:
        return market_price

    explicit_reference = float(sku_data.get("reference_price", 0.0))
    if explicit_reference > 0:
        return explicit_reference

    fallback = unit_cost * max(DEFAULT_REFERENCE_MARKUP, margin_floor)
    if fallback <= 0:
        raise ValueError("Unable to derive a strictly positive reference price.")

    return fallback


def _extract_reference_price(competitor_snapshot: Sequence[Any]) -> float | None:
    """
    Extract a robust reference price from a competitor snapshot.

    The median is preferred over the mean because it is more robust to outliers.
    """
    values: list[float] = []

    for entry in competitor_snapshot or []:
        maybe_price = _extract_single_price(entry)
        if maybe_price is not None and maybe_price > 0:
            values.append(maybe_price)

    if not values:
        return None

    return float(median(values))


def _extract_single_price(entry: Any) -> float | None:
    """
    Extract one numeric competitor price from a heterogeneous entry.
    """
    if isinstance(entry, (int, float)):
        return float(entry)

    if isinstance(entry, Mapping):
        for key in (
            "price",
            "price_xaf",
            "unit_price",
            "unit_price_xaf",
            "current_price",
            "competitor_price_xaf",
        ):
            value = entry.get(key)
            if value is None:
                continue
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                continue
            if parsed > 0:
                return parsed

    return None


def _dynamic_price_cap(
    min_price: float,
    p_ref: float,
    freshness_factor: float,
    age_hours: float,
    shelf_life_hours: float,
) -> float:
    """
    Compute the maximum feasible price for live stock.

    The cap is monotone non-increasing with age and combines:
    - a competitor-based market ceiling,
    - a stronger freshness-driven cap,
    - a staged time-to-expiry markdown schedule.

    Once freshness drops below 0.5, the cap collapses more aggressively.
    """
    remaining_hours = max(0.0, shelf_life_hours - age_hours)
    market_ceiling = max(min_price, p_ref * DEFAULT_MARKET_BUFFER)

    f = max(0.0, min(1.0, float(freshness_factor)))

    if f >= LOW_FRESHNESS_THRESHOLD:
        freshness_multiplier = 0.50 + 0.50 * f
    else:
        freshness_multiplier = 0.15 + 0.70 * (f ** 2.0)

    mild_window_hours = min(96.0, 0.40 * shelf_life_hours)
    strong_window_hours = min(48.0, 0.20 * shelf_life_hours)

    if strong_window_hours <= 0:
        strong_window_hours = max(1e-6, 0.20 * shelf_life_hours)
    if mild_window_hours < strong_window_hours:
        mild_window_hours = strong_window_hours

    scheduled_discount = _scheduled_markdown_discount(
        remaining_hours=remaining_hours,
        mild_window_hours=mild_window_hours,
        strong_window_hours=strong_window_hours,
    )
    scheduled_multiplier = 1.0 - scheduled_discount

    dynamic_cap = market_ceiling * min(freshness_multiplier, scheduled_multiplier)

    # Live stock must respect the floor.
    return max(min_price, dynamic_cap)


def _scheduled_markdown_discount(
    remaining_hours: float,
    mild_window_hours: float,
    strong_window_hours: float,
) -> float:
    """
    Compute the staged markdown discount.

    Policy:
    - before mild window: 0%
    - mild window: 20% -> 45%
    - strong window: 45% -> 80%

    The hard margin floor still applies for live stock, so the engine becomes
    more aggressive by reaching the floor sooner, not by pricing below it.
    """
    remaining = max(0.0, float(remaining_hours))
    mild = max(0.0, float(mild_window_hours))
    strong = max(1e-6, float(strong_window_hours))

    if remaining > mild:
        return 0.0

    if remaining > strong:
        if mild == strong:
            return 0.20
        progress = (mild - remaining) / (mild - strong)
        return min(0.45, max(0.20, 0.20 + 0.25 * progress))

    progress_to_zero = 1.0 - (remaining / strong)
    return min(0.80, max(0.45, 0.45 + 0.35 * progress_to_zero))


__all__ = [
    "compute_freshness_factor",
    "expected_demand",
    "expected_profit",
    "suggest_price",
    "calculate_waste_reduction",
]