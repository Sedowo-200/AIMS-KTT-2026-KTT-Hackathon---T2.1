# SMS Distribution Design: Offline Market Alerts
**Project:** AIMS KTT Dynamic Pricer  
**Design Goal:** Low-bandwidth communication for market vendors using feature phones (GSM).

---

## 📱 Design Constraints
- **Character Limit:** Max 160 characters per message (to avoid multi-part SMS costs).
- **Language:** Simple, actionable English.
- **Frequency:** Sent at 08:00 (Market Opening), 13:00 (Mid-day Check), and 16:00 (Flash Sale).

---

## 📩 SMS Templates (Examples)

### 1. Morning Price Setting (High Freshness)
> **[AIMS-Price]** SKU: TOM_023. Freshness: 98%. 
> Market Avg: 500 RWF. 
> Your Target Price: 500 RWF. 
> Status: Premium Quality. Keep price firm.

### 2. Mid-day Adjustment (Minor Decay)
> **[AIMS-Price]** SKU: TOM_023. Freshness: 65%. 
> Recommended Price: 410 RWF. 
> Rationale: Slight decay detected. Apply a 15% discount to maintain sales volume.

### 3. Flash Sale / Clearance (Critical)
> **[AIMS-Alert]** SKU: BAN_005. Freshness: 15%. 
> CLEARANCE PRICE: 150 RWF. 
> Action: Floor price reached. Sell all stock immediately to avoid 100% waste!

---

## 🛠️ Technical Implementation Logic
- **Automated Trigger:** The `math_engine.py` generates these strings automatically when `freshness` crosses specific thresholds (0.70, 0.40, and 0.20).
- **Vendor Response:** Vendors can reply with "OK" to confirm the price change or "DISPUTE [Price]" to trigger the crowd-sourced correction logic.
- **Character Count:** - Template 1: ~125 chars.
    - Template 2: ~135 chars.
    - Template 3: ~130 chars.
*(All within the 160-character GSM budget).*