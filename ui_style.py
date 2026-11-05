"""Shared CSS + banner (phone-frame look)."""
import streamlit as st

GREEN = "#3F7D0A"

CSS = f"""
<style>
.stApp, .stApp * {{ font-family: Arial, Helvetica, "Liberation Sans", sans-serif !important; }}
.stApp [data-testid="stIconMaterial"], .stApp .material-symbols-rounded {{
  font-family: "Material Symbols Rounded" !important; }}
[data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
.stApp {{ background: #EEF1EC; }}
[data-testid="stHeader"] {{ background: transparent; height: 2.2rem; pointer-events: none; }}
[data-testid="stHeader"] * {{ pointer-events: auto; }}
.block-container {{
  max-width: 410px !important; padding: 2.2rem 1rem 3rem !important; background: #FFFFFF;
  margin-top: 0.5rem; min-height: 100vh; height: auto !important; flex-shrink: 0 !important;
}}
@media (min-width: 520px) {{
  .block-container {{ border-radius: 28px; box-shadow: 0 8px 30px rgba(0,0,0,.12); margin-top: 2.2rem;
                      min-height: 780px; border: 8px solid #1d1d1f; margin-bottom: 2.2rem; }}
}}
/* keep columns side by side even on narrow phones */
[data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0.4rem !important; }}
[data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }}
.stButton button {{ border-radius: 18px; font-size: 0.82rem; padding: 0.25rem 0.6rem; min-height: 2rem; width: 100%; }}
.st-key-tilebtn .stButton button p, .st-key-tilebtn .stButton button div {{ white-space: normal !important; font-size: 0.68rem !important; line-height: 1.1; }}
.stButton button p, .stButton button div {{ white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
.stButton button[kind="primary"] {{ background: {GREEN}; border-color: {GREEN}; }}
.banner {{ background: #FFF6DB; color: #5c4a00; font-size: 0.72rem; text-align: center; padding: 6px 8px;
          border-radius: 8px; margin-bottom: 0.6rem; }}
.fund-head {{ font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0; }}
.fund-sub {{ color: #6b6b6b; font-size: 0.78rem; margin-bottom: 0.6rem; }}
.value-card {{ border: 1px solid #e6e6e6; border-radius: 14px; padding: 12px 14px; margin-bottom: 0.5rem; }}
.value-card .lbl {{ color: #6b6b6b; font-size: 0.75rem; }}
.value-card .big {{ font-size: 1.6rem; font-weight: 700; }}
.value-card .row {{ display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.85rem; }}
.neg {{ color: #B3261E; }}
.tile {{ border: 1px solid #e6e6e6; border-radius: 12px; padding: 8px 6px 4px; text-align: center; }}
.tile .lbl {{ color: #6b6b6b; font-size: 0.7rem; }}
.tile .v {{ font-weight: 700; font-size: 0.95rem; }}
.fs-label {{ color: {GREEN}; font-weight: 700; font-size: 0.75rem; letter-spacing: .3px; }}
.fs-card {{ background: #F3F8EE; border-left: 4px solid {GREEN}; border-radius: 10px; padding: 10px 12px;
           margin: 0.4rem 0; font-size: 0.9rem; line-height: 1.4; }}
.fs-q {{ background: #F1F1F1; border-radius: 12px 12px 2px 12px; padding: 7px 11px; margin: 0.6rem 0 0 2.5rem;
        font-size: 0.86rem; }}
.fs-check {{ font-size: 0.72rem; color: {GREEN}; margin-top: 6px; }}
.fs-warn {{ font-size: 0.72rem; color: #8a5a00; margin-top: 6px; }}
.fs-nums {{ width: 100%; font-size: 0.8rem; margin-top: 6px; border-collapse: collapse; }}
.fs-nums td {{ padding: 2px 0; border-bottom: 1px dashed #d9e4cf; }}
.fs-nums td:last-child {{ text-align: right; font-weight: 700; }}
.memory {{ font-size: 0.75rem; color: #444; background: #F7F7F7; border-radius: 8px; padding: 6px 9px; margin: 0.4rem 0; }}
.task {{ font-size: 0.82rem; }}
.block-container h3 {{ font-size: 1.25rem !important; padding: 0.3rem 0 0.2rem !important; }}
.block-container h4 {{ font-size: 1rem !important; padding: 0.6rem 0 0.1rem !important; color: #3F7D0A; }}
.block-container .stMarkdown p, .block-container .stMarkdown li {{ font-size: 0.88rem; }}
.st-key-topnav {{ border-bottom: 1px solid #e6e6e6; padding-bottom: 4px; margin-bottom: 0.4rem; }}
.st-key-topnav [data-testid="stPageLink"] a {{ justify-content: center; padding: 4px 2px; }}
.st-key-topnav [data-testid="stPageLink"] p {{ font-size: 0.74rem !important; white-space: nowrap; }}
</style>
"""

BANNER = '<div class="banner">Concept prototype · Not investment advice · Not affiliated with Groww</div>'


def apply(wide: bool = False):
    st.markdown(CSS, unsafe_allow_html=True)
    if wide:
        st.markdown("<style>.block-container{max-width:1100px !important;}</style>", unsafe_allow_html=True)
    st.markdown(BANNER, unsafe_allow_html=True)
