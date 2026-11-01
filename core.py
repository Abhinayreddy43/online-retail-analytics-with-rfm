"""Shared data, constants and helpers for the Online Retail dashboard.

Everything here mirrors the logic in retail_data_analysis.ipynb (cleaning, categories)
and rfm_analysis.ipynb (net spend, scoring, segments).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
XLSX_CANDIDATES = [
    ROOT / "data" / "raw" / "Online Retail.xlsx",
    ROOT / "Online Retail.xlsx",
    ROOT / "Online_Retail.xlsx",
    ROOT.parent / "Online Retail.xlsx",
    ROOT.parent / "Online_Retail.xlsx",
    Path("/mnt/project/Online_Retail.xlsx"),
]

# --------------------------------------------------------------------------- constants
NON_PRODUCT = {"POST", "M", "DOT", "C2", "BANK CHARGES", "PADS", "S", "D", "B", "CRUK", "AMAZONFEE"}

ORDER = ["Champions", "Loyal", "Potential Loyalists", "New Customers", "Promising",
         "Needs Attention", "At Risk", "Can't Lose Them", "Hibernating / Lost"]

SEGMENT_GRID = {
    5: {1: "New Customers", 2: "Potential Loyalists", 3: "Loyal", 4: "Champions", 5: "Champions"},
    4: {1: "Promising", 2: "Potential Loyalists", 3: "Loyal", 4: "Champions", 5: "Champions"},
    3: {1: "Needs Attention", 2: "Needs Attention", 3: "Needs Attention", 4: "Loyal", 5: "Loyal"},
    2: {1: "Hibernating / Lost", 2: "Hibernating / Lost", 3: "At Risk", 4: "Can't Lose Them", 5: "Can't Lose Them"},
    1: {1: "Hibernating / Lost", 2: "Hibernating / Lost", 3: "At Risk", 4: "Can't Lose Them", 5: "Can't Lose Them"},
}

SEGMENT_META = {
    "Champions": dict(color="#4F46E5", icon="🏆", priority="Protect",
        tagline="Bought recently, buy often and spend the most. The core of the business.",
        actions=["Give early access to new ranges and seasonal launches.",
                 "Reward with loyalty perks or a thank-you; ask for referrals and reviews.",
                 "Do not discount: they already buy. Make sure their favourite lines are always in stock."]),
    "Loyal": dict(color="#2563EB", icon="💙", priority="Grow",
        tagline="Regular buyers with healthy spend. Ready to be grown into Champions.",
        actions=["Cross-sell and bundle (e.g. add jumbo bags or t-lights to a decor order).",
                 "Offer a volume incentive that rewards a slightly larger or more frequent basket.",
                 "Ask for reviews and feedback on the range."]),
    "Potential Loyalists": dict(color="#0EA5E9", icon="🌱", priority="Convert",
        tagline="Recent customers with a couple of orders. A repeat habit is forming.",
        actions=["Nudge a repeat order with a time-limited offer or free-postage threshold.",
                 "Recommend products related to what they already bought.",
                 "Invite them into the loyalty programme."]),
    "New Customers": dict(color="#14B8A6", icon="✨", priority="Onboard",
        tagline="Just placed their first order. The next 30 days decide whether they return.",
        actions=["Send a welcome sequence that shows best sellers and ranges.",
                 "Give a clear reason to reorder within 30 days.",
                 "Make the first delivery and returns experience excellent."]),
    "Promising": dict(color="#22C55E", icon="🌟", priority="Convert",
        tagline="Recent first-time buyers who have not yet formed a habit.",
        actions=["Prompt a larger second basket with related-product suggestions.",
                 "Highlight bundles and multi-buy savings.",
                 "Follow up after delivery with a simple reorder link."]),
    "Needs Attention": dict(color="#F59E0B", icon="⏰", priority="Re-engage",
        tagline="Average on every measure and starting to slip. Easy to lose without a nudge.",
        actions=["Send a reminder based on their previous purchases.",
                 "Use seasonal prompts (new season, gifting periods).",
                 "Offer a limited-time incentive for the next order."]),
    "At Risk": dict(color="#F97316", icon="⚠️", priority="Win back",
        tagline="Used to order several times but have gone quiet. Win them back before they lapse.",
        actions=["Run a personalised win-back email using their past categories.",
                 "Offer a targeted incentive tied to a deadline.",
                 "Ask what changed (range, price, delivery) via a short survey."]),
    "Can't Lose Them": dict(color="#EF4444", icon="🚨", priority="Urgent",
        tagline="Frequent, high-value buyers who have gone quiet. The most valuable group to recover.",
        actions=["Personal outreach: a call or message from an account manager.",
                 "Ask directly what changed and fix it (stock, pricing, service).",
                 "Offer a tailored deal or priority service to restart ordering."]),
    "Hibernating / Lost": dict(color="#94A3B8", icon="💤", priority="Low effort",
        tagline="Old, infrequent customers with low spend. Rarely worth individual effort.",
        actions=["Include in low-cost seasonal reactivation campaigns only.",
                 "Do not spend per-customer effort or margin on discounts.",
                 "Suppress from frequent mailings to protect email reputation."]),
}

COUNTRY_ISO = {
    "Australia": "AUS", "Austria": "AUT", "Bahrain": "BHR", "Belgium": "BEL", "Brazil": "BRA", "Canada": "CAN",
    "Channel Islands": "GBR", "Cyprus": "CYP", "Czech Republic": "CZE", "Denmark": "DNK", "EIRE": "IRL",
    "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Iceland": "ISL", "Israel": "ISR",
    "Italy": "ITA", "Japan": "JPN", "Lebanon": "LBN", "Lithuania": "LTU", "Malta": "MLT", "Netherlands": "NLD",
    "Norway": "NOR", "Poland": "POL", "Portugal": "PRT", "RSA": "ZAF", "Saudi Arabia": "SAU", "Singapore": "SGP",
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "CHE", "USA": "USA", "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
}   # "European Community" and "Unspecified" have no country -> not drawn on the map

PALETTE = ["#4F46E5", "#0EA5E9", "#14B8A6", "#F59E0B", "#EF4444", "#8B5CF6", "#22C55E", "#F97316", "#64748B", "#EC4899"]


# --------------------------------------------------------------------------- categories (from retail_data_analysis.ipynb)
def assign_category(stock_code, description):
    code = str(stock_code).strip().upper()
    if code in NON_PRODUCT:
        return "Fees / postage"
    text = str(description).upper()
    rules = [
        ("Bags", ["BAG", "PURSE", "SACK", "HANDBAG", "SHOPPER"]),
        ("Lighting & candles", ["T-LIGHT", "TLIGHT", "CANDLE", "LANTERN", "LAMP", "LIGHT"]),
        ("Kitchen & tableware", ["CAKESTAND", "CAKE STAND", "MUG", "CUP", "BOWL", "PLATE", "JUG", "JAR", "BOTTLE",
                                 "CUTLERY", "TEAPOT", "KITCHEN", "TIN", "TRAY", "DISH", "GLASS", "NAPKIN", "COASTER",
                                 "CHOPPING", "CAKE CASE", "JAM MAKING", "MOULD"]),
        ("Christmas & seasonal", ["CHRISTMAS", "ADVENT", "BAUBLE", "WREATH", "SNOWMAN", "NUTCRACKER"]),
        ("Home decor", ["BUNTING", "ORNAMENT", "DECORATION", "DOORMAT", "SIGN", "CLOCK", "MIRROR", "FRAME", "CUSHION",
                        "HOOK", "HANGER", "GARDEN", "VASE", "POT", "CERAMIC", "HEART", "STAR", "FLOWER", "BIRD",
                        "FOLKART", "BOARD", "PARASOL", "RACK", "FAN", "RIBBON"]),
        ("Stationery & paper", ["PAPER", "CARD", "WRAP", "NOTEBOOK", "STICKER", "TAPE", "STAMP", "CRAFT", "LETTER"]),
        ("Storage & organisation", ["BOX", "BASKET", "STORAGE", "DRAWER", "CABINET", "HANGER"]),
        ("Toys & games", ["TOY", "GAME", "DOLL", "GLIDER", "PLAYHOUSE", "JIGSAW"]),
        ("Apparel & accessories", ["T-SHIRT", "SCARF", "HAT", "SOCK", "GLOVE", "JEWELLERY", "NECKLACE", "BRACELET", "EARRING"]),
    ]
    for category, keywords in rules:
        if any(k in text for k in keywords):
            return category
    return "Other"


# --------------------------------------------------------------------------- build
def _is_product(codes: pd.Series) -> pd.Series:
    c = codes.str.upper().str.strip()
    return ~c.isin(NON_PRODUCT) & ~c.str.startswith("DCGS")


def build_datasets(xlsx_path: Path):
    """Return (tx, credits, rfm). tx == df_clean of retail_data_analysis.ipynb."""
    raw = pd.read_excel(
    xlsx_path,
    usecols=[
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country"
    ]
)
    raw["StockCode"] = raw["StockCode"].astype(str)
    step2 = raw.drop_duplicates().dropna()
    is_cancel = step2["InvoiceNo"].astype(str).str.startswith("C")
    credits = step2[is_cancel].copy()
    tx = step2[~is_cancel & (step2["Quantity"] > 0)].copy()

    for part in (tx, credits):
        part["Revenue"] = part["Quantity"] * part["UnitPrice"]
        part["CustomerID"] = part["CustomerID"].astype(int)
        part["InvoiceNo"] = part["InvoiceNo"].astype(str)
        part["IsProduct"] = _is_product(part["StockCode"])

    # reconcile with retail_data_analysis.ipynb
    assert len(tx) == 392_732 and tx["InvoiceNo"].nunique() == 18_536
    assert tx["CustomerID"].nunique() == 4_339 and round(tx["Revenue"].sum(), 2) == 8_887_208.89

    pairs = tx[["StockCode", "Description"]].drop_duplicates()
    cat = {(s, d): assign_category(s, d) for s, d in zip(pairs["StockCode"], pairs["Description"])}
    tx["Category"] = [cat[k] for k in zip(tx["StockCode"], tx["Description"])]
    tx["Month"] = tx["InvoiceDate"].dt.to_period("M").astype(str)
    credits["Month"] = credits["InvoiceDate"].dt.to_period("M").astype(str)

    # ---- RFM (rfm_analysis.ipynb)
    sales = tx[tx["IsProduct"]]
    cr = credits[credits["IsProduct"]]
    snapshot = tx["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

    rfm = sales.groupby("CustomerID").agg(
        FirstPurchase=("InvoiceDate", "min"), LastPurchase=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"), GrossSpend=("Revenue", "sum"),
        Country=("Country", lambda s: s.mode().iat[0]))
    rfm["Credits"] = cr.groupby("CustomerID")["Revenue"].sum().reindex(rfm.index).fillna(0)
    rfm["Monetary"] = rfm["GrossSpend"] + rfm["Credits"]
    rfm["Recency"] = (snapshot - rfm["LastPurchase"]).dt.days
    rfm = rfm[~(rfm["Monetary"] <= 0.05 * rfm["GrossSpend"])].copy()

    rfm["R"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["M"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["F"] = pd.cut(rfm["Frequency"], bins=[0, 1, 2, 4, 7, np.inf], labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["Segment"] = [SEGMENT_GRID[r][f] for r, f in zip(rfm["R"], rfm["F"])]
    rfm = rfm.reset_index()
    assert len(rfm) == 4_318

    keep = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID",
            "Country", "Revenue", "IsProduct", "Month"]
    return tx[keep + ["Category"]].reset_index(drop=True), credits[keep].reset_index(drop=True), rfm


def build_and_save() -> None:
    path = next((p for p in XLSX_CANDIDATES if p.exists()), None)
    if path is None:
        raise FileNotFoundError("Put 'Online Retail.xlsx' next to core.py, then run: python build_data.py")
    tx, credits, rfm = build_datasets(path)
    DATA_DIR.mkdir(exist_ok=True)
    tx.to_parquet(DATA_DIR / "transactions.parquet", index=False)
    credits.to_parquet(DATA_DIR / "credit_notes.parquet", index=False)
    rfm.to_parquet(DATA_DIR / "rfm.parquet", index=False)


def load_data():
    files = [DATA_DIR / n for n in ("transactions.parquet", "credit_notes.parquet", "rfm.parquet")]
    if not all(f.exists() for f in files):
        build_and_save()
    tx, credits, rfm = (pd.read_parquet(f) for f in files)
    rfm["Segment"] = pd.Categorical(rfm["Segment"], ORDER, ordered=True)
    return tx, credits, rfm


# --------------------------------------------------------------------------- formatting / UI helpers
def money(x: float, decimals: int = 0) -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1_000_000:
        return f"{sign}£{x/1_000_000:,.2f}M"
    if x >= 10_000:
        return f"{sign}£{x/1_000:,.1f}k"
    return f"{sign}£{x:,.{decimals}f}"


CSS = """
<style>
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px;}
h1, h2, h3 {letter-spacing: -0.01em;}
.hero-title {font-size: 2.1rem; font-weight: 800; margin-bottom: 0.1rem; color: #111827;}
.hero-sub {color: #6B7280; font-size: 1.0rem; margin-bottom: 1.2rem;}
.kpi {background: #fff; border: 1px solid #E5E7EB; border-radius: 16px; padding: 18px 20px; height: 100%; min-height: 128px;
      box-shadow: 0 1px 2px rgba(16,24,40,.04);}
.kpi .label {font-size: .78rem; color: #6B7280; text-transform: uppercase; letter-spacing: .06em; font-weight: 600;}
.kpi .value {font-size: 1.9rem; font-weight: 800; color: #111827; line-height: 1.25;}
.kpi .sub {font-size: .8rem; color: #6B7280;}
.card {background: #fff; border: 1px solid #E5E7EB; border-radius: 16px; padding: 20px 22px;
       box-shadow: 0 1px 2px rgba(16,24,40,.04); height: 100%;}
.card h4 {margin: 0 0 .6rem 0; font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; color: #6B7280;}
.row {display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px dashed #EEF0F3; font-size: .95rem;}
.row:last-child {border-bottom: none;}
.row span:first-child {color: #6B7280;}
.row span:last-child {font-weight: 600; color: #111827;}
.badge {display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: .78rem; font-weight: 700; color: #fff;}
.chip {display: inline-block; text-align: center; background: #F3F4F6; border-radius: 12px; padding: 8px 14px; margin-right: 8px;}
.chip .k {font-size: .68rem; color: #6B7280; text-transform: uppercase; letter-spacing: .06em;}
.chip .v {font-size: 1.35rem; font-weight: 800; color: #111827; line-height: 1.1;}
.chip .s {font-size: .7rem; color: #6B7280;}
.seg-hero {border-radius: 20px; padding: 26px 28px; color: #fff;}
.seg-hero .name {font-size: 2rem; font-weight: 800; line-height: 1.1;}
.seg-hero .tag {opacity: .95; font-size: 1.02rem; margin-top: 6px;}
.insight {background: #EEF2FF; border-left: 4px solid #4F46E5; padding: 10px 14px; border-radius: 8px;
          color: #1F2937; font-size: .92rem; margin: .4rem 0 1rem 0;}
.reco li {margin-bottom: .45rem;}
section[data-testid="stSidebar"] {background: #F8FAFC;}
</style>
"""


def inject_css(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def kpi(st, label: str, value: str, sub: str = "") -> None:
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>'
                f'<div class="sub">{sub}&nbsp;</div></div>', unsafe_allow_html=True)


def style_fig(fig, height: int = 380):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40, b=10), template="plotly_white",
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#374151"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(font=dict(size=15, color="#111827"), x=0.0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(showgrid=False, linecolor="#E5E7EB")
    fig.update_yaxes(gridcolor="#EEF0F3", zeroline=False)
    return fig
