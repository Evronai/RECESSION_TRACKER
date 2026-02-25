import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta

# ----------------------------
# Page configuration
# ----------------------------
st.set_page_config(
    page_title="Global Recession Tracker",
    page_icon="📉",
    layout="wide"
)

# ----------------------------
# Custom CSS
# ----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
    }
    .stApp {
        background: #0a0e1a;
        color: #e8eaf0;
    }
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        letter-spacing: -0.02em;
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00d4ff 0%, #7b61ff 50%, #ff6b6b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #6b7280;
        font-size: 1rem;
        font-family: 'Space Mono', monospace;
        margin-bottom: 2rem;
    }
    .map-container {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    .map-instructions {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-left: 3px solid #00d4ff;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        font-family: 'Space Mono', monospace;
        font-size: 0.8rem;
        color: #9ca3af;
    }
    .country-chip {
        display: inline-block;
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 0.8rem;
        font-family: 'Space Mono', monospace;
        color: #e5e7eb;
    }
    .selected-chip {
        border-color: #00d4ff;
        color: #00d4ff;
        background: rgba(0, 212, 255, 0.1);
    }
    .recession-badge {
        background: rgba(255, 107, 107, 0.15);
        border: 1px solid rgba(255, 107, 107, 0.4);
        color: #ff6b6b;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-family: 'Space Mono', monospace;
    }
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    div[data-testid="metric-container"] {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 0.8rem;
    }
    .stButton > button {
        font-family: 'Space Mono', monospace;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Mono', monospace;
        font-size: 0.85rem;
    }
    .stExpander {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e8eaf0;
        border-bottom: 1px solid #1f2937;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Title
# ----------------------------
st.markdown('<div class="main-title">🌍 Global Recession Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">// track indicators · detect recessions · ask AI · read news</div>', unsafe_allow_html=True)

# ----------------------------
# Country → FRED indicator map
# ----------------------------
COUNTRY_INDICATOR_MAP = {
    ("United States", "Real GDP"):            "GDPC1",
    ("United States", "Unemployment Rate"):   "UNRATE",
    ("United States", "Inflation (CPI)"):     "CPIAUCSL",
    ("United States", "Industrial Production"):"INDPRO",
    ("United States", "Yield Curve (10Y-2Y)"):"T10Y2Y",
    ("Canada", "Real GDP"):                   "NAEXKP01CAQ189S",
    ("Canada", "Unemployment Rate"):          "LRUNTTTTCAM156S",
    ("Canada", "Inflation (CPI)"):            "CPALCY01CAM661N",
    ("Canada", "Industrial Production"):      "CANPRINTO01GPSAM",
    ("Japan", "Real GDP"):                    "JPNRGDPEXP",
    ("Japan", "Unemployment Rate"):           "LRUNTTTTJPQ156S",
    ("Japan", "Inflation (CPI)"):             "JPNCPIALLMINMEI",
    ("Japan", "Industrial Production"):       "JPNPROINDMISMEI",
    ("Germany", "Real GDP"):                  "CLVMNACSCAB1GQDE",
    ("Germany", "Unemployment Rate"):         "LRUNTTTTDEQ156S",
    ("Germany", "Inflation (CPI)"):           "DEUCPIALLMINMEI",
    ("Germany", "Industrial Production"):     "DEUPROINDMISMEI",
    ("France", "Real GDP"):                   "CLVMNACSCAB1GQFR",
    ("France", "Unemployment Rate"):          "LRUNTTTTFRQ156S",
    ("France", "Inflation (CPI)"):            "FRACPIALLMINMEI",
    ("France", "Industrial Production"):      "FRAPROINDMISMEI",
    ("United Kingdom", "Real GDP"):           "CLVMNACSCAB1GQUK",
    ("United Kingdom", "Unemployment Rate"):  "LRUN64TTGBM156S",
    ("United Kingdom", "Inflation (CPI)"):    "GBRCPIALLMINMEI",
    ("United Kingdom", "Industrial Production"):"GBRPRINTO01GYSAM",
    ("Italy", "Real GDP"):                    "CLVMNACSCAB1GQIT",
    ("Italy", "Unemployment Rate"):           "LRUNTTTTITQ156S",
    ("Italy", "Inflation (CPI)"):             "ITACPIALLMINMEI",
    ("Italy", "Industrial Production"):       "ITAPROINDMISMEI",
    ("Australia", "Real GDP"):                "AUSGDPRQDSMEI",
    ("Australia", "Unemployment Rate"):       "LRUNTTTTAUM156S",
    ("Australia", "Inflation (CPI)"):         "AUSCPIALLMINMEI",
    ("South Korea", "Real GDP"):              "KORRGDPEXP",
    ("South Korea", "Unemployment Rate"):     "LRUNTTTTKOQ156S",
    ("South Korea", "Inflation (CPI)"):       "KORCPIALLMINMEI",
    ("Brazil", "Real GDP"):                   "BRAGDPNQDSMEI",
    ("Brazil", "Unemployment Rate"):          "LRUNTTTTBRM156S",
    ("Brazil", "Inflation (CPI)"):            "BRACPIALLMINMEI",
    ("Mexico", "Real GDP"):                   "MEXRGDPEXP",
    ("Mexico", "Unemployment Rate"):          "LRUNTTTTMXM156S",
    ("Mexico", "Inflation (CPI)"):            "MEXCPIALLMINMEI",
    ("India", "Real GDP"):                    "INDRGDPEXP",
    ("India", "Unemployment Rate"):           "LRUNTTTTINQ156S",
    ("India", "Inflation (CPI)"):             "INDCPIALLMINMEI",
    ("China", "Real GDP"):                    "CHNGDPNQDSMEI",
    ("China", "Inflation (CPI)"):             "CHNCPIALLMINMEI",
    ("Sweden", "Real GDP"):                   "CLVMNACSCAB1GQSE",
    ("Sweden", "Unemployment Rate"):          "LRUNTTTTSEQ156S",
    ("Sweden", "Inflation (CPI)"):            "SWECPIALLMINMEI",
    ("Spain", "Real GDP"):                    "CLVMNACSCAB1GQES",
    ("Spain", "Unemployment Rate"):           "LRUNTTTTESQ156S",
    ("Spain", "Inflation (CPI)"):             "ESPCIALLMINMEI",
    ("Netherlands", "Real GDP"):              "CLVMNACSCAB1GQNL",
    ("Netherlands", "Unemployment Rate"):     "LRUNTTTTNLQ156S",
    ("Netherlands", "Inflation (CPI)"):       "NLDCPIALLMINMEI",
    ("South Africa", "Real GDP"):             "ZAFRGDPEXP",
    ("South Africa", "Unemployment Rate"):    "LRUNTTTTZAQ156S",
    ("South Africa", "Inflation (CPI)"):      "ZAFCPIALLMINMEI",
}

ALL_COUNTRIES = sorted(set(k[0] for k in COUNTRY_INDICATOR_MAP.keys()))
ALL_INDICATORS = sorted(set(k[1] for k in COUNTRY_INDICATOR_MAP.keys()))

# Country ISO codes for choropleth map
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

# ----------------------------
# Session State Initialization
# ----------------------------
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = ["United States", "United Kingdom", "Germany"]
if "recession_periods" not in st.session_state:
    st.session_state.recession_periods = {}
if "latest_values" not in st.session_state:
    st.session_state.latest_values = {}

# ----------------------------
# Sidebar: API Keys
# ----------------------------
st.sidebar.markdown("## 🔑 API Keys")

fred_api_key = st.sidebar.text_input(
    "FRED API Key (required)",
    type="password",
    help="Free from https://fred.stlouisfed.org/docs/api/api_key.html"
)
deepseek_api_key = st.sidebar.text_input(
    "DeepSeek API Key (optional)",
    type="password",
    help="From https://platform.deepseek.com/"
)
newsapi_key = st.sidebar.text_input(
    "NewsAPI Key (optional)",
    type="password",
    help="From https://newsapi.org/"
)

if not fred_api_key:
    st.warning("⚠️ Please enter your FRED API key in the sidebar to continue.")
    st.info("""
**How to get a FRED API key:**
1. Visit https://fred.stlouisfed.org/docs/api/api_key.html
2. Click **"Request a FRED API Key"**
3. Fill out the short form — you'll receive the key instantly by email
    """)
    st.stop()

# ----------------------------
# Sidebar: Settings
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ Settings")

selected_indicators = st.sidebar.multiselect(
    "Indicators to display",
    ALL_INDICATORS,
    default=["Real GDP", "Unemployment Rate", "Inflation (CPI)"]
)

today = datetime.today()
default_start = today - timedelta(days=10 * 365)
start_date = st.sidebar.date_input("Start date", default_start)
end_date = st.sidebar.date_input("End date", today)

if start_date >= end_date:
    st.sidebar.error("End date must be after start date.")
    st.stop()

if (end_date - start_date).days > 365 * 30:
    st.sidebar.warning("⚠️ Date range > 30 years may be slow.")

# ----------------------------
# Helper: FRED REST fetch (replaces pandas_datareader)
# ----------------------------
@st.cache_data(ttl=3600)
def fetch_fred_data(series_id: str, start: str, end: str, api_key: str) -> pd.DataFrame:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "observation_start": start,
        "observation_end": end,
        "api_key": api_key,
        "file_type": "json",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        observations = r.json().get("observations", [])
        if not observations:
            return pd.DataFrame()
        df = pd.DataFrame(observations)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"]).set_index("date")[["value"]]
        return df
    except Exception as e:
        return pd.DataFrame()

# ----------------------------
# Helper: Recession detection (fixed)
# ----------------------------
def detect_recessions(gdp_series: pd.Series):
    gdp_q = gdp_series.resample("Q").last().dropna()
    if len(gdp_q) < 3:
        return []
    growth = gdp_q.pct_change()
    recessions, in_rec, start = [], False, None
    for date, val in growth.items():
        if pd.isna(val):
            continue
        if val < 0 and not in_rec:
            start = date - pd.DateOffset(months=3)
            in_rec = True
        elif val >= 0 and in_rec:
            recessions.append((start, date + pd.DateOffset(months=2)))
            in_rec = False
    if in_rec and start:
        recessions.append((start, gdp_q.index[-1]))
    return recessions

# ----------------------------
# Helper: Plot indicator chart
# ----------------------------
def plot_indicator(data: pd.DataFrame, title: str, recession_periods: list):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index, y=data["value"],
        mode="lines", name=title,
        line=dict(color="#00d4ff", width=2),
        fill="tozeroy",
        fillcolor="rgba(0, 212, 255, 0.05)"
    ))
    for s, e in recession_periods:
        fig.add_vrect(x0=s, x1=e, fillcolor="rgba(255,107,107,0.15)",
                      layer="below", line_width=0,
                      annotation_text="Recession", annotation_position="top left",
                      annotation_font_size=9, annotation_font_color="#ff6b6b")
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#e8eaf0")),
        plot_bgcolor="#0d1117", paper_bgcolor="#111827",
        font=dict(color="#9ca3af", family="Space Mono"),
        xaxis=dict(showgrid=True, gridcolor="#1f2937", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#1f2937", zeroline=False),
        hovermode="x unified", height=340,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig

# ----------------------------
# ★  WORLD MAP SECTION
# ----------------------------
st.markdown('<div class="section-header">🗺️ Select Countries on the Map</div>', unsafe_allow_html=True)

st.markdown("""
<div class="map-instructions">
  💡 Click any highlighted country on the map to add/remove it from your selection.
     Use the multiselect below for fine-grained control. Selected countries glow in cyan.
</div>
""", unsafe_allow_html=True)

# Build choropleth data
map_countries = list(COUNTRY_ISO.keys())
map_iso = [COUNTRY_ISO[c] for c in map_countries]
map_selected = [1 if c in st.session_state.selected_countries else 0 for c in map_countries]
map_labels = [
    f"{'✅ ' if c in st.session_state.selected_countries else ''}{c}"
    for c in map_countries
]

map_fig = go.Figure(go.Choropleth(
    locations=map_iso,
    z=map_selected,
    text=map_labels,
    hovertemplate="<b>%{text}</b><br>Click to toggle<extra></extra>",
    colorscale=[
        [0.0, "#1a2235"],
        [0.5, "#1a2235"],
        [0.5, "#00d4ff"],
        [1.0, "#7b61ff"],
    ],
    zmin=0, zmax=1,
    showscale=False,
    marker=dict(
        line=dict(color="#2d3748", width=0.5),
    ),
))

map_fig.update_layout(
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#2d3748",
        showland=True,
        landcolor="#0d1117",
        showocean=True,
        oceancolor="#070b14",
        showlakes=False,
        showcountries=True,
        countrycolor="#1a2235",
        bgcolor="#070b14",
        projection_type="natural earth",
    ),
    paper_bgcolor="#111827",
    margin=dict(l=0, r=0, t=0, b=0),
    height=420,
    clickmode="event+select",
)

