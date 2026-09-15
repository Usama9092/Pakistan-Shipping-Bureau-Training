from __future__ import annotations

from psb_app.common import st


def apply_professional_theme() -> None:
    """Apply one consistent PSB visual language across every authenticated page.

    The base application already supplies functional styling.  This layer is a
    deliberately late override that standardises typography, spacing, cards,
    forms, navigation, tables, tabs and status surfaces across the whole portal.
    """
    st.markdown(
        r"""
<style>
:root{
  --psb-ink:#10243a;
  --psb-navy:#061a31;
  --psb-navy-2:#0a315d;
  --psb-blue:#0d4f8f;
  --psb-green:#087443;
  --psb-green-2:#0d8f56;
  --psb-gold:#c9912f;
  --psb-bg:#f4f7fb;
  --psb-surface:#ffffff;
  --psb-surface-2:#f8fafc;
  --psb-line:#dbe4ee;
  --psb-line-strong:#c8d5e3;
  --psb-muted:#66788a;
  --psb-success:#087443;
  --psb-warning:#a86610;
  --psb-danger:#b42318;
  --psb-shadow:0 12px 32px rgba(16,36,58,.07);
  --psb-shadow-soft:0 4px 16px rgba(16,36,58,.055);
  --psb-radius:16px;
}

html,body,[class*="css"]{
  font-family:Inter,"Segoe UI",Roboto,Arial,sans-serif;
}
.stApp{
  background:
    radial-gradient(circle at 88% 2%,rgba(13,79,143,.055),transparent 24rem),
    linear-gradient(180deg,#f8fafc 0,#f4f7fb 100%)!important;
  color:var(--psb-ink)!important;
}
[data-testid="stAppViewContainer"]>.main{
  background:transparent;
}
.block-container{
  max-width:1500px!important;
  padding:1.25rem 2rem 3rem!important;
}

/* Page typography */
h1,h2,h3,h4,h5,h6{
  color:var(--psb-ink)!important;
  letter-spacing:-.02em;
}
h1{font-size:2rem!important;font-weight:850!important;margin-bottom:.35rem!important}
h2{font-size:1.48rem!important;font-weight:820!important}
h3{font-size:1.13rem!important;font-weight:800!important}
p,.stMarkdown{line-height:1.62}
[data-testid="stCaptionContainer"],small{color:var(--psb-muted)!important}
hr{border-color:var(--psb-line)!important;margin:1.35rem 0!important}

/* Sidebar */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#05162a 0%,#092c54 55%,#0a3a62 100%)!important;
  border-right:1px solid rgba(255,255,255,.09)!important;
  box-shadow:8px 0 28px rgba(6,26,49,.10)!important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label,
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  transition:background .16s ease,border-color .16s ease,transform .16s ease;
  border:1px solid transparent!important;
  border-radius:11px!important;
  padding:.48rem .62rem!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
  background:rgba(255,255,255,.105)!important;
  border-color:rgba(255,255,255,.09)!important;
  transform:translateX(2px);
}
section[data-testid="stSidebar"] .psb-user-card{
  background:linear-gradient(135deg,rgba(255,255,255,.10),rgba(255,255,255,.055))!important;
  border:1px solid rgba(255,255,255,.14)!important;
  box-shadow:0 8px 22px rgba(0,0,0,.10);
}
section[data-testid="stSidebar"] .psb-nav-section{
  color:#9ed5ff!important;
  border-top:1px solid rgba(255,255,255,.11)!important;
}

/* Native Streamlit containers/cards */
[data-testid="stVerticalBlockBorderWrapper"]>div,
div[data-testid="stMetric"],
div[data-testid="stExpander"],
.stTabs [data-baseweb="tab-list"],
[data-testid="stForm"]{
  border-color:var(--psb-line)!important;
}
div[data-testid="stMetric"]{
  background:linear-gradient(180deg,#ffffff 0%,#fbfcfe 100%)!important;
  border:1px solid var(--psb-line)!important;
  border-radius:var(--psb-radius)!important;
  padding:1rem 1.05rem!important;
  box-shadow:var(--psb-shadow-soft)!important;
  min-height:104px;
}
div[data-testid="stMetric"] label{
  color:var(--psb-muted)!important;
  font-size:.78rem!important;
  font-weight:780!important;
  text-transform:uppercase;
  letter-spacing:.045em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
  color:var(--psb-ink)!important;
  font-weight:850!important;
  letter-spacing:-.035em;
}

/* Forms */
[data-testid="stForm"]{
  background:var(--psb-surface)!important;
  border:1px solid var(--psb-line)!important;
  border-radius:18px!important;
  padding:1.1rem 1.2rem!important;
  box-shadow:var(--psb-shadow-soft)!important;
}
label,.stSelectbox label,.stTextInput label,.stTextArea label,.stDateInput label,.stNumberInput label,.stFileUploader label{
  color:#2b4156!important;
  font-weight:760!important;
}
input,textarea,[data-baseweb="select"]>div,[data-baseweb="input"]>div{
  background:#fff!important;
  color:var(--psb-ink)!important;
  border-color:var(--psb-line-strong)!important;
  border-radius:11px!important;
  box-shadow:none!important;
}
input:focus,textarea:focus,[data-baseweb="select"]>div:focus-within{
  border-color:#6f9fca!important;
  box-shadow:0 0 0 3px rgba(13,79,143,.09)!important;
}

/* Buttons */
.stButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{
  min-height:2.7rem!important;
  border-radius:11px!important;
  font-weight:800!important;
  letter-spacing:.005em!important;
  border:1px solid #0a416f!important;
  background:linear-gradient(135deg,var(--psb-blue),var(--psb-navy-2))!important;
  color:#fff!important;
  box-shadow:0 7px 18px rgba(13,79,143,.16)!important;
  transition:transform .15s ease,box-shadow .15s ease,filter .15s ease!important;
}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stLinkButton"] a:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 10px 24px rgba(13,79,143,.22)!important;
  filter:brightness(.97);
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--psb-green-2),var(--psb-green))!important;
  border-color:#087443!important;
  box-shadow:0 8px 20px rgba(8,116,67,.18)!important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{
  gap:.35rem!important;
  background:#edf2f7!important;
  border:1px solid var(--psb-line)!important;
  border-radius:13px!important;
  padding:.28rem!important;
}
.stTabs [data-baseweb="tab"]{
  height:2.55rem!important;
  border:0!important;
  border-radius:10px!important;
  background:transparent!important;
  color:#526779!important;
  font-weight:780!important;
  padding:0 .95rem!important;
}
.stTabs [aria-selected="true"]{
  background:#fff!important;
  color:var(--psb-navy-2)!important;
  box-shadow:0 2px 10px rgba(16,36,58,.09)!important;
}
.stTabs [data-baseweb="tab-highlight"]{display:none!important}

/* Expanders */
div[data-testid="stExpander"]{
  background:rgba(255,255,255,.92)!important;
  border:1px solid var(--psb-line)!important;
  border-radius:14px!important;
  box-shadow:0 3px 13px rgba(16,36,58,.04)!important;
  overflow:hidden!important;
}
div[data-testid="stExpander"] summary{font-weight:790!important;color:#29445c!important}

/* Data frames and tables */
[data-testid="stDataFrame"],.stTable{
  border:1px solid var(--psb-line)!important;
  border-radius:14px!important;
  overflow:hidden!important;
  box-shadow:0 3px 14px rgba(16,36,58,.045)!important;
  background:#fff!important;
}
[data-testid="stDataFrame"] *{font-size:.91rem}

/* Alerts */
[data-testid="stAlert"]{
  border-radius:13px!important;
  border-width:1px!important;
  box-shadow:none!important;
}

/* Existing app components */
.psb-card,.step{
  background:linear-gradient(180deg,#fff,#fcfdff)!important;
  border:1px solid var(--psb-line)!important;
  border-radius:17px!important;
  box-shadow:var(--psb-shadow-soft)!important;
}
.psb-section-title{color:var(--psb-navy-2)!important;font-weight:850!important}
.psb-hero{
  background:
    radial-gradient(circle at 88% 18%,rgba(255,255,255,.13),transparent 18rem),
    linear-gradient(125deg,#061a31 0%,#0a3b6a 60%,#087443 120%)!important;
  border-radius:22px!important;
  box-shadow:0 20px 46px rgba(6,26,49,.18)!important;
  border:1px solid rgba(255,255,255,.13)!important;
}
.psb-hero h1,.psb-hero h2,.psb-hero h3{color:#fff!important}
.pill{
  border-radius:999px!important;
  font-weight:760!important;
  box-shadow:none!important;
}

/* Certificate and status presentation */
.psb-cert-hero{
  border-radius:18px!important;
  border:1px solid var(--psb-line)!important;
  box-shadow:var(--psb-shadow)!important;
}
.psb-cert-field{
  border-color:var(--psb-line)!important;
  border-radius:12px!important;
  box-shadow:0 2px 8px rgba(16,36,58,.035);
}

/* Professional content hierarchy for generic markdown */
[data-testid="stMarkdownContainer"] blockquote{
  border-left:4px solid var(--psb-blue)!important;
  background:#f5f8fc!important;
  border-radius:0 10px 10px 0!important;
  padding:.7rem 1rem!important;
  color:#40566b!important;
}

/* Keep layout crisp on laptops/tablets/mobile */
@media(max-width:1100px){
  .block-container{padding:1rem 1.15rem 2.3rem!important}
}
@media(max-width:700px){
  .block-container{padding:.75rem .75rem 2rem!important}
  h1{font-size:1.62rem!important}
  h2{font-size:1.28rem!important}
  div[data-testid="stMetric"]{min-height:92px;padding:.85rem!important}
  .stTabs [data-baseweb="tab"]{padding:0 .65rem!important;font-size:.86rem!important}
}
</style>
""",
        unsafe_allow_html=True,
    )
