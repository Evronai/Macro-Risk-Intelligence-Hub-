import streamlit as st
import yfinance as yf
import feedparser
from openai import OpenAI
import os
import time
import requests
import concurrent.futures
from typing import Dict, List, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Macro-Risk Intelligence Hub",
    page_icon="🌍",
    layout="wide"
)

# ==========================================
# 2. SOURCE REGISTRY (100+ FREE SOURCES)
# ==========================================
ALL_SOURCES = [
    # ----- COMMODITIES & ENERGY (20 sources) -----
    {"name": "Crude Oil (WTI)", "type": "yfinance", "symbol": "CL=F", "category": "Energy"},
    {"name": "Natural Gas", "type": "yfinance", "symbol": "NG=F", "category": "Energy"},
    {"name": "Copper", "type": "yfinance", "symbol": "HG=F", "category": "Metals"},
    {"name": "Gold", "type": "yfinance", "symbol": "GC=F", "category": "Metals"},
    {"name": "Silver", "type": "yfinance", "symbol": "SI=F", "category": "Metals"},
    {"name": "Platinum", "type": "yfinance", "symbol": "PL=F", "category": "Metals"},
    {"name": "Wheat", "type": "yfinance", "symbol": "ZW=F", "category": "Agriculture"},
    {"name": "Corn", "type": "yfinance", "symbol": "ZC=F", "category": "Agriculture"},
    {"name": "Soybeans", "type": "yfinance", "symbol": "ZS=F", "category": "Agriculture"},
    {"name": "Coffee", "type": "yfinance", "symbol": "KC=F", "category": "Agriculture"},
    {"name": "Sugar", "type": "yfinance", "symbol": "SB=F", "category": "Agriculture"},
    {"name": "Cotton", "type": "yfinance", "symbol": "CT=F", "category": "Agriculture"},
    {"name": "Live Cattle", "type": "yfinance", "symbol": "LE=F", "category": "Agriculture"},
    {"name": "Lean Hogs", "type": "yfinance", "symbol": "HE=F", "category": "Agriculture"},
    {"name": "Brent Oil", "type": "yfinance", "symbol": "BZ=F", "category": "Energy"},
    {"name": "Heating Oil", "type": "yfinance", "symbol": "HO=F", "category": "Energy"},
    {"name": "RBOB Gasoline", "type": "yfinance", "symbol": "RB=F", "category": "Energy"},
    {"name": "Carbon Emissions", "type": "yfinance", "symbol": "CFI=F", "category": "Energy"},
    {"name": "Uranium", "type": "yfinance", "symbol": "URAXF", "category": "Energy"},
    {"name": "Lithium", "type": "yfinance", "symbol": "LIT", "category": "Metals"},

    # ----- ECONOMIC INDICATORS (25 sources) -----
    {"name": "US GDP", "type": "fred", "series_id": "GDP", "category": "Economic"},
    {"name": "US Unemployment Rate", "type": "fred", "series_id": "UNRATE", "category": "Economic"},
    {"name": "US CPI", "type": "fred", "series_id": "CPIAUCSL", "category": "Economic"},
    {"name": "US PPI", "type": "fred", "series_id": "PPIACO", "category": "Economic"},
    {"name": "US Fed Funds Rate", "type": "fred", "series_id": "FEDFUNDS", "category": "Monetary"},
    {"name": "US 10-Year Treasury", "type": "yfinance", "symbol": "^TNX", "category": "Monetary"},
    {"name": "US 2-Year Treasury", "type": "yfinance", "symbol": "^IRX", "category": "Monetary"},
    {"name": "US Dollar Index", "type": "yfinance", "symbol": "DX-Y.NYB", "category": "Currency"},
    {"name": "EUR/USD", "type": "yfinance", "symbol": "EURUSD=X", "category": "Currency"},
    {"name": "GBP/USD", "type": "yfinance", "symbol": "GBPUSD=X", "category": "Currency"},
    {"name": "USD/JPY", "type": "yfinance", "symbol": "JPY=X", "category": "Currency"},
    {"name": "USD/CNY", "type": "yfinance", "symbol": "CNY=X", "category": "Currency"},
    {"name": "Bitcoin", "type": "yfinance", "symbol": "BTC-USD", "category": "Crypto"},
    {"name": "Ethereum", "type": "yfinance", "symbol": "ETH-USD", "category": "Crypto"},
    {"name": "S&P 500", "type": "yfinance", "symbol": "^GSPC", "category": "Equities"},
    {"name": "Dow Jones", "type": "yfinance", "symbol": "^DJI", "category": "Equities"},
    {"name": "NASDAQ", "type": "yfinance", "symbol": "^IXIC", "category": "Equities"},
    {"name": "VIX", "type": "yfinance", "symbol": "^VIX", "category": "Volatility"},
    {"name": "China PMI", "type": "tradingeconomics", "country": "china", "indicator": "pmi", "category": "Economic"},
    {"name": "Eurozone GDP", "type": "tradingeconomics", "country": "eurozone", "indicator": "gdp", "category": "Economic"},
    {"name": "Japan CPI", "type": "tradingeconomics", "country": "japan", "indicator": "cpi", "category": "Economic"},
    {"name": "UK Unemployment", "type": "tradingeconomics", "country": "united-kingdom", "indicator": "unemployment-rate", "category": "Economic"},
    {"name": "Brazil Interest Rate", "type": "tradingeconomics", "country": "brazil", "indicator": "interest-rate", "category": "Monetary"},
    {"name": "India GDP", "type": "tradingeconomics", "country": "india", "indicator": "gdp", "category": "Economic"},
    {"name": "Australia CPI", "type": "tradingeconomics", "country": "australia", "indicator": "cpi", "category": "Economic"},

    # ----- NEWS RSS FEEDS (30 sources) -----
    {"name": "Reuters Business", "type": "rss", "url": "https://www.reuters.com/arc/outboundfeeds/en-us/?outputType=xml", "category": "News"},
    {"name": "Reuters Energy", "type": "rss", "url": "https://www.reuters.com/arc/outboundfeeds/en-us/country/usa/sector/energy/?outputType=xml", "category": "News"},
    {"name": "Reuters Commodities", "type": "rss", "url": "https://www.reuters.com/arc/outboundfeeds/en-us/country/usa/sector/commodities/?outputType=xml", "category": "News"},
    {"name": "BBC News", "type": "rss", "url": "http://feeds.bbci.co.uk/news/rss.xml", "category": "News"},
    {"name": "BBC Business", "type": "rss", "url": "http://feeds.bbci.co.uk/news/business/rss.xml", "category": "News"},
    {"name": "BBC Technology", "type": "rss", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "category": "News"},
    {"name": "BBC World", "type": "rss", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "category": "News"},
    {"name": "The Guardian Business", "type": "rss", "url": "https://www.theguardian.com/business/rss", "category": "News"},
    {"name": "The Guardian Economics", "type": "rss", "url": "https://www.theguardian.com/business/economics/rss", "category": "News"},
    {"name": "The Guardian Environment", "type": "rss", "url": "https://www.theguardian.com/environment/rss", "category": "News"},
    {"name": "WSJ Markets", "type": "rss", "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "category": "News"},
    {"name": "WSJ US Business", "type": "rss", "url": "https://feeds.a.dj.com/rss/RSSWSJS.xml", "category": "News"},
    {"name": "FT World", "type": "rss", "url": "https://www.ft.com/world?format=rss", "category": "News"},
    {"name": "FT Commodities", "type": "rss", "url": "https://www.ft.com/commodities?format=rss", "category": "News"},
    {"name": "FT Energy", "type": "rss", "url": "https://www.ft.com/energy?format=rss", "category": "News"},
    {"name": "Bloomberg Markets", "type": "rss", "url": "https://feeds.bloomberg.com/markets/news.rss", "category": "News"},
    {"name": "Bloomberg Economics", "type": "rss", "url": "https://feeds.bloomberg.com/economics/news.rss", "category": "News"},
    {"name": "Bloomberg Politics", "type": "rss", "url": "https://feeds.bloomberg.com/politics/news.rss", "category": "News"},
    {"name": "CNBC World News", "type": "rss", "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "category": "News"},
    {"name": "CNBC Energy", "type": "rss", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19836768", "category": "News"},
    {"name": "OilPrice.com", "type": "rss", "url": "https://oilprice.com/rss/main", "category": "News"},
    {"name": "MarineLink", "type": "rss", "url": "https://www.marinelink.com/news/rss", "category": "News"},
    {"name": "gCaptain", "type": "rss", "url": "https://gcaptain.com/feed/", "category": "News"},
    {"name": "Hellenic Shipping News", "type": "rss", "url": "https://www.hellenicshippingnews.com/feed/", "category": "News"},
    {"name": "TradeWinds", "type": "rss", "url": "https://www.tradewindsnews.com/arc/outboundfeeds/rss/", "category": "News"},
    {"name": "Lloyd's List", "type": "rss", "url": "https://lloydslist.maritimeintelligence.informa.com/~/media/feed/rss/lloydslist", "category": "News"},
    {"name": "Splash 24/7", "type": "rss", "url": "https://splash247.com/feed/", "category": "News"},
    {"name": "Seatrade Maritime", "type": "rss", "url": "https://www.seatrade-maritime.com/rss.xml", "category": "News"},
    {"name": "Mining.com", "type": "rss", "url": "https://www.mining.com/feed/", "category": "News"},
    {"name": "Al Jazeera Business", "type": "rss", "url": "https://www.aljazeera.com/xml/rss/business.xml", "category": "News"},

    # ----- GEOPOLITICAL & RISK (15 sources) -----
    {"name": "ACLED Conflict Data", "type": "api", "url": "https://api.acleddata.com/acled/read", "category": "Geopolitical"},
    {"name": "GDELT", "type": "api", "url": "https://api.gdeltproject.org/api/v2/summary/summary", "category": "Geopolitical"},
    {"name": "REST Countries API", "type": "api", "url": "https://restcountries.com/v3.1/all", "category": "Geopolitical"},
    {"name": "World Bank Country Data", "type": "api", "url": "https://api.worldbank.org/v2/country", "category": "Geopolitical"},
    {"name": "Nager.Date (Holidays)", "type": "api", "url": "https://date.nager.at/api/v3/publicholidays/2026/US", "category": "Geopolitical"},
    {"name": "Fragile States Index", "type": "csv", "url": "https://fragilestatesindex.org/data/", "category": "Geopolitical"},
    {"name": "Transparency CPI", "type": "csv", "url": "https://www.transparency.org/en/cpi/2023", "category": "Geopolitical"},
    {"name": "Heritage Economic Freedom", "type": "csv", "url": "https://www.heritage.org/index/explore", "category": "Geopolitical"},
    {"name": "UNDP HDI", "type": "csv", "url": "https://hdr.undp.org/data-center", "category": "Geopolitical"},
    {"name": "UNHCR Refugee Data", "type": "api", "url": "https://api.unhcr.org/", "category": "Geopolitical"},
    {"name": "IOM Migration Data", "type": "api", "url": "https://api.iom.int/", "category": "Geopolitical"},
    {"name": "ND-GAIN Climate Risk", "type": "csv", "url": "https://gain.nd.edu/our-work/country-index/download-data/", "category": "Geopolitical"},
    {"name": "World Bank Climate", "type": "api", "url": "https://climateknowledgeportal.worldbank.org/api", "category": "Geopolitical"},
    {"name": "USGS Earthquakes", "type": "api", "url": "https://earthquake.usgs.gov/fdsnws/event/1/query", "category": "Geopolitical"},
    {"name": "NOAA Climate Data", "type": "api", "url": "https://www.ncdc.noaa.gov/cdo-web/api/v2/data", "category": "Geopolitical"},
]

# ==========================================
# 3. DATA SOURCE MANAGER
# ==========================================
class DataSourceManager:
    def __init__(self, sources: List[Dict]):
        self.sources = sources
        self.cache = {}
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_source(self, source: Dict) -> Dict:
        try:
            if source["type"] == "yfinance":
                return self._fetch_yfinance(source)
            elif source["type"] == "rss":
                return self._fetch_rss(source)
            elif source["type"] == "fred":
                return self._fetch_fred(source)
            elif source["type"] == "tradingeconomics":
                return self._fetch_tradingeconomics(source)
            elif source["type"] == "api":
                return self._fetch_api(source)
            elif source["type"] == "csv":
                return {"note": "CSV source not fully implemented"}
            else:
                return {"error": f"Unknown type: {source['type']}"}
        except Exception as e:
            return {"error": str(e)}

    def _fetch_yfinance(self, source):
        ticker = yf.Ticker(source["symbol"])
        hist = ticker.history(period="2d")
        if hist.empty or len(hist) < 1:
            return {"error": "No data"}
        price = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) >= 2 else price
        change = price - prev
        return {"price": round(price, 2), "change": round(change, 2)}

    def _fetch_rss(self, source):
        try:
            resp = self.session.get(source["url"], timeout=10)
            feed = feedparser.parse(resp.content)
            headlines = []
            for entry in feed.entries[:3]:
                headlines.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", "Unknown")
                })
            return {"headlines": headlines}
        except Exception as e:
            return {"error": str(e)}

    def _fetch_fred(self, source):
        api_key = os.environ.get("FRED_API_KEY")
        if not api_key:
            return {"error": "FRED_API_KEY not set"}
        series = source["series_id"]
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1
        }
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json()
        observations = data.get("observations", [])
        if observations:
            value = observations[0]["value"]
            return {"value": value, "date": observations[0]["date"]}
        return {"error": "No observations"}

    def _fetch_tradingeconomics(self, source):
        api_key = os.environ.get("TRADINGECONOMICS_API_KEY")
        if not api_key:
            return {"error": "TRADINGECONOMICS_API_KEY not set"}
        return {"note": "Trading Economics not fully implemented"}

    def _fetch_api(self, source):
        try:
            resp = self.session.get(source["url"], timeout=10)
            if resp.status_code == 200:
                return {"data": resp.json()}
            else:
                return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def fetch_selected(self, selected_names: List[str], max_workers=10) -> Dict[str, Dict]:
        results = {}
        sources_to_fetch = [s for s in self.sources if s["name"] in selected_names]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {
                executor.submit(self.fetch_source, src): src["name"]
                for src in sources_to_fetch
            }
            for future in concurrent.futures.as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    data = future.result(timeout=30)
                    results[name] = data
                    self.cache[name] = (data, time.time())
                except Exception as e:
                    results[name] = {"error": f"Fetch timeout/error: {str(e)}"}
        return results