# Render map and capture clicks
map_event = st.plotly_chart(
    map_fig,
    use_container_width=True,
    key="world_map",
    on_select="rerun",
    selection_mode="points",
)

# Handle map click — toggle selected country
if map_event and map_event.get("selection") and map_event["selection"].get("points"):
    for point in map_event["selection"]["points"]:
        clicked_label = point.get("text", "")
        # Strip the checkmark prefix if present
        clicked_country = clicked_label.replace("✅ ", "").strip()
        if clicked_country in ALL_COUNTRIES:
            current = list(st.session_state.selected_countries)
            if clicked_country in current:
                current.remove(clicked_country)
            else:
                if len(current) < 8:
                    current.append(clicked_country)
                else:
                    st.toast("⚠️ Maximum 8 countries. Remove one first.", icon="⚠️")
            st.session_state.selected_countries = current
            # Invalidate cached recession periods when selection changes
            st.session_state.recession_periods = {}
            st.rerun()

# ----------------------------
# Multiselect (synced with map)
# ----------------------------
col_sel, col_clear = st.columns([5, 1])
with col_sel:
    multiselect_val = st.multiselect(
        "Selected countries (also editable here)",
        ALL_COUNTRIES,
        default=st.session_state.selected_countries,
        key="country_multiselect",
        max_selections=8,
    )
