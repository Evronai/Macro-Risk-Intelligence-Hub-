import streamlit as st
import yfinance as yf
import feedparser
from openai import OpenAI
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="Macro-Risk Intelligence Hub",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS for a professional look
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: #f8f9fa;
    }
    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', sans-serif;
    }
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
    }
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    /* Status messages */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=LOGO", width=150)  # Replace with your logo URL
    st.title("⚙️ Configuration")
    
    # API Key input
    api_key = st.text_input("DeepSeek API Key", type="password")
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
        except:
            pass
    
    # Status indicator
    if api_key:
        st.success("✅ API Key set")
    else:
        st.warning("⚠️ API Key missing")
    
    st.markdown("---")
    
    # Data sources info
    with st.expander("📡 Data Sources", expanded=False):
        st.write("**Commodities:** Yahoo Finance")
        st.write("**News:** Reuters, OilPrice, BBC")
    
    # Manual refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.cached_market_data = None
        st.session_state.cached_news_data = None
        st.success("Cache cleared! Next analysis will fetch fresh data.")
    
    st.markdown("---")
    st.caption("© 2026 Macro-Risk Intelligence")

# ==========================================
# 3. INITIALISE SESSION STATE
# ==========================================
if "analysis_in_progress" not in st.session_state:
    st.session_state.analysis_in_progress = False
if "last_analysis_type" not in st.session_state:
    st.session_state.last_analysis_type = None

