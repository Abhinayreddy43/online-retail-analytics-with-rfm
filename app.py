"""Online Retail dashboard — run with:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Online Retail Dashboard", page_icon="🛍️", layout="wide")

pages = [
    st.Page("views/overview.py", title="Business Overview", icon="📊", default=True),
    st.Page("views/customers.py", title="Customer RFM", icon="👥"),
]
st.navigation(pages).run()