with col_clear:
    st.write("")
    st.write("")
    if st.button("Clear all", use_container_width=True):
        st.session_state.selected_countries = []
        st.session_state.recession_periods = {}
        st.rerun()

# Sync multiselect → session state
if sorted(multiselect_val) != sorted(st.session_state.selected_countries):
    st.session_state.selected_countries = multiselect_val
    st.session_state.recession_periods = {}
    st.rerun()

selected_countries = st.session_state.selected_countries

# Show selected country chips
if selected_countries:
    chips_html = " ".join(
        f'<span class="country-chip selected-chip">{FLAG_MAP.get(c,"🌍")} {c}</span>'
        for c in selected_countries
    )
    st.markdown(chips_html, unsafe_allow_html=True)
else:
    st.info("👆 Click countries on the map or use the multiselect above to get started.")

# ----------------------------
# Economic Charts Section
# ----------------------------
if selected_countries and selected_indicators:
    st.markdown('<div class="section-header">📈 Economic Indicators</div>', unsafe_allow_html=True)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, country in enumerate(selected_countries):
        status_text.text(f"Loading {country}...")

        flag = FLAG_MAP.get(country, "🌍")
        st.subheader(f"{flag} {country}")

        # Always fetch GDP first for recession shading
        gdp_key = (country, "Real GDP")
        if country not in st.session_state.recession_periods:
            if gdp_key in COUNTRY_INDICATOR_MAP:
                gdp_df = fetch_fred_data(
                    COUNTRY_INDICATOR_MAP[gdp_key],
                    str(start_date), str(end_date), fred_api_key
                )
                if not gdp_df.empty:
                    st.session_state.recession_periods[country] = detect_recessions(gdp_df["value"])
                else:
                    st.session_state.recession_periods[country] = []
            else:
                st.session_state.recession_periods[country] = []

        recessions = st.session_state.recession_periods.get(country, [])

        # Render indicator charts in columns
        available_indicators = [
            ind for ind in selected_indicators
            if (country, ind) in COUNTRY_INDICATOR_MAP
        ]

        if not available_indicators:
            st.warning(f"No selected indicators available for {country}.")
        else:
            cols = st.columns(min(2, len(available_indicators)))
            for j, indicator in enumerate(available_indicators):
                series_id = COUNTRY_INDICATOR_MAP[(country, indicator)]
                df = fetch_fred_data(series_id, str(start_date), str(end_date), fred_api_key)

                with cols[j % 2]:
                    if df.empty:
                        st.warning(f"No data: {indicator} ({series_id})")
                        continue

                    # Cache latest value
                    latest_val = df["value"].iloc[-1]
                    prev_val = df["value"].iloc[-2] if len(df) > 1 else latest_val
                    delta = latest_val - prev_val
                    st.session_state.latest_values[(country, indicator)] = latest_val

                    fig = plot_indicator(df, f"{country} — {indicator}", recessions)
                    st.plotly_chart(fig, use_container_width=True)

                    st.metric(
                        label=f"Latest {indicator}",
                        value=f"{latest_val:.2f}",
                        delta=f"{delta:+.2f} vs prior period"
                    )

        # Recession status badge
        if recessions:
            last_rec_end = max(e for _, e in recessions)
            months_since = (pd.Timestamp(end_date) - last_rec_end).days / 30
            if months_since < 6:
                st.markdown('<span class="recession-badge">⚠️ RECENT RECESSION DETECTED</span>', unsafe_allow_html=True)

        st.markdown("---")
        progress_bar.progress((i + 1) / len(selected_countries))

    status_text.empty()
    progress_bar.empty()

