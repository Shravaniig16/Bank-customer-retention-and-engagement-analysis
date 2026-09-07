"""
Utility functions for the Customer Retention Intelligence dashboard.
Handles data validation, engagement segmentation, KPI computation, and the
what-if churn risk model.
"""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "CustomerId", "Surname", "CreditScore", "Geography", "Gender", "Age",
    "Tenure", "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember",
    "EstimatedSalary", "Exited",
]


def load_and_validate(path_or_buffer):
    df = pd.read_csv(path_or_buffer)
    warnings = []

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        warnings.append(f"Missing expected columns: {missing_cols}")

    for col in ["HasCrCard", "IsActiveMember", "Exited"]:
        if col in df.columns:
            bad = df[~df[col].isin([0, 1])]
            if len(bad) > 0:
                warnings.append(f"{col}: {len(bad)} rows had non-binary values; coerced to 0/1.")
                df[col] = df[col].apply(lambda v: 1 if v in [1, "1", True, "Yes", "yes"] else 0)

    if "CustomerId" in df.columns:
        dup_count = df["CustomerId"].duplicated().sum()
        if dup_count > 0:
            warnings.append(f"Removed {dup_count} duplicate CustomerId rows.")
            df = df.drop_duplicates(subset="CustomerId", keep="first")

    numeric_cols = ["CreditScore", "Age", "Tenure", "Balance", "NumOfProducts", "EstimatedSalary"]
    for col in numeric_cols:
        if col in df.columns and df[col].isna().any():
            n_null = df[col].isna().sum()
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            warnings.append(f"{col}: filled {n_null} missing values with median ({median_val:.1f}).")

    return df, warnings


def classify_engagement(df: pd.DataFrame, balance_pctl: float = 0.75) -> pd.DataFrame:
    df = df.copy()
    high_balance_threshold = df["Balance"].quantile(balance_pctl)

    def _profile(row):
        if row["IsActiveMember"] == 0 and row["Balance"] >= high_balance_threshold:
            return "Inactive High-Balance"
        if row["IsActiveMember"] == 0:
            return "Inactive Disengaged"
        if row["NumOfProducts"] == 1:
            return "Active Low-Product"
        return "Active Engaged"

    df["EngagementProfile"] = df.apply(_profile, axis=1)
    df["HighBalanceThreshold"] = high_balance_threshold
    return df


def compute_relationship_strength(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    product_component = np.minimum(df["NumOfProducts"], 2) / 2 * 30
    tenure_component = np.minimum(df["Tenure"], 10) / 10 * 20
    activity_component = df["IsActiveMember"] * 40
    card_component = df["HasCrCard"] * 10

    df["RelationshipStrengthScore"] = (
        activity_component + product_component + card_component + tenure_component
    ).round(1)

    bins = [-1, 25, 50, 75, 100]
    labels = ["Low", "Medium", "High", "Very High"]
    df["RelationshipStrengthTier"] = pd.cut(df["RelationshipStrengthScore"], bins=bins, labels=labels)
    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    kpis = {}
    if len(df) == 0:
        return {k: np.nan for k in [
            "engagement_retention_ratio", "product_depth_index",
            "high_balance_disengagement_rate", "credit_card_stickiness_score",
            "relationship_strength_index",
        ]}

    active = df[df["IsActiveMember"] == 1]
    inactive = df[df["IsActiveMember"] == 0]
    ret_active = 1 - active["Exited"].mean() if len(active) else np.nan
    ret_inactive = 1 - inactive["Exited"].mean() if len(inactive) else np.nan
    kpis["engagement_retention_ratio"] = (
        ret_active / ret_inactive if ret_inactive not in (0, np.nan) and not np.isnan(ret_inactive) else np.nan
    )
    kpis["retention_active"] = ret_active
    kpis["retention_inactive"] = ret_inactive

    by_product = df.groupby("NumOfProducts")["Exited"].agg(["mean", "count"])
    by_product["retention"] = 1 - by_product["mean"]
    kpis["product_depth_table"] = by_product
    if 1 in by_product.index and len(by_product) > 1:
        best_tier_retention = by_product["retention"].max()
        single_retention = by_product.loc[1, "retention"]
        kpis["product_depth_index"] = (best_tier_retention - single_retention) * 100
    else:
        kpis["product_depth_index"] = np.nan

    hb_threshold = df["Balance"].quantile(0.75)
    high_balance = df[df["Balance"] >= hb_threshold]
    kpis["high_balance_disengagement_rate"] = (
        (high_balance["IsActiveMember"] == 0).mean() if len(high_balance) else np.nan
    )
    kpis["high_balance_threshold"] = hb_threshold

    has_card = df[df["HasCrCard"] == 1]
    no_card = df[df["HasCrCard"] == 0]
    ret_card = 1 - has_card["Exited"].mean() if len(has_card) else np.nan
    ret_no_card = 1 - no_card["Exited"].mean() if len(no_card) else np.nan
    kpis["credit_card_stickiness_score"] = (
        (ret_card - ret_no_card) * 100 if not (np.isnan(ret_card) or np.isnan(ret_no_card)) else np.nan
    )

    if "RelationshipStrengthScore" in df.columns:
        kpis["relationship_strength_index"] = df["RelationshipStrengthScore"].mean()
    else:
        kpis["relationship_strength_index"] = np.nan

    return kpis


MODEL_NUMERIC_FEATURES = [
    "CreditScore", "Age", "Tenure", "Balance", "NumOfProducts",
    "HasCrCard", "IsActiveMember", "EstimatedSalary",
]
MODEL_CATEGORICAL_FEATURES = ["Geography", "Gender"]


def train_churn_model(df: pd.DataFrame):
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    X = df[MODEL_NUMERIC_FEATURES + MODEL_CATEGORICAL_FEATURES]
    y = df["Exited"]

    preprocessor = ColumnTransformer(transformers=[
        ("num", StandardScaler(), MODEL_NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), MODEL_CATEGORICAL_FEATURES),
    ])

    pipeline = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    pipeline.fit(X, y)
    return pipeline


