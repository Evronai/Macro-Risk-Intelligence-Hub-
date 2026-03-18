import streamlit as st
import yfinance as yf
import feedparser
from openai import OpenAI
import os

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
st.sidebar.markdown("Enter your API key to activate the intelligence engine.")
api_key = st.sidebar.text_input("DeepSeek API Key", type="password")

# Fallback to local environment variables if available
if not api_key:
    api_key = os.getenv("DEEPSEEK_API_KEY")

if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ==========================================
# 2. DATA GATHERING FUNCTIONS
# ==========================================
@st.cache_data(ttl=3600) # Caches data for 1 hour so you don't over-ping Yahoo Finance
def get_market_data():
    try:
        tickers = "CL=F NG=F HG=F ^GSPC"
        data = yf.Tickers(tickers)
        market_summary = []
        for ticker in ["CL=F", "NG=F", "HG=F", "^GSPC"]:
            price = data.tickers[ticker].info.get("regularMarketPrice", "N/A")
            market_summary.append(f"{ticker}: ${price}")
        return " | ".join(market_summary)
    except Exception:
        return "Market data fetch failed."

@st.cache_data(ttl=3600)
def get_global_news():
    try:
        feeds = [
            "https://gcaptain.com/feed/", 
            "https://oilprice.com/rss/main", 
            "http://feeds.bbci.co.uk/news/technology/rss.xml"
        ]
        headlines = []
        for url in feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]: 
                headlines.append(f"- {entry.title}")
        return "\n".join(headlines)
    except Exception:
        return "News fetch failed."

# ==========================================
# 3. DEEPSEEK AI ANALYSIS
# ==========================================
def analyze_with_deepseek(prompt_type: str, market_context: str, news_context: str) -> str:
    system_prompt = (
        "You are an elite Macro-Risk Analyst specializing in IT services, "
        "digitalization, warehouse management, and energy logistics. "
        "Keep your briefing highly actionable, concise, and structured in markdown bullet points."
    )
    
    prompts = {
        'general': "Provide an executive macro-economic and supply chain briefing. Highlight immediate red flags for global operations.",
        'energy': "Analyze the data strictly focusing on energy commodities, oil/gas pricing impacts, and downstream maritime/shipping logistics.",
        'regional': "Analyze the data focusing on geopolitical stability, shipping chokepoints, and economic risk specifically impacting the Caribbean (focusing on Trinidad & Tobago) and LATAM.",
        'tech': "Analyze the data for macro trends in IT services, automation, and digitalization. How might these events force operational shifts in legacy warehouse or field environments?"
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
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Analysis failed: {e}"

# ==========================================
# 4. INTERACTIVE DASHBOARD UI
# ==========================================
st.subheader("Select an Analysis Module:")

# Create 4 columns for the interactive buttons
col1, col2, col3, col4 = st.columns(4)
analysis_type = None

with col1:
    if st.button("📊 Executive Macro Brief", use_container_width=True):
        analysis_type = "general"
with col2:
    if st.button("🛢️ Energy & Maritime", use_container_width=True):
        analysis_type = "energy"
with col3:
    if st.button("🌎 Caribbean & LATAM Risk", use_container_width=True):
        analysis_type = "regional"
with col4:
    if st.button("⚙️ Tech & Digitalization", use_container_width=True):
        analysis_type = "tech"

# Execute analysis when a button is clicked
if analysis_type:
    if not api_key:
        st.error("⚠️ Please enter your DeepSeek API Key in the sidebar to run the analysis.")
    else:
        with st.spinner("Gathering live intelligence and analyzing... ⏳"):
            market_data = get_market_data()
            news_data = get_global_news()
            
            # Display the raw data feed
            st.markdown("### 📡 Live Data Feed")
            st.info(f"**Commodities:** {market_data}")
            
            # Display the AI briefing
            st.markdown("### 🧠 Strategic Briefing")
            report = analyze_with_deepseek(analysis_type, market_data, news_data)
            st.write(report)
