import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pandas_datareader.data as web
from datetime import datetime, timedelta
import requests
import feedparser
import time

# ----------------------------
# Page configuration
# ----------------------------
st.set_page_config(
    page_title="Global Recession Tracker",
    page_icon="📉",
    layout="wide"
)

st.title("🌍 Global Recession Tracker with AI Assistant")
st.markdown("Track key economic indicators, identify recessions, and ask an AI about the data.")

# ----------------------------
# API Key Input Section in Sidebar
# ----------------------------
st.sidebar.header("🔑 API Configuration")

# FRED API Key (required)
fred_api_key = st.sidebar.text_input(
    "FRED API Key (required)",
    type="password",
    help="Get a free key from https://fred.stlouisfed.org/docs/api/api_key.html"
)

# DeepSeek API Key (optional)
deepseek_api_key = st.sidebar.text_input(
    "DeepSeek API Key (optional)",
    type="password",
    help="Get a key from https://platform.deepseek.com/"
)

# NewsAPI Key (optional)
newsapi_key = st.sidebar.text_input(
    "NewsAPI Key (optional)",
    type="password",
    help="Get a key from https://newsapi.org/"
)

# Check if FRED API key is provided
if not fred_api_key:
    st.warning("⚠️ Please enter your FRED API key in the sidebar to continue.")
    st.info("""
    ### How to get a FRED API key:
    1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
    2. Click "Request a FRED API Key"
    3. Fill out the simple form
    4. You'll receive your key via email instantly
    """)
    st.stop()

# ----------------------------
# Mapping: (country, indicator) -> FRED series ID
# ----------------------------
country_indicator_map = {
    ("United States", "Real GDP"): "GDPC1",
    ("United States", "Unemployment Rate"): "UNRATE",
    ("United States", "Inflation (CPI)"): "CPIAUCSL",
    ("United States", "Industrial Production"): "INDPRO",
    ("United States", "Yield Curve (10Y-2Y)"): "T10Y2Y",
    ("Canada", "Real GDP"): "NAEXKP01CAQ189S",
    ("Canada", "Unemployment Rate"): "LRUNTTTTCAM156S",
    ("Canada", "Inflation (CPI)"): "CPALCY01CAM661N",
    ("Canada", "Industrial Production"): "CANPRINTO01GPSAM",
    ("Japan", "Real GDP"): "JPNRGDPEXP",
    ("Japan", "Unemployment Rate"): "LRUNTTTTJPQ156S",
    ("Japan", "Inflation (CPI)"): "JPNCPIALLMINMEI",
    ("Japan", "Industrial Production"): "JPNPROINDMISMEI",
    ("Germany", "Real GDP"): "DEURGDP",
    ("Germany", "Unemployment Rate"): "LRUNTTTTDEQ156S",
    ("Germany", "Inflation (CPI)"): "DEUCPIALLMINMEI",
    ("Germany", "Industrial Production"): "DEUPROINDMISMEI",
    ("France", "Real GDP"): "FRARGDP",
    ("France", "Unemployment Rate"): "LRUNTTTTFRQ156S",
    ("France", "Inflation (CPI)"): "FRACPIALLMINMEI",
    ("France", "Industrial Production"): "FRAPROINDMISMEI",
    ("United Kingdom", "Real GDP"): "CLVMNACSCAB1GQUK",
    ("United Kingdom", "Unemployment Rate"): "LRUN64TTGBM156S",
    ("United Kingdom", "Inflation (CPI)"): "GBRCPIALLMINMEI",
    ("United Kingdom", "Industrial Production"): "GBRPRINTO01GYSAM",
    ("Italy", "Real GDP"): "ITARGDP",
    ("Italy", "Unemployment Rate"): "LRUNTTTTITQ156S",
    ("Italy", "Inflation (CPI)"): "ITACPIALLMINMEI",
    ("Italy", "Industrial Production"): "ITAPROINDMISMEI",
}

countries = sorted(set(k[0] for k in country_indicator_map.keys()))
indicators = sorted(set(k[1] for k in country_indicator_map.keys()))

# ----------------------------
# Helper functions (data fetching, recession detection, plotting)
# ----------------------------
@st.cache_data(ttl=3600)
def fetch_fred_data(series_id, start, end, api_key):
    """Fetch data from FRED using the provided API key."""
    try:
        df = web.DataReader(series_id, "fred", start, end, api_key=api_key)
        return df
    except Exception as e:
        st.warning(f"Failed to fetch {series_id}: {e}")
        return pd.DataFrame()

