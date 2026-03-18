import streamlit as st
import yfinance as yf
import feedparser
from openai import OpenAI
import os
import time

# ==========================================
# 1. PAGE CONFIGURATION & UI SETUP
# ==========================================
st.set_page_config(
    page_title="Macro-Risk Intelligence Hub", 
    page_icon="🌍", 
    layout="wide"
)

st.title("🌍 Macro-Risk Intelligence Hub")
st.markdown("Live macro-economic data, energy commodities, and geopolitical news analysis.")

# Sidebar for secure API Key entry
st.sidebar.title("⚙️ Configuration")
api_key = st.sidebar.text_input("DeepSeek API Key", type="password")

# Fallback: first environment variable, then Streamlit secrets (for cloud)
if not api_key:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except:
        pass

if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Initialize session state for tracking analysis progress
if "analysis_in_progress" not in st.session_state:
    st.session_state.analysis_in_progress = False
if "last_analysis_type" not in st.session_state:
    st.session_state.last_analysis_type = None
if "cached_market_data" not in st.session_state:
    st.session_state.cached_market_data = None
if "cached_news_data" not in st.session_state:
    st.session_state.cached_news_data = None

# Manual refresh button (clears cache)
col_refresh, _ = st.sidebar.columns([1, 3])
with col_refresh:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.session_state.cached_market_data = None
        st.session_state.cached_news_data = None
        st.success("Cache cleared! Next analysis will fetch fresh data.")

# ==========================================
# 2. DATA GATHERING FUNCTIONS (with caching)
# ==========================================
@st.cache_data(ttl=3600, show_spinner="Fetching market data...")
def get_market_data():
    """Fetch current commodity prices using yfinance."""
    try:
        tickers = "CL=F NG=F HG=F ^GSPC"
        data = yf.Tickers(tickers)
        prices = []
        for ticker in ["CL=F", "NG=F", "HG=F", "^GSPC"]:
            # Use history which is more reliable than .info
            hist = data.tickers[ticker].history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                prices.append(f"{ticker}: ${price:.2f}")
            else:
                prices.append(f"{ticker}: N/A")
        return " | ".join(prices)
    except Exception as e:
        st.warning(f"⚠️ Market data fetch failed: {e}. Using cached data if available.")
        return "Market data currently unavailable"

@st.cache_data(ttl=600, show_spinner="Fetching latest news...")
def get_global_news():
    """Fetch headlines from reliable RSS feeds."""
    # Updated feeds: Reuters Energy, OilPrice, BBC Technology (more reliable)
    feeds = [
        "https://www.reuters.com/arc/outboundfeeds/en-us/?outputType=xml",  # Reuters main feed
        "https://oilprice.com/rss/main",
        "http://feeds.bbci.co.uk/news/technology/rss.xml"
    ]
    headlines = []
    try:
        for url in feeds:
            feed = feedparser.parse(url)
            # If feed fails, feed.entries may be empty; we continue
            for entry in feed.entries[:2]:
                headlines.append(f"- {entry.title}")
        if not headlines:
            return "No news headlines available at this time."
        return "\n".join(headlines)
    except Exception as e:
        st.warning(f"⚠️ News fetch failed: {e}. Using cached data if available.")
        return "News feed unavailable"

# ==========================================
# 3. DEEPSEEK AI ANALYSIS
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
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3, 
            max_tokens=1500  # Increased for more detailed briefings
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"**Analysis failed:** {e}"

# ==========================================
# 4. INTERACTIVE DASHBOARD UI
# ==========================================
st.subheader("Select an Analysis Module:")

# Disable buttons if analysis is in progress
button_disabled = st.session_state.analysis_in_progress

# Row 1 of Buttons
col1, col2, col3, col4 = st.columns(4)
analysis_type = None

with col1:
    if st.button("📊 Executive Macro", use_container_width=True, disabled=button_disabled):
        analysis_type = "general"
with col2:
    if st.button("🛢️ Energy & Maritime", use_container_width=True, disabled=button_disabled):
        analysis_type = "energy"
with col3:
    if st.button("🌎 LATAM/Caribbean Risk", use_container_width=True, disabled=button_disabled):
        analysis_type = "regional"
with col4:
    if st.button("⚙️ Tech & Digitalization", use_container_width=True, disabled=button_disabled):
        analysis_type = "tech"

# Row 2 of Buttons
col5, col6, col7, col8 = st.columns(4)

with col5:
    if st.button("📦 Warehouse Ops", use_container_width=True, disabled=button_disabled):
        analysis_type = "warehouse"
with col6:
    if st.button("📋 PM Risk Assessment", use_container_width=True, disabled=button_disabled):
        analysis_type = "pm_risk"
with col7:
    if st.button("🪙 Crypto & Digital Assets", use_container_width=True, disabled=button_disabled):
        analysis_type = "crypto"
with col8:
    if st.button("🏛️ Geopolitical Power", use_container_width=True, disabled=button_disabled):
        analysis_type = "power_structures"

# Execute analysis when a button is clicked
if analysis_type and not st.session_state.analysis_in_progress:
    if not api_key:
        st.error("⚠️ Please enter your DeepSeek API Key in the sidebar to run the analysis.")
    else:
        st.session_state.analysis_in_progress = True
        st.session_state.last_analysis_type = analysis_type
        
        with st.spinner("Gathering live intelligence and analyzing... ⏳"):
            # Fetch data (cached)
            market_data = get_market_data()
            news_data = get_global_news()
            
            # Store in session state for later export
            st.session_state.cached_market_data = market_data
            st.session_state.cached_news_data = news_data
            
            # Display the raw data feed
            st.markdown("### 📡 Live Data Feed")
            st.info(f"**Commodities:** {market_data}")
            
            # Show news headlines in an expander for transparency
            with st.expander("📰 View Raw News Headlines"):
                st.text(news_data)
            
            # Generate and display the AI briefing
            st.markdown("### 🧠 Strategic Briefing")
            report = analyze_with_deepseek(analysis_type, market_data, news_data)
            st.markdown(report)  # Use markdown to render bullet points
            
            # Add download button for the briefing
            st.download_button(
                label="📥 Download Briefing as Text",
                data=report,
                file_name=f"macro_briefing_{analysis_type}_{int(time.time())}.md",
                mime="text/markdown"
            )
        
        st.session_state.analysis_in_progress = False
        st.rerun()  # Re-run to re-enable buttons

# If analysis just completed, show a success message (optional)
if st.session_state.get("last_analysis_type") and not st.session_state.analysis_in_progress:
    st.success("✅ Analysis complete. You can run another module or refresh data.")
    # Clear last type to avoid persistent message
    st.session_state.last_analysis_type = None