def predict_churn_probability(pipeline, customer: dict) -> float:
    row = pd.DataFrame([customer])[MODEL_NUMERIC_FEATURES + MODEL_CATEGORICAL_FEATURES]
    return float(pipeline.predict_proba(row)[0, 1])


def get_model_feature_importance(pipeline) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    coefs = model.coef_[0]

    label_map = {
        "num__CreditScore": "Credit Score", "num__Age": "Age", "num__Tenure": "Tenure",
        "num__Balance": "Balance", "num__NumOfProducts": "Number of Products",
        "num__HasCrCard": "Has Credit Card", "num__IsActiveMember": "Active Member",
        "num__EstimatedSalary": "Estimated Salary",
    }
    labels = [label_map.get(f, f.replace("cat__", "").replace("_", ": ")) for f in feature_names]

    imp_df = pd.DataFrame({"Feature": labels, "Coefficient": coefs})
    imp_df["AbsCoefficient"] = imp_df["Coefficient"].abs()
    imp_df["Direction"] = imp_df["Coefficient"].apply(lambda c: "Increases churn risk" if c > 0 else "Reduces churn risk")
    return imp_df.sort_values("AbsCoefficient", ascending=False)


def identify_at_risk_premium(df: pd.DataFrame, balance_pctl: float = 0.75, salary_pctl: float = 0.5) -> pd.DataFrame:
    balance_threshold = df["Balance"].quantile(balance_pctl)
    salary_threshold = df["EstimatedSalary"].quantile(salary_pctl)
    at_risk = df[
        (df["IsActiveMember"] == 0)
        & (df["Balance"] >= balance_threshold)
        & (df["EstimatedSalary"] >= salary_threshold)
    ].copy()
    return at_risk.sort_values("Balance", ascending=False)


def identify_salary_balance_mismatch(df: pd.DataFrame, salary_pctl: float = 0.75, balance_pctl: float = 0.25) -> pd.DataFrame:
    """High income, low balance -- money likely not landing at this institution."""
    salary_threshold = df["EstimatedSalary"].quantile(salary_pctl)
    balance_threshold = df["Balance"].quantile(balance_pctl)
    mismatch = df[
        (df["EstimatedSalary"] >= salary_threshold) & (df["Balance"] <= balance_threshold)
    ].copy()
    return mismatch.sort_values("EstimatedSalary", ascending=False)
