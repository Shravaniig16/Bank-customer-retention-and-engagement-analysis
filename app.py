"""
Customer Retention Intelligence
=================================
A client-facing analytics platform quantifying how engagement, product
depth, and balance levels relate to churn, and flagging high-value
customers who are disengaging silently.
"""

import os
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st
from streamlit_option_menu import option_menu

from design_system import (
    CHART_COLORWAY, GOLD, GREEN, INK, MUTED, RED, SLATE,
    badge, hero_html, inject_css, kpi_card_html,
)
from generate_data import generate_dataset
from utils import (
    classify_engagement,
    compute_kpis,
    compute_relationship_strength,
    get_model_feature_importance,
    identify_at_risk_premium,
    identify_salary_balance_mismatch,
    load_and_validate,
    predict_churn_probability,
    train_churn_model,
)

st.set_page_config(
    page_title="Customer Retention Intelligence",
    page_icon="\u25C6",
    layout="wide",
)

st.markdown(inject_css(), unsafe_allow_html=True)

pio.templates["statement"] = pio.templates["plotly_white"]
pio.templates["statement"].layout.colorway = CHART_COLORWAY
pio.templates["statement"].layout.font = dict(family="Inter, sans-serif", color=INK, size=13)
pio.templates["statement"].layout.title.font = dict(family="Fraunces, serif", size=16, color=INK)
pio.templates["statement"].layout.paper_bgcolor = "rgba(0,0,0,0)"
pio.templates["statement"].layout.plot_bgcolor = "rgba(0,0,0,0)"
pio.templates.default = "statement"

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "churn_data.csv")

