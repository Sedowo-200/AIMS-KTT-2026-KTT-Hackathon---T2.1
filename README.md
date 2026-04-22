# 🥦 Perishable Goods Dynamic Pricer
### AIMS Knowledge Transfer & Training (KTT) Hackathon 2026 — Track 1.3
**Author:** Jerome Teyi | **Date:** 22 April 2026

---

## 📌 Project Title

**Perishable Goods Dynamic Pricer** — An AI-powered, real-time pricing engine for short shelf-life retail products in African informal markets, built to run under low-connectivity conditions.

---

## 🏆 Challenge Overview

Vendors in Sub-Saharan African open markets (e.g., Rwanda's informal grocery stalls) routinely suffer 30–50% post-harvest losses because they cannot react fast enough to freshness decay, competitor price shifts, or unsold stock. The AIMS KTT challenge asked participants to build a dynamic pricing system that:

- Implements a **non-linear freshness decay model** (`f = max(0, 1 − (age/shelf_life)^1.5)`)
- Uses a **log-linear demand curve** (`Q(p) = Q₀ · exp(−α · (p − p_ref)/p_ref) · f`)
- Optimizes profit while respecting a **hard margin floor** (≥ 18% above unit cost)
- Delivers price recommendations even **without internet access** (SMS / offline-first design)
- Simulates across 4 products (tomato, milk, tilapia, banana) denominated in **RWF**

---

## 💡 Solution Summary

This solution implements a **waste-aware numerical pricing optimizer** built entirely in Python with no ML framework dependency. Key engineering decisions:

| Feature | Approach |
|---|---|
| Freshness decay | Non-linear power law: exponent **1.5** |
| Demand model | Log-linear exponential with `α ≥ 2.5` floor |
| Price optimization | Grid search over 1 024 candidate prices |
| Waste penalty | Dynamic urgency multiplier (`freshness × expiry urgency`) |
| Margin protection | Hard floor: `price ≥ unit_cost × 1.18` |
| Offline delivery | SMS price-sheets via 160-char GSM templates |
| Data pipeline | Fully synthetic, reproducible (seed = 42) |

The optimizer balances **profit maximization** against an **inventory sell-through penalty** so that, as a SKU approaches expiry, the engine actively lowers prices rather than hoarding stock at high margins.

---

## 🗂️ Repository Structure

```
AIMS_KTT_JEROME_TEYI_2026/
│
├── pricer.py                  # CLI entry point — live pricing demo
│
├── src/
│   ├── math_engine.py         # Core pricing engine (freshness, demand, optimizer)
│   └── data_generator.py      # Synthetic dataset generator (seed=42)
│
├── data/
│   ├── stock.csv              # 120 procurement records (4 products, 12 stalls)
│   ├── competitor_prices.csv  # 48-hour competitor price snapshots (30-min grid)
│   └── sales_history.csv      # Simulated sales demand history
│
├── docs/
│   ├── process_log.md         # Engineering decisions & AI tool declarations
│   └── sms_pricesheet.md      # Offline SMS alert templates (GSM 160-char format)
│
├── src/simulation_rwf.ipynb   # Full end-to-end simulation notebook
│
├── requirements.txt           # Python dependencies
├── SIGNED.md                  # Honor code declaration
└── README.md                  # This file
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python **3.10+**
- `pip` or a virtual environment manager

### 1. Clone the repository
```bash
git clone https://drive.google.com/drive/folders/1JRxm3EulW72O9pQ4DUiLBMckAzj4fJ1J
cd AIMS_KTT_JEROME_TEYI_2026
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

**Dependencies:**
```
numpy>=1.26,<3.0
pandas>=2.2,<3.0
matplotlib>=3.8,<4.0
scipy>=1.13,<2.0
jupyter>=1.0,<2.0
ipykernel>=6.29,<7.0
notebook>=7.0,<8.0
```

---

## 📊 How to Generate Data

The synthetic dataset is fully reproducible (global seed = 42). Run the data generator from the project root:

```bash
python -m src.data_generator
```

This produces **3 CSV files** inside `data/`:

| File | Rows | Description |
|---|---|---|
| `stock.csv` | 120 | Procurement records per SKU (product, cost, age, supplier) |
| `competitor_prices.csv` | ~9 216 | 30-min competitor price snapshots across 12 stalls × 4 products × 48 h |
| `sales_history.csv` | ~384 | Demand outcomes per product per time slot |

Products covered: **tomato** (72h shelf life), **milk** (24h), **tilapia** (18h), **banana** (120h).

---

## 🚀 How to Run the Pricer / Simulator

### Option A — CLI Pricer (single SKU, live demo)

```bash
python pricer.py --sku <SKU_ID> --now <ISO_TIMESTAMP>
```

The pricer will:
1. Load the mathematical engine from `src/math_engine.py`
2. Compute the freshness factor using the 1.5-exponent formula
3. Fetch competitor price benchmarks
4. Run the waste-aware numerical optimizer
5. Print the recommended price with full rationale

### Option B — Full Simulation Notebook

Launch Jupyter and open `src/simulation_rwf.ipynb`:

```bash
jupyter notebook src/simulation_rwf.ipynb
```

Run all cells to simulate the full 48-hour pricing cycle and view:
- Revenue and waste comparison (AI pricer vs. baseline)
- Freshness decay curves per product
- Price trajectories and markdown triggers
- Demand sensitivity plots

---

## 💻 Sample Command

```bash
python pricer.py --sku TOM_023 --now 2026-04-20T15:30
```

**Expected output:**
```
============================================================
Dynamic Pricing Demo
============================================================
SKU          : TOM_023
Now          : 2026-04-20T15:30
Chosen Price : 1,244 RWF
Freshness    : 0.7071
Rationale    : We use a 1.5 exponent non-linear freshness decay model
               while enforcing a margin floor of 18% above unit cost.
============================================================
```

---

## 📤 Outputs Produced

| Output | Location | Description |
|---|---|---|
| Recommended price (RWF) | `stdout` | Single best price for the queried SKU |
| Freshness factor | `stdout` | Value in [0, 1] using the 1.5-exponent decay |
| Rationale string | `stdout` | Human-readable pricing justification |
| Stock CSV | `data/stock.csv` | Synthetic procurement inventory |
| Competitor CSV | `data/competitor_prices.csv` | Market price landscape |
| Sales history CSV | `data/sales_history.csv` | Simulated demand outcomes |
| Simulation plots | Notebook cells | Revenue, waste, freshness, and demand charts |
| SMS price-sheets | `docs/sms_pricesheet.md` | Offline alert templates for GSM feature phones |

---

## 📈 Business Impact

Based on the simulation results from `simulation_rwf.ipynb`:

- **Waste reduction:** The AI pricer triggers markdowns earlier and more aggressively than a static-price baseline, reducing unsold expired stock.
- **Margin protection:** The hard 18% margin floor ensures vendors never sell below cost — critical for micro-entrepreneur sustainability.
- **Revenue uplift:** By staying competitive with local market prices (median competitor anchoring) while accounting for freshness, the engine captures more demand during peak hours.
- **Equity by design:** The system is calibrated to informal African markets (RWF currency, small-batch SKUs, 8–60 unit quantities), not large supermarket chains.

---

## 📵 Low-Connectivity Deployment Note

A key design constraint of this project is **offline-first delivery**. Many vendors in Rwandan open-air markets use feature phones without data plans. The solution addresses this with:

- **SMS price-sheet templates** (`docs/sms_pricesheet.md`): Pre-formatted 160-character GSM messages that can be sent via automated SMS gateway (e.g., Africa's Talking).
- **Three daily dispatch windows:** 08:00 (market open), 13:00 (midday adjustment), 16:00 (flash sale / clearance alert).
- **No internet required at the vendor side:** The engine runs server-side; vendors receive only the final recommended price and action via SMS.
- **Vendor feedback loop:** Vendors can reply `OK` to confirm or `DISPUTE [Price]` to trigger crowd-sourced correction.

| SMS Type | Freshness Threshold | Action |
|---|---|---|
| Premium / Hold | ≥ 70% | Keep price firm at market average |
| Adjustment | 40–70% | Apply ~15% discount, maintain volume |
| Flash Sale / Clearance | ≤ 20% | Floor price — sell all stock immediately |

---

## 📦 Submission Assets

| Asset | Link / Location |
|---|---|
| **Repository (Google Drive)** | [https://drive.google.com/drive/folders/1JRxm3EulW72O9pQ4DUiLBMckAzj4fJ1J?usp=sharing](https://drive.google.com/drive/folders/1JRxm3EulW72O9pQ4DUiLBMckAzj4fJ1J?usp=sharing) |
| **Pricing Model** | `src/math_engine.py` — `suggest_price()` function |
| **Data Generator Script** | `src/data_generator.py` — run with `python -m src.data_generator` |
| **Simulation Notebook** | `src/simulation_rwf.ipynb` |
| **Demo Video** | *(To be added — record `python pricer.py --sku TOM_023 --now 2026-04-20T15:30` as screen capture)* |

---

## 🔏 Honor Code

> *"I will use any LLM or coding-assistant tool I find useful, and I will declare each tool I use, why I used it, and three sample prompts in my process_log.md. I will not have another human do my work. I will defend my own code in the Live Defense session. I understand undeclared LLM or human assistance is grounds for disqualification."*

**Signed:** Jerome Teyi — 22 April 2026

See [`SIGNED.md`](./SIGNED.md) and [`docs/process_log.md`](./docs/process_log.md) for full AI tool declarations and engineering decisions.

---

*Built for the AIMS KTT Hackathon 2026 · Prices denominated in Rwandan Franc (RWF) · Seed 42*
