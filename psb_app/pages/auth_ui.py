from psb_app.common import (
    APP_SUBTITLE,
    APP_TITLE,
    AUTH_CALLBACK_URL,
    AUTH_MODE,
    ENABLE_DEMO_SEED,
    INITIAL_ADMIN_PASSWORD,
    LOGIN_BLOCK_MINUTES,
    LOGO_PATH,
    MAX_LOGIN_ATTEMPTS,
    ORG_ROLES,
    ROLE_NAVIGATION,
    STANDARDS,
    SUPABASE_AUTH_PROVIDER,
    SUPABASE_SERVICE_ROLE_KEY,
    actor_get,
    audit,
    backend_status_badges,
    clean,
    clear_auth_token,
    components,
    create_auth_token,
    datetime,
    db_all,
    db_count,
    db_insert,
    db_update,
    db_where,
    logo_data_uri,
    now,
    pd,
    phash,
    random,
    resolve_auth_token,
    restrict_user_frame,
    st,
    table,
    table_exists,
    timedelta,
    verify_password,
)
from core.design_system import page_kicker as _page_kicker, role_presentation as _role_presentation
from core.security import password_errors as _password_errors, valid_email as _valid_email
from core.system_write import system_write

def apply_style() -> None:
    st.markdown('\n    <style>\n    :root{--psb-navy:#071225;--psb-blue:#0b3b76;--psb-sky:#124f9e;--psb-card:#ffffff;--psb-line:#dbe3ef;--psb-text:#0f172a;--psb-muted:#64748b}\n    @media (prefers-color-scheme: dark) {\n        :root{--psb-card:#0b1220;--psb-line:rgba(255,255,255,0.06);--psb-text:#e6eef8;--psb-muted:#9aa7b8}\n        .stApp{background:radial-gradient(circle at top left,#041022 0,#07121a 34%,#052036 100%);color:var(--psb-text)}\n        section[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--psb-navy) 0%,var(--psb-blue) 72%,#08244b 100%);border-right:1px solid rgba(255,255,255,.03)}\n        .psb-card, .step, div[data-testid="stMetric"]{background:var(--psb-card);border:1px solid var(--psb-line)}\n        /* Panels, cards and form controls */\n        .login-panel{background:transparent}\n        .login-frame{background:linear-gradient(180deg,rgba(6,10,18,0.6),rgba(4,10,20,0.65));border-color:rgba(255,255,255,0.03);box-shadow:0 30px 80px rgba(0,0,0,0.6)}\n        .login-card{background:var(--psb-card);border:1px solid var(--psb-line);box-shadow:0 14px 40px rgba(2,6,12,0.6)}\n        .login-card h2{color:var(--psb-text)}\n        .login-card .muted{color:var(--psb-muted)}\n        .login-card label{color:var(--psb-text)!important}\n        input, textarea, select, .stTextInput>div>div input, .stTextArea>div>div textarea{background:var(--psb-card)!important;color:var(--psb-text)!important;border:1px solid var(--psb-line)!important}\n        input::placeholder, textarea::placeholder{color:var(--psb-muted)!important}\n        .stButton>button, .stDownloadButton>button{background:linear-gradient(135deg,var(--psb-blue),var(--psb-navy));border-color:var(--psb-navy);color:white}\n        .stExpander, div[data-testid="stExpander"]{background:transparent;border:1px solid var(--psb-line)}\n        div[data-testid="stDataFrame"], .stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab-list"]{background:var(--psb-card)!important;border:1px solid var(--psb-line)}\n        h1,h2,h3{color:var(--psb-text)}\n    }\n    /* Use solid white background in light mode to ensure consistent white page background */\n    .stApp{background:var(--psb-card);color:var(--psb-text)}\n    /* Inputs, controls and buttons use card/bg vars so they adapt to theme */\n    input, textarea, select, button, .stButton > button, .stTextInput>div>div, .stTextArea>div>div{background:var(--psb-card)!important;color:var(--psb-text)!important;border:1px solid var(--psb-line)!important}\n    .stButton>button{box-shadow:none;border-radius:10px;padding:8px 12px}\n    a, a:hover{color:var(--psb-sky)}\n    .block-container{padding-top:1rem;padding-bottom:2.5rem;max-width:1480px}\n    #MainMenu, footer, header[data-testid="stHeader"]{visibility:hidden}\n    button[title="Toggle sidebar"], button[aria-label="Toggle sidebar"], button[aria-label="Collapse sidebar"], button[aria-label="Expand sidebar"], div[role="button"][aria-label*="sidebar"]{display:none!important}\n    /* Permanent PSB navigation: never collapse, slide, or create horizontal overflow. */\n    html, body, .stApp, [data-testid="stAppViewContainer"]{overflow-x:hidden!important}\n    section[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--psb-navy) 0%,var(--psb-blue) 72%,#08244b 100%);border-right:1px solid rgba(255,255,255,.10);visibility:visible!important;min-width:290px!important;max-width:290px!important;width:290px!important;transform:none!important;overflow-x:hidden!important;overflow-y:auto!important}\n    section[data-testid="stSidebar"] *{color:#f8fafc}\n    section[data-testid="stSidebar"] [data-testid="stSidebarContent"], section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{overflow-x:hidden!important}\n    section[data-testid="stSidebar"] [data-testid="stRadio"] label{font-weight:800;letter-spacing:.01em;white-space:normal!important;word-break:break-word!important}\n    section[data-testid="stSidebar"] div[role="radiogroup"] label{border-radius:10px;padding:.38rem .55rem;margin:.08rem 0;width:100%;box-sizing:border-box}\n    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(255,255,255,.11)}\n    section[data-testid="stSidebar"] .psb-nav-section{font-size:.68rem;font-weight:950;letter-spacing:.12em;text-transform:uppercase;color:#93c5fd!important;margin:.9rem .35rem .25rem;padding-top:.45rem;border-top:1px solid rgba(255,255,255,.12)}\n    section[data-testid="stSidebar"] .psb-user-card{padding:.65rem .75rem;border:1px solid rgba(255,255,255,.14);border-radius:14px;background:rgba(255,255,255,.07);margin:.3rem 0 .6rem}\n    section[data-testid="stSidebar"] .psb-signout{position:sticky;bottom:0;background:var(--psb-navy);padding:.4rem 0;z-index:3} section[data-testid="stSidebar"] .psb-signout button{width:100%!important;background:#b91c1c!important;border-color:#b91c1c!important;color:white!important;font-weight:900!important}\n    @media (max-width: 900px){button[title="Toggle sidebar"],button[aria-label="Toggle sidebar"],button[aria-label="Collapse sidebar"],button[aria-label="Expand sidebar"]{display:block!important} section[data-testid="stSidebar"]{min-width:260px!important;max-width:82vw!important;width:82vw!important}}\n    div[data-testid="stMetric"]{background:var(--psb-card);border:1px solid var(--psb-line);border-radius:20px;padding:16px;box-shadow:0 14px 35px rgba(15,23,42,.08)}\n    div[data-testid="stMetric"] label{color:var(--psb-muted)!important;font-weight:700}\n    .psb-hero{background:linear-gradient(135deg,var(--psb-navy),var(--psb-blue) 62%,var(--psb-sky));color:white;padding:1.55rem 1.85rem;border-radius:30px;margin-bottom:1.3rem;box-shadow:0 26px 75px rgba(15,23,42,.25);display:flex;gap:20px;align-items:center;border:1px solid rgba(255,255,255,.17)}\n    .psb-hero img{width:96px;height:96px;border-radius:50%;object-fit:contain;background:white;padding:6px;box-shadow:0 14px 34px rgba(0,0,0,.25)}\n    .psb-hero h1{margin:0;font-size:2.18rem;letter-spacing:-.035em;font-weight:900}\n    .psb-hero p{color:#dbeafe;margin:.42rem 0 .25rem;font-size:1.03rem}\n    .pill{display:inline-flex;padding:6px 12px;border-radius:999px;background:#e8eef7;color:#0f172a;font-size:12px;font-weight:800;margin:4px 5px 4px 0;border:1px solid #d7e0ec;white-space:nowrap}\n    .psb-hero .pill{background:rgba(255,255,255,.14);color:white;border:1px solid rgba(255,255,255,.24)}\n    .step{border-left:5px solid var(--psb-blue);background:white;border-radius:18px;padding:.9rem 1rem;margin:.48rem 0;box-shadow:0 12px 32px rgba(15,23,42,.07)}\n    .psb-card{background:white;border:1px solid var(--psb-line);border-radius:22px;padding:1rem 1.1rem;margin:.65rem 0;box-shadow:0 12px 32px rgba(15,23,42,.07)}\n    .psb-section-title{font-size:1.02rem;font-weight:900;color:var(--psb-blue);margin:.25rem 0 .65rem}\n    .login-shell{min-height:calc(100vh - 3.5rem);display:flex;align-items:center;justify-content:center;padding:1.5rem 0 2.8rem}\n    .login-frame{width:min(1180px,96vw);display:grid;grid-template-columns:1.08fr .92fr;gap:0;background:var(--psb-card);border:1px solid rgba(219,227,239,.95);border-radius:36px;overflow:hidden;box-shadow:0 38px 110px rgba(7,18,37,.22)}\n    .login-brand{position:relative;padding:3rem 2.8rem;color:white;background:radial-gradient(circle at 18% 18%,rgba(245,180,51,.30),transparent 25%),linear-gradient(135deg,#06162f 0%,#082b59 52%,#0b4b91 100%);min-height:650px;display:flex;flex-direction:column;justify-content:space-between}\n    .login-brand:before{content:"";position:absolute;inset:0;background:linear-gradient(120deg,rgba(255,255,255,.08) 0 1px,transparent 1px 18px),radial-gradient(circle at 86% 14%,rgba(255,255,255,.20),transparent 20%);opacity:.7;pointer-events:none}\n    .brand-content,.brand-footer{position:relative;z-index:1}\n    .login-logo-row{display:flex;align-items:center;gap:16px;margin-bottom:2rem}\n    .login-logo-row img{width:86px;height:86px;border-radius:22px;background:white;padding:8px;object-fit:contain;box-shadow:0 18px 45px rgba(0,0,0,.28)}\n    .login-kicker{font-size:.78rem;font-weight:900;text-transform:uppercase;letter-spacing:.18em;color:#f5b433;margin-bottom:.4rem}\n    .login-brand h1{margin:0;font-size:2.65rem;line-height:1.04;letter-spacing:-.055em;color:white;font-weight:950}\n    .login-brand p{font-size:1.03rem;line-height:1.65;color:#dbeafe;max-width:610px;margin:1.05rem 0}\n    .login-badges{display:flex;gap:9px;flex-wrap:wrap;margin:1.25rem 0 0}\n    .login-badge{display:inline-flex;align-items:center;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.12);border-radius:999px;padding:7px 11px;color:#fff;font-size:.78rem;font-weight:850}\n    .login-feature-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:1.5rem}\n    .login-feature{border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.10);border-radius:18px;padding:13px 14px;color:#eaf2ff}\n    .login-feature b{display:block;color:white;font-size:.92rem;margin-bottom:4px}.login-feature span{font-size:.78rem;color:#cfe1ff}\n    .brand-footer{border-top:1px solid rgba(255,255,255,.18);padding-top:1rem;color:#cbd5e1;font-size:.82rem;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}\n    .login-panel{padding:3rem 2.6rem;background:var(--psb-card);display:flex;flex-direction:column;justify-content:center}\n    .login-card{background:white;border:1px solid #dce6f2;border-radius:30px;padding:2rem;box-shadow:0 18px 55px rgba(15,23,42,.10)}\n    .login-card h2{font-size:1.75rem;margin:0 0 .35rem;color:#071225;font-weight:950}.login-card .muted{color:#64748b;margin:0 0 1.25rem;line-height:1.55}\n    .login-mini{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:1.1rem 0 0}.login-mini div{background:#f1f5f9;border:1px solid #dbe3ef;border-radius:16px;padding:10px;text-align:center}.login-mini b{display:block;color:#0b3b76;font-size:1rem}.login-mini span{font-size:.70rem;color:#64748b;font-weight:800;text-transform:uppercase;letter-spacing:.05em}\n    .login-help{margin-top:1rem;padding:12px 14px;border-radius:18px;background:#fff8eb;border:1px solid #f3d79a;color:#6b4b0b;font-size:.86rem;line-height:1.5}\n    .login-card div[data-testid="stForm"]{border:0;padding:0}.login-card label{font-weight:850;color:#0f172a!important}.login-card input{border-radius:14px!important}\n    .login-card .stButton>button{width:100%;height:3rem;border-radius:16px;background:linear-gradient(135deg,#071225,#0b3b76);border:0;color:white;font-weight:950;letter-spacing:.02em;box-shadow:0 14px 32px rgba(11,59,118,.24)}\n    .login-card .stButton>button:hover{background:linear-gradient(135deg,#04101f,#08315f);transform:translateY(-1px)}\n    .login-demo{margin-top:1rem}.login-demo div[data-testid="stExpander"]{box-shadow:none;border-radius:18px;background:#f8fafc}\n    @media(max-width:920px){.login-frame{grid-template-columns:1fr}.login-brand{min-height:auto;padding:2.1rem}.login-panel{padding:1.4rem}.login-brand h1{font-size:2rem}.login-feature-grid{grid-template-columns:1fr}.login-mini{grid-template-columns:1fr}}\n    .stButton>button,.stDownloadButton>button{border-radius:13px;border:1px solid var(--psb-blue);background:var(--psb-blue);color:white;font-weight:800;box-shadow:0 8px 18px rgba(11,59,118,.16)}\n    .stButton>button:hover,.stDownloadButton>button:hover{background:var(--psb-navy);color:white;border-color:var(--psb-navy)}\n    div[data-testid="stDataFrame"]{border-radius:18px;overflow:hidden;border:1px solid var(--psb-line);box-shadow:0 10px 26px rgba(15,23,42,.05)}\n    div[data-testid="stExpander"]{border-radius:18px;border:1px solid var(--psb-line);background:white;box-shadow:0 8px 22px rgba(15,23,42,.04)}\n    .stTabs [data-baseweb="tab-list"]{gap:8px}\n    .stTabs [data-baseweb="tab"]{border-radius:999px;background:#e8eef7;padding:.45rem 1rem;font-weight:800}\n    h1,h2,h3{letter-spacing:-.025em;color:#0f172a}\n    /* PSB Design System — shared across every role/page */\n    :root{--psb-radius-sm:10px;--psb-radius-md:14px;--psb-radius-lg:22px;--psb-space-1:4px;--psb-space-2:8px;--psb-space-3:12px;--psb-space-4:16px;--psb-space-5:24px;--psb-shadow-sm:0 6px 18px rgba(15,23,42,.05);--psb-shadow-md:0 12px 32px rgba(15,23,42,.08)}\n    .psb-page-kicker{display:flex;align-items:center;gap:8px;margin:-.35rem 0 1rem;color:#64748b;font-size:.78rem;font-weight:850;letter-spacing:.03em;flex-wrap:wrap}\n    .psb-role-dot{width:9px;height:9px;border-radius:50%;display:inline-block;box-shadow:0 0 0 4px rgba(11,59,118,.08)}\n    .psb-kicker-sep{color:#cbd5e1}.psb-role-description{font-weight:700;color:#94a3b8}\n    .psb-empty{padding:1.25rem 1rem;border:1px dashed var(--psb-line);border-radius:var(--psb-radius-lg);background:linear-gradient(180deg,rgba(248,250,252,.7),rgba(255,255,255,.95));text-align:center;color:var(--psb-muted);font-weight:750}\n    .psb-status{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:999px;font-size:.72rem;font-weight:900;border:1px solid rgba(100,116,139,.18);background:#f8fafc;color:#334155}\n    .psb-status.success{background:#ecfdf5;color:#047857;border-color:#a7f3d0}.psb-status.warning{background:#fffbeb;color:#b45309;border-color:#fde68a}.psb-status.danger{background:#fef2f2;color:#b91c1c;border-color:#fecaca}.psb-status.info{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.psb-status.neutral{background:#f8fafc;color:#475569;border-color:#e2e8f0}\n    .stButton>button,.stDownloadButton>button{min-height:2.6rem;border-radius:var(--psb-radius-md);font-weight:850;transition:transform .12s ease,box-shadow .12s ease,background .12s ease}\n    .stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(11,59,118,.16)}\n    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stTextArea"] textarea{border-radius:var(--psb-radius-md)!important}\n    div[data-baseweb="select"]>div{border-radius:var(--psb-radius-md)!important;min-height:2.65rem}\n    div[data-testid="stForm"]{border:1px solid var(--psb-line);border-radius:var(--psb-radius-lg);padding:1rem 1.1rem;background:var(--psb-card);box-shadow:var(--psb-shadow-sm)}\n    div[data-testid="stDataFrame"]{border-radius:var(--psb-radius-lg);overflow:hidden;box-shadow:var(--psb-shadow-sm)}\n    div[data-testid="stAlert"]{border-radius:var(--psb-radius-md)!important}\n    div[data-testid="stExpander"]{border-radius:var(--psb-radius-lg)!important}\n    .stTabs [data-baseweb="tab"]{transition:background .12s ease,transform .12s ease}.stTabs [data-baseweb="tab"]:hover{transform:translateY(-1px)}\n\n    /* PSB State-of-the-Art Enterprise Theme — brand-led, restrained, accessible */\n    :root{\n      --psb-ink:#010819;--psb-navy:#061b36;--psb-navy-2:#0a2f5d;--psb-blue:#0d477f;--psb-green:#095b25;\n      --psb-green-2:#0b7432;--psb-green-soft:#eaf6ee;--psb-surface:#ffffff;--psb-bg:#f4f7f6;\n      --psb-line:#d9e2e0;--psb-text:#101828;--psb-muted:#667085;--psb-focus:#1f7a44;\n      --psb-danger:#b42318;--psb-warning:#b54708;--psb-info:#175cd3;\n      --psb-radius-sm:8px;--psb-radius-md:12px;--psb-radius-lg:16px;--psb-radius-xl:22px;\n      --psb-shadow-sm:0 1px 2px rgba(1,8,25,.04),0 4px 14px rgba(1,8,25,.05);\n      --psb-shadow-md:0 12px 32px rgba(1,8,25,.08);\n    }\n    html{scroll-behavior:smooth} body,.stApp{background:var(--psb-bg)!important;color:var(--psb-text)}\n    .block-container{max-width:1460px;padding-top:1.1rem;padding-bottom:3.5rem}\n    h1,h2,h3{color:var(--psb-ink);letter-spacing:-.02em} h1{font-weight:800} h2,h3{font-weight:750}\n    p,li,.stCaption{line-height:1.55}\n\n    /* accessible keyboard focus */\n    button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible,[role=tab]:focus-visible,[role=option]:focus-visible{\n      outline:3px solid rgba(31,122,68,.32)!important;outline-offset:2px!important;box-shadow:0 0 0 1px var(--psb-focus)!important\n    }\n    @media (prefers-reduced-motion: reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}\n\n    /* Sidebar: crest-led institutional navigation, static desktop / drawer mobile */\n    section[data-testid=\"stSidebar\"]{background:linear-gradient(180deg,#010819 0%,#061b36 64%,#083621 140%)!important;border-right:1px solid rgba(255,255,255,.08);min-width:282px!important;max-width:282px!important;width:282px!important}\n    section[data-testid=\"stSidebar\"]>div{display:flex;flex-direction:column;min-height:100vh}\n    section[data-testid=\"stSidebar\"] img{filter:drop-shadow(0 10px 22px rgba(0,0,0,.28));margin:.2rem auto .25rem}\n    .psb-brand-lockup{text-align:center;margin:-.1rem .25rem .75rem;color:white}.psb-brand-lockup b{display:block;font-size:.88rem;letter-spacing:.02em}.psb-brand-lockup span{display:block;color:#a9c8b2;font-size:.69rem;margin-top:.18rem;letter-spacing:.06em;text-transform:uppercase;font-weight:700}\n    section[data-testid=\"stSidebar\"] .psb-user-card{padding:.7rem .8rem;border:1px solid rgba(255,255,255,.12);border-radius:12px;background:rgba(255,255,255,.055);margin:.25rem 0 .65rem;box-shadow:none}\n    section[data-testid=\"stSidebar\"] .psb-user-card span{color:#b7d7c0!important;font-weight:700} section[data-testid=\"stSidebar\"] .psb-user-card small{color:#b8c7d9!important}\n    section[data-testid=\"stSidebar\"] .psb-nav-section{font-size:.66rem;font-weight:800;letter-spacing:.105em;color:#7fb38e!important;margin:.85rem .25rem .25rem;padding-top:.48rem;border-top:1px solid rgba(255,255,255,.09)}\n    section[data-testid=\"stSidebar\"] .stButton>button{min-height:2.38rem;text-align:left!important;justify-content:flex-start!important;background:transparent!important;border:1px solid transparent!important;color:#eaf1f7!important;border-radius:9px!important;box-shadow:none!important;padding:.48rem .68rem!important;font-weight:650!important;transition:background .16s ease,border-color .16s ease,transform .16s ease}\n    section[data-testid=\"stSidebar\"] .stButton>button:hover{background:rgba(255,255,255,.075)!important;border-color:rgba(255,255,255,.08)!important;transform:none!important}\n    section[data-testid=\"stSidebar\"] .stButton>button:active{transform:translateY(1px)!important}\n    .psb-nav-active{position:relative;margin:.12rem 0;padding:.59rem .7rem .59rem .88rem;border-radius:9px;background:linear-gradient(90deg,rgba(9,91,37,.42),rgba(9,91,37,.16));border:1px solid rgba(106,190,130,.22);color:#fff;font-weight:800;font-size:.88rem}\n    .psb-nav-active:before{content:\"\";position:absolute;left:.34rem;top:50%;transform:translateY(-50%);width:4px;height:18px;border-radius:3px;background:#56b36f}\n    .psb-sidebar-spacer{min-height:1rem;flex:1}.psb-signout{position:sticky!important;bottom:0!important;background:linear-gradient(180deg,rgba(1,8,25,0),#010819 28%)!important;padding:.75rem 0 .45rem!important;z-index:5!important}\n    section[data-testid=\"stSidebar\"] .psb-signout .stButton>button{justify-content:center!important;background:rgba(255,255,255,.06)!important;border:1px solid rgba(255,255,255,.18)!important;color:#fff!important}.psb-signout .stButton>button:hover{background:rgba(180,35,24,.20)!important;border-color:rgba(255,150,145,.35)!important}\n\n    /* Header and context */\n    .psb-hero{background:linear-gradient(118deg,#010819 0%,#0a2f5d 60%,#095b25 122%)!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:18px!important;padding:1.15rem 1.35rem!important;margin-bottom:1.1rem!important;box-shadow:var(--psb-shadow-md)!important;min-height:126px}\n    .psb-hero img{width:84px!important;height:104px!important;border-radius:12px!important;padding:2px!important;background:rgba(255,255,255,.97)!important;object-fit:contain!important;box-shadow:0 10px 25px rgba(0,0,0,.20)!important}\n    .psb-hero h1{font-size:1.75rem!important;letter-spacing:-.025em!important}.psb-hero p{font-size:.93rem!important;margin:.22rem 0 .35rem!important;color:#dbe8ef!important}\n    .pill{border-radius:6px!important;padding:4px 8px!important;font-size:.69rem!important;box-shadow:none!important}.psb-hero .pill{background:rgba(255,255,255,.08)!important;border-color:rgba(255,255,255,.15)!important}\n    .psb-page-kicker{color:#d7e4ea!important}.psb-role-dot{background:#53ad6b!important;box-shadow:0 0 0 4px rgba(83,173,107,.15)!important}\n\n    /* Surfaces and metrics — less generic card noise */\n    .psb-card,.step,div[data-testid=\"stMetric\"],div[data-testid=\"stForm\"],div[data-testid=\"stExpander\"]{background:var(--psb-surface)!important;border:1px solid var(--psb-line)!important;box-shadow:var(--psb-shadow-sm)!important}\n    .psb-card{border-radius:var(--psb-radius-lg)!important}.step{border-radius:var(--psb-radius-md)!important;border-left:4px solid var(--psb-green)!important}\n    div[data-testid=\"stMetric\"]{border-radius:14px!important;padding:14px 15px!important;position:relative;overflow:hidden}\n    div[data-testid=\"stMetric\"]:before{content:\"\";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--psb-green)}\n    div[data-testid=\"stMetric\"] label{color:var(--psb-muted)!important;font-weight:700!important} div[data-testid=\"stMetricValue\"]{color:var(--psb-ink)!important;font-weight:800!important}\n\n    /* Controls and tables */\n    .stButton>button,.stDownloadButton>button{min-height:2.55rem;border-radius:10px!important;background:#0a2f5d!important;border:1px solid #0a2f5d!important;color:white!important;font-weight:750!important;box-shadow:none!important;transition:background .16s ease,border-color .16s ease,transform .12s ease!important}\n    .stButton>button:hover,.stDownloadButton>button:hover{background:#061b36!important;border-color:#061b36!important;transform:translateY(-1px)!important;box-shadow:0 8px 18px rgba(1,8,25,.12)!important}\n    .stButton>button:active,.stDownloadButton>button:active{transform:translateY(1px)!important}\n    div[data-testid=\"stForm\"]{border-radius:14px!important;padding:1rem 1.05rem!important}\n    input,textarea,select,.stTextInput>div>div input,.stTextArea>div>div textarea{border-radius:10px!important;border-color:#cdd8d5!important;background:#fff!important}\n    div[data-baseweb=\"select\"]>div{border-radius:10px!important;border-color:#cdd8d5!important;background:#fff!important}\n    div[data-testid=\"stDataFrame\"]{border:1px solid var(--psb-line)!important;border-radius:12px!important;box-shadow:none!important;background:#fff!important}\n    div[data-testid=\"stExpander\"]{border-radius:12px!important;box-shadow:none!important}\n    .stTabs [data-baseweb=\"tab-list\"]{gap:2px!important;background:#edf2f0!important;border:1px solid #dbe5e1!important;border-radius:10px!important;padding:3px!important;overflow-x:auto!important}\n    .stTabs [data-baseweb=\"tab\"]{border:0!important;border-radius:7px!important;background:transparent!important;padding:.42rem .72rem!important;font-weight:700!important;color:#475467!important;white-space:nowrap!important}\n    .stTabs [aria-selected=\"true\"]{background:#fff!important;color:#061b36!important;box-shadow:0 1px 3px rgba(1,8,25,.08)!important}\n    div[data-testid=\"stAlert\"]{border-radius:10px!important}\n    .psb-empty{border-radius:12px!important;background:#f8faf9!important;border-color:#cad8d2!important;padding:1.2rem!important}\n    .psb-status{border-radius:6px!important}.psb-status.success{background:#eaf6ee!important;color:#075b27!important;border-color:#b9dfc4!important}.psb-status.warning{background:#fff7ed!important;color:#9a3412!important}.psb-status.danger{background:#fef2f2!important;color:#b42318!important}.psb-status.info{background:#eff6ff!important;color:#175cd3!important}\n\n    /* Login */\n    .login-shell{background:radial-gradient(circle at 10% 12%,rgba(9,91,37,.10),transparent 26%),linear-gradient(180deg,#f7faf8,#eef4f1)!important}\n    .login-frame{border-radius:22px!important;border-color:#d7e1dd!important;box-shadow:0 24px 70px rgba(1,8,25,.14)!important}\n    .login-brand{background:linear-gradient(145deg,#010819 0%,#061b36 64%,#095b25 155%)!important;padding:2.5rem!important}\n    .login-logo-row img{width:92px!important;height:118px!important;border-radius:12px!important;padding:3px!important}\n    .login-kicker{color:#78c18d!important;letter-spacing:.11em!important}.login-brand h1{font-size:2.25rem!important;letter-spacing:-.035em!important}.login-brand p{color:#dbe5eb!important}\n    .login-badge{border-radius:6px!important;background:rgba(255,255,255,.075)!important}.login-feature{border-radius:12px!important;background:rgba(255,255,255,.055)!important}.login-card{border-radius:18px!important}.login-card .stButton>button{border-radius:10px!important;background:#095b25!important;border-color:#095b25!important}.login-card .stButton>button:hover{background:#07491e!important;border-color:#07491e!important}\n\n    /* Responsive behavior: static on desktop; controlled drawer on mobile */\n    @media (max-width:900px){\n      .block-container{padding-left:1rem!important;padding-right:1rem!important}.psb-hero{align-items:flex-start!important}.psb-hero img{width:66px!important;height:82px!important}.psb-hero h1{font-size:1.4rem!important}\n      section[data-testid=\"stSidebar\"]{min-width:260px!important;max-width:86vw!important;width:86vw!important}\n      button[title=\"Toggle sidebar\"],button[aria-label=\"Toggle sidebar\"],button[aria-label=\"Collapse sidebar\"],button[aria-label=\"Expand sidebar\"]{display:block!important}\n    }\n        </style>\n    ', unsafe_allow_html=True)

