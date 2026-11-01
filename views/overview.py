import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from core import COUNTRY_ISO, PALETTE, inject_css, kpi, load_data, money, style_fig

inject_css(st)


@st.cache_data(show_spinner="Loading data…")
def get_data():
    tx, credits, _ = load_data()
    return tx, credits


tx, credits = get_data()
months = sorted(tx["Month"].unique())
LAST = months[-1]

# ------------------------------------------------------------------ sidebar filters
with st.sidebar:
    st.header("Filters")
    m0, m1 = st.select_slider("Period (months)", options=months, value=(months[0], months[-1]))
    market = st.radio("Market", ["All", "United Kingdom", "International"], horizontal=False)
    st.caption("Revenue = completed sales of identified customers (same basis as the sales analysis notebook: "
               "£8.89M, 18,536 orders). Dec 2011 covers 1–9 Dec only.")


def apply(df):
    out = df[(df["Month"] >= m0) & (df["Month"] <= m1)]
    if market == "United Kingdom":
        out = out[out["Country"] == "United Kingdom"]
    elif market == "International":
        out = out[out["Country"] != "United Kingdom"]
    return out


f, fc = apply(tx), apply(credits)
if f.empty:
    st.warning("No data for this selection.")
    st.stop()

# ------------------------------------------------------------------ header + KPIs
st.markdown('<div class="hero-title">Business Overview</div>'
            f'<div class="hero-sub">Online Retail · {m0} to {m1} · {market} market(s)</div>', unsafe_allow_html=True)

revenue = f["Revenue"].sum()
orders = f["InvoiceNo"].nunique()
customers = f["CustomerID"].nunique()
aov = revenue / orders
ret_value = -fc["Revenue"].sum()
ret_rate = ret_value / revenue
ret_orders = fc["InvoiceNo"].nunique()
ret_order_rate = ret_orders / (orders + ret_orders)

c = st.columns(5)
with c[0]: kpi(st, "Revenue", money(revenue), f"{len(f):,} order lines")
with c[1]: kpi(st, "Customers", f"{customers:,}", f"{orders / customers:.1f} orders per customer")
with c[2]: kpi(st, "Orders", f"{orders:,}", f"{f['Quantity'].sum():,} units sold")
with c[3]: kpi(st, "Avg order value", f"£{aov:,.0f}", f"median £{f.groupby('InvoiceNo')['Revenue'].sum().median():,.0f}")
with c[4]: kpi(st, "Return rate", f"{ret_rate:.1%}", f"{money(ret_value)} credited")
st.caption(f"Return rate = value of credit notes ÷ completed sales. {ret_orders:,} orders were fully or partly returned or "
           f"cancelled ({ret_order_rate:.0%} of all orders).")

# ------------------------------------------------------------------ revenue trends
st.subheader("Revenue trends")
monthly = f.groupby("Month").agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"),
                                 Customers=("CustomerID", "nunique")).reset_index()
monthly["AOV"] = monthly["Revenue"] / monthly["Orders"]
partial = monthly["Month"] == LAST

left, right = st.columns([3, 2])
with left:
    fig = go.Figure()
    fig.add_bar(x=monthly["Month"], y=monthly["Revenue"], name="Revenue",
                marker_color=np.where(partial, "#C7D2FE", "#4F46E5"),
                hovertemplate="%{x}<br>Revenue £%{y:,.0f}<extra></extra>")
    fig.add_scatter(x=monthly["Month"], y=monthly["Orders"], name="Orders", yaxis="y2", mode="lines+markers",
                    line=dict(color="#F59E0B", width=3), hovertemplate="%{x}<br>%{y:,} orders<extra></extra>")
    fig.update_layout(title="Monthly revenue and orders", yaxis=dict(title="Revenue (£)", tickprefix="£", rangemode="tozero"),
                      yaxis2=dict(title="Orders", overlaying="y", side="right", showgrid=False, rangemode="tozero"))
    st.plotly_chart(style_fig(fig, 400), width="stretch")
with right:
    fig = px.line(monthly, x="Month", y="AOV", markers=True, title="Average order value by month")
    fig.update_traces(line_color="#14B8A6", line_width=3, hovertemplate="%{x}<br>AOV £%{y:,.0f}<extra></extra>")
    fig.add_hline(y=aov, line_dash="dot", line_color="#9CA3AF", annotation_text=f"overall £{aov:,.0f}")
    fig.update_yaxes(tickprefix="£", title=None); fig.update_xaxes(title=None)
    st.plotly_chart(style_fig(fig, 400), width="stretch")

