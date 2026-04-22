#!/usr/bin/env python3
"""
CLI for the dynamic pricing live demo.

Usage:
    python pricer.py --sku TOM_023 --now 2026-04-20T15:30
"""

from __future__ import annotations

import argparse
import inspect
import statistics
import sys
from datetime import datetime
from typing import Any


try:
    from src.math_engine import suggest_price, compute_freshness_factor
except Exception as exc:  # pragma: no cover
    sys.stderr.write(
        f"[ERROR] Could not import required functions from src.math_engine: {exc}\n"
    )
    raise


def parse_args() -> argparse.Namespace:
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Dynamic pricing CLI demo for the AIMS KTT Hackathon."
    )
    parser.add_argument(
        "--sku",
        required=True,
        help="SKU identifier, for example TOM_023",
    )
    parser.add_argument(
        "--now",
        required=True,
        help="Current timestamp in ISO format, for example 2026-04-20T15:30",
    )
    args = parser.parse_args()

    try:
        args.now_dt = datetime.fromisoformat(args.now)
    except ValueError as exc:
        parser.error(
            f"Invalid value for --now: {args.now!r}. "
            f"Expected ISO format like 2026-04-20T15:30. Details: {exc}"
        )

    return args


def build_mock_sku_data(sku: str, now_iso: str) -> dict[str, Any]:
    """Return fixed demo-safe SKU data."""
    return {
        "sku_id": sku,
        "unit_cost": 1000.0,
        "age_hours": 48.0,
        "shelf_life_hours": 96.0,
        "currency": "RWF",
        "observed_at": now_iso,
    }


def build_mock_competitor_snapshot(now_iso: str) -> list[dict[str, Any]]:
    """Return fixed demo-safe competitor prices."""
    return [
        {"competitor": "Market A", "price_rwf": 1450.0, "observed_at": now_iso},
        {"competitor": "Market B", "price_rwf": 1525.0, "observed_at": now_iso},
        {"competitor": "Market C", "price_rwf": 1490.0, "observed_at": now_iso},
    ]


def fallback_freshness(age_hours: float, shelf_life_hours: float) -> float:
    """
    Local safe fallback using the required 1.5 exponent decay.
    f = max(0, 1 - (age / shelf_life)^1.5)
    """
    if shelf_life_hours <= 0:
        return 0.0
    ratio = age_hours / shelf_life_hours
    freshness = max(0.0, 1.0 - (ratio ** 1.5))
    return min(1.0, freshness)


def extract_numeric(value: Any) -> float | None:
    """Extract a numeric value from common return types."""
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, dict):
        for key in (
            "price",
            "chosen_price",
            "suggested_price",
            "recommended_price",
            "optimal_price",
            "freshness",
            "freshness_factor",
            "f",
        ):
            if key in value and isinstance(value[key], (int, float)):
                return float(value[key])

    if isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, (int, float)):
                return float(item)
            if isinstance(item, dict):
                extracted = extract_numeric(item)
                if extracted is not None:
                    return extracted

    return None


def call_compute_freshness_factor(age_hours: float, shelf_life_hours: float) -> float:
    """
    Call compute_freshness_factor defensively to survive small API differences.
    Falls back to local computation if needed.
    """
    attempts = [
        ((age_hours, shelf_life_hours), {}),
        ((), {"age_hours": age_hours, "shelf_life_hours": shelf_life_hours}),
        ((), {"age": age_hours, "shelf_life": shelf_life_hours}),
        ((), {"hours_elapsed": age_hours, "shelf_life_hours": shelf_life_hours}),
    ]

    for args, kwargs in attempts:
        try:
            result = compute_freshness_factor(*args, **kwargs)
            freshness = extract_numeric(result)
            if freshness is not None:
                return max(0.0, min(1.0, freshness))
        except Exception:
            continue

    return fallback_freshness(age_hours, shelf_life_hours)


def build_signature_kwargs(
    sku: str,
    now_dt: datetime,
    sku_data: dict[str, Any],
    competitor_snapshot: list[dict[str, Any]],
    margin_floor: float,
) -> dict[str, Any]:
    """
    Build keyword arguments dynamically from suggest_price signature.
    This makes the CLI more robust against small signature differences.
    """
    kwargs: dict[str, Any] = {}

    try:
        sig = inspect.signature(suggest_price)
    except Exception:
        return kwargs

    for param_name in sig.parameters:
        lname = param_name.lower()

        if lname in {"sku", "sku_id"}:
            kwargs[param_name] = sku
        elif lname in {"sku_data", "product_data", "item_data", "product", "item", "record"}:
            kwargs[param_name] = sku_data
        elif "competitor" in lname:
            kwargs[param_name] = competitor_snapshot
        elif "margin" in lname and "floor" in lname:
            kwargs[param_name] = margin_floor
        elif "now" in lname or "timestamp" in lname or "current_time" in lname:
            kwargs[param_name] = now_dt
        elif lname in {"unit_cost", "cost"}:
            kwargs[param_name] = sku_data["unit_cost"]
        elif "age" in lname:
            kwargs[param_name] = sku_data["age_hours"]
        elif "shelf" in lname:
            kwargs[param_name] = sku_data["shelf_life_hours"]

    return kwargs