# ----------------------------
# AI Assistant Section
# ----------------------------
if selected_countries:
    st.markdown('<div class="section-header">🤖 AI Economic Assistant</div>', unsafe_allow_html=True)

    def build_context():
        lines = ["Current economic data by country:"]
        for (country, indicator), val in st.session_state.latest_values.items():
            lines.append(f"  {country} — {indicator}: {val:.2f}")
        return "\n".join(lines)

    def ask_deepseek(prompt, context, api_key):
        if not api_key:
            return "DeepSeek API key not provided. Add it in the sidebar to enable AI features."
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert economist. Be concise and precise."},
                {"role": "user", "content": f"{context}\n\nQuestion: {prompt}"}
            ],
            "temperature": 0.3,
            "max_tokens": 600,
        }
        try:
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                              json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {e}"

    ai_tab1, ai_tab2 = st.tabs(["💬 Ask Questions", "📊 Auto Analysis"])

    with ai_tab1:
        if deepseek_api_key:
            user_query = st.text_area("Ask anything about the economic data:", height=90,
                                       placeholder="e.g. Which country shows the highest recession risk right now?")
            if st.button("Get Answer ›", type="primary") and user_query:
                with st.spinner("Analyzing..."):
                    answer = ask_deepseek(user_query, build_context(), deepseek_api_key)
                    st.success(answer)
        else:
            st.info("💡 Add a DeepSeek API key in the sidebar to enable the AI assistant.")

    with ai_tab2:
        if deepseek_api_key:
            if st.button("🔍 Analyze Recession Risk Across All Selected Countries", type="primary"):
                with st.spinner("Generating analysis..."):
                    prompt = """Based on the economic data, provide:
1. Recession risk level (Low/Medium/High) for each country
2. The single most concerning indicator per country
3. A one-sentence overall outlook
Be concise."""
                    answer = ask_deepseek(prompt, build_context(), deepseek_api_key)
                    st.info(answer)
        else:
            st.info("💡 Add a DeepSeek API key in the sidebar to enable auto-analysis.")

