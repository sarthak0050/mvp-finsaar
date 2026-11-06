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


/* ---------- Groww-style design system (inside the phone) ---------- */
.st-key-phone {{ --gw-text: #44475b; --gw-dark: #1d1d1f; --gw-grey: #7c7e8c; --gw-line: #e9e9eb;
  --gw-green: #00b386; --gw-red: #eb5b3c; --gw-blue: #5367ff; color: var(--gw-text); }}
.st-key-phone .neg {{ color: var(--gw-red) !important; }}
.st-key-phone .pos {{ color: var(--gw-green) !important; }}
.gw-head {{ display: flex; align-items: center; gap: 10px; padding: 6px 2px 8px; }}
.gw-mark {{ width: 34px; height: 34px; border-radius: 50%; flex: none;
           background: radial-gradient(circle at 35% 35%, #7b8cff, #5367ff 55%, #00d09c); }}
.gw-title {{ font-size: 1.12rem; color: var(--gw-dark); font-weight: 600; }}
.gw-icons {{ margin-left: auto; display: flex; align-items: center; gap: 14px; font-size: 1.3rem; color: var(--gw-text); }}
.gw-av {{ width: 32px; height: 32px; border-radius: 50%; background: #eef3e2; color: #6b7d2a; font-size: .8rem;
         display: inline-flex; align-items: center; justify-content: center; font-weight: 600; }}
.st-key-mftabs {{ border-bottom: 1px solid var(--gw-line); margin: 0 -10px 10px; padding: 0 6px; }}
.st-key-mftabs [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0 !important; }}
.st-key-mftabs [data-testid="stColumn"] {{ min-width: 0 !important; }}
.st-key-mftabs .stButton button, .st-key-mftabs .stButton button[kind="tertiary"], .st-key-mftabs .stButton button[kind="primary"] {{
  width: 100% !important; height: 40px; justify-content: center !important; align-items: center !important; background: transparent !important; border: none !important; border-radius: 0 !important;
  color: #8a8c99 !important; padding: 6px 0 9px !important; min-height: 0 !important; box-shadow: none !important; }}
.st-key-mftabs .stButton button p {{ font-size: .84rem !important; white-space: nowrap; }}
.st-key-mftabs .stButton button[kind="primary"] {{ color: var(--gw-dark) !important; border-bottom: 3px solid #44475b !important;
  border-radius: 2px 2px 0 0 !important; }}
.st-key-mftabs .stButton button[kind="tertiary"] {{ border-bottom: 3px solid transparent !important; }}
.st-key-mftabs .stButton button[kind="primary"] p {{ font-weight: 600; }}
.gw-card, .st-key-holdcard {{ border: 1px solid var(--gw-line) !important; border-radius: 16px; padding: 14px 16px !important;
  margin-bottom: 12px; background: #fff; }}
.st-key-holdcard {{ gap: 0 !important; }}
.gw-cap {{ font-size: .68rem; letter-spacing: 2.2px; color: var(--gw-grey); font-weight: 600; }}
.gw-big {{ font-size: 1.55rem; color: var(--gw-dark); font-weight: 600; margin: 2px 0 2px; }}
.gw-dash {{ border-top: 1px dashed #d6d6da; margin: 8px 0 4px; }}
.st-key-holdcard [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .3rem !important; min-height: 34px; }}
.st-key-holdcard [data-testid="stColumn"] {{ min-width: 0 !important; }}
.gw-lbl {{ font-size: .88rem; color: var(--gw-grey); }}
.gw-val {{ font-size: .9rem; text-align: right; color: var(--gw-dark); }}
.st-key-phone .stButton button[kind="tertiary"] {{ padding: 0 !important; min-height: 0 !important; width: auto !important;
  background: transparent !important; border: none !important; justify-content: flex-start; }}
.st-key-holdcard .stButton button[kind="tertiary"] p {{ font-size: .88rem !important; color: var(--gw-grey);
  text-decoration: underline dotted #a5a7b3; text-underline-offset: 4px; }}
.gw-listhead {{ display: flex; justify-content: space-between; align-items: center; margin: 6px 0 4px; font-size: .84rem; }}
.gw-filter {{ border: 1px solid var(--gw-line); border-radius: 50%; width: 34px; height: 34px; display: inline-flex;
             align-items: center; justify-content: center; }}
.gw-dotted {{ text-decoration: underline dotted #a5a7b3; text-underline-offset: 4px; color: var(--gw-dark); font-size: .84rem; }}
.st-key-fundrow, .st-key-siprow {{ border-bottom: 1px solid var(--gw-line); padding: 6px 0 8px; }}
.st-key-fundrow [data-testid="stHorizontalBlock"], .st-key-siprow [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; }}
.st-key-fundrow [data-testid="stColumn"], .st-key-siprow [data-testid="stColumn"] {{ min-width: 0 !important; }}
.st-key-fundrow .stButton button, .st-key-siprow .stButton button {{ border: none !important; background: transparent !important;
  padding: 0 !important; justify-content: flex-start !important; min-height: 0 !important; }}
.st-key-fundrow .stButton button p, .st-key-siprow .stButton button p {{ text-align: left; font-size: .9rem !important;
  color: var(--gw-dark); line-height: 1.55; }}
.st-key-fundrow .stButton button > div, .st-key-siprow .stButton button > div {{ justify-content: flex-start !important; width: 100%; }}
.gw-rowval {{ text-align: right; font-size: .95rem; }}
.gw-rowval small {{ color: var(--gw-grey); font-size: .8rem; }}
.gw-pill-btn {{ margin: 18px auto 6px; width: fit-content; border: 1px solid #d9d9de; border-radius: 10px; padding: 8px 16px;
               font-size: .85rem; cursor: default; }}
.gw-sechead {{ display: flex; justify-content: space-between; align-items: center; margin: 14px 0 8px; font-size: .95rem;
              color: var(--gw-dark); }}
.gw-muted {{ color: var(--gw-grey); font-size: .8rem; }}
.gw-link {{ color: var(--gw-green); font-size: .88rem; cursor: default; }}
.gw-date {{ border: 1px solid var(--gw-line); border-radius: 10px; text-align: center; font-size: .75rem; color: var(--gw-grey);
           padding: 4px 0; line-height: 1.3; }}
.gw-date b {{ font-size: .95rem; color: var(--gw-dark); font-weight: 600; }}
.gw-tile {{ display: inline-flex; width: 36px; height: 36px; border-radius: 9px; color: #fff; font-size: .72rem; font-weight: 700;
           align-items: center; justify-content: center; flex: none; }}
.gw-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.gw-fcard {{ border: 1px solid var(--gw-line); border-radius: 14px; padding: 12px; font-size: .84rem; color: var(--gw-dark);
            cursor: default; display: flex; flex-direction: column; gap: 8px; }}
.gw-wrow {{ display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--gw-line);
           font-size: .88rem; color: var(--gw-dark); cursor: default; }}
.gw-fhead {{ display: flex; align-items: center; gap: 10px; font-weight: 600; color: var(--gw-dark); font-size: .95rem; line-height: 1.25; }}
.gw-sip {{ display: flex; justify-content: space-between; font-size: .9rem; color: var(--gw-dark); margin-bottom: 0; }}
.gw-manage {{ display: flex; justify-content: space-between; padding: 10px 2px; border-bottom: 1px solid var(--gw-line);
             font-size: .88rem; color: var(--gw-dark); cursor: default; }}
.gw-tx {{ display: flex; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid var(--gw-line);
         font-size: .86rem; color: var(--gw-dark); }}
.gw-nav {{ position: sticky; bottom: -1px; background: #fff; border-top: 1px solid var(--gw-line); display: flex;
          justify-content: space-around; padding: 8px 0 6px; margin: 18px -10px 0; z-index: 5; }}
.gw-nav div {{ font-size: .68rem; color: #8a8c99; text-align: center; cursor: default; }}
.gw-nav div span {{ display: block; font-size: 1.1rem; }}
.gw-nav div.on {{ color: var(--gw-blue); font-weight: 600; }}
/* FinSaar inside the host UI: quiet, inline, dismissible */
.st-key-fsline {{ background: #F3F8EE; border-radius: 12px; padding: 10px 12px !important; margin: 0 0 10px; gap: .4rem !important; }}
.fs-line {{ display: flex; gap: 8px; font-size: .86rem; color: var(--gw-dark); line-height: 1.4; }}
.fs-dot {{ color: {GREEN}; font-weight: 700; }}
.fs-dot.big {{ font-size: 1.1rem; }}
.st-key-fsline [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .5rem !important; }}
.st-key-fsline [data-testid="stColumn"] {{ min-width: 0 !important; }}
.st-key-fsline .stButton button[kind="tertiary"] p {{ color: var(--gw-grey); font-size: .82rem !important; }}
.st-key-fsline .stButton button[kind="tertiary"] {{ padding-top: 6px !important; }}
.st-key-fspill {{ position: sticky; bottom: 14px; z-index: 6; display: flex; align-items: flex-end; margin-top: 10px; }}
.st-key-fspill .stButton {{ display: flex; justify-content: flex-end; width: 100%; }}
.st-key-fspill .stButton button {{ width: auto !important; border-radius: 22px !important; background: #1d1d1f !important;
  border-color: #1d1d1f !important; box-shadow: 0 6px 18px rgba(0,0,0,.25); padding: 8px 16px !important; }}
.sh-grab {{ width: 40px; height: 4px; border-radius: 3px; background: #d9d9de; margin: 0 auto 8px; }}
.sh-sec {{ text-transform: uppercase; }}
.st-key-sheet .sh-val {{ float: right; color: var(--gw-dark); font-weight: 600; }}
.st-key-sheetchips {{ flex-direction: row !important; flex-wrap: wrap; gap: 6px !important; margin-top: 4px; }}
.st-key-sheetchips > div {{ width: auto !important; }}

/* ---------- phone prototype ---------- */
.st-key-phone {{ background: #fff; }}
@media (min-width: 641px) {{
  [data-testid="stLayoutWrapper"]:has(> .st-key-phone) {{ border: 11px solid #16181a !important; border-radius: 42px !important;
     box-shadow: 0 18px 50px rgba(0,0,0,.22); overflow: hidden; max-width: 414px; margin: 0 auto; }}
  .st-key-phone {{ border: none !important; border-radius: 30px; padding: 6px 10px 0 !important; scrollbar-width: thin; }}
}}
@media (max-width: 640px) {{
  .st-key-phone {{ height: auto !important; max-height: none !important; overflow: visible !important; border: none !important; padding: 0 !important; }}
  [data-testid="stLayoutWrapper"]:has(> .st-key-phone) {{ height: auto !important; border: none !important; }}
}}
.st-key-phone {{ max-width: 392px; margin: 0 auto; }}
.ph-status {{ display: flex; justify-content: space-between; font-size: .72rem; color: #222; padding: 2px 4px 6px; }}
.ph-head {{ display: flex; justify-content: space-between; align-items: center; padding: 2px 0 6px; }}
.wordmark {{ display: flex; align-items: center; gap: 7px; font-weight: 700; font-size: 1.1rem; }}
.wordmark .h-mark {{ width: 24px; height: 24px; }}
.ph-icons {{ font-size: .95rem; letter-spacing: 6px; }}
.ph-tabs {{ display: flex; gap: 16px; font-size: .85rem; color: #44475b; border-bottom: 1px solid #eee; }}
.ph-tabs span {{ padding-bottom: 6px; }}
.ph-tabs span.on {{ color: #1d1d1f; font-weight: 700; border-bottom: 2px solid {HOST}; }}
.ph-title {{ font-weight: 700; font-size: .98rem; line-height: 1.25; }}
.ph-sub {{ font-size: .72rem; color: #6b6b6b; }}
.ph-actions {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 10px 0 2px; }}
.ph-actions span {{ border: 1px solid #e3e3e3; border-radius: 8px; padding: 5px 9px; font-size: .74rem; color: #555; cursor: default; }}
.ph-nav {{ position: sticky; bottom: -1px; background: #fff; border-top: 1px solid #eee; display: flex;
          justify-content: space-around; padding: 6px 0 4px; margin: 14px -4px 0; z-index: 5; }}
.ph-nav div {{ font-size: .64rem; color: #7a7a7a; text-align: center; cursor: default; }}
.ph-nav div span {{ display: block; font-size: 1rem; }}
.ph-nav div.on {{ color: {HOST}; font-weight: 700; }}
.st-key-phone .d-sum {{ padding: 12px 14px; }}
.st-key-phone .d-sum .big {{ font-size: 1.6rem; }}
.st-key-phone .d-sum .grid {{ gap: 14px; font-size: .78rem; }}
.st-key-phone .d-sum .grid b {{ font-size: .88rem; }}
.st-key-phone .g-hold .big {{ font-size: 1.55rem; }}
.st-key-phone .fs-card {{ font-size: .86rem; padding: 10px 12px; }}
.st-key-phone .fs-q {{ font-size: .84rem; margin-left: 15%; background: #1f2a24; color: #fff; }}
.st-key-phone .d-sec {{ font-size: .92rem; margin: 14px 0 6px; }}
.st-key-phone .stButton button {{ font-size: .78rem; }}
.st-key-phone [data-testid="stExpander"] summary p {{ font-size: .76rem; }}
.fs-outside {{ display: inline-block; background: #FFF1E6; color: #8a4b12; font-size: .72rem; border-radius: 6px;
              padding: 2px 8px; margin: 2px 0 6px; }}
.fs-links {{ font-size: .74rem; margin-top: 6px; }}
.fs-src {{ font-size: .7rem; color: #6b6b6b; margin-top: 4px; }}
.fs-help {{ font-size: .78rem; color: #444; margin: 4px 0 2px; }}
/* bottom sheet inside the phone */
.st-key-sheet {{ position: sticky; bottom: 0; z-index: 10; background: #fff; border-radius: 18px 18px 0 0;
                box-shadow: 0 -8px 28px rgba(0,0,0,.18); padding: 10px 12px 12px; margin: 10px -6px 0;
                }}
.sh-title {{ font-weight: 700; font-size: 1.05rem; }}
.sh-val {{ float: right; color: #B3261E; }}
.sh-sec {{ font-size: .66rem; letter-spacing: .6px; color: #6b6b6b; font-weight: 700; margin: 10px 0 2px; }}
.sh-txt {{ font-size: .86rem; line-height: 1.4; }}
.st-key-sheetchips .stButton button {{ border-radius: 16px; font-size: .76rem; width: auto; margin-bottom: 4px; }}
.st-key-sheetchips .stButton {{ display: inline-block; margin-right: 6px; }}
[class*="st-key-fbsheet"] [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .4rem !important; }}
[class*="st-key-fbsheet"] [data-testid="stColumn"] {{ min-width: 0 !important; }}
.st-key-backbtn [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; }}
.st-key-backbtn [data-testid="stColumn"] {{ min-width: 0 !important; }}
/* side panels */
.pc-h {{ font-weight: 700; font-size: .78rem; letter-spacing: .6px; text-transform: uppercase; color: #6b6b6b; margin-bottom: 6px; }}
.pc-task {{ background: #FFF8E6; border: 1px solid #f1e2b8; border-radius: 10px; padding: 9px 11px; font-size: .82rem; margin: 10px 0; }}
.nt-h {{ font-weight: 700; color: {GREEN}; font-size: .92rem; margin-bottom: 4px; }}
.st-key-notespanel p, .st-key-notespanel li {{ font-size: .82rem; }}
.st-key-ctrlpanel, .st-key-notespanel {{ position: sticky; top: 10px; }}
@media (min-width: 900px) {{
  div:has(> .st-key-phone) {{ }}
}}
@media (max-width: 640px) {{
  [data-testid="stColumn"]:has(.st-key-ctrlpanel) {{ order: 2; }}
  [data-testid="stColumn"]:has(.st-key-notespanel) {{ order: 3; }}
  .block-container {{ padding: .4rem .6rem 2rem !important; }}
}}

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
PROTO = '<div class="proto">Concept prototype · Fictional data · Not investment advice · Not affiliated with Groww</div>'


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(CSS_FIX, unsafe_allow_html=True)
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown(LINKS_CSS, unsafe_allow_html=True)
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

CSS_FIX = """
<style>
.st-key-holdcard .stMarkdown, .st-key-fsline .stMarkdown, .st-key-fundrow .stMarkdown, .st-key-siprow .stMarkdown { margin-bottom: 0 !important; }
.st-key-holdcard [data-testid="stMarkdownContainer"] p, .st-key-fsline [data-testid="stMarkdownContainer"] p { margin: 0; }
.st-key-holdcard [data-testid="stHorizontalBlock"] { align-items: center !important; min-height: 36px; }
.st-key-holdcard [data-testid="stColumn"] > div { justify-content: center; }
.st-key-holdcard .stButton button[kind="tertiary"] { height: 28px; align-items: center !important; }
.st-key-fsline { gap: .55rem !important; }
.st-key-fundrow .stButton button [data-testid="stMarkdownContainer"],
.st-key-siprow .stButton button [data-testid="stMarkdownContainer"] { text-align: left !important; width: 100%; }
.st-key-fundrow .stButton button p, .st-key-siprow .stButton button p { text-align: left !important; }
.st-key-mftabs .stButton button { align-items: center !important; padding: 0 !important; }
.st-key-mftabs .stButton button > div { align-items: center; }
.st-key-holdcard .stButton button[kind="tertiary"] { position: relative; top: 8px; }
.st-key-fsline [data-testid="stElementContainer"] { height: auto !important; min-height: fit-content; }
/* the phone is a fixed-height scroll box: never let its contents shrink to fit */
.st-key-phone > *, .st-key-phone [data-testid="stVerticalBlock"] > * { flex-shrink: 0 !important; }
.st-key-fsline .stMarkdown, .st-key-fsline [data-testid="stMarkdownContainer"] { height: auto !important; overflow: visible;
  margin-bottom: 0 !important; }
.fs-line { display: flex; padding-bottom: 2px; }
.gw-nav svg { width: 22px; height: 22px; display: block; margin: 0 auto 2px; stroke: currentColor; fill: none; stroke-width: 1.6; }
</style>
"""

APP_CSS = """
<style>
/* canvas */
.stApp { background: radial-gradient(1200px 700px at 50% 30%, #f6f8f5 0%, #e9efe8 70%, #e3eae2 100%) !important; }
.block-container { max-width: 1320px !important; }
.proto { background: transparent !important; color: #6b7a6f !important; border: 1px solid #d6dfd4; font-size: .72rem !important; }
/* left panel */
.lp-cap { font-size: .7rem; letter-spacing: 2.4px; color: #56645a; font-weight: 700; margin: 14px 0 8px; }
.lp-title { font-size: 2.9rem; font-weight: 600; letter-spacing: -1.5px; color: #16201a; line-height: 1.05; }
.lp-sub { color: #4b5750; font-size: .98rem; line-height: 1.5; margin-top: 10px; }
.st-key-momentlist { background: #fff; border: 1px solid #dfe6dd; border-radius: 14px; padding: 6px !important; }
.st-key-momentlist [role="radiogroup"] { gap: 2px !important; width: 100%; align-items: stretch !important; display: flex !important; flex-direction: column !important; }
.st-key-momentlist [role="radiogroup"] label { width: 100%; padding: 9px 12px; border-radius: 10px; margin: 0 !important; }
.st-key-momentlist [role="radiogroup"] label:has(input:checked) { background: #f3f6f2; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.st-key-momentlist [role="radiogroup"] label:has(input:checked) p { font-weight: 700; color: #16201a; }
.st-key-momentlist [role="radiogroup"] label > div:first-child { display: none; }
.st-key-momentlist [role="radiogroup"] label p { font-size: .9rem !important; color: #3b4740; }
.st-key-openchat .stButton button { background: #1f3d2b !important; border-color: #1f3d2b !important; border-radius: 12px !important;
  min-height: 46px; margin-top: 14px; }
.lp-task { font-size: .8rem; color: #4b5750; background: #fff; border: 1px dashed #cdd8cb; border-radius: 12px;
  padding: 10px 12px; margin-top: 10px; }
/* right panel */
.rp-title { font-size: 2rem; font-weight: 600; letter-spacing: -1px; color: #16201a; line-height: 1.12; margin-bottom: 18px; }
.rp-step { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 16px; opacity: .55; }
.rp-step.on { opacity: 1; }
.rp-step b { color: #1f3d2b; font-size: .95rem; }
.rp-step div div { font-size: .78rem; color: #6b7a6f; }
.rp-n { width: 40px; height: 40px; border-radius: 50%; border: 1px solid #cdd8cb; display: inline-flex; align-items: center;
  justify-content: center; font-size: .72rem; font-weight: 700; color: #56645a; flex: none; background: #fff; }
.rp-step.on .rp-n { background: #1f3d2b; color: #fff; border-color: #1f3d2b; box-shadow: 0 0 0 5px #d9e6d6; }
.rp-guard { background: #fff; border: 1px solid #dfe6dd; border-radius: 14px; padding: 14px 18px; margin-top: 18px;
  font-size: .8rem; color: #4b5750; line-height: 1.8; }
.rp-guard b { color: #16201a; font-size: .9rem; display: block; margin-bottom: 4px; }
.rp-note { font-size: .74rem; color: #6b7a6f; margin-top: 10px; }
/* phone shell */
[data-testid="stLayoutWrapper"]:has(> .st-key-phone) { border: 10px solid #121413 !important; border-radius: 46px !important;
  box-shadow: 0 30px 70px rgba(20,40,25,.22) !important; }
.ph-status { padding: 6px 10px 8px !important; font-size: .88rem !important; }
.ph-sig { font-size: .7rem; letter-spacing: 1px; }
.ph-batt { background: #121413; color: #fff; border-radius: 5px; padding: 0 5px; font-size: .68rem; font-weight: 700; }
.ph-foot { text-align: center; font-size: .78rem; color: #56645a; margin-top: 10px; }
.ph-foot .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #1fa463; margin-right: 6px; }
.gw-icons svg { width: 21px; height: 21px; fill: none; stroke: #44475b; stroke-width: 1.7; }
.gw-mark { background: conic-gradient(from 200deg, #5367ff, #00d09c, #5367ff) !important; border: 3px solid #fff;
  box-shadow: 0 0 0 2px #5367ff; }
.gw-tile { background: linear-gradient(135deg, #2f7d5b, #144a35); width: 40px !important; height: 40px !important; border-radius: 10px !important;
  font-size: .95rem !important; }
.fsm { color: #3F7D0A; font-weight: 700; font-size: .8em; }
/* holdings */
.gw-bigrow { display: flex; justify-content: space-between; align-items: center; }
.gw-eye { width: 40px; height: 40px; border: 1px solid #e3e3e6; border-radius: 50%; display: inline-flex; align-items: center;
  justify-content: center; font-size: .9rem; }
[class*="st-key-tapv_"] { align-items: flex-end; }
[class*="st-key-tapv_"] .stButton { display: flex; justify-content: flex-end; width: 100%; }
[class*="st-key-tapv_"] .stButton button p { font-size: .92rem !important; color: #1d1d1f; font-weight: 600;
  text-decoration: underline dotted #9aa0a6; text-underline-offset: 5px; }
.st-key-holdcard .stButton button[kind="tertiary"] { top: 0 !important; }
.gw-rowval .chev, .chev { color: #7c7e8c; font-size: 1.1rem; margin-left: 4px; }
.st-key-fundrow .stButton button p strong { font-weight: 600; }
/* FinSaar card on the dashboard */
.st-key-fscard { background: linear-gradient(135deg, #f7f5ff, #f1f8f3); border: 1px solid #dcdcf4; border-radius: 16px;
  padding: 12px 12px 10px !important; margin-bottom: 10px; }
.st-key-fscard [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.st-key-fscard [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-fscard .stMarkdown, .st-key-fscard [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.fs-icon { width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, #3F7D0A, #1f3d2b); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.fs-tag { color: #3F7D0A; font-size: .72rem; font-weight: 700; }
.fs-title { color: #1d1d1f; font-size: .95rem; font-weight: 600; line-height: 1.35; margin: 2px 0 2px; }
.st-key-fscard .stButton button[kind="tertiary"] p { color: #3F7D0A !important; font-size: .84rem !important; }
.st-key-fscard [data-testid="stColumn"]:last-child .stButton button p { color: #7c7e8c !important; font-size: 1rem !important; }
.gw-empty .gw-muted { margin-top: 6px; }
.gw-promo { display: flex; flex-direction: column; gap: 12px; font-size: .95rem; color: #1d1d1f; cursor: default; }
.gw-cta { background: #00b386; color: #fff; border-radius: 8px; padding: 8px 16px; width: fit-content; font-weight: 600; font-size: .85rem; }
/* fund details */
.st-key-fdhead { border-bottom: 1px solid #ececef; margin: 0 -10px 10px; padding: 0 10px 6px; }
.st-key-fdhead [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.st-key-fdhead [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-fdhead .stButton button p { font-size: 1.6rem !important; color: #1d1d1f; }
.fd-title { text-align: center; font-weight: 600; font-size: 1rem; color: #1d1d1f; }
.fd-more { text-align: right; color: #7c7e8c; font-size: 1.1rem; }
.st-key-askbanner .stButton button { background: linear-gradient(135deg, #f7f5ff, #f1f8f3) !important; border: 1px solid #dcdcf4 !important;
  border-radius: 14px !important; justify-content: flex-start !important; padding: 12px 14px !important; min-height: 60px; }
.st-key-askbanner .stButton button p { text-align: left; font-size: .9rem !important; color: #1d1d1f; line-height: 1.45; }
.st-key-askbanner .stButton button > div { justify-content: flex-start !important; width: 100%; }
.st-key-askbanner .stButton button::after { content: "›"; position: absolute; right: 16px; color: #7c7e8c; font-size: 1.3rem; }
.fd-sec { font-size: 1rem; color: #1d1d1f; margin: 18px 0 8px; font-weight: 500; }
.fd-fund { display: flex; gap: 12px; align-items: center; font-size: .88rem; color: #1d1d1f; margin-bottom: 6px; }
[class*="st-key-drow_"] { border-bottom: 1px solid #f0f0f2; padding: 4px 0; }
[class*="st-key-drow_"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; min-height: 40px; }
[class*="st-key-drow_"] [data-testid="stColumn"] { min-width: 0 !important; }
[class*="st-key-drow_"] [data-testid="stColumn"]:last-child .stButton { display: flex; justify-content: flex-end; width: 100%; }
[class*="st-key-drow_"] .stButton button p { font-size: .92rem !important; color: #3F7D0A; font-weight: 600; }
.fd-lbl { font-size: .9rem; color: #1d1d1f; }
.fd-val { text-align: right; font-size: .92rem; color: #1d1d1f; font-weight: 600; padding-right: 14px; }
.st-key-yoursip { border-top: 8px solid #f4f5f6; border-bottom: 8px solid #f4f5f6; margin: 14px -10px 0; padding: 14px 10px !important; }
.st-key-yoursip [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.st-key-yoursip [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-yoursip .stButton { display: flex; justify-content: flex-end; width: 100%; }
.st-key-yoursip .stButton button p { color: #00b386 !important; font-weight: 600; }
.fd-sip { font-size: 1rem; color: #1d1d1f; margin: 4px 0 2px; }
.gw-done { color: #00b386; font-size: .74rem; }
/* chat */
.ch-fund { border: 1px solid #ececef; border-radius: 14px; padding: 10px 12px; font-size: .86rem; color: #1d1d1f; margin-bottom: 10px; }
.fs-ans { background: #fff; border: 1px solid #e6e8ea; border-radius: 16px; padding: 12px 14px; margin: 8px 15% 6px 0;
  font-size: .86rem; color: #1d1d1f; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
.fs-ans .fs-label { color: #3F7D0A; font-size: .72rem; font-weight: 700; margin-bottom: 4px; }
.fs-rule { border-top: 1px solid #eef0f1; margin: 10px 0 6px; }
.fs-ans .fs-check { color: #1f8a4c; font-size: .74rem; font-weight: 600; margin: 0; }
.fs-ans .fs-src { color: #7c7e8c; font-size: .7rem; margin-top: 2px; }
.st-key-phone .fs-q { background: #1f3d2b !important; color: #fff; border-radius: 16px 16px 4px 16px !important; padding: 12px 14px !important;
  margin: 10px 0 4px 18% !important; font-size: .86rem !important; }
[class*="st-key-fb"] .stButton button { border-radius: 18px !important; border: 1px solid #dfe3e6 !important; background: #fff !important;
  min-height: 30px !important; padding: 2px 12px !important; }
[class*="st-key-fb"] .stButton button p { font-size: .76rem !important; color: #1d1d1f; }
.st-key-askbox .stTextInput input { border-radius: 24px !important; border: 1px solid #1f3d2b !important; background: #fff !important; }
.st-key-askbox [data-testid="stFormSubmitButton"] button { border-radius: 50% !important; width: 44px; height: 44px;
  background: #1f3d2b !important; color: #fff !important; border: none !important; }
.st-key-phone .memory { font-size: .74rem; }
[class*="st-key-drow_"] .stButton button { position: relative; top: 9px; }
[class*="st-key-tabon_"] .stButton button { border-bottom: 3px solid #44475b !important; border-radius: 2px 2px 0 0 !important; }
[class*="st-key-tabon_"] .stButton button p { color: #1d1d1f !important; font-weight: 600 !important; }
[class*="st-key-taboff_"] .stButton button p { color: #8a8c99 !important; }
/* ---- pinned to the bottom of the phone (the phone itself is the scroll box) ---- */
.st-key-phone { padding-bottom: 0 !important; }
.st-key-phone > [data-testid="stElementContainer"]:has(.gw-nav) { position: sticky; bottom: 0; margin-top: auto;
  z-index: 30; background: #fff; margin-left: -10px; margin-right: -10px; }
.st-key-phone > [data-testid="stElementContainer"]:has(.gw-nav) .stMarkdown,
.st-key-phone > [data-testid="stElementContainer"]:has(.gw-nav) [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.st-key-phone .gw-nav { position: static !important; margin: 0 !important; padding: 8px 0 10px !important; }
.st-key-phone > *:has(.st-key-askbox) { position: sticky; bottom: 0; margin-top: auto; z-index: 30; background: #fff;
  margin-left: -10px; margin-right: -10px; padding: 8px 10px 12px; border-top: 1px solid #eef0f1; }
.st-key-askbox [data-testid="stHorizontalBlock"] { align-items: center !important; }
.st-key-askbox .stTextInput input { height: 44px; padding: 0 16px; font-size: .88rem; border: none !important; background: transparent !important; }
.st-key-askbox [data-baseweb="input"], .st-key-askbox [data-baseweb="base-input"] { border-radius: 24px !important; background: #fff !important;
  border: 1.5px solid #1f3d2b !important; }
.st-key-askbox [data-baseweb="base-input"] { border: none !important; }
.st-key-askbox [data-testid="stTextInputRootElement"] { background: #fff !important; border: 1.5px solid #1f3d2b !important;
  border-radius: 24px !important; overflow: hidden; }
.st-key-askbox [data-testid="stFormSubmitButton"] { display: flex; justify-content: flex-end; }
/* ---- bottom sheet: overlay pinned to the bottom, scrolls inside, dims the screen above ---- */
.st-key-phone > *:has(> .st-key-sheet), .st-key-phone > *:has(.st-key-sheet) { position: sticky; bottom: 0; z-index: 40;
  margin-left: -10px; margin-right: -10px; margin-top: -60vh; }
.st-key-sheet { max-height: 600px; overflow-y: auto; background: #fff; border-radius: 22px 22px 0 0 !important;
  padding: 8px 16px 16px !important; margin: 0 !important; box-shadow: 0 0 0 2000px rgba(16,24,20,.38), 0 -6px 24px rgba(0,0,0,.18) !important;
  gap: .35rem !important; }
.sh-grab { width: 42px; height: 5px; border-radius: 3px; background: #d6d8dc; margin: 4px auto 6px; }
.st-key-shhead [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center !important; }
.st-key-shhead [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-shhead [data-testid="stColumn"]:last-child .stButton { display: flex; justify-content: flex-end; width: 100%; }
.st-key-shhead .stButton button p { font-size: 1.15rem !important; color: #7c7e8c; }
.st-key-shhead .stMarkdown, .st-key-shhead [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.sh-title { font-size: 1.12rem !important; font-weight: 600 !important; color: #1d1d1f; }
.st-key-sheet .sh-val { float: none !important; text-align: right; font-size: 1.12rem; font-weight: 600; color: #1d1d1f; }
.st-key-sheet .sh-val.neg { color: #eb5b3c; } .st-key-sheet .sh-val.pos { color: #00b386; }
.sh-sec { font-size: .66rem !important; letter-spacing: 1px; color: #7c7e8c !important; margin: 10px 0 2px !important; }
.sh-txt { font-size: .88rem !important; color: #1d1d1f; }
[class*="st-key-fbsheet"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .5rem !important; }
[class*="st-key-fbsheet"] [data-testid="stColumn"] { min-width: 0 !important; }
[class*="st-key-fbsheet"] .stButton button { border-radius: 20px !important; border: 1px solid #dfe3e6 !important; background: #fff !important;
  min-height: 34px !important; }
[class*="st-key-fbsheet"] [data-testid="stColumn"]:first-child .stButton button { background: #1f3d2b !important; border-color: #1f3d2b !important; }
[class*="st-key-fbsheet"] [data-testid="stColumn"]:first-child .stButton button p { color: #fff !important; }
[class*="st-key-fbsheet"] .stButton button p { font-size: .78rem !important; color: #1d1d1f; }
.st-key-sheet [data-testid="stButtonGroup"] button { font-size: .78rem; }
/* ---- answer card (chat + sheet): one card, chips inside ---- */
[class*="st-key-anscard_"] { background: #fff; border: 1px solid #e6e8ea; border-radius: 16px; padding: 12px 14px !important;
  gap: .4rem !important; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
[class*="st-key-anscard_t"] { margin-right: 12%; }
[class*="st-key-anscard_"] .stMarkdown, [class*="st-key-anscard_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[class*="st-key-anscard_"] .fs-label { color: #3F7D0A; font-size: .72rem; font-weight: 700; margin-bottom: 4px; }
[class*="st-key-anscard_"] .fs-body { font-size: .86rem; line-height: 1.5; color: #1d1d1f; }
[class*="st-key-anscard_"] [data-testid="stExpander"] { border: none !important; }
[class*="st-key-anscard_"] [data-testid="stExpander"] details { border: none !important; }
[class*="st-key-anscard_"] [data-testid="stExpander"] summary { padding: 0 !important; background: transparent !important; }
[class*="st-key-anscard_"] [data-testid="stExpander"] details, [class*="st-key-anscard_"] [data-testid="stExpander"] > div { background: transparent !important; }
[class*="st-key-anscard_"] [data-testid="stExpander"] summary p { font-size: .72rem !important; color: #7c7e8c; }
[class*="st-key-anscard_"] [class*="st-key-fb"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .4rem !important; }
[class*="st-key-anscard_"] [class*="st-key-fb"] [data-testid="stColumn"] { min-width: 0 !important; }
[class*="st-key-anscard_"] [class*="st-key-fb"] .stButton button { width: auto !important; white-space: nowrap; }
.fs-greet { margin-right: 12% !important; }
/* ---- fund details tidy ---- */
[class*="st-key-drow_"] { padding: 2px 0 !important; }
[class*="st-key-drow_"] [data-testid="stHorizontalBlock"] { min-height: 46px; }
.gw-tx { font-size: .84rem !important; padding: 12px 0 !important; }
/* ---- journey list: no radio dots, a check on the selected row ---- */
.st-key-momentlist label[data-testid="stRadioOption"] > div > div:first-child { display: none !important; }
.st-key-momentlist label[data-testid="stRadioOption"] { position: relative; width: 100% !important; display: flex !important;
  padding-right: 40px !important; box-sizing: border-box; }
.st-key-momentlist [data-testid="stElementContainer"], .st-key-momentlist [data-testid="stRadio"],
.st-key-momentlist [data-testid="stRadioGroup"], .st-key-momentlist [data-testid="stRadioGroup"] > div,
.st-key-momentlist [data-testid="stRadioOption"] { width: 100% !important; }
.st-key-momentlist label[data-testid="stRadioOption"][data-selected="true"]::after { content: "✓"; position: absolute; right: 14px;
  top: 50%; transform: translateY(-50%); color: #16201a; font-weight: 700; }
.st-key-momentlist label[data-testid="stRadioOption"][data-selected="true"] { background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
.st-key-momentlist label[data-testid="stRadioOption"][data-selected="true"] p { font-weight: 700 !important; color: #16201a !important; }

</style>
"""

LINKS_CSS = """
<style>
.st-key-lplinks [data-testid="stHorizontalBlock"] { align-items: center !important; flex-wrap: nowrap !important; }
.st-key-lplinks [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-lplinks [data-testid="stPageLink"] a, .st-key-lplinks .stButton button { padding: 4px 0 !important; min-height: 0 !important; }
.st-key-lplinks .stButton button p, .st-key-lplinks [data-testid="stPageLink"] p { font-size: .88rem !important; color: #1f3d2b !important; }
</style>
"""
