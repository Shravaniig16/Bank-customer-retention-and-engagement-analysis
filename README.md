# Customer Retention Intelligence

A client-facing analytics platform quantifying how engagement, product depth,
and balance levels relate to customer churn in retail banking, and flagging
high-value customers who are disengaging silently.

## Design

Built as a "statement" aesthetic — navy and brass palette (`design_system.py`),
Fraunces for display type, Inter for body/UI, and IBM Plex Mono (tabular
figures) for all KPI numbers, evoking a bank statement / ledger. KPI values
render as ledger cards with a hairline gold top border; the landing hero
mirrors a statement header band.

## What's inside

- `app.py` — the Streamlit application (6 modules + sidebar filters + KPI strip)
- `design_system.py` — the color/type tokens and reusable HTML components (hero, KPI cards, badges)
- `utils.py` — data validation, engagement segmentation, KPI logic, and the churn risk model
- `generate_data.py` — generates the bundled synthetic sample dataset
- `.streamlit/config.toml` — Streamlit theme configuration
- `data/churn_data.csv` — 10,000-row synthetic dataset matching the standard
  bank-churn schema, with realistic relationships baked in (inactive members
  churn more, 1- and 3-4-product customers churn more than 2-product
  customers, Germany runs hotter than France/Spain, etc.)

## Setup

```bash
cd bank_churn_app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Opens in your browser at `http://localhost:8501`.

## Using your own data

Use the **"Upload customer data"** control in the sidebar. The file must
contain the same columns (case-sensitive): CustomerId, Surname, CreditScore,
Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard,
IsActiveMember, EstimatedSalary, Exited. The app validates on upload —
non-binary flags are coerced to 0/1, duplicate CustomerIds are dropped, and
missing numeric values are median-filled — with a summary of any fixes shown
in the sidebar.

## Modules

1. **Overview** — problem framing, how to use the dashboard, and an
   at-a-glance engagement-profile breakdown. The landing page for a first-time
   or client viewer.
2. **Engagement vs Churn** — churn by activity status, by the four engagement
   profiles, by geography, with a drill-down into any profile's customer list.
3. **Product Utilization** — churn by product count (surfaces the 2-product
   sweet spot), single vs multi-product comparison.
4. **High-Value Disengaged** — adjustable balance/salary percentile
   thresholds, a sortable "silent churn" watchlist with CSV export, and a
   salary–balance mismatch detector (high income, low balance at this
   institution).
5. **Retention Strength** — the composite 0–100 Relationship Strength Index
   and churn by strength tier.
6. **What-If Simulator** — build a hypothetical customer and get a live
   predicted churn probability, with a side-by-side comparison of which
   single intervention (activation, +1 product, card issuance) would reduce
   their risk the most, plus overall model feature importance.

## KPI definitions

| KPI | Definition |
|---|---|
| Engagement Retention Ratio | Retention rate of active members ÷ retention rate of inactive members |
| Product Depth Index | Retention-rate gap between the best-performing product tier and single-product customers |
| High-Balance Disengagement Rate | Share of top-quartile-balance customers who are currently inactive |
| Credit Card Stickiness Score | Retention-rate gap between cardholders and non-cardholders |
| Relationship Strength Index | Composite 0–100 score: activity (40%), product depth (30%), tenure (20%), card ownership (10%) |

## Engagement profile definitions

Each customer gets exactly one profile, in this priority order:

1. **Inactive High-Balance** — inactive, balance in the top quartile. The primary silent-churn flag.
2. **Inactive Disengaged** — inactive, balance below that threshold.
3. **Active Low-Product** — active with exactly 1 product.
4. **Active Engaged** — active with 2+ products.