def detect_recessions(gdp_series):
    """Detect recessions from GDP data."""
    gdp_q = gdp_series.resample('Q').last().dropna()
    if len(gdp_q) < 2:
        return []
    growth = gdp_q.pct_change() * 100
    growth_annualized = ((1 + growth/100)**4 - 1) * 100
    negative = growth_annualized < 0
    recession_starts = negative & negative.shift(1) & ~negative.shift(1).fillna(False)
    recession_ends = ~negative & negative.shift(1) & negative.shift(2).fillna(False)
    start_dates = growth_annualized.index[recession_starts]
    end_dates = growth_annualized.index[recession_ends]
    if len(start_dates) > len(end_dates):
        end_dates = end_dates.append(pd.Index([growth_annualized.index[-1]]))
    recessions = [(start, end) for start, end in zip(start_dates, end_dates)]
    expanded = []
    for s, e in recessions:
        start_month = s - pd.DateOffset(months=2)
        end_month = e + pd.DateOffset(months=2)
        expanded.append((start_month, end_month))
    return expanded

def plot_indicator(data, title, recession_periods):
    """Create a Plotly figure with recession shading."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data.iloc[:, 0], mode='lines', name=title))
    for start, end in recession_periods:
        fig.add_vrect(x0=start, x1=end, fillcolor="red", opacity=0.2, layer="below", line_width=0)
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Value", hovermode="x unified", height=400)
    return fig

# ----------------------------
# AI Functions (DeepSeek)
# ----------------------------
def ask_deepseek(prompt, context, api_key):
    """Query the DeepSeek API."""
    if not api_key:
        return "DeepSeek API key not provided. Add it in the sidebar to enable AI features."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "You are an expert economist helping users understand recession indicators and economic data. Keep responses concise and informative."},
        {"role": "user", "content": f"{context}\n\nQuestion: {prompt}"}
    ]
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 500
    }
    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling DeepSeek API: {e}"

# ----------------------------
# News Functions (RSS + optional NewsAPI)
# ----------------------------
@st.cache_data(ttl=1800)
def get_rss_news(country, query="recession"):
    """Fetch news headlines from Google News RSS."""
    search_query = f"{query} {country}".replace(" ", "%20")
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "Unknown date"),
                "source": entry.get("source", {}).get("title", "Google News")
            })
        return articles
    except:
        return []

@st.cache_data(ttl=1800)
def get_newsapi_news(country, api_key, query="recession"):
    """Fetch news from NewsAPI."""
    if not api_key:
        return None
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{query} {country}",
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 10,
        "apiKey": api_key
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["status"] == "ok":
            articles = []
            for article in data["articles"]:
                articles.append({
                    "title": article["title"],
                    "link": article["url"],
                    "published": article["publishedAt"][:10],
                    "source": article["source"]["name"]
                })
            return articles
        else:
            return None
    except:
        return None

# ----------------------------
# Sidebar controls (after API keys)
# ----------------------------
st.sidebar.header("📊 Data Settings")

selected_countries = st.sidebar.multiselect(
    "Select countries", 
    countries, 
    default=["United States", "United Kingdom", "Germany"][:min(3, len(countries))]
)

selected_indicators = st.sidebar.multiselect(
    "Select indicators", 
    indicators, 
    default=["Real GDP", "Unemployment Rate", "Inflation (CPI)"]
)

today = datetime.today()
default_start = today - timedelta(days=10*365)
start_date = st.sidebar.date_input("Start date", default_start)
end_date = st.sidebar.date_input("End date", today)

if start_date >= end_date:
    st.sidebar.error("End date must be after start date.")
    st.stop()

# ----------------------------
# Main content: Economic charts
# ----------------------------
if "recession_periods" not in st.session_state:
    st.session_state.recession_periods = {}

# Progress indicator
if selected_countries and selected_indicators:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, country in enumerate(selected_countries):
        status_text.text(f"Loading data for {country}...")
        st.header(f"🇺🇳 {country}")
        
        for indicator in selected_indicators:
            key = (country, indicator)
            if key not in country_indicator_map:
                st.warning(f"Indicator '{indicator}' not available for {country}. Skipping.")
                continue

            series_id = country_indicator_map[key]
            df = fetch_fred_data(series_id, start_date, end_date, fred_api_key)

            if df.empty:
                st.warning(f"No data for {country} - {indicator} ({series_id})")
                continue

            if indicator == "Real GDP":
                recessions = detect_recessions(df.iloc[:, 0])
                st.session_state.recession_periods[country] = recessions
            else:
                recessions = st.session_state.recession_periods.get(country, [])

            fig = plot_indicator(df, f"{country} - {indicator}", recessions)
            st.plotly_chart(fig, use_container_width=True)

            latest = df.iloc[-1]
            st.metric(
                label=f"Latest {indicator}", 
                value=f"{latest.iloc[0]:.2f}",
                delta=None
            )

        st.markdown("---")
        progress_bar.progress((i + 1) / len(selected_countries))
    
    status_text.text("")
    progress_bar.empty()

# ----------------------------
# AI Assistant Section
# ----------------------------
if selected_countries:
    st.header("🤖 AI Economic Assistant")
    
    # Create tabs for different AI features
    ai_tab1, ai_tab2 = st.tabs(["💬 Ask Questions", "📊 Auto Analysis"])
    
    with ai_tab1:
        if deepseek_api_key:
            user_query = st.text_area("Ask anything about recessions, indicators, or the current economic situation:", height=100)
            if st.button("Get Answer", type="primary") and user_query:
                with st.spinner("Analyzing with DeepSeek AI..."):
                    # Build context from latest data
                    context_lines = ["Current economic data:"]
                    for country in selected_countries:
                        context_lines.append(f"\n{country}:")
                        for indicator in selected_indicators:
                            key = (country, indicator)
                            if key in country_indicator_map:
                                series_id = country_indicator_map[key]
                                df = fetch_fred_data(series_id, start_date, end_date, fred_api_key)
                                if not df.empty:
                                    latest_val = df.iloc[-1, 0]
                                    context_lines.append(f"  - {indicator}: {latest_val:.2f}")
                    
                    context = "\n".join(context_lines)
                    answer = ask_deepseek(user_query, context, deepseek_api_key)
                    st.success(answer)
        else:
            st.info("💡 Enter a DeepSeek API key in the sidebar to enable the AI assistant.")
    
    with ai_tab2:
        if deepseek_api_key:
            if st.button("🔍 Analyze Current Recession Risk", type="primary"):
                with st.spinner("Generating economic analysis..."):
                    # Build detailed context
                    context_lines = ["Current economic indicators by country:"]
                    for country in selected_countries:
                        context_lines.append(f"\n## {country}")
                        for indicator in selected_indicators:
                            key = (country, indicator)
                            if key in country_indicator_map:
                                series_id = country_indicator_map[key]
                                df = fetch_fred_data(series_id, start_date, end_date, fred_api_key)
                                if not df.empty:
                                    latest_val = df.iloc[-1, 0]
                                    # Add trend info
                                    if len(df) > 1:
                                        prev_val = df.iloc[-2, 0]
                                        trend = "increasing" if latest_val > prev_val else "decreasing"
                                        context_lines.append(f"  - {indicator}: {latest_val:.2f} ({trend})")
                                    else:
                                        context_lines.append(f"  - {indicator}: {latest_val:.2f}")
                    
                    context = "\n".join(context_lines)
                    prompt = """Based on the economic data provided, please provide:
