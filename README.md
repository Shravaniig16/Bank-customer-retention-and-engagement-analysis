# Customer Retention Intelligence

A client-facing analytics platform quantifying how engagement, product depth,
and balance levels relate to customer churn in retail banking, and flagging
high-value customers who are disengaging silently.

## Why this deploys cleanly

Earlier versions of this app crashed on Streamlit Community Cloud with a
`FileNotFoundError` if `data/churn_data.csv` wasn't present in the deployed
repository (e.g. an upload that silently missed the data folder, or a
case-sensitivity mismatch between Windows and Linux paths). This version
fixes that at the source: `generate_data.py` exposes `generate_dataset()` as
a plain function, and `app.py` calls it automatically as a fallback if the
CSV is missing on disk for any reason. **The app cannot crash from a missing
data file** — worst case, it silently regenerates the sample dataset in
memory and shows a note in the sidebar's validation panel.

## What's inside

- `app.py` — the Streamlit application (6 modules + sidebar filters + KPI strip)
- `design_system.py` — color/type tokens and reusable HTML components
- `utils.py` — data validation, engagement segmentation, KPI logic, churn model
- `generate_data.py` — synthetic dataset generator, both a callable function and a script
- `.streamlit/config.toml` — theme configuration
- `data/churn_data.csv` — bundled 10,000-row sample dataset
- `requirements.txt` — every package the app needs, pinned to minimum versions
- `.gitignore` — excludes venv, cache files, and Word docs from version control

## Local setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploying to Streamlit Community Cloud

1. Push this entire folder to a **public** GitHub repository (everything
   except what's in `.gitignore`).
2. On GitHub, double check `data/churn_data.csv` actually shows up in the
   repo's file listing — this is the single most common deployment failure.
3. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **Create app**, pick your repo, branch `main`, main file
   `app.py`, and click Deploy.
4. Even if step 2 goes wrong and the CSV doesn't make it into the repo, the
   app will still boot successfully using the in-memory fallback described
   above — you'll just see a note in the sidebar instead of a crash.

## Using your own data

Use the "Upload customer data" control in the sidebar. Required columns
(case-sensitive): CustomerId, Surname, CreditScore, Geography, Gender, Age,
Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary,
Exited. The app validates on upload — non-binary flags are coerced to 0/1,
duplicate CustomerIds are dropped, missing numeric values are median-filled.

## Modules

1. **Overview** — problem framing, how to use the dashboard, at-a-glance
   engagement breakdown, and an Excel export of the current filtered view.
2. **Engagement vs Churn** — churn by activity status and engagement profile,
   with drill-down into any profile's customer list.
3. **Product Utilization** — churn by product count, surfacing the
   two-product sweet spot.
4. **High-Value Disengaged** — adjustable thresholds, a "silent churn"
   watchlist with CSV export, and a salary-balance mismatch detector.
5. **Retention Strength** — the composite 0-100 Relationship Strength Index.
6. **What-If Simulator** — live churn probability for a hypothetical
   customer, with a comparison of which single intervention reduces risk most.
