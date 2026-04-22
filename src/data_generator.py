from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# Global random seed required by the challenge specification.
np.random.seed(42)


REFERENCE_TIME = pd.Timestamp("2026-04-22 08:00:00")
PRODUCTS: Dict[str, Dict[str, float]] = {
    "tomato": {
        "shelf_life_hours": 72,
        "unit_cost_min": 300,
        "unit_cost_max": 420,
        "p_ref": 650,
        "q0": 18,
        "alpha": 1.6,
    },
    "milk": {
        "shelf_life_hours": 24,
        "unit_cost_min": 350,
        "unit_cost_max": 500,
        "p_ref": 800,
        "q0": 12,
        "alpha": 1.8,
    },
    "tilapia": {
        "shelf_life_hours": 18,
        "unit_cost_min": 420,
        "unit_cost_max": 500,
        "p_ref": 1200,
        "q0": 9,
        "alpha": 2.0,
    },
    "banana": {
        "shelf_life_hours": 120,
        "unit_cost_min": 300,
        "unit_cost_max": 380,
        "p_ref": 550,
        "q0": 15,
        "alpha": 1.3,
    },
}

SUPPLIERS: Dict[str, List[str]] = {
    "tomato": ["Green Valley Co-op", "Mfoundi Fresh", "Sahel Produce Hub"],
    "milk": ["LactoPlus", "DairyLink", "ColdChain Foods"],
    "tilapia": ["LakeFresh Fisheries", "BlueWater Supply", "RiverNet Foods"],
    "banana": ["Tropic Harvest", "Banana Brothers", "SunBelt Produce"],
}

STALL_IDS = [f"stall_{i:02d}" for i in range(1, 13)]


def get_project_paths() -> Tuple[Path, Path]:
    """Resolve the project root and data directory relative to this script.

    If the script is inside a src/ folder, the project root is taken as the
    parent of src/. Otherwise, the folder containing the script is treated as
    the project root.

    Returns:
        Tuple[Path, Path]: The project root path and the data directory path.
    """
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent

    if script_dir.name == "src":
        project_root = script_dir.parent
    else:
        project_root = script_dir

    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    return project_root, data_dir


def build_time_grid(
    end_time: pd.Timestamp,
    hours: int = 48,
    freq: str = "30min"
) -> pd.DatetimeIndex:
    """Build a reproducible chronological timestamp grid.

    Args:
        end_time (pd.Timestamp): The final timestamp of the grid.
        hours (int, optional): The total lookback window in hours. Defaults to 48.
        freq (str, optional): The grid frequency. Defaults to "30min".

    Returns:
        pd.DatetimeIndex: A pandas DatetimeIndex covering the requested period.
    """
    step = pd.Timedelta(freq)
    total_duration = pd.Timedelta(hours=hours)

    periods = int(total_duration / step)
    start_time = end_time - total_duration + step

    return pd.date_range(start=start_time, periods=periods, freq=freq)


def generate_stock_data(
    n_rows: int = 120,
    reference_time: pd.Timestamp = REFERENCE_TIME
) -> pd.DataFrame:
    """Generate synthetic stock procurement data.

    Args:
        n_rows (int, optional): Total number of stock records. Defaults to 120.
        reference_time (pd.Timestamp, optional): The anchor time for purchase age
            calculations. Defaults to REFERENCE_TIME.

    Returns:
        pd.DataFrame: Stock dataframe with procurement information in RWF.
    """
    product_names = list(PRODUCTS.keys())
    base_rows = n_rows // len(product_names)
    remainder = n_rows % len(product_names)

    records = []
    sku_counter = 1

    for idx, product in enumerate(product_names):
        meta = PRODUCTS[product]
        rows_for_product = base_rows + (1 if idx < remainder else 0)

        for _ in range(rows_for_product):
            max_age = min(meta["shelf_life_hours"] * 0.95, meta["shelf_life_hours"] - 1)
            age_hours = np.random.uniform(1, max(2, max_age))
            purchased_at = reference_time - pd.Timedelta(hours=float(age_hours))

            records.append(
                {
                    "sku_id": f"SKU{sku_counter:04d}",
                    "product": product,
                    "purchased_at": purchased_at.round("min"),
                    "quantity": int(np.random.randint(8, 61)),
                    "unit_cost_rwf": int(
                        np.random.randint(meta["unit_cost_min"], meta["unit_cost_max"] + 1)
                    ),
                    "shelf_life_hours": int(meta["shelf_life_hours"]),
                    "supplier": np.random.choice(SUPPLIERS[product]),
                }
            )
            sku_counter += 1

    stock_df = pd.DataFrame(records).sort_values(["product", "purchased_at", "sku_id"])
    return stock_df.reset_index(drop=True)


def generate_competitor_prices(
    time_grid: pd.DatetimeIndex
) -> pd.DataFrame:
    """Simulate competitor prices across multiple stalls.

    The simulation includes daily oscillations, small stall-level bias,
    and a morning premium.

    Args:
        time_grid (pd.DatetimeIndex): The chronological timestamps to evaluate.

    Returns:
        pd.DataFrame: Competitor pricing records denominated in RWF.
    """
    records = []

    for product, meta in PRODUCTS.items():
        p_ref = meta["p_ref"]

        for stall_id in STALL_IDS:
            stall_mean = p_ref * np.random.uniform(0.95, 1.05)
            phase_shift = np.random.uniform(0, 2 * np.pi)
            stall_bias = np.random.uniform(-0.03, 0.03)

            for ts in time_grid:
                minutes_since_start = (ts - time_grid[0]).total_seconds() / 60.0
                hour = ts.hour + ts.minute / 60.0

                daily_wave = 0.07 * np.sin(
                    (2 * np.pi * minutes_since_start / (24 * 60)) + phase_shift
                )
                morning_premium = 0.05 if 6 <= hour < 10 else 0.0
                noise = np.random.normal(0, 0.012)

                ratio = np.clip(
                    1.0 + stall_bias + daily_wave + morning_premium + noise,
                    0.85,
                    1.15,
                )
                competitor_price = max(50, round(stall_mean * ratio))

                records.append(
                    {
                        "timestamp": ts,
                        "product": product,
                        "stall_id": stall_id,
                        "competitor_price_rwf": int(competitor_price),
                    }
                )

    price_df = pd.DataFrame(records).sort_values(["timestamp", "product", "stall_id"])
    return price_df.reset_index(drop=True)


