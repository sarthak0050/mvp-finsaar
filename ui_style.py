"""Shared CSS + header (normal responsive web app, no sidebar)."""
import streamlit as st

GREEN = "#3F7D0A"     # FinSaar (AI) accent, kept distinct from the host app
HOST = "#00B386"      # host-app (Groww-style) accent

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
.st-key-membox [data-testid="stHorizontalBlock"], .st-key-txlist [data-testid="stHorizontalBlock"]
  {{ flex-wrap: nowrap !important; gap: 0.5rem !important; }}
.st-key-tilebtn [data-testid="stColumn"], [class*="st-key-fb"] [data-testid="stColumn"],
.st-key-nudge [data-testid="stColumn"], .st-key-askbox [data-testid="stColumn"],
.st-key-membox [data-testid="stColumn"], .st-key-txlist [data-testid="stColumn"] {{ min-width: 0 !important; }}

.stButton button {{ border-radius: 18px; font-size: 0.85rem; padding: 0.3rem 0.8rem; min-height: 2.1rem; width: 100%; }}
.stButton button p, .stButton button div {{ white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }}
.st-key-tilebtn .stButton button {{ border-radius: 12px; border: 1px solid #ececec; background: #fff;
  min-height: 70px; padding: 8px 6px; transition: border-color .15s, background .15s, box-shadow .15s; }}
