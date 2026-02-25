import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import feedparser
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RECESSION MONITOR // GLOBAL",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# MASTER CSS  —  Bloomberg War Room Aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=IBM+Plex+Mono:wght@300;400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    background: #000000 !important;
    color: #c8a84b !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── Scanline overlay ── */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.07) 2px,
        rgba(0,0,0,0.07) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── HERO HEADER ── */
.hero-wrap {
    position: relative;
    padding: 2.5rem 0 1.5rem 0;
    border-bottom: 1px solid #2a1f00;
    margin-bottom: 2rem;
    overflow: hidden;
}
.hero-bg-grid {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(200,168,75,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(200,168,75,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
}
.hero-glow {
    position: absolute;
    top: -40px; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 200px;
    background: radial-gradient(ellipse, rgba(200,168,75,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.hero-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    color: #4a3a10;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.hero-title {
    font-family: 'Orbitron', sans-serif;
    font-size: clamp(2.2rem, 5vw, 4rem);
    font-weight: 900;
    color: #c8a84b;
    letter-spacing: 0.06em;
    line-height: 0.95;
    text-shadow:
        0 0 20px rgba(200,168,75,0.5),
        0 0 60px rgba(200,168,75,0.15);
    animation: flicker 8s infinite;
}
@keyframes flicker {
    0%,93%,100% { opacity: 1; }
    94% { opacity: 0.82; }
    95% { opacity: 1; }
    97% { opacity: 0.65; }
    98% { opacity: 1; }
}
.hero-sub {
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    color: #4a3a10;
    margin-top: 0.7rem;
    text-transform: uppercase;
}
.hero-live {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    color: #3a8a3a;
    margin-top: 0.9rem;
    text-transform: uppercase;
}
.live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #3a8a3a;
    box-shadow: 0 0 6px #3a8a3a;
    animation: blink 2s infinite;
}
@keyframes blink {
    0%,100% { opacity:1; box-shadow: 0 0 6px #3a8a3a; }
    50% { opacity:0.3; box-shadow: 0 0 2px #3a8a3a; }
}

/* ── SECTION LABELS ── */
.sec-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.4em;
    color: #4a3a10;
    text-transform: uppercase;
    border-top: 1px solid #1a1200;
    padding-top: 1.8rem;
    margin: 1.5rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 12px;
}
.sec-num { color: #c8a84b; font-size: 0.65rem; }
.sec-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #2a1f00 0%, transparent 100%);
}

/* ── MAP BAR ── */
.map-bar {
    background: #060500;
    border: 1px solid #1a1200;
    border-left: 3px solid #c8a84b;
    padding: 0.55rem 1rem;
    font-size: 0.65rem;
    color: #6a5a2a;
    letter-spacing: 0.08em;
    margin-bottom: 0.8rem;
}

/* ── CHIPS ── */
.chips-row {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin: 0.8rem 0 1.2rem 0;
}
.chip {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    padding: 3px 10px;
    border: 1px solid #2a1f00;
    color: #4a3a10;
    background: #060500;
    letter-spacing: 0.05em;
}
.chip-on {
    border-color: #c8a84b;
    color: #c8a84b;
    background: rgba(200,168,75,0.07);
    box-shadow: 0 0 8px rgba(200,168,75,0.15);
}

/* ── COUNTRY HEADER ── */
.cty-head {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #c8a84b;
    letter-spacing: 0.12em;
    padding: 0.7rem 1rem;
    background: linear-gradient(90deg, rgba(200,168,75,0.05) 0%, transparent 100%);
    border-left: 3px solid #c8a84b;
    margin: 1rem 0 0.7rem 0;
    text-transform: uppercase;
}

/* ── RECESSION ALERT ── */
.rec-alert {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    color: #e05555;
    background: rgba(224,85,85,0.06);
    border: 1px solid rgba(224,85,85,0.25);
    padding: 3px 10px;
    margin-bottom: 0.8rem;
    text-transform: uppercase;
    animation: rec-blink 2s infinite;
}
@keyframes rec-blink {
    0%,100% { border-color: rgba(224,85,85,0.25); }
    50% { border-color: rgba(224,85,85,0.6); box-shadow: 0 0 8px rgba(224,85,85,0.15); }
}
.rdot { width:5px; height:5px; border-radius:50%; background:#e05555; animation: blink 1s infinite; }

/* ── DIVIDER ── */
hr.div { border:none; border-top:1px solid #100e00; margin:2rem 0; }

/* ── METRICS ── */
div[data-testid="metric-container"] {
    background: #060500 !important;
    border: 1px solid #1a1200 !important;
    border-radius: 0 !important;
    padding: 0.8rem !important;
}
div[data-testid="metric-container"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.55rem !important;
    letter-spacing: 0.18em !important;
    color: #4a3a10 !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 1.35rem !important;
    color: #c8a84b !important;
    text-shadow: 0 0 10px rgba(200,168,75,0.3) !important;
}

/* ── BUTTONS ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border: 1px solid #c8a84b !important;
    color: #c8a84b !important;
    border-radius: 0 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(200,168,75,0.08) !important;
    box-shadow: 0 0 14px rgba(200,168,75,0.25) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #060500 !important;
    border: 1px solid #1a1200 !important;
    border-radius: 0 !important;
    color: #c8a84b !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #c8a84b !important;
    box-shadow: 0 0 8px rgba(200,168,75,0.12) !important;
}

/* ── MULTISELECT ── */
.stMultiSelect > div > div {
    background: #060500 !important;
    border: 1px solid #1a1200 !important;
    border-radius: 0 !important;
}
[data-baseweb="tag"] {
    background: rgba(200,168,75,0.1) !important;
    border: 1px solid #c8a84b !important;
    border-radius: 0 !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1a1200 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #4a3a10 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #c8a84b !important;
    border-bottom: 2px solid #c8a84b !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    color: #6a5a2a !important;
    background: #060500 !important;
    border: 1px solid #1a1200 !important;
    border-radius: 0 !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #030200 !important;
    border-right: 1px solid #1a1200 !important;
}
section[data-testid="stSidebar"] * { color: #6a5a2a !important; }
section[data-testid="stSidebar"] h3 {
    color: #c8a84b !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
}

/* ── PROGRESS ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #c8a84b, #f0c84b) !important;
    box-shadow: 0 0 8px rgba(200,168,75,0.4) !important;
}

/* ── LABELS ── */
label[data-testid="stWidgetLabel"] p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.18em !important;
    color: #4a3a10 !important;
    text-transform: uppercase !important;
}

/* ── RADIO ── */
.stRadio label p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #6a5a2a !important;
}

/* ── NEWS ── */
.nitem { padding: 0.6rem 0; border-bottom: 1px solid #0e0c00; }
.nitem a { color: #c8a84b !important; text-decoration: none; font-size: 0.75rem; line-height:1.45; }
.nitem a:hover { color: #f0d070 !important; text-decoration: underline; }
.nmeta { font-size: 0.58rem; color: #3a2f10; margin-top: 3px; letter-spacing: 0.05em; }

/* ── HIDE CHROME ── */
#MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA MAPS
# ─────────────────────────────────────────────
COUNTRY_INDICATOR_MAP = {
    ("United States",  "Real GDP"):             "GDPC1",
    ("United States",  "Unemployment Rate"):     "UNRATE",
    ("United States",  "Inflation (CPI)"):       "CPIAUCSL",
    ("United States",  "Industrial Production"): "INDPRO",
    ("United States",  "Yield Curve (10Y-2Y)"):  "T10Y2Y",
    ("Canada",         "Real GDP"):              "NAEXKP01CAQ189S",
    ("Canada",         "Unemployment Rate"):      "LRUNTTTTCAM156S",
    ("Canada",         "Inflation (CPI)"):        "CPALCY01CAM661N",
    ("Canada",         "Industrial Production"):  "CANPRINTO01GPSAM",
    ("Japan",          "Real GDP"):              "JPNRGDPEXP",
    ("Japan",          "Unemployment Rate"):      "LRUNTTTTJPQ156S",
    ("Japan",          "Inflation (CPI)"):        "JPNCPIALLMINMEI",
    ("Japan",          "Industrial Production"):  "JPNPROINDMISMEI",
    ("Germany",        "Real GDP"):              "CLVMNACSCAB1GQDE",
    ("Germany",        "Unemployment Rate"):      "LRUNTTTTDEQ156S",
    ("Germany",        "Inflation (CPI)"):        "DEUCPIALLMINMEI",
    ("Germany",        "Industrial Production"):  "DEUPROINDMISMEI",
    ("France",         "Real GDP"):              "CLVMNACSCAB1GQFR",
    ("France",         "Unemployment Rate"):      "LRUNTTTTFRQ156S",
    ("France",         "Inflation (CPI)"):        "FRACPIALLMINMEI",
    ("France",         "Industrial Production"):  "FRAPROINDMISMEI",
    ("United Kingdom", "Real GDP"):              "CLVMNACSCAB1GQUK",
    ("United Kingdom", "Unemployment Rate"):      "LRUN64TTGBM156S",
    ("United Kingdom", "Inflation (CPI)"):        "GBRCPIALLMINMEI",
    ("United Kingdom", "Industrial Production"):  "GBRPRINTO01GYSAM",
    ("Italy",          "Real GDP"):              "CLVMNACSCAB1GQIT",
    ("Italy",          "Unemployment Rate"):      "LRUNTTTTITQ156S",
    ("Italy",          "Inflation (CPI)"):        "ITACPIALLMINMEI",
    ("Italy",          "Industrial Production"):  "ITAPROINDMISMEI",
    ("Australia",      "Real GDP"):              "AUSGDPRQDSMEI",
    ("Australia",      "Unemployment Rate"):      "LRUNTTTTAUM156S",
    ("Australia",      "Inflation (CPI)"):        "AUSCPIALLMINMEI",
    ("South Korea",    "Real GDP"):              "KORRGDPEXP",
    ("South Korea",    "Unemployment Rate"):      "LRUNTTTTKOQ156S",
    ("South Korea",    "Inflation (CPI)"):        "KORCPIALLMINMEI",
    ("Brazil",         "Real GDP"):              "BRAGDPNQDSMEI",
    ("Brazil",         "Unemployment Rate"):      "LRUNTTTTBRM156S",
    ("Brazil",         "Inflation (CPI)"):        "BRACPIALLMINMEI",
    ("Mexico",         "Real GDP"):              "MEXRGDPEXP",
    ("Mexico",         "Unemployment Rate"):      "LRUNTTTTMXM156S",
    ("Mexico",         "Inflation (CPI)"):        "MEXCPIALLMINMEI",
    ("India",          "Real GDP"):              "INDRGDPEXP",
    ("India",          "Inflation (CPI)"):        "INDCPIALLMINMEI",
    ("China",          "Real GDP"):              "CHNGDPNQDSMEI",
    ("China",          "Inflation (CPI)"):        "CHNCPIALLMINMEI",
    ("Sweden",         "Real GDP"):              "CLVMNACSCAB1GQSE",
    ("Sweden",         "Unemployment Rate"):      "LRUNTTTTSEQ156S",
    ("Sweden",         "Inflation (CPI)"):        "SWECPIALLMINMEI",
    ("Spain",          "Real GDP"):              "CLVMNACSCAB1GQES",
    ("Spain",          "Unemployment Rate"):      "LRUNTTTTESQ156S",
    ("Netherlands",    "Real GDP"):              "CLVMNACSCAB1GQNL",
    ("Netherlands",    "Unemployment Rate"):      "LRUNTTTTNLQ156S",
    ("Netherlands",    "Inflation (CPI)"):        "NLDCPIALLMINMEI",
    ("South Africa",   "Real GDP"):              "ZAFRGDPEXP",
    ("South Africa",   "Unemployment Rate"):      "LRUNTTTTZAQ156S",
    ("South Africa",   "Inflation (CPI)"):        "ZAFCPIALLMINMEI",
}

ALL_COUNTRIES = sorted(set(k[0] for k in COUNTRY_INDICATOR_MAP.keys()))
ALL_INDICATORS = sorted(set(k[1] for k in COUNTRY_INDICATOR_MAP.keys()))

COUNTRY_ISO = {
    "United States": "USA", "Canada": "CAN", "Japan": "JPN",
    "Germany": "DEU", "France": "FRA", "United Kingdom": "GBR",
    "Italy": "ITA", "Australia": "AUS", "South Korea": "KOR",
    "Brazil": "BRA", "Mexico": "MEX", "India": "IND",
    "China": "CHN", "Sweden": "SWE", "Spain": "ESP",
    "Netherlands": "NLD", "South Africa": "ZAF",
}

FLAG_MAP = {
    "United States": "🇺🇸", "Canada": "🇨🇦", "Japan": "🇯🇵",
    "Germany": "🇩🇪", "France": "🇫🇷", "United Kingdom": "🇬🇧",
    "Italy": "🇮🇹", "Australia": "🇦🇺", "South Korea": "🇰🇷",
    "Brazil": "🇧🇷", "Mexico": "🇲🇽", "India": "🇮🇳",
    "China": "🇨🇳", "Sweden": "🇸🇪", "Spain": "🇪🇸",
    "Netherlands": "🇳🇱", "South Africa": "🇿🇦",
}

INDICATOR_COLORS = {
    "Real GDP":              "#c8a84b",
    "Unemployment Rate":     "#e05c5c",
    "Inflation (CPI)":       "#e0974a",
    "Industrial Production": "#5ab8d0",
    "Yield Curve (10Y-2Y)":  "#7ac85a",
}

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key, default in [
    ("selected_countries", ["United States", "United Kingdom", "Germany"]),
    ("recession_periods", {}),
    ("latest_values", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ SYSTEM ACCESS")
    fred_api_key     = st.text_input("FRED API KEY",     type="password")
    deepseek_api_key = st.text_input("DEEPSEEK API KEY", type="password")
    newsapi_key      = st.text_input("NEWSAPI KEY",      type="password")
    st.markdown("---")
    st.markdown("### ◈ PARAMETERS")
    selected_indicators = st.multiselect(
        "INDICATORS", ALL_INDICATORS,
        default=["Real GDP", "Unemployment Rate", "Inflation (CPI)"],
    )
    today      = datetime.today()
    start_date = st.date_input("START DATE", today - timedelta(days=10 * 365))
    end_date   = st.date_input("END DATE",   today)
    st.markdown("---")
    st.markdown("""
<div style="font-size:0.6rem;line-height:2;color:#4a3a10;">
▸ AMBER = MONITORED NATION<br>
▸ RED BANDS = RECESSION PERIOD<br>
▸ GREEN = SYSTEM LIVE<br>
▸ CLICK MAP TO TOGGLE COUNTRY<br>
▸ MAX 8 SIMULTANEOUS TARGETS
</div>""", unsafe_allow_html=True)
    with st.expander("◈ DEBUG"):
        st.write(f"FRED: {'✅' if fred_api_key else '❌'}")
        st.write(f"DeepSeek: {'✅' if deepseek_api_key else '❌'}")
        st.write(f"NewsAPI: {'✅' if newsapi_key else '❌'}")
        st.write(f"Countries: {len(st.session_state.selected_countries)}")
        st.write(f"Cached pts: {len(st.session_state.latest_values)}")

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
now_str = datetime.now().strftime("%Y.%m.%d  //  %H:%M UTC")
st.markdown(f"""
<div class="hero-wrap">
  <div class="hero-bg-grid"></div>
  <div class="hero-glow"></div>
  <div class="hero-eyebrow">▸ MACROECONOMIC INTELLIGENCE SYSTEM  ·  FRED DATA FEED  ·  G20 COVERAGE</div>
  <div class="hero-title">RECESSION<br>MONITOR</div>
  <div class="hero-sub">Global Economic Threat Assessment  ·  {now_str}</div>
  <div class="hero-live"><span class="live-dot"></span>SYSTEM ONLINE  ·  FRED API ACTIVE  ·  CACHE TTL 3600s</div>
</div>
""", unsafe_allow_html=True)

# Gate on FRED key
if not fred_api_key:
    st.markdown("""
<div style="border:1px solid #2a1f00;background:#060500;padding:1.5rem;
            font-family:'IBM Plex Mono',monospace;max-width:600px;">
  <div style="color:#e05555;font-size:0.65rem;letter-spacing:0.25em;margin-bottom:1rem;">
    ⚠ AUTHENTICATION REQUIRED  ·  ACCESS DENIED
  </div>
  <div style="color:#6a5a2a;font-size:0.75rem;line-height:1.9;">
    A FRED API key is required to proceed.<br><br>
    1 · Visit <b style="color:#c8a84b;">fred.stlouisfed.org</b><br>
    2 · Navigate to API Keys → Request Free Key<br>
    3 · Enter key in the sidebar (←)<br><br>
    <span style="color:#3a2f10;">// Keys delivered instantly via email. Free tier supports full app.</span>
  </div>
</div>""", unsafe_allow_html=True)
    st.stop()

if start_date >= end_date:
    st.error("// ERROR: END DATE MUST BE AFTER START DATE")
    st.stop()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_fred(series_id: str, start: str, end: str, _key: str) -> pd.DataFrame:
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series_id, "observation_start": start,
                    "observation_end": end, "api_key": _key, "file_type": "json"},
            timeout=12,
        )
        r.raise_for_status()
        obs = r.json().get("observations", [])
        if not obs:
            return pd.DataFrame()
        df = pd.DataFrame(obs)
        df["date"]  = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna(subset=["value"]).set_index("date")[["value"]]
    except:
        return pd.DataFrame()

def detect_recessions(series: pd.Series):
    q = series.resample("Q").last().dropna()
    if len(q) < 3:
        return []
    g = q.pct_change()
    recs, active, start = [], False, None
    for d, v in g.items():
        if pd.isna(v):
            continue
        if v < 0 and not active:
            start, active = d - pd.DateOffset(months=3), True
        elif v >= 0 and active:
            recs.append((start, d + pd.DateOffset(months=2)))
            active = False
    if active and start:
        recs.append((start, q.index[-1]))
    return recs

def make_chart(df: pd.DataFrame, title: str, recessions: list, color: str) -> go.Figure:
    fig = go.Figure()
    for s, e in recessions:
        fig.add_vrect(x0=s, x1=e, fillcolor="rgba(224,85,85,0.07)", layer="below", line_width=0)
        fig.add_vrect(x0=s, x1=s + pd.DateOffset(days=6),
                      fillcolor="rgba(224,85,85,0.28)", layer="below", line_width=0)
    # Fill area
    fig.add_trace(go.Scatter(
        x=data.index if (data := df) is not None else [],
        y=df["value"],
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.07)",
        hovertemplate="%{x|%b %Y}  <b>%{y:.2f}</b><extra></extra>",
        name="",
    ))
    # Glowing last point
    fig.add_trace(go.Scatter(
        x=[df.index[-1]], y=[df["value"].iloc[-1]],
        mode="markers",
        marker=dict(color=color, size=7, symbol="circle",
                    line=dict(color=color.replace(")", ",0.3)").replace("rgb","rgba") if "rgb" in color
                              else color, width=7)),
        hoverinfo="skip", name="",
    ))
    fig.update_layout(
        title=dict(
            text=f"<span style='font-family:IBM Plex Mono;font-size:10px;"
                 f"letter-spacing:0.15em;color:#4a3a10;'>{title.upper()}</span>",
            x=0, xanchor="left",
        ),
        plot_bgcolor="#030200",
        paper_bgcolor="#060500",
        font=dict(color="#4a3a10", family="IBM Plex Mono", size=9),
        xaxis=dict(showgrid=True, gridcolor="#100e00", zeroline=False,
                   showline=True, linecolor="#1a1200",
                   tickfont=dict(size=8, color="#3a2d10")),
        yaxis=dict(showgrid=True, gridcolor="#100e00", zeroline=False,
                   showline=True, linecolor="#1a1200",
                   tickfont=dict(size=8, color="#3a2d10")),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#060500", bordercolor=color,
                        font=dict(color=color, family="IBM Plex Mono", size=11)),
        height=290,
        margin=dict(l=5, r=5, t=32, b=5),
        showlegend=False,
    )
    return fig

# ─────────────────────────────────────────────
# SECTION 01 — WORLD MAP
# ─────────────────────────────────────────────
st.markdown("""
<div class="sec-label"><span class="sec-num">[ 01 ]</span> MISSION SELECT  ·  TARGET NATIONS</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="map-bar">
▸ CLICK ANY ILLUMINATED NATION TO TOGGLE ACTIVE MONITORING  ·  SELECTED COUNTRIES GLOW AMBER  ·  MAX 8 TARGETS
</div>
""", unsafe_allow_html=True)

map_countries = list(COUNTRY_ISO.keys())
map_iso = [COUNTRY_ISO[c] for c in map_countries]
map_z   = [1.0 if c in st.session_state.selected_countries else 0.0 for c in map_countries]
map_txt = [f"{'▶ ' if c in st.session_state.selected_countries else '· '}{c.upper()}" for c in map_countries]

map_fig = go.Figure(go.Choropleth(
    locations=map_iso,
    z=map_z,
    text=map_txt,
    hovertemplate="<b>%{text}</b><extra></extra>",
    colorscale=[[0.0, "#0d0b02"], [0.01, "#0d0b02"], [0.01, "#c8a84b"], [1.0, "#f5d060"]],
    zmin=0, zmax=1,
    showscale=False,
    marker=dict(line=dict(color="#1a1500", width=0.5)),
))

map_fig.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=True,  coastlinecolor="#1a1500",
        showland=True,        landcolor="#0a0800",
        showocean=True,       oceancolor="#030200",
        showlakes=True,       lakecolor="#030200",
        showcountries=True,   countrycolor="#1a1500",
        bgcolor="#030200",
        projection_type="natural earth",
        lataxis_range=[-60, 85],
    ),
    paper_bgcolor="#060500",
    margin=dict(l=0, r=0, t=0, b=0),
    height=450,
    clickmode="event+select",
    hoverlabel=dict(
        bgcolor="#060500", bordercolor="#c8a84b",
        font=dict(color="#c8a84b", family="IBM Plex Mono", size=12),
    ),
)

map_event = st.plotly_chart(
    map_fig, use_container_width=True,
    key="world_map", on_select="rerun", selection_mode="points",
)

# Handle click
if map_event and map_event.get("selection") and map_event["selection"].get("points"):
    for pt in map_event["selection"]["points"]:
        raw     = pt.get("text", "").replace("▶ ", "").replace("· ", "").strip()
        matched = next((c for c in ALL_COUNTRIES if c.upper() == raw.upper()), None)
        if matched:
            cur = list(st.session_state.selected_countries)
            if matched in cur:
                cur.remove(matched)
            else:
                if len(cur) < 8:
                    cur.append(matched)
                else:
                    st.toast("⚠ MAXIMUM 8 TARGETS ACTIVE", icon="⚠️")
            st.session_state.selected_countries = cur
            st.session_state.recession_periods  = {}
            st.rerun()

# Multiselect (synced)
col_ms, col_clr = st.columns([5, 1])
with col_ms:
    ms_val = st.multiselect(
        "ACTIVE NATIONS", ALL_COUNTRIES,
        default=st.session_state.selected_countries,
        key="ms", max_selections=8,
    )
with col_clr:
    st.write(""); st.write("")
    if st.button("CLEAR ALL"):
        st.session_state.selected_countries = []
        st.session_state.recession_periods  = {}
        st.rerun()

if sorted(ms_val) != sorted(st.session_state.selected_countries):
    st.session_state.selected_countries = ms_val
    st.session_state.recession_periods  = {}
    st.rerun()

selected_countries = st.session_state.selected_countries

# Chips
if selected_countries:
    chips = "".join(
        f'<span class="chip chip-on">{FLAG_MAP.get(c,"🌍")} {c.upper()}</span>'
        for c in selected_countries
    )
    st.markdown(f'<div class="chips-row">{chips}</div>', unsafe_allow_html=True)
else:
    st.markdown(
        "<div style='color:#3a2d10;font-size:0.7rem;letter-spacing:0.12em;padding:1rem 0;'>"
        "▸ NO TARGETS SELECTED  ·  CLICK MAP OR USE DROPDOWN ABOVE</div>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# SECTION 02 — CHARTS
# ─────────────────────────────────────────────
if selected_countries and selected_indicators:
    st.markdown("""
<div class="sec-label"><span class="sec-num">[ 02 ]</span> ECONOMIC INDICATORS  ·  FRED LIVE STREAM</div>
""", unsafe_allow_html=True)

    prog = st.progress(0)
    stat = st.empty()

    for i, country in enumerate(selected_countries):
        stat.markdown(
            f"<span style='font-family:IBM Plex Mono;font-size:0.65rem;color:#4a3a10;"
            f"letter-spacing:0.12em;'>▸ ACQUIRING DATA  ·  {country.upper()}</span>",
            unsafe_allow_html=True,
        )
        flag = FLAG_MAP.get(country, "🌍")
        st.markdown(
            f'<div class="cty-head">{flag} &nbsp; {country.upper()}</div>',
            unsafe_allow_html=True,
        )

        # Always fetch GDP for shading
        if country not in st.session_state.recession_periods:
            gk = (country, "Real GDP")
            if gk in COUNTRY_INDICATOR_MAP:
                gdf = fetch_fred(COUNTRY_INDICATOR_MAP[gk], str(start_date), str(end_date), fred_api_key)
                st.session_state.recession_periods[country] = (
                    detect_recessions(gdf["value"]) if not gdf.empty else []
                )
            else:
                st.session_state.recession_periods[country] = []

        recs = st.session_state.recession_periods.get(country, [])

        if recs:
            last_end = max(e for _, e in recs)
            if (pd.Timestamp(end_date) - last_end).days < 365 * 2:
                st.markdown(
                    '<div class="rec-alert"><span class="rdot"></span>'
                    'RECESSION DETECTED IN RECENT HISTORY  ·  ELEVATED RISK</div>',
                    unsafe_allow_html=True,
                )

        avail = [ind for ind in selected_indicators if (country, ind) in COUNTRY_INDICATOR_MAP]
        if not avail:
            st.markdown(
                f"<span style='color:#3a2d10;font-size:0.7rem;'>"
                f"// NO SELECTED INDICATORS AVAILABLE FOR {country.upper()}</span>",
                unsafe_allow_html=True,
            )
        else:
            cols = st.columns(min(2, len(avail)))
            for j, indicator in enumerate(avail):
                sid   = COUNTRY_INDICATOR_MAP[(country, indicator)]
                df    = fetch_fred(sid, str(start_date), str(end_date), fred_api_key)
                color = INDICATOR_COLORS.get(indicator, "#c8a84b")

                with cols[j % 2]:
                    if df.empty:
                        st.markdown(
                            f"<div style='border:1px solid #1a1200;background:#060500;"
                            f"padding:1rem;color:#3a2d10;font-size:0.65rem;height:290px;"
                            f"display:flex;align-items:center;'>"
                            f"// NO DATA  ·  SERIES {sid}</div>",
                            unsafe_allow_html=True,
                        )
                        continue

                    latest = df["value"].iloc[-1]
                    prev   = df["value"].iloc[-2] if len(df) > 1 else latest
                    delta  = latest - prev
                    st.session_state.latest_values[(country, indicator)] = latest

                    fig = make_chart(df, f"{country} — {indicator}", recs, color)
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric(
                        label=indicator.upper(),
                        value=f"{latest:.2f}",
                        delta=f"{delta:+.3f}",
                    )

        st.markdown('<hr class="div">', unsafe_allow_html=True)
        prog.progress((i + 1) / len(selected_countries))

    stat.empty()
    prog.empty()

# ─────────────────────────────────────────────
# SECTION 03 — AI ANALYST
# ─────────────────────────────────────────────
if selected_countries:
    st.markdown("""
<div class="sec-label"><span class="sec-num">[ 03 ]</span> AI ECONOMIC ANALYST  ·  DEEPSEEK INFERENCE ENGINE</div>
""", unsafe_allow_html=True)

    def build_ctx():
        lines = ["LIVE ECONOMIC READINGS:"]
        for (c, ind), v in st.session_state.latest_values.items():
            lines.append(f"  {c} — {ind}: {v:.2f}")
        return "\n".join(lines)

    def ask_ds(prompt, ctx, key):
        if not key:
            return "// DEEPSEEK API KEY NOT PROVIDED  ·  ADD IN SIDEBAR TO ENABLE ANALYST"
        try:
            r = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content":
                            "You are a senior macroeconomic analyst at a global investment bank. "
                            "Be precise, data-driven, direct. No fluff."},
                        {"role": "user", "content": f"{ctx}\n\n{prompt}"},
                    ],
                    "temperature": 0.25,
                    "max_tokens": 700,
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"// ERROR: {e}"

    tab1, tab2 = st.tabs(["▸ QUERY ANALYST", "▸ THREAT ASSESSMENT"])

    with tab1:
        if deepseek_api_key:
            q = st.text_area(
                "INPUT QUERY", height=75,
                placeholder="e.g. Which country shows the highest recession probability given yield curve and unemployment trends?"
            )
            if st.button("▸ TRANSMIT") and q:
                with st.spinner("// PROCESSING QUERY..."):
                    ans = ask_ds(q, build_ctx(), deepseek_api_key)
                    st.markdown(
                        f"<div style='background:#060500;border:1px solid #1a1200;"
                        f"border-left:3px solid #c8a84b;padding:1.2rem;"
                        f"font-size:0.78rem;line-height:1.75;color:#c8a84b;"
                        f"font-family:IBM Plex Mono,monospace;white-space:pre-wrap;'>{ans}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                "<div style='color:#3a2d10;font-size:0.7rem;letter-spacing:0.1em;'>"
                "▸ DEEPSEEK API KEY REQUIRED  ·  ADD IN SIDEBAR</div>",
                unsafe_allow_html=True,
            )

    with tab2:
        if deepseek_api_key:
            if st.button("▸ INITIATE THREAT ASSESSMENT"):
                with st.spinner("// ANALYZING ALL TARGETS..."):
                    prompt = (
                        "For each country in the data, output a brief threat report:\n"
                        "RISK LEVEL: CRITICAL / HIGH / MODERATE / LOW\n"
                        "PRIMARY RISK FACTOR: (one line)\n"
                        "OUTLOOK: (one sentence)\n\n"
                        "Format cleanly. Be direct. No boilerplate."
                    )
                    ans = ask_ds(prompt, build_ctx(), deepseek_api_key)
                    st.markdown(
                        f"<div style='background:#060500;border:1px solid #1a1200;"
                        f"border-left:3px solid #e05c5c;padding:1.2rem;"
                        f"font-size:0.78rem;line-height:1.85;color:#c8a84b;"
                        f"font-family:IBM Plex Mono,monospace;white-space:pre-wrap;'>{ans}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                "<div style='color:#3a2d10;font-size:0.7rem;'>▸ DEEPSEEK KEY REQUIRED</div>",
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────
# SECTION 04 — NEWS INTEL
# ─────────────────────────────────────────────
if selected_countries:
    st.markdown("""
<div class="sec-label"><span class="sec-num">[ 04 ]</span> NEWS INTELLIGENCE  ·  LIVE DISPATCH FEED</div>
""", unsafe_allow_html=True)

    src = st.radio(
        "FEED SOURCE",
        ["GOOGLE NEWS RSS  ·  FREE", "NEWSAPI  ·  REQUIRES KEY"],
        horizontal=True,
    )

    @st.cache_data(ttl=1800)
    def rss_news(country):
        q = f"recession+economy+{country.replace(' ', '+')}+GDP"
        try:
            feed = feedparser.parse(
                f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            )
            return [{"title": e.title, "link": e.link,
                     "published": e.get("published", "")[:16],
                     "source": e.get("source", {}).get("title", "News")}
                    for e in feed.entries[:6]]
        except:
            return []

    @st.cache_data(ttl=1800)
    def napi_news(country, _key):
        try:
            r = requests.get("https://newsapi.org/v2/everything", timeout=10, params={
                "q": f"recession economy GDP {country}",
                "language": "en", "sortBy": "relevancy",
                "pageSize": 6, "apiKey": _key,
            })
            d = r.json()
            if d.get("status") == "ok":
                return [{"title": a["title"], "link": a["url"],
                         "published": a["publishedAt"][:10],
                         "source": a["source"]["name"]}
                        for a in d["articles"]]
        except:
            pass
        return []

    ncols = st.columns(min(3, len(selected_countries)))
    for idx, country in enumerate(selected_countries):
        with ncols[idx % 3]:
            flag = FLAG_MAP.get(country, "🌍")
            with st.expander(f"{flag}  {country.upper()}"):
                arts = (
                    napi_news(country, newsapi_key)
                    if "NEWSAPI" in src and newsapi_key
                    else rss_news(country)
                )
                if arts:
                    for a in arts:
                        st.markdown(
                            f'<div class="nitem">'
                            f'<a href="{a["link"]}" target="_blank">{a["title"]}</a>'
                            f'<div class="nmeta">▸ {a["source"].upper()}  ·  {a["published"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        "<span style='color:#3a2d10;font-size:0.65rem;'>// NO FEED DATA AVAILABLE</span>",
                        unsafe_allow_html=True,
                    )

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="border-top:1px solid #0e0c00;margin-top:3rem;padding:1rem 0;
            display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
  <div style="font-family:'IBM Plex Mono',monospace;font-size:0.55rem;
              color:#2a2010;letter-spacing:0.2em;">
    RECESSION MONITOR  ·  POWERED BY FRED API  ·  {now_str}
  </div>
  <div style="font-family:'IBM Plex Mono',monospace;font-size:0.55rem;color:#2a2010;letter-spacing:0.1em;">
    RECESSION DEFINITION: 2 CONSECUTIVE QUARTERS OF NEGATIVE GDP GROWTH  ·  CACHE TTL 3600s
  </div>
</div>
""", unsafe_allow_html=True)