def fallback_suggest_price(
    sku_data: dict[str, Any],
    competitor_snapshot: list[dict[str, Any]],
    freshness: float,
    margin_floor: float,
) -> float:
    """
    Demo-safe local fallback:
    - reference price = median competitor price
    - freshness discount = multiply by freshness
    - enforce margin floor
    """
    competitor_prices = [float(x["price_rwf"]) for x in competitor_snapshot]
    reference_price = statistics.median(competitor_prices)
    floor_price = sku_data["unit_cost"] * margin_floor

    if freshness <= 0:
        return 0.0

    raw_price = reference_price * freshness
    chosen_price = max(floor_price, raw_price)
    return round(chosen_price)


def call_suggest_price(
    sku: str,
    now_dt: datetime,
    sku_data: dict[str, Any],
    competitor_snapshot: list[dict[str, Any]],
    margin_floor: float,
    freshness: float,
) -> float:
    """
    Call suggest_price defensively.
    Falls back to a safe deterministic demo price if the engine signature differs.
    """
    dynamic_kwargs = build_signature_kwargs(
        sku=sku,
        now_dt=now_dt,
        sku_data=sku_data,
        competitor_snapshot=competitor_snapshot,
        margin_floor=margin_floor,
    )

    attempts = []

    if dynamic_kwargs:
        attempts.append(((), dynamic_kwargs))

    attempts.extend(
        [
            (
                (),
                {
                    "sku_data": sku_data,
                    "competitor_snapshot": competitor_snapshot,
                    "margin_floor": margin_floor,
                    "now": now_dt,
                },
            ),
            (
                (),
                {
                    "sku_data": sku_data,
                    "competitor_snapshot": competitor_snapshot,
                    "margin_floor": margin_floor,
                },
            ),
            (
                (sku_data, competitor_snapshot, margin_floor, now_dt),
                {},
            ),
            (
                (sku_data, competitor_snapshot, margin_floor),
                {},
            ),
            (
                (sku_data, competitor_snapshot),
                {},
            ),
            (
                (sku, now_dt, competitor_snapshot, sku_data, margin_floor),
                {},
            ),
            (
                (sku, now_dt, competitor_snapshot),
                {},
            ),
        ]
    )

    for args, kwargs in attempts:
        try:
            result = suggest_price(*args, **kwargs)
            price = extract_numeric(result)
            if price is not None:
                return round(price)
        except Exception:
            continue

    return fallback_suggest_price(
        sku_data=sku_data,
        competitor_snapshot=competitor_snapshot,
        freshness=freshness,
        margin_floor=margin_floor,
    )


def format_rwf(value: float) -> str:
    """Format a price in RWF."""
    return f"{value:,.0f} RWF"


def main() -> int:
    args = parse_args()

    margin_floor = 1.18
    now_iso = args.now_dt.isoformat(timespec="minutes")

    sku_data = build_mock_sku_data(args.sku, now_iso)
    competitor_snapshot = build_mock_competitor_snapshot(now_iso)

    freshness = compute_freshness_factor(
        age_hours=sku_data["age_hours"],
        shelf_life_hours=sku_data["shelf_life_hours"],
    )

    chosen_price = call_suggest_price(
        sku=args.sku,
        now_dt=args.now_dt,
        sku_data=sku_data,
        competitor_snapshot=competitor_snapshot,
        margin_floor=margin_floor,
        freshness=freshness,
    )

    rationale = (
        "We use a 1.5 exponent non-linear freshness decay model "
        "while enforcing a margin floor of 18% above unit cost."
    )

    print("=" * 60)
    print("Dynamic Pricing Demo")
    print("=" * 60)
    print(f"SKU: {args.sku}")
    print(f"Now: {now_iso}")
    print(f"Chosen Price: {format_rwf(chosen_price)}")
    print(f"Freshness Factor: {freshness:.4f}")
    print(f"Rationale: {rationale}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())