# ==========================================
# 4. INITIALISE SESSION STATE
# ==========================================
if "data_manager" not in st.session_state:
    st.session_state.data_manager = DataSourceManager(ALL_SOURCES)
if "fetched_results" not in st.session_state:
    st.session_state.fetched_results = None
if "analysis_in_progress" not in st.session_state:
    st.session_state.analysis_in_progress = False

# ==========================================
# 5. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.title("⚙️ Configuration")
    
    api_key = st.text_input("DeepSeek API Key", type="password")
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
        except:
            pass
    
    if api_key:
        st.success("✅ DeepSeek key set")
    else:
        st.warning("⚠️ DeepSeek key missing")
    
    st.markdown("---")
    
    st.subheader("📡 Data Sources")
    categories = list(set(s["category"] for s in ALL_SOURCES))
    selected_category = st.selectbox("Filter by category", ["All"] + sorted(categories))
    
    filtered_sources = ALL_SOURCES
    if selected_category != "All":
        filtered_sources = [s for s in ALL_SOURCES if s["category"] == selected_category]
    
    source_names = [s["name"] for s in filtered_sources]
    selected_sources = st.multiselect(
        "Select sources to fetch",
        options=source_names,
        default=source_names[:10]
    )
    
    update_freq = st.slider("Cache duration (seconds)", 300, 7200, 3600, step=300)
    
    if st.button("🔄 Fetch Selected Sources", use_container_width=True):
        with st.spinner(f"Fetching {len(selected_sources)} sources..."):
            results = st.session_state.data_manager.fetch_selected(selected_sources)
            st.session_state.fetched_results = results
            success_count = sum(1 for v in results.values() if "error" not in v)
            st.success(f"Fetched {success_count}/{len(selected_sources)} sources")
    
    st.markdown("---")
    st.caption("© 2026 Macro-Risk Intelligence")