1. A brief assessment of current recession risk for each country
2. The most concerning indicators
3. Any early warning signs
Keep it concise and accessible."""
                    
                    answer = ask_deepseek(prompt, context, deepseek_api_key)
                    st.info(answer)
        else:
            st.info("💡 Enter a DeepSeek API key in the sidebar to enable auto-analysis.")

# ----------------------------
# News Section
# ----------------------------
if selected_countries:
    st.header("📰 Latest Economic News")
    
    # News source selector
    news_source = st.radio(
        "News source",
        ["Google News RSS (Free)", "NewsAPI (if key provided)"],
        horizontal=True,
        key="news_source"
    )
    
    for country in selected_countries:
        with st.expander(f"📰 News about {country}"):
            with st.spinner(f"Fetching news for {country}..."):
                if news_source == "NewsAPI (if key provided)" and newsapi_key:
                    articles = get_newsapi_news(country, newsapi_key)
                    if articles is None:
                        st.warning("NewsAPI failed, showing RSS results instead.")
                        articles = get_rss_news(country)
                else:
                    articles = get_rss_news(country)
                
                if articles:
                    for art in articles:
                        st.markdown(f"### [{art['title']}]({art['link']})")
                        st.caption(f"📌 {art['source']} · 🕐 {art['published']}")
                        st.markdown("---")
                else:
                    st.write("No recent news articles found for this country.")

# ----------------------------
# Footer with instructions
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.header("ℹ️ How to Use")
st.sidebar.markdown("""
1. **Enter your FRED API key** (required) at the top of the sidebar
2. **Optional**: Add DeepSeek and NewsAPI keys for extra features
3. Select countries and indicators to track
4. View charts with automatic recession shading (red areas)
5. Ask the AI assistant questions about the data
6. Check latest news headlines

### About the data
- **Recession shading**: Two consecutive quarters of negative GDP growth
- **Data source**: Federal Reserve Economic Data (FRED)
- **Update frequency**: Data refreshes hourly
""")

# Debug info in expander (optional)
with st.sidebar.expander("🔧 Debug Info"):
    st.write(f"FRED API Key provided: {'✅' if fred_api_key else '❌'}")
    st.write(f"DeepSeek API Key provided: {'✅' if deepseek_api_key else '❌'}")
    st.write(f"NewsAPI Key provided: {'✅' if newsapi_key else '❌'}")
    st.write(f"Selected countries: {len(selected_countries)}")
    st.write(f"Selected indicators: {len(selected_indicators)}")