def compute_freshness_factor(
    stock_df: pd.DataFrame,
    product: str,
    timestamp: pd.Timestamp
) -> float:
    """Calculate the weighted freshness degradation for a product.

    The freshness formula is:
        max(0, 1 - (age / shelf_life)^1.5)

    A hard floor of 0.05 is applied to avoid total demand collapse.

    Args:
        stock_df (pd.DataFrame): Stock dataframe containing active inventory.
        product (str): Product identifier.
        timestamp (pd.Timestamp): Evaluation timestamp.

    Returns:
        float: Freshness factor bounded in [0.05, 1.0].
    """
    product_stock = stock_df[stock_df["product"] == product].copy()
    age_hours = (timestamp - product_stock["purchased_at"]).dt.total_seconds() / 3600.0

    active_mask = (age_hours >= 0) & (age_hours <= product_stock["shelf_life_hours"])
    active_stock = product_stock.loc[active_mask].copy()

    if active_stock.empty or active_stock["quantity"].sum() == 0:
        return 0.05

    active_age_hours = (timestamp - active_stock["purchased_at"]).dt.total_seconds() / 3600.0
    sl_hours = active_stock["shelf_life_hours"]

    decay_metric = np.maximum(0.0, 1.0 - (active_age_hours / sl_hours) ** 1.5)
    weighted_freshness = np.average(decay_metric, weights=active_stock["quantity"])

    return float(np.clip(weighted_freshness, 0.05, 1.0))


def generate_sales_history(
    stock_df: pd.DataFrame,
    competitor_df: pd.DataFrame,
    time_grid: pd.DatetimeIndex
) -> pd.DataFrame:
    """Generate synthetic sales history using the exponential demand curve.

    Demand model:
        Q(p) = Q0 * exp(-alpha * (p - p_ref) / p_ref) * freshness_factor

    Args:
        stock_df (pd.DataFrame): Stock dataframe.
        competitor_df (pd.DataFrame): Competitor pricing history.
        time_grid (pd.DatetimeIndex): The chronological evaluation grid.

    Returns:
        pd.DataFrame: Sales history dataframe with demand drivers in RWF.
    """
    records = []

    competitor_mean = (
        competitor_df.groupby(["timestamp", "product"], as_index=False)["competitor_price_rwf"]
        .mean()
        .rename(columns={"competitor_price_rwf": "competitor_mean_price_rwf"})
    )

    for ts in time_grid:
        current_prices = competitor_mean[competitor_mean["timestamp"] == ts]

        for _, row in current_prices.iterrows():
            product = row["product"]
            meta = PRODUCTS[product]
            p_ref = meta["p_ref"]
            q0 = meta["q0"]
            alpha = meta["alpha"]

            freshness_factor = compute_freshness_factor(stock_df, product, ts)

            # Simple pricing strategy: stay close to the market average
            offered_price = row["competitor_mean_price_rwf"] * np.random.uniform(0.96, 1.04)
            offered_price = int(max(50, round(offered_price)))

            expected_demand = q0 * np.exp(
                -alpha * (offered_price - p_ref) / p_ref
            ) * freshness_factor
            expected_demand = max(0.05, expected_demand)

            units_sold = int(np.random.poisson(expected_demand))

            records.append(
                {
                    "timestamp": ts,
                    "product": product,
                    "offered_price_rwf": offered_price,
                    "competitor_mean_price_rwf": round(float(row["competitor_mean_price_rwf"]), 2),
                    "p_ref_rwf": int(p_ref),
                    "q0": float(q0),
                    "alpha": float(alpha),
                    "freshness_factor": round(float(freshness_factor), 4),
                    "expected_demand": round(float(expected_demand), 4),
                    "units_sold": units_sold,
                }
            )

    sales_df = pd.DataFrame(records).sort_values(["timestamp", "product"])
    return sales_df.reset_index(drop=True)


def save_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Save a pandas DataFrame to CSV.

    Args:
        df (pd.DataFrame): The dataframe to export.
        output_path (Path): The destination path.
    """
    df.to_csv(output_path, index=False)


def main() -> None:
    """Generate and save all datasets for the AIMS KTT challenge."""
    _, data_dir = get_project_paths()
    time_grid = build_time_grid(REFERENCE_TIME, hours=48, freq="30min")

    stock_df = generate_stock_data(n_rows=120, reference_time=REFERENCE_TIME)
    competitor_df = generate_competitor_prices(time_grid=time_grid)
    sales_df = generate_sales_history(
        stock_df=stock_df,
        competitor_df=competitor_df,
        time_grid=time_grid,
    )

    save_csv(stock_df, data_dir / "stock.csv")
    save_csv(competitor_df, data_dir / "competitor_prices.csv")
    save_csv(sales_df, data_dir / "sales_history.csv")

    print(f"Generated files in: {data_dir}")
    print(f"- stock.csv: {len(stock_df):,} rows")
    print(f"- competitor_prices.csv: {len(competitor_df):,} rows")
    print(f"- sales_history.csv: {len(sales_df):,} rows")


if __name__ == "__main__":
    main()