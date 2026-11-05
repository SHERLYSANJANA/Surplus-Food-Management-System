import streamlit as st

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
[data-testid="stMetric"] {
    background: rgba(128,128,128,.08);
    border: 1px solid rgba(128,128,128,.22);
    border-left: 5px solid #2e7d32;
    border-radius: 12px; padding: 14px 18px;
}
[data-testid="stMetricValue"] {font-weight: 700;}
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    border-radius: 10px; font-weight: 600;
}
.hero {
    background: linear-gradient(120deg, #1b5e20 0%, #43a047 60%, #81c784 100%);
    color: #fff; padding: 2rem 2.2rem; border-radius: 18px; margin-bottom: 1.4rem;
}
.hero h1 {margin: 0 0 .3rem 0; font-size: 2.2rem; color: #fff;}
.hero p {margin: 0; font-size: 1.05rem; opacity: .95;}
.page-header {display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;
    padding-bottom: .8rem; border-bottom: 2px solid rgba(46,125,50,.35);}
.page-header .icon {font-size: 2.4rem;}
.page-header h1 {margin: 0; padding: 0; font-size: 1.9rem;}
.page-header p {margin: 0; opacity: .7;}
.step-card {background: rgba(128,128,128,.08); border: 1px solid rgba(128,128,128,.22);
    border-radius: 14px; padding: 1rem 1.2rem; height: 100%;}
.step-card .num {display: inline-block; width: 28px; height: 28px; line-height: 28px;
    text-align: center; border-radius: 50%; background: #2e7d32; color: #fff;
    font-weight: 700; margin-bottom: .4rem;}
.step-card h4 {margin: .2rem 0;}
.step-card p {margin: 0; opacity: .75; font-size: .92rem;}
</style>
"""


def setup(page_title, icon):
    st.set_page_config(page_title=page_title, page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(icon, title, subtitle=""):
    setup(f"{title} · Food Redistribution", icon)
    st.markdown(
        f'<div class="page-header"><span class="icon">{icon}</span>'
        f"<div><h1>{title}</h1><p>{subtitle}</p></div></div>",
        unsafe_allow_html=True,
    )