# ---------------------------------------------------------------------------
# Sidebar — branding + data + filters
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    f"""
    <div style="padding: 0.4rem 0 1rem 0;">
        <div style="font-family:'Fraunces',serif; font-size:1.3rem; font-weight:600; color:{INK};">
            &#9670; Retention Intelligence
        </div>
        <div style="font-family:'Inter',sans-serif; font-size:0.74rem; color:{MUTED}; letter-spacing:0.03em; text-transform:uppercase; margin-top:0.1rem;">
            Prepared for: European Central Bank
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.sidebar.file_uploader("Upload customer data (CSV)", type=["csv"])


@st.cache_data(show_spinner=False)
def _load_uploaded(path_or_buffer):
    return load_and_validate(path_or_buffer)


@st.cache_data(show_spinner=False)
def _load_default_or_generate(path: str):
    """Load the bundled sample CSV. If it's missing for any reason (e.g. a
    deployment where the data file didn't get uploaded, or a case-sensitive
    filesystem mismatch), regenerate the dataset in memory instead of
    crashing the app.
    """
    if os.path.exists(path):
        try:
            return load_and_validate(path)
        except Exception:
            pass
    df = generate_dataset()
    return df, ["Sample data file not found on disk — generated a fresh sample dataset in memory instead."]


if uploaded_file is not None:
    raw_df, warnings = _load_uploaded(uploaded_file)
    st.sidebar.success(f"Loaded {len(raw_df):,} customer records.")
else:
    raw_df, warnings = _load_default_or_generate(DEFAULT_DATA_PATH)
    st.sidebar.caption(f"Using sample dataset ({len(raw_df):,} records). Upload a file to replace it.")

if warnings:
    with st.sidebar.expander(f"Data validation notes ({len(warnings)})"):
        for w in warnings:
            st.write(f"- {w}")

st.sidebar.markdown("<hr class='gold-rule' style='margin:0.8rem 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("**Filters**")

geo_options = sorted(raw_df["Geography"].dropna().unique().tolist())
selected_geo = st.sidebar.multiselect("Geography", geo_options, default=geo_options)

engagement_filter = st.sidebar.radio("Engagement status", ["All", "Active only", "Inactive only"], index=0)

product_min, product_max = int(raw_df["NumOfProducts"].min()), int(raw_df["NumOfProducts"].max())
product_range = st.sidebar.slider("Number of products", product_min, product_max, (product_min, product_max))

balance_max = float(raw_df["Balance"].max())
balance_threshold = st.sidebar.slider("Minimum balance ($)", 0.0, float(round(balance_max, -3)), 0.0, step=1000.0)

salary_max = float(raw_df["EstimatedSalary"].max())
salary_threshold = st.sidebar.slider("Minimum estimated salary ($)", 0.0, float(round(salary_max, -3)), 0.0, step=1000.0)

df = raw_df[
    raw_df["Geography"].isin(selected_geo)
    & raw_df["NumOfProducts"].between(product_range[0], product_range[1])
    & (raw_df["Balance"] >= balance_threshold)
    & (raw_df["EstimatedSalary"] >= salary_threshold)
].copy()

if engagement_filter == "Active only":
    df = df[df["IsActiveMember"] == 1]
elif engagement_filter == "Inactive only":
    df = df[df["IsActiveMember"] == 0]

st.sidebar.markdown("<hr class='gold-rule' style='margin:0.8rem 0;'>", unsafe_allow_html=True)
st.sidebar.caption(f"**{len(df):,}** of {len(raw_df):,} customers match current filters.")

with st.sidebar.expander("Look up a customer"):
    search_term = st.text_input("CustomerId or Surname", key="customer_search")
    if search_term:
        matches = raw_df[
            raw_df["CustomerId"].astype(str).str.contains(search_term, case=False, na=False)
            | raw_df["Surname"].str.contains(search_term, case=False, na=False)
        ]
        if len(matches) == 0:
            st.write("No matches.")
        else:
            for _, row in matches.head(5).iterrows():
                status = "Churned" if row["Exited"] == 1 else "Retained"
                activity = "Active" if row["IsActiveMember"] == 1 else "Inactive"
                st.markdown(
                    f"**{row['CustomerId']} — {row['Surname']}**  \n"
                    f"{row['Geography']} · {activity} · {row['NumOfProducts']} product(s) · "
                    f"${row['Balance']:,.0f} · **{status}**"
                )

if len(df) == 0:
    st.warning("No customers match the current filters. Loosen a filter in the sidebar.")
    st.stop()

df = classify_engagement(df)
df = compute_relationship_strength(df)
kpis = compute_kpis(df)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    hero_html(
        eyebrow="Retail Banking · Prepared for the European Central Bank",
        title="Customer Retention Intelligence",
        subtitle=(
            "Quantifying how engagement, product depth, and balance relate to churn — "
            "and surfacing high-value customers disengaging silently, before they leave."
        ),
        figure=f"{df['Exited'].mean():.1%}",
        figure_label="Churn rate, filtered base",
    ),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI ledger strip
# ---------------------------------------------------------------------------

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card_html(
        "\u26A1 Engagement Retention Ratio",
        f"{kpis['engagement_retention_ratio']:.2f}x" if pd.notna(kpis['engagement_retention_ratio']) else "N/A",
        "Active vs. inactive retention",
    ), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card_html(
        "\U0001F4E6 Product Depth Index",
        f"{kpis['product_depth_index']:+.1f} pp" if pd.notna(kpis['product_depth_index']) else "N/A",
        "Best tier vs. single-product",
    ), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card_html(
        "\U0001F6A8 High-Balance Disengagement",
        f"{kpis['high_balance_disengagement_rate']:.1%}" if pd.notna(kpis['high_balance_disengagement_rate']) else "N/A",
        "Top-quartile balance, inactive",
    ), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card_html(
        "\U0001F4B3 Card Stickiness Score",
        f"{kpis['credit_card_stickiness_score']:+.1f} pp" if pd.notna(kpis['credit_card_stickiness_score']) else "N/A",
        "Cardholder retention gap",
    ), unsafe_allow_html=True)
with k5:
    st.markdown(kpi_card_html(
        "\U0001F91D Relationship Strength",
        f"{kpis['relationship_strength_index']:.1f} / 100" if pd.notna(kpis['relationship_strength_index']) else "N/A",
        "Composite loyalty score",
    ), unsafe_allow_html=True)

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

selected = option_menu(
    menu_title=None,
    options=["Overview", "Engagement vs Churn", "Product Utilization", "High-Value Disengaged", "Retention Strength", "What-If Simulator"],
    icons=["house", "activity", "box-seam", "exclamation-triangle", "shield-check", "sliders"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#FFFFFF", "border": "1px solid #E2E6ED", "border-radius": "8px"},
        "icon": {"color": SLATE, "font-size": "14px"},
        "nav-link": {
            "font-family": "Inter, sans-serif", "font-size": "0.85rem", "font-weight": "600",
            "text-align": "center", "color": MUTED, "padding": "12px 10px", "margin": "0px",
            "--hover-color": "#F3F5F9",
        },
        "nav-link-selected": {"background-color": INK, "color": "#FFFFFF"},
    },
)

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

if selected == "Overview":
    oc1, oc2 = st.columns([3, 2])
    with oc1:
        st.markdown("### The Problem")
        st.markdown(
            "Banks capture rich engagement and product-usage data, but rarely convert it into a "
            "quantitative view of what actually drives customers to leave — so retention strategies "
            "stay generic even when the behavioral evidence is sitting in the data. This platform, "
            "prepared for the European Central Bank under the Unified Mentor Program, answers three "
            "specific questions using the customer base currently loaded:"
        )
        st.markdown(
            f"""
            <div class="insight-card"><b>Does engagement drive retention?</b> — measured directly via the Engagement Retention Ratio and the Engagement vs Churn module.</div>
            <div class="insight-card"><b>Does product depth reduce churn?</b> — measured via the Product Depth Index and per-product-count churn breakdown.</div>
            <div class="insight-card"><b>Do high balances guarantee loyalty?</b> — tested directly in the High-Value Disengaged module, which finds customers where the answer is no.</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### How to Use This Dashboard")
        st.markdown(
            "Use the sidebar to filter by geography, engagement status, product count, and balance/salary "
            "thresholds — every module recalculates live against your selection. Start with **Engagement vs "
            "Churn** for the headline relationship, then **Product Utilization** and **High-Value Disengaged** "
            "for the two most actionable findings. **What-If Simulator** lets you test a specific customer "
            "profile and see which single intervention would move their risk the most."
        )

    with oc2:
        st.markdown("### At a Glance")
        prof_counts = df["EngagementProfile"].value_counts()
        fig_donut = px.pie(
            values=prof_counts.values, names=prof_counts.index, hole=0.62,
            color=prof_counts.index,
            color_discrete_map={
                "Active Engaged": GREEN, "Active Low-Product": SLATE,
                "Inactive Disengaged": "#E08E00", "Inactive High-Balance": RED,
            },
        )
        fig_donut.update_traces(textinfo="percent", textfont_size=11)
        fig_donut.update_layout(
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=10)),
            margin=dict(t=10, b=10, l=10, r=10), height=300,
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.caption("Customer base by engagement profile")

        st.markdown(
            f"""
            <div style="margin-top:0.6rem;">
                {badge(f"{len(df):,} customers in scope", "navy")}
                &nbsp;{badge(f"{df['Exited'].sum():,} churned", "red")}
                &nbsp;{badge(f"{(1-df['Exited'].mean()):.0%} retained", "green")}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)

        @st.cache_data(show_spinner=False)
        def _build_excel_report(_df, _kpis, _at_risk, _mismatch):
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                kpi_rows = pd.DataFrame([
                    {"KPI": "Engagement Retention Ratio", "Value": f"{_kpis['engagement_retention_ratio']:.2f}x"},
                    {"KPI": "Product Depth Index", "Value": f"{_kpis['product_depth_index']:+.1f} pp"},
                    {"KPI": "High-Balance Disengagement Rate", "Value": f"{_kpis['high_balance_disengagement_rate']:.1%}"},
                    {"KPI": "Credit Card Stickiness Score", "Value": f"{_kpis['credit_card_stickiness_score']:+.1f} pp"},
                    {"KPI": "Relationship Strength Index", "Value": f"{_kpis['relationship_strength_index']:.1f} / 100"},
                    {"KPI": "Filtered Base Size", "Value": f"{len(_df):,}"},
                    {"KPI": "Overall Churn Rate", "Value": f"{_df['Exited'].mean():.1%}"},
                ])
                kpi_rows.to_excel(writer, sheet_name="KPI Summary", index=False)

                _df.groupby("EngagementProfile").agg(
                    Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean"), AvgBalance=("Balance", "mean")
                ).reset_index().to_excel(writer, sheet_name="Engagement Profiles", index=False)

                _df.groupby("NumOfProducts").agg(
                    Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")
                ).reset_index().to_excel(writer, sheet_name="Product Depth", index=False)

                _at_risk.to_excel(writer, sheet_name="At-Risk Premium Watchlist", index=False)
                _mismatch.to_excel(writer, sheet_name="Salary-Balance Mismatch", index=False)
            return buf.getvalue()

        _at_risk_export = identify_at_risk_premium(df)
        _mismatch_export = identify_salary_balance_mismatch(df)
        excel_bytes = _build_excel_report(df, kpis, _at_risk_export, _mismatch_export)
        st.download_button(
            "\U0001F4E5 Export Executive Report (Excel)",
            data=excel_bytes,
            file_name="retention_intelligence_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.caption("KPI summary, engagement profiles, product depth, and both watchlists — for the current filtered view.")

# ---------------------------------------------------------------------------
# Engagement vs Churn Overview
# ---------------------------------------------------------------------------

elif selected == "Engagement vs Churn":
    st.markdown("### Engagement vs Churn Overview")

    col1, col2 = st.columns([1, 1])
    with col1:
        engagement_churn = (
            df.groupby("IsActiveMember")["Exited"].mean()
            .rename(index={0: "Inactive", 1: "Active"}).reset_index()
        )
        engagement_churn.columns = ["Status", "ChurnRate"]
        fig = px.bar(
            engagement_churn, x="Status", y="ChurnRate", color="Status",
            text=engagement_churn["ChurnRate"].apply(lambda x: f"{x:.1%}"),
            title="Churn Rate: Active vs Inactive Members",
            color_discrete_map={"Active": GREEN, "Inactive": RED},
        )
        fig.update_layout(yaxis_tickformat=".0%", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        profile_churn = df.groupby("EngagementProfile")["Exited"].agg(["mean", "count"]).reset_index()
        profile_churn.columns = ["Profile", "ChurnRate", "Count"]
        fig2 = px.bar(
            profile_churn.sort_values("ChurnRate", ascending=False),
            x="ChurnRate", y="Profile", orientation="h",
            text=profile_churn["ChurnRate"].apply(lambda x: f"{x:.1%}"),
            title="Churn Rate by Engagement Profile",
            color_discrete_sequence=[SLATE],
        )
        fig2.update_layout(xaxis_tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Engagement Profile Breakdown")
    profile_summary = (
        df.groupby("EngagementProfile")
        .agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean"),
             AvgBalance=("Balance", "mean"), AvgProducts=("NumOfProducts", "mean"))
        .reset_index().sort_values("ChurnRate", ascending=False)
    )
    profile_summary["ChurnRate"] = profile_summary["ChurnRate"].apply(lambda x: f"{x:.1%}")
    profile_summary["AvgBalance"] = profile_summary["AvgBalance"].apply(lambda x: f"${x:,.0f}")
    profile_summary["AvgProducts"] = profile_summary["AvgProducts"].round(2)
    st.dataframe(profile_summary, use_container_width=True, hide_index=True)

    st.markdown("#### Drill Into a Profile")
    selected_profile = st.selectbox(
        "Select an engagement profile to see its customers",
        ["(none)"] + sorted(df["EngagementProfile"].unique().tolist()),
    )
    if selected_profile != "(none)":
        profile_customers = df[df["EngagementProfile"] == selected_profile][
            ["CustomerId", "Surname", "Geography", "Age", "Balance", "NumOfProducts", "Tenure", "Exited"]
        ].copy()
        profile_customers["Exited"] = profile_customers["Exited"].map({0: "Retained", 1: "Churned"})
        st.caption(f"{len(profile_customers):,} customers in **{selected_profile}**")
        st.dataframe(profile_customers, use_container_width=True, hide_index=True, height=260)

    st.markdown("#### Geography x Engagement")
    geo_engagement = df.groupby(["Geography", "IsActiveMember"])["Exited"].mean().reset_index()
    geo_engagement["IsActiveMember"] = geo_engagement["IsActiveMember"].map({0: "Inactive", 1: "Active"})
    fig3 = px.bar(
        geo_engagement, x="Geography", y="Exited", color="IsActiveMember", barmode="group",
        title="Churn Rate by Geography and Engagement", labels={"Exited": "Churn Rate"},
        color_discrete_map={"Active": GREEN, "Inactive": RED},
    )
    fig3.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------------------------
# Product Utilization Impact Analysis
# ---------------------------------------------------------------------------

elif selected == "Product Utilization":
    st.markdown("### Product Utilization Impact Analysis")

    by_product = df.groupby("NumOfProducts").agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")).reset_index()
    by_product["RetentionRate"] = 1 - by_product["ChurnRate"]

    col1, col2 = st.columns([1, 1])
    with col1:
        fig4 = px.bar(
            by_product, x="NumOfProducts", y="ChurnRate",
            text=by_product["ChurnRate"].apply(lambda x: f"{x:.1%}"),
            title="Churn Rate by Number of Products",
            color_discrete_sequence=[SLATE],
        )
        fig4.update_layout(yaxis_tickformat=".0%", xaxis=dict(dtick=1))
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        single_vs_multi = df.assign(
            Tier=lambda d: d["NumOfProducts"].apply(lambda p: "Single-product" if p == 1 else "Multi-product")
        ).groupby("Tier")["Exited"].mean().reset_index()
        single_vs_multi.columns = ["Tier", "ChurnRate"]
        fig5 = px.bar(
            single_vs_multi, x="Tier", y="ChurnRate", color="Tier",
            text=single_vs_multi["ChurnRate"].apply(lambda x: f"{x:.1%}"),
            title="Single-Product vs Multi-Product Retention",
            color_discrete_map={"Single-product": GOLD, "Multi-product": SLATE},
        )
        fig5.update_layout(yaxis_tickformat=".0%", showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown(
        "<div class='insight-card'>If churn dips at 2 products and spikes at 3-4, it signals a "
        "<b>product-depth sweet spot</b> rather than a simple 'more products = more loyalty' relationship — "
        "over-bundling can correlate with distress-driven sign-ups (e.g. loan consolidation) rather than genuine engagement.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("#### Product Count Distribution")
    fig6 = px.histogram(
        df, x="NumOfProducts", color="Exited", barmode="group",
        title="Customer Volume by Product Count and Churn Status", labels={"Exited": "Churned"},
        color_discrete_map={0: SLATE, 1: RED},
    )
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown("#### Product Depth Table")
    display_table = by_product.copy()
    display_table["ChurnRate"] = display_table["ChurnRate"].apply(lambda x: f"{x:.1%}")
    display_table["RetentionRate"] = display_table["RetentionRate"].apply(lambda x: f"{x:.1%}")
    st.dataframe(display_table, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# High-Value Disengaged Customer Detector
# ---------------------------------------------------------------------------

elif selected == "High-Value Disengaged":
    st.markdown("### High-Value Disengaged Customer Detector")
    st.caption(
        "Customers who are inactive, hold above-threshold balances, and above-median salary — "
        "the 'silent churn' watchlist. High balance alone does not guarantee loyalty."
    )

    c1, c2 = st.columns(2)
    with c1:
        balance_pctl = st.slider("Balance percentile threshold", 50, 95, 75, step=5, key="risk_balance_pctl") / 100
    with c2:
        salary_pctl = st.slider("Salary percentile threshold", 0, 95, 50, step=5, key="risk_salary_pctl") / 100

    at_risk = identify_at_risk_premium(df, balance_pctl=balance_pctl, salary_pctl=salary_pctl)

    m1, m2, m3 = st.columns(3)
    m1.markdown(kpi_card_html("At-Risk Premium Customers", f"{len(at_risk):,}", ""), unsafe_allow_html=True)
    m2.markdown(kpi_card_html("Share of Filtered Base", f"{len(at_risk) / len(df):.1%}" if len(df) else "N/A", ""), unsafe_allow_html=True)
    m3.markdown(kpi_card_html("Their Actual Churn Rate", f"{at_risk['Exited'].mean():.1%}" if len(at_risk) else "N/A", "Silent churn already realized"), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    fig7 = px.scatter(
        df, x="Balance", y="EstimatedSalary", color="IsActiveMember", symbol="Exited",
        title="Balance vs Salary, Colored by Activity Status", labels={"IsActiveMember": "Active"},
        opacity=0.6, color_continuous_scale=[RED, GREEN],
    )
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("#### Watchlist")
    show_cols = ["CustomerId", "Surname", "Geography", "Age", "Balance", "EstimatedSalary", "NumOfProducts", "Tenure", "HasCrCard", "Exited"]
    watchlist_display = at_risk[show_cols].copy()
    watchlist_display["Balance"] = watchlist_display["Balance"].apply(lambda x: f"${x:,.0f}")
    watchlist_display["EstimatedSalary"] = watchlist_display["EstimatedSalary"].apply(lambda x: f"${x:,.0f}")
    watchlist_display["Exited"] = watchlist_display["Exited"].map({0: "Retained", 1: "Churned"})
    st.dataframe(watchlist_display, use_container_width=True, hide_index=True, height=320)

    csv = at_risk[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button("Download watchlist CSV", csv, "at_risk_premium_customers.csv", "text/csv")

    st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)
    st.markdown("#### Salary–Balance Mismatch")
    st.caption(
        "Customers with high estimated income but low balance at this institution — income that "
        "may not be landing here. A share-of-wallet signal as much as a churn-risk one."
    )
    mismatch = identify_salary_balance_mismatch(df)
    mm1, mm2 = st.columns(2)
    mm1.markdown(kpi_card_html("Mismatch Customers", f"{len(mismatch):,}", f"{len(mismatch)/len(df):.1%} of filtered base"), unsafe_allow_html=True)
    mm2.markdown(kpi_card_html("Their Churn Rate", f"{mismatch['Exited'].mean():.1%}" if len(mismatch) else "N/A", "vs. overall base"), unsafe_allow_html=True)
    with st.expander("View mismatch customers"):
        mm_display = mismatch[show_cols].copy()
        mm_display["Balance"] = mm_display["Balance"].apply(lambda x: f"${x:,.0f}")
        mm_display["EstimatedSalary"] = mm_display["EstimatedSalary"].apply(lambda x: f"${x:,.0f}")
        mm_display["Exited"] = mm_display["Exited"].map({0: "Retained", 1: "Churned"})
        st.dataframe(mm_display, use_container_width=True, hide_index=True, height=260)

# ---------------------------------------------------------------------------
# Retention Strength Scoring Panels
# ---------------------------------------------------------------------------

elif selected == "Retention Strength":
    st.markdown("### Retention Strength Scoring Panels")
    st.caption(
        "Relationship Strength Index blends activity (40%), product depth (30%), "
        "tenure (20%), and card ownership (10%) into a single 0-100 score."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        tier_churn = df.groupby("RelationshipStrengthTier", observed=True)["Exited"].agg(["mean", "count"]).reset_index()
        tier_churn.columns = ["Tier", "ChurnRate", "Count"]
        order = ["Low", "Medium", "High", "Very High"]
        tier_churn["Tier"] = pd.Categorical(tier_churn["Tier"], categories=order, ordered=True)
        tier_churn = tier_churn.sort_values("Tier")
        tier_color_map = {"Low": RED, "Medium": "#E08E00", "High": "#5B7FBF", "Very High": GREEN}
        fig8 = px.bar(
            tier_churn, x="Tier", y="ChurnRate", color="Tier",
            text=tier_churn["ChurnRate"].apply(lambda x: f"{x:.1%}"),
            title="Churn Rate by Relationship Strength Tier",
            color_discrete_map=tier_color_map,
        )
        fig8.update_layout(yaxis_tickformat=".0%", showlegend=False)
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        fig9 = px.histogram(
            df, x="RelationshipStrengthScore", color="Exited", nbins=25, barmode="overlay", opacity=0.65,
            title="Relationship Strength Score Distribution by Churn Status", labels={"Exited": "Churned"},
            color_discrete_map={0: SLATE, 1: RED},
        )
        st.plotly_chart(fig9, use_container_width=True)

    st.markdown(
        "<div class='insight-card'><b>'Sticky' customers</b> (score \u2265 75, tier = Very High) are active "
        "members with 2+ products, meaningful tenure, and a credit card. Use this panel to see how much "
        "retention improves as customers move up a tier — that gap is the retention lever.</div>",
        unsafe_allow_html=True,
    )

    sticky_summary = df.groupby("RelationshipStrengthTier", observed=True).agg(
        Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean"), AvgScore=("RelationshipStrengthScore", "mean"),
    ).reset_index()
    sticky_summary["Tier"] = pd.Categorical(sticky_summary["RelationshipStrengthTier"], categories=order, ordered=True)
    sticky_summary = sticky_summary.sort_values("Tier").drop(columns=["RelationshipStrengthTier"])
    sticky_summary["ChurnRate"] = sticky_summary["ChurnRate"].apply(lambda x: f"{x:.1%}")
    sticky_summary["AvgScore"] = sticky_summary["AvgScore"].round(1)
    st.dataframe(sticky_summary[["Tier", "Customers", "ChurnRate", "AvgScore"]], use_container_width=True, hide_index=True)

    st.markdown("#### Customer-Level Scores")
    score_cols = ["CustomerId", "Surname", "IsActiveMember", "NumOfProducts", "HasCrCard", "Tenure", "RelationshipStrengthScore", "RelationshipStrengthTier", "Exited"]
    score_display = df[score_cols].sort_values("RelationshipStrengthScore", ascending=False).copy()
    score_display["Exited"] = score_display["Exited"].map({0: "Retained", 1: "Churned"})
    st.dataframe(score_display, use_container_width=True, hide_index=True, height=320)

# ---------------------------------------------------------------------------
# What-If Churn Risk Simulator
# ---------------------------------------------------------------------------

elif selected == "What-If Simulator":
    st.markdown("### What-If Churn Risk Simulator")
    st.caption(
        "Build a hypothetical customer, get a live predicted churn probability, and see exactly how "
        "much activating them or adding a product would move the needle."
    )

    @st.cache_resource(show_spinner="Training risk model...")
    def _get_model(_df):
        return train_churn_model(_df)

    model = _get_model(raw_df)

    st.markdown("#### Customer Profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        sim_geo = st.selectbox("Geography", geo_options, key="sim_geo")
        sim_gender = st.selectbox("Gender", ["Male", "Female"], key="sim_gender")
        sim_age = st.slider("Age", 18, 92, 40, key="sim_age")
    with c2:
        sim_credit = st.slider("Credit score", 350, 850, 650, key="sim_credit")
        sim_tenure = st.slider("Tenure (years)", 0, 10, 5, key="sim_tenure")
        sim_products = st.slider("Number of products", 1, 4, 2, key="sim_products")
    with c3:
        sim_balance = st.number_input("Balance ($)", 0.0, 260000.0, 75000.0, step=1000.0, key="sim_balance")
        sim_salary = st.number_input("Estimated salary ($)", 1000.0, 200000.0, 100000.0, step=1000.0, key="sim_salary")
        sim_active = st.checkbox("Active member", value=True, key="sim_active")
        sim_card = st.checkbox("Has credit card", value=True, key="sim_card")

    base_customer = {
        "CreditScore": sim_credit, "Age": sim_age, "Tenure": sim_tenure, "Balance": sim_balance,
        "NumOfProducts": sim_products, "HasCrCard": int(sim_card), "IsActiveMember": int(sim_active),
        "EstimatedSalary": sim_salary, "Geography": sim_geo, "Gender": sim_gender,
    }
    base_prob = predict_churn_probability(model, base_customer)

    risk_label = "Low" if base_prob < 0.25 else "Moderate" if base_prob < 0.5 else "High" if base_prob < 0.75 else "Very High"
    risk_color = GREEN if base_prob < 0.25 else "#E08E00" if base_prob < 0.5 else "#D96B00" if base_prob < 0.75 else RED

    st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)
    st.markdown("#### Predicted Result")
    r1, r2 = st.columns([1, 2])
    with r1:
        st.markdown(
            f"<div style='text-align:center; padding: 24px; border-radius: 10px; "
            f"background-color: {risk_color}18; border: 1px solid {risk_color}; border-top: 3px solid {risk_color};'>"
            f"<div style='font-family:\"IBM Plex Mono\",monospace; font-size: 40px; font-weight: 600; color: {risk_color};'>{base_prob:.1%}</div>"
            f"<div style='font-family:Inter,sans-serif; font-size: 14px; color: {risk_color}; text-transform:uppercase; letter-spacing:0.06em; margin-top:4px;'>{risk_label} churn risk</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown("**Retention Lever Comparison** — how much would each intervention move this customer's risk?")
        scenarios = {
            "Current profile": base_customer,
            ("→ If activated" if not sim_active else "→ If made inactive"): {**base_customer, "IsActiveMember": 0 if sim_active else 1},
            "→ If +1 product (up to 4)": {**base_customer, "NumOfProducts": min(sim_products + 1, 4)},
            ("→ If given a credit card" if not sim_card else "→ If card removed"): {**base_customer, "HasCrCard": 0 if sim_card else 1},
        }
        scenario_rows = [{"Scenario": label, "ChurnRisk": predict_churn_probability(model, cust)} for label, cust in scenarios.items()]
        scenario_df = pd.DataFrame(scenario_rows)
        fig10 = px.bar(
            scenario_df, x="ChurnRisk", y="Scenario", orientation="h",
            text=scenario_df["ChurnRisk"].apply(lambda x: f"{x:.1%}"),
            color_discrete_sequence=[SLATE],
        )
        fig10.update_layout(xaxis_tickformat=".0%", height=280)
        st.plotly_chart(fig10, use_container_width=True)

    st.markdown("#### What Drives This Model")
    st.caption("Standardized coefficients across the full customer base — bigger bars matter more.")
    importance_df = get_model_feature_importance(model)
    fig11 = px.bar(
        importance_df.head(10), x="AbsCoefficient", y="Feature", orientation="h", color="Direction",
        color_discrete_map={"Increases churn risk": RED, "Reduces churn risk": GREEN},
        title="Top Churn Drivers",
    )
    fig11.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig11, use_container_width=True)

st.markdown(
    "<div class='footer-note'>Customer Retention Intelligence &nbsp;·&nbsp; Prepared for the European Central Bank "
    "&nbsp;·&nbsp; Unified Mentor Program &nbsp;·&nbsp; Data shown is illustrative unless a verified file has been uploaded above.</div>",
    unsafe_allow_html=True,
)
