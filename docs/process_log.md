# Process Log: AI-Augmented Engineering Workflow
**Lead Architect:** Jerome Teyi  
**Project:** Perishable Goods Dynamic Pricer (AIMS KTT 2026)

---

## 1. Methodology: The Human-in-the-Loop Orchestration
Rather than simply generating code, I designed a **multi-stage pipeline** where I acted as the System Architect. I leveraged specialized AI personas as "expert modules" to accelerate development while maintaining strict control over the mathematical constraints and business logic required by the KTT brief.

### My Role as Architect:
* **Mathematical Modeling:** I mandated the use of a non-linear decay function (1.5 power) to accurately reflect biological reality.
* **Constraint Enforcement:** I manually defined the `margin_floor` logic (1.18) to ensure vendor sustainability.
* **System Validation:** I performed critical audits of the AI-generated outputs, specifically fixing "greedy" optimization bugs that appeared in early simulations.

---

## 2. Technical Justifications & Human Decisions

### Why the 1.5 Exponent Decay?
I directed the engine to implement: $f = \max(0, 1 - (age/SL)^{1.5})$. 
* **The Decision:** Linear decay is too simplistic for agricultural products like tomatoes. 
* **The Logic:** I wanted the price to stay stable during the "peak freshness" phase and only drop aggressively once the product enters its critical degradation phase. This protects the vendor's early-day margins.

### Handling the "Greedy Optimizer" Bug
During the first simulation run, I noticed the AI kept prices too high, leading to a massive **-442% waste reduction** (more waste than the baseline). 
* **My Intervention:** I identified that the AI was prioritizing immediate unit margin over inventory turnover. 
* **The Fix:** I re-engineered the prompt to increase the price elasticity ($\alpha$) in the demand model and forced an earlier markdown trigger. This intervention brought the waste reduction back into a positive, profitable range.

---

## 3. Workflow Chronology

1.  **System Design:** I defined the folder structure and the interaction protocol between the `math_engine.py` and the CLI wrapper.
2.  **Data Synthesis:** I tasked the AI with generating synthetic CSVs strictly following my demand parameters ($Q_0$, $\alpha$).
3.  **Core Implementation:** I used AI to boilerplate the `math_engine.py` functions while I manually reviewed the implementation of the 1.5 exponent.
4.  **Refactoring:** I integrated the `margin_floor` security check to ensure the code remains robust during the live demo.
5.  **Simulation & Correction:** I used the `simulation.ipynb` results as a feedback loop to fine-tune the pricing sensitivity.

---

## 4. AI Prompting Strategy
I utilized **Chain-of-Thought prompting** to ensure high-quality, bug-free output:
* **Backend Persona:** Used for clean, typed Python code.
* **Economist Persona:** Used to validate that our "Rationale" text made sense for a real-world market environment.
* **Zero-Shot Prompting:** Used for rapid CSV generation.
* **Contextual Prompting:** Used for the complex optimization loop to ensure the $1.5$ exponent was not hallucinated.