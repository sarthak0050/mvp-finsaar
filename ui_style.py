"""Shared CSS + header (normal responsive web app, no sidebar)."""
import streamlit as st

GREEN = "#3F7D0A"

CSS = f"""
<style>
.stApp, .stApp * {{ font-family: Arial, Helvetica, "Liberation Sans", sans-serif !important; }}
.stApp [data-testid="stIconMaterial"], .stApp .material-symbols-rounded {{
  font-family: "Material Symbols Rounded" !important; }}
/* no sidebar, no Streamlit toolbar */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"],
[data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stHeader"] {{ display: none !important; }}
.stApp {{ background: #FFFFFF; }}
.block-container {{ max-width: 1100px !important; padding: 1rem 1.5rem 3rem !important; }}

/* app header */
.app-brand {{ display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 2px; }}
.app-brand .name {{ color: {GREEN}; font-weight: 700; font-size: 1.5rem; }}
.app-brand .tag {{ color: #555; font-size: 0.95rem; }}
.banner {{ background: #FFF6DB; color: #5c4a00; font-size: 0.8rem; text-align: center; padding: 6px 10px;
          border-radius: 8px; margin: 6px 0 4px; }}
.st-key-topnav {{ border-bottom: 1px solid #e6e6e6; padding-bottom: 2px; margin-bottom: 0.6rem; }}
.st-key-topnav [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0.3rem !important; }}
.st-key-topnav [data-testid="stColumn"] {{ min-width: 0 !important; flex: 0 1 auto !important; width: auto !important; }}
.st-key-topnav [data-testid="stPageLink"] p {{ font-size: 0.9rem !important; white-space: nowrap; }}

/* rows of small buttons stay side by side even on narrow screens */
.st-key-tilebtn [data-testid="stHorizontalBlock"], [class*="st-key-fb"] [data-testid="stHorizontalBlock"],
.st-key-nudge [data-testid="stHorizontalBlock"], .st-key-askbox [data-testid="stHorizontalBlock"],
.st-key-membox [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0.5rem !important; }}
.st-key-tilebtn [data-testid="stColumn"], [class*="st-key-fb"] [data-testid="stColumn"],
.st-key-nudge [data-testid="stColumn"], .st-key-askbox [data-testid="stColumn"],
.st-key-membox [data-testid="stColumn"] {{ min-width: 0 !important; }}

.stButton button {{ border-radius: 18px; font-size: 0.85rem; padding: 0.3rem 0.8rem; min-height: 2.1rem; width: 100%; }}
.stButton button p, .stButton button div {{ white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
.st-key-tilebtn [data-testid="stColumn"] {{ border: 1px solid #e6e6e6; border-radius: 12px; padding: 10px 6px 4px;
  gap: 0 !important; transition: border-color .15s; }}
.st-key-tilebtn [data-testid="stColumn"]:hover {{ border-color: {GREEN}; }}
.st-key-tilebtn .tile {{ border: none; padding: 0; }}
.st-key-tilebtn .stButton {{ display: flex; justify-content: center; }}
.st-key-tilebtn .stButton button {{ width: auto; min-height: 1.6rem; padding: 0 6px; color: {GREEN}; }}
.st-key-tilebtn .stButton button p {{ font-size: 0.8rem !important; font-weight: 700; color: {GREEN}; }}
[data-testid="stButtonGroup"], [data-testid="stButtonGroup"] > div {{ flex-wrap: wrap !important; overflow: visible !important; max-width: 100% !important; }}
.stButton button[kind="primary"] {{ background: {GREEN}; border-color: {GREEN}; }}

/* SIP card */
.section-title {{ font-weight: 700; font-size: 1rem; margin: 0.2rem 0 0.4rem; color: #1d1d1f; }}
.fund-head {{ font-size: 1.15rem; font-weight: 700; margin: 0.2rem 0 0; }}
.fund-sub {{ color: #6b6b6b; font-size: 0.85rem; margin-bottom: 0.6rem; }}
.value-card {{ border: 1px solid #e6e6e6; border-radius: 14px; padding: 14px 16px; margin-bottom: 0.6rem; }}
.value-card .lbl {{ color: #6b6b6b; font-size: 0.8rem; }}
.value-card .big {{ font-size: 1.9rem; font-weight: 700; }}
.value-card .row {{ display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.92rem; }}
.neg {{ color: #B3261E; }}
.tile {{ border: 1px solid #e6e6e6; border-radius: 12px; padding: 10px 6px 6px; text-align: center; }}
.tile .lbl {{ color: #6b6b6b; font-size: 0.78rem; }}
.tile .v {{ font-weight: 700; font-size: 1.05rem; }}

/* FinSaar (AI) */
.fs-label {{ color: {GREEN}; font-weight: 700; font-size: 0.8rem; letter-spacing: .3px; }}
.fs-card {{ background: #F3F8EE; border-left: 4px solid {GREEN}; border-radius: 10px; padding: 12px 14px;
           margin: 0.4rem 0; font-size: 0.95rem; line-height: 1.45; }}
.fs-q {{ background: #F1F1F1; border-radius: 12px 12px 2px 12px; padding: 8px 12px; margin: 0.7rem 0 0 20%;
        font-size: 0.92rem; }}
.fs-check {{ font-size: 0.78rem; color: {GREEN}; margin-top: 6px; }}
.fs-warn {{ font-size: 0.78rem; color: #8a5a00; margin-top: 6px; }}
.fs-nums {{ width: 100%; font-size: 0.85rem; margin-top: 6px; border-collapse: collapse; }}
.fs-nums td {{ padding: 3px 0; border-bottom: 1px dashed #d9e4cf; }}
.fs-nums td:last-child {{ text-align: right; font-weight: 700; }}
.fs-empty {{ border: 1px dashed #cfdcc3; border-radius: 12px; padding: 18px; color: #555; font-size: 0.92rem; }}
.memory {{ font-size: 0.8rem; color: #444; background: #F7F7F7; border-radius: 8px; padding: 7px 10px; margin: 0.5rem 0; }}
.task {{ font-size: 0.9rem; }}

/* How to use page */
.block-container h3 {{ font-size: 1.5rem !important; padding: 0.3rem 0 0.2rem !important; }}
.block-container h4 {{ font-size: 1.1rem !important; padding: 0.7rem 0 0.1rem !important; color: {GREEN}; }}
.step {{ border: 1px solid #e6e6e6; border-radius: 12px; padding: 12px 14px; height: 100%; font-size: 0.9rem; }}
.step .n {{ display: inline-block; background: {GREEN}; color: #fff; border-radius: 50%; width: 24px; height: 24px;
           text-align: center; line-height: 24px; font-weight: 700; font-size: 0.8rem; margin-right: 6px; }}
.step b.t {{ font-size: 0.95rem; }}
</style>
"""

BANNER = '<div class="banner">Concept prototype · Not investment advice · Not affiliated with Groww</div>'


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="app-brand"><span class="name">✦ FinSaar</span>'
                '<span class="tag">Aapke SIP ka saar: your SIP numbers, in words you understand</span></div>'
                + BANNER, unsafe_allow_html=True)
