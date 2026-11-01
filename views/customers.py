import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import ORDER, PALETTE, SEGMENT_META, inject_css, kpi, load_data, money, style_fig

inject_css(st)


@st.cache_data(show_spinner="Loading data…")
def get_data():
    tx, credits, rfm = load_data()
    return tx, rfm.set_index("CustomerID", drop=False)


tx, rfm = get_data()
seg_stats = rfm.groupby("Segment", observed=True).agg(
    Customers=("Monetary", "size"), Revenue=("Monetary", "sum"), AvgRecency=("Recency", "mean"),
    MedianSpend=("Monetary", "median"), AvgFrequency=("Frequency", "mean")).reindex(ORDER)
seg_stats["CustShare"] = seg_stats["Customers"] / seg_stats["Customers"].sum()
seg_stats["RevShare"] = seg_stats["Revenue"] / seg_stats["Revenue"].sum()

st.markdown('<div class="hero-title">Customer RFM Analysis</div>'
            f'<div class="hero-sub">{len(rfm):,} scored customers · Recency, Frequency and Monetary scores (1–5) · '
            'spend is net of returns · snapshot date 10 Dec 2011</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ segment landscape
st.subheader("Segment landscape")
champ = seg_stats.loc["Champions"]
risk = seg_stats.loc[["At Risk", "Can't Lose Them"]]
k = st.columns(4)
with k[0]: kpi(st, "Scored customers", f"{len(rfm):,}", "net spend > 0, product purchases")
with k[1]: kpi(st, "Champions", f"{champ.CustShare:.0%}", f"of customers · {champ.RevShare:.0%} of revenue")
with k[2]: kpi(st, "Win-back pool", f"{int(risk.Customers.sum()):,}", f"At Risk + Can't Lose Them · {money(risk.Revenue.sum())} ({risk.RevShare.sum():.1%})")
with k[3]: kpi(st, "Hibernating / Lost", f"{seg_stats.loc['Hibernating / Lost', 'CustShare']:.0%}",
              f"of customers · only {seg_stats.loc['Hibernating / Lost', 'RevShare']:.1%} of revenue")
st.write("")

sl, sr = st.columns([3, 2])
with sl:
    d = seg_stats.reset_index().iloc[::-1]
    fig = go.Figure()
    fig.add_bar(y=d["Segment"], x=d["CustShare"] * 100, orientation="h", name="% of customers", marker_color="#CBD5E1",
                hovertemplate="%{y}: %{x:.1f}% of customers<extra></extra>")
    fig.add_bar(y=d["Segment"], x=d["RevShare"] * 100, orientation="h", name="% of revenue",
                marker_color="#4F46E5",
                hovertemplate="%{y}: %{x:.1f}% of revenue<extra></extra>")
    fig.update_layout(barmode="group", title="Who the customers are vs. who brings the money", xaxis_title="Share (%)")
    st.plotly_chart(style_fig(fig, 420), width="stretch")
with sr:
    fig = px.pie(seg_stats.reset_index(), names="Segment", values="Customers", hole=0.6, title="Customers by segment",
                 color="Segment", color_discrete_map={s: SEGMENT_META[s]["color"] for s in ORDER},
                 category_orders={"Segment": ORDER})
    fig.update_traces(textinfo="percent", sort=False, textposition="inside",
                      hovertemplate="<b>%{label}</b><br>%{value:,} customers<extra></extra>")
    fig.update_layout(showlegend=False, uniformtext_minsize=11, uniformtext_mode="hide")
    st.plotly_chart(style_fig(fig, 420), width="stretch")

with st.expander("Segment playbook: what to do for each segment"):
    play = pd.DataFrame([{"Segment": f"{SEGMENT_META[s]['icon']} {s}", "Customers": int(seg_stats.loc[s, "Customers"]),
                          "Revenue share": seg_stats.loc[s, "RevShare"] * 100, "Avg days since order": seg_stats.loc[s, "AvgRecency"],
                          "Priority": SEGMENT_META[s]["priority"], "Main action": SEGMENT_META[s]["actions"][0]} for s in ORDER])
    st.dataframe(play, hide_index=True, width="stretch", column_config={
        "Revenue share": st.column_config.NumberColumn(format="%.1f%%"),
        "Avg days since order": st.column_config.NumberColumn(format="%.0f")})

# ------------------------------------------------------------------ customer lookup
st.subheader("Customer lookup")
fl, fr = st.columns([2, 3])
with fl:
    chosen_segments = st.multiselect("Narrow the list by segment (optional)", ORDER, placeholder="All segments")
pool = rfm if not chosen_segments else rfm[rfm["Segment"].isin(chosen_segments)]
pool = pool.sort_values("Monetary", ascending=False)
options = pool["CustomerID"].tolist()
labels = {cid: f"{cid} · {seg} · {ctry} · {money(m)}" for cid, seg, ctry, m in
          zip(pool["CustomerID"], pool["Segment"], pool["Country"], pool["Monetary"])}

if st.session_state.get("cust_pick") not in options:
    st.session_state["cust_pick"] = options[0]


def surprise():
    st.session_state["cust_pick"] = int(np.random.choice(options))


with fr:
    a, b = st.columns([4, 1])
    with a:
        cid = st.selectbox("Search by customer ID (type to filter)", options, key="cust_pick",
                           format_func=lambda c: labels[c])
    with b:
        st.write(""); st.write("")
        st.button("🎲 Random", on_click=surprise, width="stretch")

row = rfm.loc[cid]
seg = str(row["Segment"])
meta = SEGMENT_META[seg]
ss = seg_stats.loc[seg]

mine = tx[tx["CustomerID"] == cid]
mine_p = mine[mine["IsProduct"]]
orders = row["Frequency"]
aov = row["GrossSpend"] / orders
first, last = row["FirstPurchase"], row["LastPurchase"]
cat = mine_p.groupby("Category")["Revenue"].sum().sort_values(ascending=False)
prods = mine_p.groupby("StockCode").agg(Description=("Description", lambda s: s.mode().iat[0]), Revenue=("Revenue", "sum"),
                                        Units=("Quantity", "sum"), Orders=("InvoiceNo", "nunique")).sort_values("Revenue", ascending=False)

# ---- hero
hl, hr = st.columns([3, 2])
with hl:
    st.markdown(f'<div class="seg-hero" style="background: linear-gradient(135deg, {meta["color"]}, {meta["color"]}CC);">'
                f'<div style="opacity:.85;font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;">Customer {cid}</div>'
                f'<div class="name">{meta["icon"]} {seg}</div><div class="tag">{meta["tagline"]}</div>'
                f'<div style="margin-top:14px;"><span class="badge" style="background:rgba(255,255,255,.25);">Priority: {meta["priority"]}</span></div>'
                f'</div>', unsafe_allow_html=True)
with hr:
    st.markdown(
        '<div class="card"><h4>RFM scores (5 = best)</h4>'
        f'<span class="chip"><div class="k">Recency</div><div class="v">{row["R"]}</div><div class="s">{row["Recency"]} day{"" if row["Recency"] == 1 else "s"} ago</div></span>'
        f'<span class="chip"><div class="k">Frequency</div><div class="v">{row["F"]}</div><div class="s">{orders} orders</div></span>'
        f'<span class="chip"><div class="k">Monetary</div><div class="v">{row["M"]}</div><div class="s">{money(row["Monetary"])}</div></span>'
        f'<div style="margin-top:10px;color:#6B7280;font-size:.85rem;">RFM code <b style="color:#111827">{row["R"]}{row["F"]}{row["M"]}</b></div></div>',
        unsafe_allow_html=True)
st.write("")

# ---- recommendations
rl, rr = st.columns(2)
with rl:
    items = "".join(f"<li>{a}</li>" for a in meta["actions"])
    st.markdown(f'<div class="card" style="border-top:4px solid {meta["color"]};"><h4>Recommended actions for {seg}</h4>'
                f'<ul class="reco" style="padding-left:1.1rem;margin:0;">{items}</ul></div>', unsafe_allow_html=True)

personal = []
days = int(row["Recency"])
when = "<b>1 day ago</b>" if days == 1 else f"<b>{days} days ago</b>"
personal.append(f"Last order was {when} ({last:%d %b %Y}); the {seg} average is {ss.AvgRecency:.0f} days.")
ratio = row["Monetary"] / ss.MedianSpend if ss.MedianSpend else 1
personal.append(f"Net spend of <b>{money(row['Monetary'])}</b> is <b>{ratio:.1f}×</b> the {seg} median ({money(ss.MedianSpend)}).")
if len(cat):
    share = cat.iloc[0] / cat.sum()
    personal.append(f"<b>{share:.0%}</b> of spend is in <b>{cat.index[0]}</b>: lead messages with new {cat.index[0].lower()} arrivals or bundles.")
    if "Christmas & seasonal" in cat.index and cat["Christmas & seasonal"] / cat.sum() > 0.15:
        personal.append("Strong seasonal buyer: schedule outreach for September–October, ahead of the Christmas peak.")
if len(prods):
    personal.append(f"Most-bought item: <b>{prods.iloc[0]['Description'].title()}</b> ({int(prods.iloc[0]['Units']):,} units): offer a reorder reminder.")
if row["Country"] != "United Kingdom" and (orders >= 3 or row["Monetary"] > 3000):
    personal.append(f"Based in <b>{row['Country']}</b> with trade-style ordering: assign a named account manager.")
ret_share = -row["Credits"] / row["GrossSpend"] if row["GrossSpend"] else 0
if ret_share > 0.10:
    personal.append(f"Returns are <b>{ret_share:.0%}</b> of their gross spend: investigate quality or fit before promoting more.")
if orders == 1:
    personal.append("Only one order so far: the single most valuable goal is a second purchase.")
with rr:
    items = "".join(f"<li>{p}</li>" for p in personal)
    st.markdown(f'<div class="card"><h4>Personalised for this customer</h4><ul class="reco" style="padding-left:1.1rem;margin:0;">{items}</ul></div>',
                unsafe_allow_html=True)
st.write("")

# ---- profile cards
p1, p2, p3 = st.columns(3)
with p1:
    st.markdown('<div class="card"><h4>Location & history</h4>'
                f'<div class="row"><span>Country</span><span>{row["Country"]}</span></div>'
                f'<div class="row"><span>First purchase</span><span>{first:%d %b %Y}</span></div>'
                f'<div class="row"><span>Last purchase</span><span>{last:%d %b %Y}</span></div>'
                f'<div class="row"><span>Active span</span><span>{(last - first).days:,} days</span></div>'
                f'<div class="row"><span>Days since last order</span><span>{days:,}</span></div></div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="card"><h4>Financial summary</h4>'
                f'<div class="row"><span>Net spend</span><span>{money(row["Monetary"], 2)}</span></div>'
                f'<div class="row"><span>Gross spend</span><span>{money(row["GrossSpend"], 2)}</span></div>'
                f'<div class="row"><span>Returns / credits</span><span>{money(row["Credits"], 2)}</span></div>'
                f'<div class="row"><span>Orders</span><span>{orders:,}</span></div>'
                f'<div class="row"><span>Avg order value</span><span>{money(aov, 2)}</span></div></div>', unsafe_allow_html=True)
with p3:
    rank = int((rfm["Monetary"] > row["Monetary"]).sum()) + 1
    st.markdown('<div class="card"><h4>How they compare</h4>'
                f'<div class="row"><span>Spend rank</span><span>#{rank:,} of {len(rfm):,}</span></div>'
                f'<div class="row"><span>Segment size</span><span>{int(ss.Customers):,} customers</span></div>'
                f'<div class="row"><span>Segment avg orders</span><span>{ss.AvgFrequency:.1f}</span></div>'
                f'<div class="row"><span>Distinct products</span><span>{mine_p["StockCode"].nunique():,}</span></div>'
                f'<div class="row"><span>Units bought</span><span>{int(mine_p["Quantity"].sum()):,}</span></div></div>', unsafe_allow_html=True)
st.write("")

# ---- charts
c1, c2 = st.columns([3, 2])
with c1:
    top = prods.head(8).iloc[::-1].copy()
    top["Label"] = top["Description"].str.title().str.slice(0, 36)
    fig = px.bar(top, x="Revenue", y="Label", orientation="h", title="Top products purchased (by spend)",
                 custom_data=["Units", "Orders"], color_discrete_sequence=[meta["color"]])
    fig.update_traces(hovertemplate="<b>%{y}</b><br>£%{x:,.2f}<br>%{customdata[0]:,} units · %{customdata[1]} orders<extra></extra>")
    fig.update_xaxes(tickprefix="£", title=None); fig.update_yaxes(title=None)
    st.plotly_chart(style_fig(fig, 400), width="stretch")
with c2:
    cdf = cat.reset_index(); cdf["Share"] = cdf["Revenue"] / cdf["Revenue"].sum()
    cdf = cdf.iloc[::-1]
    fig = px.bar(cdf, x="Share", y="Category", orientation="h", title="Product categories purchased (share of spend)",
                 custom_data=["Revenue"], color_discrete_sequence=["#14B8A6"])
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1%} · £%{customdata[0]:,.2f}<extra></extra>")
    fig.update_xaxes(tickformat=".0%", title=None); fig.update_yaxes(title=None)
    st.plotly_chart(style_fig(fig, 400), width="stretch")

timeline = mine.groupby("Month")["Revenue"].sum().reset_index()
fig = px.bar(timeline, x="Month", y="Revenue", title="Spend by month (gross)", color_discrete_sequence=[meta["color"]])
fig.update_yaxes(tickprefix="£", title=None); fig.update_xaxes(title=None, type="category")
fig.update_traces(hovertemplate="%{x}<br>£%{y:,.2f}<extra></extra>")
st.plotly_chart(style_fig(fig, 280), width="stretch")
st.caption("Customers with no net product spend after returns (17 customers whose credit notes cancel at least 95% of their "
           "purchases, plus 4 who only bought non-product items) are not scored and don't appear in this list.")
