"""
Design system for the Customer Retention Intelligence dashboard.
A "statement" aesthetic: navy + brass palette, Fraunces display / Inter body /
IBM Plex Mono for figures, ledger-style KPI cards with a hairline gold top border.
"""

INK = "#0B2545"
SLATE = "#13315C"
GOLD = "#C9A227"
CANVAS = "#F7F8FA"
CARD = "#FFFFFF"
BORDER = "#E2E6ED"
MUTED = "#5B6472"
GREEN = "#1B8A5A"
RED = "#C1121F"
AMBER = "#E08E00"

CHART_COLORWAY = [SLATE, GOLD, GREEN, RED, "#5B7FBF", AMBER]


def inject_css():
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

/* ---- Layout canvas ---- */
.stApp {{
    background-color: {CANVAS};
}}
.block-container {{
    padding-top: 1.2rem;
    max-width: 1180px;
}}

/* ---- Headings ---- */
h1, h2, h3 {{
    font-family: 'Fraunces', serif !important;
    color: {INK} !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}}
h2 {{ font-size: 1.5rem !important; margin-top: 0.4rem !important; }}
h3 {{ font-size: 1.15rem !important; }}

/* ---- Hero banner ---- */
.hero-banner {{
    background: linear-gradient(135deg, {INK} 0%, {SLATE} 100%);
    border-radius: 14px;
    padding: 2.4rem 2.6rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}}
.hero-banner::after {{
    content: "";
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 6px;
    background: {GOLD};
}}
.hero-eyebrow {{
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.72rem;
    font-weight: 600;
    color: {GOLD};
    margin-bottom: 0.6rem;
}}
.hero-title {{
    font-family: 'Fraunces', serif;
    font-size: 2.1rem;
    font-weight: 600;
    color: #FFFFFF;
    line-height: 1.15;
    margin-bottom: 0.5rem;
}}
.hero-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.98rem;
    color: #C9D2E3;
    max-width: 640px;
    line-height: 1.5;
}}
.hero-figure {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 3.2rem;
    font-weight: 600;
    color: #FFFFFF;
    font-variant-numeric: tabular-nums;
    line-height: 1;
}}
.hero-figure-label {{
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.68rem;
    color: {GOLD};
    margin-top: 0.35rem;
    font-weight: 600;
}}

/* ---- Ledger KPI cards ---- */
.ledger-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-top: 3px solid {GOLD};
    border-radius: 8px;
    padding: 1rem 1.1rem 0.9rem 1.1rem;
    height: 100%;
}}
.ledger-label {{
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.66rem;
    font-weight: 600;
    color: {MUTED};
    margin-bottom: 0.35rem;
}}
.ledger-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.65rem;
    font-weight: 600;
    color: {INK};
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}}
.ledger-context {{
    font-family: 'Inter', sans-serif;
    font-size: 0.76rem;
    color: {MUTED};
    margin-top: 0.3rem;
    line-height: 1.35;
}}

/* ---- Section divider ---- */
.gold-rule {{
    border: none;
    border-top: 1px solid {GOLD};
    opacity: 0.5;
    margin: 1.6rem 0 1.2rem 0;
}}

/* ---- Pills / badges ---- */
.badge {{
    display: inline-block;
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    letter-spacing: 0.02em;
}}
.badge-red {{ background: #FBE4E4; color: {RED}; }}
.badge-green {{ background: #E1F1E9; color: {GREEN}; }}
.badge-amber {{ background: #FBEED8; color: {AMBER}; }}
.badge-navy {{ background: #E7ECF5; color: {SLATE}; }}

/* ---- Objective / insight cards ---- */
.insight-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-left: 3px solid {SLATE};
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.65rem;
}}
.insight-card b {{ color: {INK}; }}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.88rem;
    color: {MUTED};
    padding: 0.6rem 1rem;
}}
.stTabs [aria-selected="true"] {{
    color: {INK} !important;
    border-bottom: 2px solid {GOLD} !important;
}}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {{
    background-color: #FFFFFF;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] h1 {{
    font-size: 1.15rem !important;
}}

/* ---- DataFrames ---- */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

/* ---- Footer ---- */
.footer-note {{
    font-family: 'Inter', sans-serif;
    font-size: 0.76rem;
    color: {MUTED};
    text-align: center;
    padding: 1.2rem 0 0.4rem 0;
}}
</style>
"""


def kpi_card_html(label: str, value: str, context: str = "") -> str:
    return f"""
<div class="ledger-card">
    <div class="ledger-label">{label}</div>
    <div class="ledger-value">{value}</div>
    <div class="ledger-context">{context}</div>
</div>
"""


def hero_html(eyebrow: str, title: str, subtitle: str, figure: str, figure_label: str) -> str:
    return f"""
<div class="hero-banner">
    <div style="display:flex; justify-content:space-between; align-items:center; gap: 2rem; flex-wrap: wrap;">
        <div style="flex: 2; min-width: 320px;">
            <div class="hero-eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-sub">{subtitle}</div>
        </div>
        <div style="flex: 1; min-width: 160px; text-align: right;">
            <div class="hero-figure">{figure}</div>
            <div class="hero-figure-label">{figure_label}</div>
        </div>
    </div>
</div>
"""


def badge(text: str, kind: str = "navy") -> str:
    return f'<span class="badge badge-{kind}">{text}</span>'
