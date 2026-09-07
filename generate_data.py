"""
Synthetic Bank Customer Churn Dataset Generator
-------------------------------------------------
Produces a CSV matching the schema of the classic bank-churn dataset
(CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure,
Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited)
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 10000

FIRST_SURNAMES = [
    "Hargrove", "Delacroix", "Whitfield", "Osei", "Nakamura", "Petrov",
    "Fontaine", "Okafor", "Bergstrom", "Rousseau", "Mendez", "Kowalski",
    "Iyer", "Falk", "Sorensen", "Duarte", "Weiss", "Abubakar", "Lindqvist",
    "Castellano", "Novak", "Girard", "Odom", "Thibault", "Reyes", "Marchetti",
    "Kessler", "Adeyemi", "Voss", "Laurent", "Schmitt", "Balogh", "Renner",
    "Okonkwo", "Fairweather", "Dubois", "Hallgren", "Marceau", "Winters", "Aoki",
]

geographies = RNG.choice(["France", "Spain", "Germany"], size=N, p=[0.50, 0.25, 0.25])
gender = RNG.choice(["Male", "Female"], size=N, p=[0.545, 0.455])
age = np.clip(RNG.normal(38.5, 10.2, N), 18, 92).round().astype(int)
tenure = RNG.integers(0, 11, N)
credit_score = np.clip(RNG.normal(650, 96, N), 350, 850).round().astype(int)

zero_balance_mask = RNG.random(N) < 0.36
balance = np.where(
    zero_balance_mask, 0.0,
    np.clip(RNG.normal(112000, 50000, N), 3000, 260000)
).round(2)

num_of_products = RNG.choice([1, 2, 3, 4], size=N, p=[0.51, 0.40, 0.07, 0.02])
has_cr_card = RNG.choice([0, 1], size=N, p=[0.29, 0.71])

active_base_prob = 0.52
active_prob = np.clip(
    active_base_prob - 0.001 * (age - 38) + (~zero_balance_mask) * 0.03,
    0.15, 0.85
)
is_active_member = (RNG.random(N) < active_prob).astype(int)

estimated_salary = np.clip(RNG.normal(100000, 57500, N), 1000, 200000).round(2)

logit = np.full(N, -1.35)
logit += np.where(is_active_member == 1, -0.95, 0.85)
product_effect = {1: 0.35, 2: -0.55, 3: 1.55, 4: 2.15}
logit += np.array([product_effect[p] for p in num_of_products])
logit += np.where(geographies == "Germany", 0.55, 0.0)
logit += np.where(geographies == "Spain", -0.10, 0.0)
logit += 0.018 * (age - 38)
logit += np.where(gender == "Female", 0.12, 0.0)
logit += np.where(has_cr_card == 1, -0.10, 0.05)

high_balance_thresh = np.quantile(balance, 0.75)
at_risk_premium = (balance >= high_balance_thresh) & (is_active_member == 0)
logit += np.where(at_risk_premium, 0.55, 0.0)
logit += np.where(tenure <= 1, 0.20, 0.0)
logit += RNG.normal(0, 0.35, N)

churn_prob = 1 / (1 + np.exp(-logit))
exited = (RNG.random(N) < churn_prob).astype(int)

surname = RNG.choice(FIRST_SURNAMES, size=N)

df = pd.DataFrame({
    "CustomerId": np.arange(15600000, 15600000 + N),
    "Surname": surname,
    "CreditScore": credit_score,
    "Geography": geographies,
    "Gender": gender,
    "Age": age,
    "Tenure": tenure,
    "Balance": balance,
    "NumOfProducts": num_of_products,
    "HasCrCard": has_cr_card,
    "IsActiveMember": is_active_member,
    "EstimatedSalary": estimated_salary,
    "Exited": exited,
})

df.to_csv("data/churn_data.csv", index=False)
print(f"Generated {len(df)} rows -> data/churn_data.csv")
print(f"Overall churn rate: {df['Exited'].mean():.3%}")