# ==========================================
# 6. MAIN DASHBOARD UI
# ==========================================
st.title("🌍 Macro-Risk Intelligence Hub")
st.markdown("Real‑time economic, energy & geopolitical risk monitoring with 100+ sources")

if st.session_state.fetched_results:
    results = st.session_state.fetched_results
    
    categories_in_results = {}
    for src_name, data in results.items():
        src = next((s for s in ALL_SOURCES if s["name"] == src_name), None)
        cat = src["category"] if src else "Other"
        categories_in_results.setdefault(cat, []).append((src_name, data))
    
    st.subheader("📊 Key Commodity Prices")
    price_sources = [(name, data) for name, data in results.items() 
                     if isinstance(data, dict) and "price" in data]
    if price_sources:
        cols = st.columns(min(4, len(price_sources)))
        for i, (name, data) in enumerate(price_sources[:4]):
            with cols[i]:
                st.metric(
                    label=name,
                    value=f"${data['price']}",
                    delta=f"{data.get('change', 0):+.2f}"
                )
    else:
        st.info("No price data in current selection")
    
    for cat, items in categories_in_results.items():
        with st.expander(f"📁 {cat} Sources ({len(items)})", expanded=cat in ["Energy", "Economic"]):
            cols = st.columns(3)
            for i, (name, data) in enumerate(items):
                with cols[i % 3]:
                    st.markdown(f"**{name}**")
                    if "error" in data:
                        st.error(f"❌ {data['error']}")
                    elif "price" in data:
                        st.metric("Price", f"${data['price']}", delta=f"{data.get('change',0):+.2f}")
                    elif "headlines" in data:
                        for hl in data["headlines"][:2]:
                            st.markdown(f"- {hl['title'][:60]}...")
                    elif "value" in data:
                        st.write(f"Value: {data['value']} ({data.get('date', '')})")
                    elif "data" in data:
                        preview = str(data["data"])[:100] + "..."
                        st.text(preview)
                    else:
                        st.write("Data available")
    
    st.markdown("---")
    st.subheader("🧠 AI Analysis")
    
    analysis_type = st.selectbox(
        "Select analysis focus",
        ["General Macro", "Energy & Maritime", "LATAM/Caribbean Risk", 
         "Tech & Digitalization", "Warehouse Ops", "PM Risk", 
         "Crypto", "Geopolitical Power"]
    )
    
    prompt_map = {
        "General Macro": "general",
        "Energy & Maritime": "energy",
        "LATAM/Caribbean Risk": "regional",
        "Tech & Digitalization": "tech",
        "Warehouse Ops": "warehouse",
        "PM Risk": "pm_risk",
        "Crypto": "crypto",
        "Geopolitical Power": "power_structures"
    }
    
    if st.button("Generate Analysis", disabled=st.session_state.analysis_in_progress):
        if not api_key:
            st.error("DeepSeek API key required")
        elif not st.session_state.fetched_results:
            st.warning("Please fetch sources first")
        else:
            st.session_state.analysis_in_progress = True
            
            with st.status("Running analysis...", expanded=True) as status:
                st.write("📊 Preparing data...")
                market_lines = []
                news_lines = []
                for name, data in results.items():
                    if "error" in data:
                        continue
                    if "price" in data:
                        market_lines.append(f"{name}: ${data['price']} ({data.get('change',0):+.2f})")
                    elif "headlines" in data:
                        for hl in data["headlines"][:2]:
                            news_lines.append(f"- {hl['title']}")
                    elif "value" in data:
                        market_lines.append(f"{name}: {data['value']} ({data.get('date','')})")
                
                market_context = "\n".join(market_lines[:20])
                news_context = "\n".join(news_lines[:10])
                
                st.write("🧠 Calling DeepSeek API...")
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                
                system_prompt = (
                    "You are an elite Macro-Risk Analyst with over 10 years of combined experience. "
                    "Keep your briefing highly actionable, concise, and structured in markdown bullet points."
                )
                
                prompts = {
                    "general": "Provide an executive macro-economic and supply chain briefing. Highlight immediate red flags.",
                    "energy": "Analyze energy commodities, oil/gas pricing impacts, and downstream maritime/shipping logistics.",
                    "regional": "Analyze geopolitical stability, shipping chokepoints, and economic risk specifically impacting the Caribbean and LATAM.",
                    "tech": "Analyze macro trends in IT services, automation, and digitalization. How might these events force operational shifts?",
                    "warehouse": "Analyze from the perspective of a Warehouse Manager. Focus on procurement lead times, inventory holding costs, and facility resource allocation.",
                    "pm_risk": "Act as a Senior Project Manager. Identify potential scope, schedule, and cost risks for heavy-industry projects. Suggest mitigation.",
                    "crypto": "Analyze impact on digital assets and crypto markets. How do commodity shifts and geopolitical news influence decentralized finance?",
                    "power_structures": "Provide an advanced geopolitical analysis focusing on global power structures, central authority shifts, economic warfare."
                }
                
                user_prompt = f"Market Data:\n{market_context}\n\nLatest Intelligence:\n{news_context}\n\nTask: {prompts.get(prompt_map[analysis_type], prompts['general'])}"
                
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1500
                    )
                    report = response.choices[0].message.content
                except Exception as e:
                    report = f"**Analysis failed:** {e}"
                
                status.update(label="✅ Analysis complete", state="complete")
            
            st.markdown("### 🧠 Strategic Briefing")
            st.markdown(report)
            
            st.download_button(
                label="📥 Download Briefing",
                data=report,
                file_name=f"briefing_{int(time.time())}.md",
                mime="text/markdown"
            )
            
            st.session_state.analysis_in_progress = False
else:
    st.info("👈 Select sources in the sidebar and click 'Fetch Selected Sources' to begin.")