def header(actor: dict | None=None, page: str='Dashboard', view_context: str | None=None) -> None:
    logo = f"<img src='{logo_data_uri()}' />" if LOGO_PATH.exists() else ''
    st.markdown(f"""\n    <div class='psb-hero'>{logo}<div style='width:100%'>\n    <h1>{APP_TITLE}</h1><p>{APP_SUBTITLE}</p>\n    </div></div>\n    """, unsafe_allow_html=True)

def metrics(items):
    cols = st.columns(4)
    for i, (label, value) in enumerate(items):
        cols[i % 4].metric(label, value)

def _setting_value(key: str, default: str='') -> str:
    try:
        row = db_where('system_settings', 'setting_key = :key', (('key', key),))
        return str(row.iloc[-1].get('setting_value') or default) if not row.empty else default
    except Exception:
        return default

def _persistent_login_state(login_key: str):
    try:
        row = db_where('login_security_state', 'login_key = :key', (('key', login_key),))
        return row.iloc[-1].to_dict() if not row.empty else {}
    except Exception:
        return {}

def _record_login_failure(login_key: str):
    if not login_key: return
    state=_persistent_login_state(login_key); failures=int(state.get('failure_count') or 0)+1
    blocked=''
    if failures >= MAX_LOGIN_ATTEMPTS:
        blocked=(datetime.utcnow()+timedelta(minutes=LOGIN_BLOCK_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
    row={'login_key':login_key,'failure_count':failures,'blocked_until':blocked,'last_failure_on':now(),'updated_on':now()}
    with system_write('login_security_failure'):
        if state: db_update('login_security_state','login_key',login_key,row)
        else: db_insert('login_security_state',row)

def _clear_login_failures(login_key: str):
    if login_key and _persistent_login_state(login_key):
        with system_write('login_security_clear'):
            db_update('login_security_state','login_key',login_key,{'failure_count':0,'blocked_until':'','updated_on':now()})

def _is_persistently_blocked(login_key: str) -> tuple[bool,int]:
    state=_persistent_login_state(login_key); value=str(state.get('blocked_until') or '')
    if not value: return False,0
    try:
        until=datetime.strptime(value[:19],'%Y-%m-%d %H:%M:%S'); delta=(until-datetime.utcnow()).total_seconds()
        return (delta>0, max(1,int(delta/60)+1) if delta>0 else 0)
    except Exception: return False,0

def _password_expired(user: dict) -> bool:
    try: days=int(_setting_value('password_expiry_days','90') or 0)
    except Exception: days=90
    if days <= 0: return False
    changed=str(user.get('password_changed_on') or user.get('created_on') or '')[:10]
    if not changed: return True
    try: return (datetime.utcnow().date()-datetime.strptime(changed,'%Y-%m-%d').date()).days >= days
    except Exception: return True

def _totp_code(secret: str, timestamp=None, step: int=30) -> str:
    import base64, hmac, struct, hashlib as _hashlib, time as _time
    key=base64.b32decode(secret.upper() + '='*((8-len(secret)%8)%8)); counter=int((timestamp or _time.time())//step)
    digest=hmac.new(key,struct.pack('>Q',counter),_hashlib.sha1).digest(); off=digest[-1]&15
    val=(struct.unpack('>I',digest[off:off+4])[0]&0x7fffffff)%1000000
    return f'{val:06d}'

def _verify_totp(secret: str, code: str) -> bool:
    import time as _time, secrets as _secrets
    c=str(code or '').strip()
    return len(c)==6 and any(_secrets.compare_digest(_totp_code(secret,_time.time()+offset),c) for offset in (-30,0,30))

def _mfa_required() -> bool:
    return _setting_value('require_2fa','No').strip().lower() in {'yes','true','1','on'}

def _mfa_cipher():
    import os, base64, hashlib
    raw=os.getenv('PSB_MFA_ENCRYPTION_KEY','').encode('utf-8')
    if not raw:
        return None
    try:
        from cryptography.fernet import Fernet
        key=base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
        return Fernet(key)
    except Exception:
        return None

def _encrypt_mfa_secret(secret: str) -> str:
    cipher=_mfa_cipher()
    if cipher is None: raise RuntimeError('PSB_MFA_ENCRYPTION_KEY and cryptography are required when local MFA is enabled.')
    return 'enc:'+cipher.encrypt(secret.encode('utf-8')).decode('utf-8')

def _decrypt_mfa_secret(value: str) -> str:
    value=str(value or '')
    if not value.startswith('enc:'): return value
    cipher=_mfa_cipher()
    if cipher is None: raise RuntimeError('MFA encryption key is unavailable.')
    return cipher.decrypt(value[4:].encode('utf-8')).decode('utf-8')

def _mfa_page(user: dict) -> None:
    import base64, os
    st.title('Two-Factor Authentication')
    uidv=str(user.get('user_id') or ''); stored=str(user.get('mfa_secret') or '')
    try: secret=_decrypt_mfa_secret(stored) if stored else ''
    except Exception as exc: st.error(str(exc)); return
    if not secret:
        secret=base64.b32encode(os.urandom(20)).decode().rstrip('=')
        try: encrypted=_encrypt_mfa_secret(secret)
        except Exception as exc: st.error(str(exc)); return
        db_update('users','user_id',uidv,{'mfa_secret':encrypted,'mfa_enabled':'Pending'})
        user['mfa_secret']=encrypted
    st.caption('Enter this secret in an authenticator application. MFA is required before portal access.')
    st.code(secret)
    code=st.text_input('6-digit authenticator code',max_chars=6)
    if st.button('Verify & Continue',type='primary'):
        if _verify_totp(secret,code):
            db_update('users','user_id',uidv,{'mfa_enabled':'Yes','mfa_verified_on':now()})
            st.session_state['mfa_verified']=True; st.rerun()
        st.error('Invalid or expired authentication code.')

def login_page() -> None:
    if 'captcha_question' not in st.session_state:
        a, b = (random.randint(2, 12), random.randint(2, 12))
        st.session_state['captcha_question'] = f'{a} + {b}'
        st.session_state['captcha_answer'] = str(a + b)
    logo_html = f"<img src='{logo_data_uri()}' alt='PSB Logo' />" if LOGO_PATH.exists() else ''
    st.markdown(
        "<style>.login-logo-row > div{font-size:2.65rem!important;line-height:1.08!important;font-weight:950!important}</style>",
        unsafe_allow_html=True,
    )
    st.markdown(f"\n    <div class='login-shell'>\n      <div class='login-frame'>\n        <section class='login-brand'>\n          <div class='brand-content'>\n            <div class='login-logo-row'>\n              {logo_html}\n              <div style='font-weight:950;color:#fff;font-size:1.55rem;line-height:1.2'>Pakistan Shipping Bureau</div>\n            </div>\n            <h1>HRD&amp;M Portal</h1>\n          </div>\n        </section>\n        <section class='login-panel'>\n          <div class='login-card'>\n            <h2>Sign In</h2>\n            <p class='muted'>Access your account</p>\n    ", unsafe_allow_html=True)
    login_attempts = st.session_state.get('login_attempts', 0)
    blocked_until = st.session_state.get('login_blocked_until')
    now_ts = datetime.utcnow()
    if blocked_until and isinstance(blocked_until, datetime) and (now_ts < blocked_until):
        remaining = int((blocked_until - now_ts).total_seconds() / 60) + 1
        st.error(f'Too many failed login attempts. Please try again in {remaining} minute(s).')
    with st.form('login', clear_on_submit=False):
        login = st.text_input('Login ID or Email', placeholder='Enter your login ID or official email')
        password = st.text_input('Password', type='password', placeholder='Enter your password')
        captcha = st.text_input(f"Security Verification: {st.session_state['captcha_question']} = ?", placeholder='Answer')
        submit = st.form_submit_button('Sign in to PSB Portal')
    if AUTH_MODE.lower() == 'supabase':
        with st.expander('Forgot password?', expanded=False):
            reset_email = st.text_input('Official email', key='supabase_reset_email')
            if st.button('Send password reset link', key='supabase_reset_btn'):
                if not _valid_email(reset_email):
                    st.error('Enter a valid official email address.')
                else:
                    result = SUPABASE_AUTH_PROVIDER.request_password_reset(reset_email, AUTH_CALLBACK_URL or None)
                    st.success('If the account exists, a password reset email has been requested.') if result.ok else st.error(result.error)
    if submit:
        if blocked_until and isinstance(blocked_until, datetime) and (now_ts < blocked_until):
            st.error('You are temporarily blocked due to too many failed login attempts.')
            return
        if captcha.strip() != st.session_state.get('captcha_answer', ''):
            st.error('Security verification failed. Please try again.')
            return
        login_value = clean(login).lower().strip()
        password_value = clean(password)
        blocked_persistently, blocked_minutes = _is_persistently_blocked(login_value)
        if blocked_persistently:
            st.error(f'This login is temporarily blocked after repeated failures. Try again in {blocked_minutes} minute(s).')
            return
        if not login_value or not password_value:
            st.error('Login ID/email and password are required.')
            return
        authenticated_row = None
        needs_rehash = False
        if AUTH_MODE.lower() == 'supabase':
            auth_email = login_value if '@' in login_value else ''
            if not auth_email:
                lookup = db_where('users', "lower(login_id) = :login_key and status = 'Active'", (('login_key', login_value),))
                auth_email = str(lookup.iloc[0].get('email', '')) if not lookup.empty else ''
            result = SUPABASE_AUTH_PROVIDER.sign_in(auth_email, password_value) if auth_email else None
            if result and result.ok:
                match = db_where('users', "auth_user_id = :auth_id and status = 'Active'", (('auth_id', result.identity_id),))
                if match.empty:
                    match = db_where('users', "lower(email) = :email and status = 'Active'", (('email', result.email.lower()),))
                    if not match.empty:
                        db_update('users', 'user_id', str(match.iloc[0]['user_id']), {'auth_user_id': result.identity_id})
                if not match.empty:
                    authenticated_row = match.iloc[0]
            elif result:
                authenticated_row = None
        else:
            match = db_where('users', "(lower(login_id) = :login_key or lower(email) = :login_key) and status = 'Active'", (('login_key', login_value),))
            if not match.empty:
                for _, candidate in match.iterrows():
                    ok, candidate_needs_rehash = verify_password(str(candidate.get('password_hash', '')), password_value)
                    if ok:
                        authenticated_row = candidate
                        needs_rehash = candidate_needs_rehash
                        break
        if authenticated_row is None:
            _record_login_failure(login_value)
            st.session_state['login_attempts'] = login_attempts + 1
            if st.session_state['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
                st.session_state['login_blocked_until'] = now_ts + timedelta(minutes=LOGIN_BLOCK_MINUTES)
                st.error(f'Too many failed attempts. Try again after {LOGIN_BLOCK_MINUTES} minute(s).')
            else:
                remaining = MAX_LOGIN_ATTEMPTS - st.session_state['login_attempts']
                st.error(f'Invalid login ID/email or password. {remaining} attempt(s) remaining.')
        else:
            user = authenticated_row.to_dict()
            if needs_rehash:
                original_force = str(user.get('force_password_change', 'No')) == 'Yes'
                db_update('users', 'user_id', user['user_id'], {'password_hash': phash(password_value)})
                user['password_hash'] = ''
                user['force_password_change'] = 'Yes' if original_force else 'No'
            db_update('users', 'user_id', user['user_id'], {'last_login': now()})
            user['last_login'] = now()
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.session_state['must_change_password'] = str(user.get('force_password_change', 'No')) == 'Yes'
            st.session_state['psb_current_page'] = 'Dashboard'
            st.session_state['login_attempts'] = 0
            st.session_state['login_blocked_until'] = None
            token = create_auth_token(user['user_id'])
            st.session_state['auth_token'] = token
            _clear_login_failures(login_value)
            if _password_expired(user):
                st.session_state['must_change_password'] = True
            st.session_state['mfa_verified'] = not _mfa_required()
            audit('User Login', f"{user['name']} logged in", actor=user)
            st.rerun()
    st.markdown("\n          </div>\n        </section>\n      </div>\n    </div>\n    ", unsafe_allow_html=True)

def require_login() -> dict:
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user' not in st.session_state:
        st.session_state['user'] = {}
    if not st.session_state['logged_in']:
        login_page()
        st.stop()
    if st.session_state.get('must_change_password'):
        password_change_page(st.session_state['user'])
        st.stop()
    if _mfa_required() and not st.session_state.get('mfa_verified', False):
        _mfa_page(st.session_state['user'])
        st.stop()
    return st.session_state['user']

def password_change_page(actor: dict) -> None:
    st.title('Set a New Password')
    st.caption('Your temporary password has been verified. Set and confirm a new private password to access the PSB portal.')
    with st.form('forced_password_change', clear_on_submit=True):
        new1 = st.text_input('New password', type='password')
        new2 = st.text_input('Confirm new password', type='password')
        submit = st.form_submit_button('Change Password', type='primary')
    if submit:
        if not new1 or not new2:
            st.error('Both new password fields are required.')
            return
        if new1 != new2:
            st.error('The new passwords do not match.')
            return
        pwd_errors = _password_errors(new1)
        if pwd_errors:
            st.error(' '.join(pwd_errors))
            return
        uidv = actor_get(actor, 'user_id')
        # Reaching this page already requires require_login() to have completed
        # successfully.  Keep a minimal server-side session guard without
        # re-querying or comparing differently shaped actor/session objects.
        if not uidv or not st.session_state.get('logged_in'):
            st.error('Your authenticated session could not be verified. Please sign in again.')
            return
        # A forced first-login password change is an authenticated self-service
        # security operation.  It must not depend on the user's business-module
        # permission to edit Users & Roles.
        with system_write('authenticated_self_password_change'):
            db_update('users', 'user_id', uidv, {'password_hash': phash(new1), 'force_password_change': 'No', 'password_changed_on': now()})
        st.session_state['must_change_password'] = False
        audit('Password Changed', 'Forced password change completed', actor=actor, entity_type='User', entity_id=uidv, reason='Required account security change')
        st.success('Password changed successfully. Please continue to the PSB portal.')
        st.rerun()

def sidebar(actor):
    """Task-oriented PSB navigation with one canonical role map and persistent bottom sign-out."""
    st.sidebar.markdown(
        """<style>
        section[data-testid="stSidebar"] > div {min-height:0 !important;}
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-bottom:0 !important;
            margin-bottom:0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:last-child {
            padding-bottom:0 !important;
            margin-bottom:0 !important;
        }
        section[data-testid="stSidebar"] .psb-brand-lockup b {
            font-size:1.2rem !important;
            line-height:1.25 !important;
            font-weight:900 !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=92)
    name = actor_get(actor, 'name')
    role = actor_get(actor, 'role')
    email = actor_get(actor, 'email')
    st.sidebar.markdown(
        f"<div class='psb-brand-lockup'><b>Pakistan Shipping Bureau</b><span>Qualification & Authorization</span></div>"
        f"<div class='psb-user-card'><b>{name}</b><br><span>{role}</span><br><small>{email}</small></div>",
        unsafe_allow_html=True,
    )

    groups = ROLE_NAVIGATION.get(role)
    if groups is None:
        st.error('Your account role is not configured. Please contact an administrator.')
        return 'Dashboard'

    default_page = 'GM Capability' if role == 'GM' else 'Dashboard'
    if 'psb_current_page' not in st.session_state:
        st.session_state['psb_current_page'] = default_page

    allowed_pages={default_page} | ({'QR Verify'} if role != 'GM' else set()) | {p for _,items,_ in groups for p in items}
    if st.session_state.get('psb_current_page') not in allowed_pages:
        st.session_state['psb_current_page'] = default_page

    current = st.session_state.get('psb_current_page', default_page)
    dashboard_label = 'GM Capability' if role == 'GM' else 'Dashboard'
    if current == default_page:
        st.sidebar.markdown(f"<div class='psb-nav-active'>{dashboard_label}</div>", unsafe_allow_html=True)
    elif st.sidebar.button(dashboard_label, key='nav_dashboard_btn', use_container_width=True):
        st.session_state['psb_current_page'] = default_page
        st.rerun()

    for title, options, key in groups:
        st.sidebar.markdown(f"<div class='psb-nav-section'>{title}</div>", unsafe_allow_html=True)
        for idx, option in enumerate(options):
            if option == default_page:
                continue
            if option == current:
                st.sidebar.markdown(f"<div class='psb-nav-active'>{option}</div>", unsafe_allow_html=True)
            elif st.sidebar.button(option, key=f'nav_{role}_{key}_{title}_{idx}_{option}', use_container_width=True):
                st.session_state['psb_current_page'] = option
                st.rerun()

    if role != 'GM':
        st.sidebar.markdown("<div class='psb-nav-section'>Verification</div>", unsafe_allow_html=True)
        if current == 'QR Verify':
            st.sidebar.markdown("<div class='psb-nav-active'>QR Verify</div>", unsafe_allow_html=True)
        elif st.sidebar.button('QR Verify', key=f'nav_{role}_qr_verify', use_container_width=True):
            st.session_state['psb_current_page'] = 'QR Verify'
            st.rerun()

    if st.sidebar.button('Sign out', key='psb_sign_out', use_container_width=True):
        audit('User Logout', f'{name} logged out', actor=actor)
        clear_auth_token()
        st.session_state['logged_in'] = False
        st.session_state['user'] = {}
        st.rerun()
    return st.session_state.get('psb_current_page', default_page)

def dashboard_page(actor):
    role=actor_get(actor, "role", "")
    st.header(f"{role} Dashboard")
    uidv=actor_get(actor,"user_id","")
    if role in ORG_ROLES:
        metric_items=[("People",db_count("users")),("Qualification Assignments",db_count("qualification_assignments") if table_exists("qualification_assignments") else 0),("Training Records",db_count("training_records")),("Authorization Cases",db_count("authorization_requests")),("Active Certificates",db_count("authorization_certificates","status = :status",(("status","Valid"),)))]
    else:
        metric_items=[("Training",len(restrict_user_frame(db_all("training_records"),actor))),("Competency",len(restrict_user_frame(db_all("competency_matrix"),actor))),("Authorization",len(restrict_user_frame(db_all("authorization_requests"),actor))),("Certificates",len(restrict_user_frame(db_all("authorization_certificates"),actor)))]
    metrics(metric_items)
    notifications=db_where("notifications","user_id = :uid",(("uid",uidv),))
    if not notifications.empty:
        st.subheader("My Notifications / Messages")
        cols=[c for c in ["created_on","subject","message","type","status"] if c in notifications.columns]
        table(notifications.sort_values("created_on",ascending=False).head(10)[cols])