# ----------------------------
# News Section
# ----------------------------
if selected_countries:
    st.markdown('<div class="section-header">📰 Latest Economic News</div>', unsafe_allow_html=True)

    news_source = st.radio(
        "News source",
        ["Google News RSS (Free)", "NewsAPI (requires key)"],
        horizontal=True,
    )

    @st.cache_data(ttl=1800)
    def get_rss_news(country, query="recession economy"):
        q = f"{query} {country}".replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(url)
            return [
                {
                    "title": e.title,
                    "link": e.link,
                    "published": e.get("published", ""),
                    "source": e.get("source", {}).get("title", "Google News"),
                }
                for e in feed.entries[:8]
            ]
        except:
            return []

    @st.cache_data(ttl=1800)
    def get_newsapi_news(country, api_key):
        url = "https://newsapi.org/v2/everything"
        params = {"q": f"recession economy {country}", "language": "en",
                  "sortBy": "relevancy", "pageSize": 8, "apiKey": api_key}
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if data.get("status") == "ok":
                return [
                    {
                        "title": a["title"],
                        "link": a["url"],
                        "published": a["publishedAt"][:10],
                        "source": a["source"]["name"],
                    }
                    for a in data["articles"]
                ]
        except:
            pass
        return []

    news_cols = st.columns(min(3, len(selected_countries)))
    for idx, country in enumerate(selected_countries):
        with news_cols[idx % 3]:
            flag = FLAG_MAP.get(country, "🌍")
            with st.expander(f"{flag} {country} news"):
                with st.spinner("Fetching..."):
                    if news_source == "NewsAPI (requires key)" and newsapi_key:
                        articles = get_newsapi_news(country, newsapi_key) or get_rss_news(country)
                    else:
                        articles = get_rss_news(country)

                    if articles:
                        for a in articles:
                            st.markdown(f"**[{a['title']}]({a['link']})**")
                            st.caption(f"📌 {a['source']} · {a['published']}")
                            st.markdown("<hr style='border:1px solid #1f2937;margin:6px 0'>",
                                        unsafe_allow_html=True)
                    else:
                        st.write("No articles found.")

# ----------------------------
# Sidebar: Help & Debug
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("## ℹ️ How to Use")
st.sidebar.markdown("""
1. Enter your **FRED API key** (required)
2. **Click countries on the map** or use the dropdown
3. Select indicators & date range
4. Charts load with red recession shading
5. Optionally add **DeepSeek** & **NewsAPI** keys
6. Ask the AI about the data

**Recession shading** = 2 consecutive quarters of negative GDP growth  
**Data source:** Federal Reserve Economic Data (FRED)  
**Refresh:** Hourly cache
""")

with st.sidebar.expander("🔧 Debug"):
    st.write(f"FRED key: {'✅' if fred_api_key else '❌'}")
    st.write(f"DeepSeek key: {'✅' if deepseek_api_key else '❌'}")
    st.write(f"NewsAPI key: {'✅' if newsapi_key else '❌'}")
    st.write(f"Countries selected: {len(selected_countries)}")
    st.write(f"Indicators selected: {len(selected_indicators)}")
    st.write(f"Cached values: {len(st.session_state.latest_values)}")