# ==========================================
# 4. DATA FETCHING FUNCTIONS (with timeouts)
# ==========================================
def fetch_url_with_retries(url, timeout=5, retries=2):
    """Fetch URL content with retries and timeout."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner="Fetching market data...")
def get_market_data():
    """
    Fetch current commodity prices and daily changes.
    Returns a tuple: (price_dict, change_dict)
    """
    tickers = {
        "CL=F": "Crude Oil (WTI)",
        "NG=F": "Natural Gas",
        "HG=F": "Copper",
        "^GSPC": "S&P 500"
    }
    prices = {}
    changes = {}
    try:
        data = yf.Tickers(list(tickers.keys()))
        for symbol, label in tickers.items():
            hist = data.tickers[symbol].history(period="2d")  # need 2 days to compute change
            if not hist.empty and len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = price - prev_close
                prices[label] = round(price, 2)
                changes[label] = round(change, 2)
            else:
                prices[label] = None
                changes[label] = None
        return prices, changes
    except Exception as e:
        st.warning(f"⚠️ Market data fetch failed: {e}. Using cached data if available.")
        return {}, {}

@st.cache_data(ttl=600, show_spinner="Fetching latest news...")
def get_global_news():
    """Fetch headlines from reliable RSS feeds with timeouts."""
    feeds = [
        "https://www.reuters.com/arc/outboundfeeds/en-us/?outputType=xml",  # Reuters
        "https://oilprice.com/rss/main",
        "http://feeds.bbci.co.uk/news/technology/rss.xml"
    ]
    headlines = []
    for url in feeds:
        content = fetch_url_with_retries(url)
        if content:
            feed = feedparser.parse(content)
            for entry in feed.entries[:2]:
                headlines.append(f"- {entry.title}")
    if not headlines:
        return "No news headlines available at this time."
    return "\n".join(headlines)

# ==========================================
# 5. DEEPSEEK ANALYSIS FUNCTION
# ==========================================
def analyze_with_deepseek(prompt_type: str, market_context: str, news_context: str) -> str:
    system_prompt = (
        "You are an elite Macro-Risk Analyst with over 10 years of combined experience in "
        "operations, field work, warehouse management, energy logistics, and IT services. "
        "Keep your briefing highly actionable, concise, and structured in markdown bullet points."
    )
    
    prompts = {
        'general': "Provide an executive macro-economic and supply chain briefing. Highlight immediate red flags for global operations.",
        'energy': "Analyze the data strictly focusing on energy commodities, oil/gas pricing impacts, and downstream maritime/shipping logistics.",
        'regional': "Analyze the data focusing on geopolitical stability, shipping chokepoints, and economic risk specifically impacting the Caribbean (focusing on Trinidad & Tobago) and LATAM.",
        'tech': "Analyze the data for macro trends in IT services, automation, and digitalization. How might these events force operational shifts in legacy warehouse or field environments?",
        'warehouse': "Analyze the data from the perspective of a Warehouse and Inventory Operations Manager. Focus on how these macro trends will impact procurement lead times, inventory holding costs, and facility resource allocation.",
        'pm_risk': "Act as a Senior Project Manager. Evaluate the current data to identify potential scope, schedule, and cost risks for ongoing heavy-industry and logistics projects. Suggest mitigation strategies.",
        'crypto': "Analyze the data for its potential impact on digital assets and cryptocurrency markets. Focus on how traditional commodity shifts and geopolitical news might influence decentralized finance and algorithmic trading volatility.",
        'power_structures': "Provide an advanced geopolitical analysis focusing on global power structures. How do these current events indicate shifts in central authority, economic warfare, or systemic control over the sovereign supply chain?"
    }
    
    user_prompt = f"Market Data: {market_context}\nLatest Intelligence:\n{news_context}\n\nTask: {prompts.get(prompt_type, prompts['general'])}"

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"**Analysis failed:** {e}"

# ==========================================
# 6. MAIN DASHBOARD UI
# ==========================================
st.title("🌍 Macro-Risk Intelligence Hub")
st.markdown("Real‑time economic, energy & geopolitical risk monitoring")

# --- Live Data Metrics Row ---
prices, changes = get_market_data()
if prices:
    cols = st.columns(4)
    for i, (label, price) in enumerate(prices.items()):
        with cols[i]:
            delta = changes.get(label)
            delta_str = f"{delta:+.2f}" if delta is not None else None
            st.metric(label, f"${price}" if price else "N/A", delta=delta_str)
else:
    st.info("Market data temporarily unavailable")

st.markdown("---")

# --- Tabs for Analysis Modules ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive", 
    "🛢️ Energy & Maritime", 
    "🌎 Regional (LATAM/Caribbean)", 
    "📦 Operations", 
    "🏛️ Geopolitical"
])

analysis_type = None

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📈 Executive Macro Brief", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "general"
    with col_b:
        if st.button("⚙️ Tech & Digitalization", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "tech"

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🛢️ Energy Commodities", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "energy"

with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🌎 LATAM/Caribbean Risk", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "regional"

with tab4:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📦 Warehouse Ops", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "warehouse"
    with col_b:
        if st.button("📋 PM Risk Assessment", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "pm_risk"

with tab5:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🪙 Crypto & Digital Assets", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "crypto"
    with col_b:
        if st.button("🏛️ Power Structures", use_container_width=True, disabled=st.session_state.analysis_in_progress):
            analysis_type = "power_structures"

# ==========================================
# 7. EXECUTE ANALYSIS
# ==========================================
if analysis_type and not st.session_state.analysis_in_progress:
    if not api_key:
        st.error("⚠️ Please enter your DeepSeek API Key in the sidebar.")
    else:
        st.session_state.analysis_in_progress = True
        
        # Use st.status for detailed progress
        with st.status("🔍 Running analysis...", expanded=True) as status:
            st.write("📡 Fetching market data...")
            market_data_raw = get_market_data()
            # Format market data for the prompt
            market_summary = " | ".join([f"{k}: ${v}" for k, v in prices.items() if v is not None])
            
            st.write("📰 Fetching latest news...")
            news_data = get_global_news()
            
            st.write("🧠 Calling DeepSeek API...")
            report = analyze_with_deepseek(analysis_type, market_summary, news_data)
            
            status.update(label="✅ Analysis complete!", state="complete")
        
        # Display results
        st.markdown("### 📡 Live Data Feed")
        st.info(f"**Commodities:** {market_summary}")
        
        with st.expander("📰 Raw News Headlines"):
            st.text(news_data)
        
        st.markdown("### 🧠 Strategic Briefing")
        st.markdown(report)
        
        # Download button
        st.download_button(
            label="📥 Download Briefing as Markdown",
            data=report,
            file_name=f"briefing_{analysis_type}_{int(time.time())}.md",
            mime="text/markdown"
        )
        
        st.session_state.analysis_in_progress = False
        # No st.rerun() – UI updates naturally

# Optional: Show success message after completion
if st.session_state.get("last_analysis_type") and not st.session_state.analysis_in_progress:
    st.success("✅ Analysis complete. You can now run another module.")
    st.session_state.last_analysis_type = None