full = monthly[~partial] if (~partial).any() else monthly
peak = full.loc[full["Revenue"].idxmax()]
low = full.loc[full["Revenue"].idxmin()]
st.markdown(f'<div class="insight"><b>Takeaway:</b> revenue peaks in <b>{peak["Month"]}</b> ({money(peak["Revenue"])}), '
            f'{peak["Revenue"] / low["Revenue"]:.1f}× the weakest full month ({low["Month"]}, {money(low["Revenue"])}). '
            f'In that peak month there were {int(peak["Orders"]):,} orders at an average of £{peak["AOV"]:,.0f} '
            f'(overall £{aov:,.0f}), so the swing is mostly {"order volume" if abs(peak["Orders"] / full["Orders"].mean() - 1) > abs(peak["AOV"] / aov - 1) else "basket size"}. '
            f'Dec 2011 (lighter bar) is a partial month.</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------ geography
st.subheader("Geographic analysis")
geo = f.groupby("Country").agg(Revenue=("Revenue", "sum"), Customers=("CustomerID", "nunique"),
                               Orders=("InvoiceNo", "nunique")).reset_index()
geo["AOV"] = geo["Revenue"] / geo["Orders"]
geo["Share"] = geo["Revenue"] / geo["Revenue"].sum()
geo = geo.sort_values("Revenue", ascending=False)

gl, gr = st.columns([3, 2])
with gl:
    mapdf = geo[geo["Country"].isin(COUNTRY_ISO)].copy()
    mapdf["iso"] = mapdf["Country"].map(COUNTRY_ISO)
    mapdf = mapdf.groupby("iso", as_index=False).agg(Revenue=("Revenue", "sum"), Customers=("Customers", "sum"),
                                                   Country=("Country", lambda s: " / ".join(s)))
    ticks = [1e2, 1e3, 1e4, 1e5, 1e6, 1e7]
    fig = go.Figure(go.Choropleth(
        locations=mapdf["iso"], z=np.log10(mapdf["Revenue"]), customdata=np.stack([mapdf["Country"], mapdf["Revenue"],
                                                                                   mapdf["Customers"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>Revenue £%{customdata[1]:,.0f}<br>%{customdata[2]} customers<extra></extra>",
        colorscale=[[0, "#E0E7FF"], [0.5, "#818CF8"], [1, "#312E81"]], marker_line_color="#FFFFFF", marker_line_width=0.5,
        zmin=2, zmax=7, colorbar=dict(title="Revenue", tickvals=np.log10(ticks),
                                      ticktext=["£100", "£1k", "£10k", "£100k", "£1M", "£10M"], len=0.7)))
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor="rgba(0,0,0,0)",
                    showcountries=True, countrycolor="#E5E7EB", landcolor="#F3F4F6")
    fig.update_layout(title="Revenue by country (log colour scale)")
    st.plotly_chart(style_fig(fig, 420), width="stretch")
    st.caption("The map outlines are loaded from Plotly's CDN, so this chart needs an internet connection.")
with gr:
    intl = geo[geo["Country"] != "United Kingdom"].head(10).sort_values("Revenue")
    if len(intl):
        fig = px.bar(intl, x="Revenue", y="Country", orientation="h", title="Top international markets",
                     color_discrete_sequence=["#0EA5E9"], custom_data=["Customers", "AOV"])
        fig.update_traces(hovertemplate="<b>%{y}</b><br>£%{x:,.0f}<br>%{customdata[0]} customers · AOV £%{customdata[1]:,.0f}<extra></extra>")
        fig.update_xaxes(tickprefix="£", title=None); fig.update_yaxes(title=None)
        st.plotly_chart(style_fig(fig, 420), width="stretch")
    else:
        st.info("The selected market has no international sales.")

uk_share = geo.loc[geo["Country"] == "United Kingdom", "Share"].sum()
top_intl = geo[geo["Country"] != "United Kingdom"].head(3)
txt = f"The UK generates <b>{uk_share:.0%}</b> of revenue in this view. " if market != "International" else ""
if len(top_intl):
    txt += "Top international markets: " + ", ".join(
        f"<b>{r.Country}</b> ({money(r.Revenue)}, {r.Customers} customers)" for r in top_intl.itertuples()) + ". "
    trade = geo[(geo["Country"] != "United Kingdom") & (geo["Customers"] <= 10) & (geo["AOV"] > 1000)].head(3)
    if len(trade):
        txt += ("Markets with very few customers but very high order values (" +
                ", ".join(f"{r.Country}: {r.Customers} customers, AOV £{r.AOV:,.0f}" for r in trade.itertuples()) +
                ") look like trade accounts: manage them as key accounts.")
st.markdown(f'<div class="insight"><b>Takeaway:</b> {txt}</div>', unsafe_allow_html=True)
with st.expander("Country table"):
    show = geo.rename(columns={"AOV": "Avg order value"}).copy()
    show["Share"] = show["Share"] * 100
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "Revenue": st.column_config.NumberColumn(format="£%,.0f"),
        "Avg order value": st.column_config.NumberColumn(format="£%,.0f"),
        "Share": st.column_config.NumberColumn("Share of revenue", format="%.2f%%")})

# ------------------------------------------------------------------ product performance
st.subheader("Product performance")
prod = f[f["IsProduct"]]
tab1, tab2 = st.tabs(["Top products", "Categories"])
with tab1:
    metric = st.radio("Rank by", ["Revenue", "Units sold", "Orders (popularity)"], horizontal=True)
    p = prod.groupby("StockCode").agg(Description=("Description", lambda s: s.mode().iat[0]), Revenue=("Revenue", "sum"),
                                      Units=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"),
                                      Customers=("CustomerID", "nunique")).reset_index()
    col = {"Revenue": "Revenue", "Units sold": "Units", "Orders (popularity)": "Orders"}[metric]
    top = p.nlargest(10, col).sort_values(col)
    top["Label"] = top["Description"].str.title().str.slice(0, 34) + np.where(top["Customers"] == 1, "  ⚠ 1 customer", "")
    fig = px.bar(top, x=col, y="Label", orientation="h", custom_data=["Revenue", "Units", "Orders", "Customers"],
                 title=f"Top 10 products by {metric.lower()}", color_discrete_sequence=["#4F46E5"])
    fig.update_traces(hovertemplate="<b>%{y}</b><br>Revenue £%{customdata[0]:,.0f}<br>Units %{customdata[1]:,}"
                                    "<br>Orders %{customdata[2]:,} · Customers %{customdata[3]:,}<extra></extra>")
    fig.update_xaxes(title=None, tickprefix="£" if col == "Revenue" else ""); fig.update_yaxes(title=None)
    st.plotly_chart(style_fig(fig, 440), width="stretch")
    st.caption("Postage, manual and other non-product codes are excluded. ⚠ marks products bought by a single customer: "
               "usually one-off bulk orders rather than repeatable demand.")
with tab2:
    cat = prod.groupby("Category").agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"),
                                       Orders=("InvoiceNo", "nunique"), Products=("StockCode", "nunique")).reset_index()
    cat["Share"] = cat["Revenue"] / cat["Revenue"].sum()
    cat = cat.sort_values("Revenue", ascending=True)
    fig = px.bar(cat, x="Revenue", y="Category", orientation="h", title="Revenue by category (label = share of product revenue)",
                 custom_data=["Share", "Orders", "Products"], color_discrete_sequence=["#14B8A6"],
                 text=cat["Share"].map(lambda v: f"{v:.1%}"))
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{y}</b><br>£%{x:,.0f} (%{customdata[0]:.1%})<br>%{customdata[1]:,} orders · "
                                    "%{customdata[2]} products<extra></extra>")
    fig.update_xaxes(tickprefix="£", title=None); fig.update_yaxes(title=None)
    st.plotly_chart(style_fig(fig, 440), width="stretch")
    top2 = cat.sort_values("Revenue", ascending=False).head(2)
    st.markdown(f'<div class="insight"><b>Takeaway:</b> <b>{top2.iloc[0]["Category"]}</b> and <b>{top2.iloc[1]["Category"]}</b> '
                f'together make up <b>{top2["Share"].sum():.0%}</b> of product revenue. Categories are keyword-based groupings '
                f'of product descriptions (see the sales notebook), not an official catalogue.</div>', unsafe_allow_html=True)