.st-key-tilebtn .stButton button:hover {{ border-color: {GREEN}; background: #F6FAF2; box-shadow: 0 2px 8px rgba(63,125,10,.12); }}
.st-key-tilebtn .stButton button p {{ margin: 0; line-height: 1.5; font-size: 0.78rem !important; color: #6b6b6b; text-align: center; }}
.st-key-tilebtn .stButton button strong {{ color: #1d1d1f !important; font-size: 1.02rem; }}
.st-key-tilebtn .stButton button .stMarkdownColoredText strong {{ color: inherit !important; }}
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

/* prototype strip (mentor controls) */
.proto {{ background: #1f2a24; color: #e8efe9; font-size: .74rem; text-align: center; padding: 5px 10px;
         border-radius: 8px; margin-bottom: 6px; }}
.st-key-protobar {{ background: #F5F7F6; border: 1px solid #e3e8e5; border-radius: 10px; padding: 4px 10px 6px; margin-bottom: 10px; }}
.st-key-protobar label p {{ font-size: .72rem !important; color: #555; }}
.st-key-protobar [data-testid="stPageLink"] p {{ font-size: .8rem !important; white-space: nowrap; }}
.st-key-protobar [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; row-gap: 4px !important; }}
.st-key-protobar [data-testid="stColumn"] {{ min-width: 150px !important; }}
.st-key-protobar [data-testid="stColumn"]:nth-child(n+3) {{ min-width: 90px !important; flex: 0 1 auto !important; }}

/* host-app shell (Groww-style, concept) */
.h-top {{ display: flex; align-items: center; gap: 22px; border-bottom: 1px solid #ececec; padding: 8px 2px 10px;
         margin-bottom: 4px; }}
.h-brand {{ display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 1.25rem; color: #1d1d1f; }}
.h-mark {{ width: 30px; height: 30px; border-radius: 50%; background: conic-gradient(from 200deg, {HOST}, #5367ff, {HOST});
          flex: none; }}
.h-tabs span {{ margin-right: 18px; font-size: .92rem; color: #44475b; cursor: default; }}
.h-tabs span.on {{ color: #1d1d1f; font-weight: 700; border-bottom: 2px solid {HOST}; padding-bottom: 8px; }}
.h-search {{ flex: 1; max-width: 420px; border: 1px solid #e3e3e3; border-radius: 8px; padding: 7px 12px; color: #9a9a9a;
            font-size: .86rem; cursor: default; }}
.h-icons {{ margin-left: auto; display: flex; gap: 16px; align-items: center; color: #44475b; font-size: 1.05rem; cursor: default; }}
.h-avatar {{ width: 30px; height: 30px; border-radius: 50%; background: #EAEFFF; color: #5367ff; font-weight: 700;
            display: flex; align-items: center; justify-content: center; font-size: .85rem; }}
.h-sub span {{ display: inline-block; margin: 6px 18px 8px 0; font-size: .86rem; color: #6b6b6b; cursor: default; }}
.h-sub span.on {{ color: {HOST}; font-weight: 700; }}
.dead {{ cursor: default; }}
@media (max-width: 700px) {{ .h-tabs, .h-search {{ display: none; }} }}

/* dashboard */
.d-sum {{ border: 1px solid #ececec; border-radius: 14px; padding: 16px 18px; }}
.d-sum .lbl {{ color: #6b6b6b; font-size: .8rem; }}
.d-sum .big {{ font-size: 2rem; font-weight: 700; }}
.d-sum .grid {{ display: flex; gap: 28px; margin-top: 10px; flex-wrap: wrap; font-size: .9rem; }}
.d-sum .grid b {{ display: block; font-size: 1rem; }}
.d-new {{ border: 1px solid #cfe5bf; background: linear-gradient(100deg, #F1F8EA, #FFFFFF); border-radius: 14px;
         padding: 16px 18px; margin-top: 12px; }}
.d-new .badge {{ display: inline-block; background: {GREEN}; color: #fff; font-size: .68rem; font-weight: 700;
                border-radius: 6px; padding: 2px 7px; letter-spacing: .4px; margin-right: 6px; }}
.d-new .name {{ color: {GREEN}; font-weight: 700; }}
.d-new .head {{ font-size: 1.25rem; font-weight: 700; margin: 6px 0 4px; }}
.d-new .body {{ color: #444; font-size: .92rem; }}
.d-sec {{ font-weight: 700; font-size: 1.05rem; margin: 18px 0 8px; }}
.st-key-holdrow .stButton button {{ border-radius: 12px; border: 1px solid #ececec; background: #fff; justify-content: flex-start;
  padding: 12px 14px; min-height: 64px; }}
.st-key-holdrow .stButton button:hover {{ border-color: {HOST}; background: #F4FBF8; }}
.st-key-holdrow .stButton button > div, .st-key-holdrow .stButton button span {{ justify-content: flex-start !important; width: 100%; }}
.st-key-holdrow .stButton button p {{ text-align: left; font-size: .86rem !important; color: #555; line-height: 1.5; margin: 0; }}
.st-key-holdrow .stButton button strong {{ color: #1d1d1f; font-size: .95rem; }}
.d-dead {{ border: 1px solid #f0f0f0; border-radius: 12px; padding: 12px 14px; color: #8a8a8a; font-size: .85rem;
          background: #FBFBFB; cursor: default; height: 100%; }}
.d-dead b {{ color: #555; display: block; margin-bottom: 2px; }}
.st-key-backbtn .stButton button {{ border: none; background: transparent; font-size: 1.2rem; min-height: 2rem; padding: 0 6px; width: auto; }}

/* investing-app (fund page) look */
.g-appbar {{ display: flex; align-items: center; gap: 10px; padding: 4px 0 10px; }}
.g-back {{ font-size: 1.2rem; color: #444; }}
.g-logo {{ width: 40px; height: 40px; border-radius: 10px; background: #EAF3E0; color: {GREEN}; font-weight: 700;
          display: flex; align-items: center; justify-content: center; font-size: .9rem; flex: none; }}
.g-fund {{ font-weight: 700; font-size: 1.05rem; }}
.g-tags span {{ display: inline-block; font-size: .72rem; color: #555; background: #F4F4F4; border-radius: 6px;
               padding: 1px 7px; margin: 3px 4px 0 0; }}
.g-hold {{ display: flex; justify-content: space-between; align-items: flex-end; border: 1px solid #ececec;
          border-radius: 14px; padding: 14px 16px; margin-bottom: 8px; }}
.g-hold .lbl {{ color: #6b6b6b; font-size: .8rem; }}
.g-hold .big {{ font-size: 1.9rem; font-weight: 700; }}
.g-hold .mid {{ font-size: 1.1rem; font-weight: 700; text-align: right; }}
.g-hold-r .lbl {{ text-align: right; }}
.g-hint {{ font-size: .78rem; color: {GREEN}; margin: 2px 0 4px; }}
.g-card {{ border: 1px solid #ececec; border-radius: 14px; padding: 12px 16px; margin-top: 10px; }}
.g-card-h {{ font-weight: 700; font-size: .95rem; margin-bottom: 6px; }}
.g-pill {{ font-size: .7rem; background: #EAF3E0; color: {GREEN}; border-radius: 10px; padding: 1px 8px; margin-left: 6px; font-weight: 700; }}
.g-row {{ display: flex; justify-content: space-between; font-size: .88rem; padding: 4px 0; border-bottom: 1px dashed #eee; }}
.g-row:last-child {{ border-bottom: none; }}
.g-tx {{ display: flex; justify-content: space-between; align-items: center; font-size: .88rem; padding: 6px 0; }}
.g-tx .sub {{ color: #6b6b6b; font-size: .76rem; }}
.g-tx .amt {{ text-align: right; font-weight: 700; }}
.st-key-txlist {{ border: 1px solid #ececec; border-radius: 14px; padding: 4px 12px; }}
.st-key-txlist .stButton button {{ border: none; background: #F6FAF2; min-height: 1.8rem; padding: 2px 8px; }}
.st-key-txlist .stButton button p {{ font-size: .74rem !important; color: #355e12; }}
.st-key-txlist .stButton button:hover {{ background: #EAF3E0; }}
.pos {{ color: {GREEN}; }}

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
.nudge-up {{ background: #EEF7E6; }}
.nudge-info {{ background: #F1F6FB; border-left-color: #2f6db5; }}
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

DEAD = 'title="Not part of this FinSaar prototype"'
PROTO = ('<div class="proto">Concept prototype · FinSaar, a concept feature for Groww · Fictional data · '
         'Not investment advice · Not affiliated with Groww</div>')


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(PROTO, unsafe_allow_html=True)


def brand_header():
    """Header for the non-app pages (How to use, Eval)."""
    st.markdown('<div class="app-brand"><span class="name">✦ FinSaar</span>'
                '<span class="tag">Aapke SIP ka saar: a concept feature for Groww</span></div>', unsafe_allow_html=True)


def host_shell(sub: str | None = "Dashboard"):
    """Groww-style top bar. Only FinSaar and what it depends on work; everything here is display-only."""
    tabs = "".join(f'<span class="{"on" if t == "Mutual Funds" else ""}" {DEAD}>{t}</span>'
                   for t in ["Stocks", "Mutual Funds", "F&amp;O", "UPI"])
    st.markdown(
        f'<div class="h-top"><div class="h-brand" {DEAD}><span class="h-mark"></span>Groww</div>'
        f'<div class="h-tabs">{tabs}</div>'
        f'<div class="h-search" {DEAD}>🔍&nbsp; Search Groww…</div>'
        f'<div class="h-icons"><span {DEAD}>🔔</span><span {DEAD}>🛒</span>'
        f'<span class="h-avatar" {DEAD}>A</span></div></div>', unsafe_allow_html=True)
    if sub:
        subs = "".join(f'<span class="{"on" if t == sub else ""}" {DEAD}>{t}</span>'
                       for t in ["Explore", "Dashboard", "SIPs", "Watchlist"])
        st.markdown(f'<div class="h-sub">{subs}</div>', unsafe_allow_html=True)
