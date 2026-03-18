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
# 2. SOURCE REGISTRY (90+ FREE SOURCES)
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
# 4. EXPANDED AI PROMPTS FUNCTION
# ==========================================
def analyze_with_deepseek(prompt_type: str, market_context: str, news_context: str, api_key: str) -> str:
    """
    Generate a strategic briefing using DeepSeek, with expanded prompts.
    """
    system_prompt = (
        "You are an elite Macro-Risk Analyst with over 15 years of combined experience in "
        "geopolitics, energy logistics, supply chain management, and financial markets. "
        "**IMPORTANT: The current date is 2026.** All analysis must be forward-looking, "
        "actionable, and grounded in the provided data. Use structured markdown with clear "
        "headings, bullet points, and where appropriate, tables. Be concise but comprehensive."
    )

    prompts = {
        'general': """
**Executive Macro-Economic & Supply Chain Briefing – 2026**

Analyze the provided market and news data to produce a high-level briefing for C-suite executives. Your response must include:

- **Global Economic Snapshot**: Key trends in growth, inflation, and monetary policy across major economies (US, Eurozone, China). Highlight divergences and potential spillovers.
- **Supply Chain Red Flags**: Immediate bottlenecks, port congestion, raw material shortages, or logistics disruptions. Quantify impacts where possible (e.g., "Copper prices up X% indicating...").
- **Energy & Commodity Outlook**: Critical price movements and their drivers (geopolitical, weather, demand shifts). Focus on oil, natural gas, and key industrial metals.
- **Risk Heatmap**: A bulleted list of top 5 macro risks for the next 6–12 months, each with a brief explanation and potential business impact.
- **Strategic Recommendations**: 3–4 actionable steps for multinational corporations to mitigate identified risks and seize opportunities.

Use a professional, decisive tone. Avoid generic statements; base insights strictly on the data provided.
""",
        'energy': """
**Energy & Maritime Analysis – 2026**

You are advising an energy trading desk and a shipping logistics team. Based on the data, deliver a detailed briefing covering:

- **Crude Oil & Natural Gas Price Drivers**: Analyze supply-side factors (OPEC+ decisions, US shale activity, Russian exports) and demand-side trends (global economic activity, weather, energy transition). Include price forecasts or scenarios where data supports.
- **Refined Products & Margins**: Cracks, diesel/gasoline spreads, and implications for downstream logistics.
- **Maritime & Shipping Impact**: How energy price volatility affects bunker fuel costs, vessel operating expenses, and shipping routes (especially LNG tankers, oil tankers). Highlight chokepoints (Strait of Hormuz, Panama Canal) and any reported disruptions.
- **Downstream Logistics**: Refinery utilization, inventory levels (crude, products), and potential bottlenecks in pipeline or rail networks.
- **Geopolitical Flashpoints**: Sanctions, conflicts, or political instability affecting energy supply chains. Focus on Russia-Ukraine, Middle East, and Venezuela/Iran.
- **Actionable Insights**: For a VP of Energy Procurement, what hedging strategies, contract renegotiations, or alternative sourcing options should be considered for H2 2026?

Structure your answer with clear headings and bullet points. Use data to support every claim.
""",
        'regional': """
**LATAM & Caribbean Geopolitical Risk Assessment – 2026**

Focus on Trinidad & Tobago, the wider Caribbean, and key Latin American economies (Brazil, Mexico, Argentina, Venezuela, Colombia). Your analysis must address:

- **Political Stability & Governance**: Recent elections, protests, or policy shifts that could impact business operations. Include corruption perceptions, rule of law trends, and social unrest risks.
- **Economic Vulnerability**: Currency volatility, inflation, debt levels, and reliance on commodity exports (oil, gas, minerals, agriculture). Highlight any IMF programs or default risks.
- **Shipping & Trade Chokepoints**: Assess risks to maritime routes (Panama Canal, Caribbean passages, Amazon River ports). Piracy, port strikes, or infrastructure bottlenecks.
- **Energy & Mining Sector Focus**: For Trinidad (LNG, petrochemicals), Guyana (oil boom), Venezuela (sanctions), Chile/Peru (copper), Brazil (mining, agribusiness). How do local dynamics affect global supply?
- **Social & Environmental Factors**: Climate change impacts (hurricanes, droughts), migration flows, and their effect on labor markets and social cohesion.
- **Risk Scenarios**: Develop two plausible scenarios for the region over the next 12 months (e.g., "Venezuela opens to foreign oil investment" vs. "Regional debt crisis") and their implications for multinational firms.
- **Recommendations**: For a regional operations director, what contingency plans, diversification strategies, or partnerships should be prioritized?

Use a structured format with numbered sections and bullet points. Reference specific countries and data points.
""",
        'tech': """
**Technology & Digitalization Macro Trends – 2026**

You are advising the CIO of a global logistics firm. Analyze how the provided data signals shifts in tech adoption, automation, and IT services. Address:

- **Automation & AI in Operations**: How are rising labor costs, supply chain volatility, or energy prices accelerating adoption of robotics and AI in warehouses, ports, and field operations? Cite any relevant news (e.g., new factory openings, labor disputes, tech investments).
- **IT Services & Cloud Demand**: Impact of geopolitical tensions (e.g., US-China tech war) on cloud infrastructure, data sovereignty, and IT outsourcing. Are there signs of regionalization of tech services?
- **Cybersecurity Risk Landscape**: Increased attacks on critical infrastructure (energy, logistics) – correlate with news events. What vulnerabilities do current macro trends create?
- **Digitalization of Supply Chains**: Adoption of blockchain for traceability, IoT for asset tracking, and digital twins. How are commodity price swings or trade policy changes influencing investment in these technologies?
- **Talent & Workforce**: Remote work trends, tech talent migration, and implications for hiring and retention in IT departments.
- **Strategic Recommendations**: For a global technology officer, what technology investments should be prioritized, delayed, or reconsidered in light of 2026's macro environment? Include specific areas (cybersecurity, AI, cloud).

Be specific and data-driven. Use examples from the news feeds where applicable.
""",
        'warehouse': """
**Warehouse & Inventory Operations Manager Briefing – 2026**

You are speaking directly to a senior warehouse and inventory manager. Translate the macro data into operational impacts and recommendations:

- **Procurement Lead Times**: Based on commodity price trends (metals, lumber, packaging) and news of supply disruptions, estimate changes in lead times for key inputs. Provide a table if possible:
  | Material | Current Trend | Expected Lead Time Impact |
  |----------|---------------|----------------------------|
  | Steel    | +5% price     | +2 weeks due to mill backlogs |
- **Inventory Holding Costs**: Rising interest rates (from economic data) increase carrying costs. Calculate the impact on cost of capital for inventory. Suggest optimal inventory levels (just-in-case vs. just-in-time).
- **Facility Resource Allocation**: Energy price volatility affects utility costs. Should the warehouse shift schedules to off-peak hours? Invest in solar? How do labor market trends (unemployment, wage pressures) affect staffing?
- **Transportation & Inbound Logistics**: Fuel surcharges, trucking availability, and port delays – correlate with news. Advise on carrier diversification or mode shifts (e.g., rail vs. truck).
- **Risk Mitigation**: Develop a contingency plan for a major disruption (e.g., port strike, energy blackout). What safety stock levels are prudent?
- **Action Items**: A checklist of 5 immediate actions for the next quarter.

Use practical language and quantify impacts wherever possible.
""",
        'pm_risk': """
**Senior Project Manager Risk Assessment – 2026**

You are managing large-scale infrastructure or industrial projects (e.g., refinery expansion, port development, mining operation). Analyze the data to identify and mitigate risks:

- **Scope Creep Risks**: How might geopolitical events (sanctions, new regulations) or commodity price swings force design changes? Provide examples.
- **Schedule Risks**: Supply chain delays for critical equipment (e.g., turbines, steel, semiconductors). Use news and price data to estimate potential delays. Create a simple risk matrix (Likelihood vs. Impact).
- **Cost Escalation**: Inflation in raw materials, labor, and energy. Quantify potential overruns. What contingency percentage is advisable?
- **Labor & Workforce**: Strikes, skilled labor shortages, or immigration policy changes affecting project staffing.
- **Financing & Currency**: Interest rate hikes (from economic data) increasing cost of capital. Currency volatility impacting imported equipment costs.
- **Mitigation Strategies**: For each top risk, propose concrete mitigation (e.g., advance procurement, dual sourcing, fixed-price contracts, modular construction).
- **Monitoring Recommendations**: Key indicators (KPIs) to track weekly to stay ahead of risks.

Structure your response as a formal risk assessment report with sections, tables, and clear bullet points.
""",
        'crypto': """
**Digital Assets & Crypto Market Analysis – 2026**

You are advising a crypto hedge fund. Analyze how traditional macro factors and news events are influencing digital assets:

- **Macro Drivers**: Correlation of Bitcoin/Ethereum with equities, commodities (especially gold), and the US dollar. How do interest rate expectations (from economic data) affect crypto as a risk asset or inflation hedge?
- **Regulatory News**: Track any mentions of crypto regulation in news feeds (SEC, EU MiCA, China bans). Assess potential market impact.
- **Institutional Adoption**: News of major companies adding crypto to balance sheets, banks offering custody, or ETF flows.
- **On-Chain & Sentiment Indicators**: While not directly in data, infer from price action and news sentiment (e.g., "fear" vs. "greed").
- **Energy & Mining**: Impact of energy prices on Bitcoin mining profitability and hash rate. Any news on mining migration?
- **Geopolitical Risk**: Use of crypto for sanctions evasion, capital flight from unstable regions. How do conflicts affect demand?
- **Outlook & Positioning**: Based on the above, provide a tactical outlook for the next 3–6 months. Recommend portfolio positioning (e.g., overweight Bitcoin, underweight altcoins, hedge with options).

Be analytical and data-backed. Avoid hype.
""",
        'power_structures': """
**Advanced Geopolitical Power Structures Analysis – 2026**

You are a geopolitical strategist advising a sovereign wealth fund. Analyze the data through the lens of shifting global power dynamics:

- **US-China Rivalry**: How do current events (trade wars, tech bans, military exercises) indicate escalation or de-escalation? Impact on global supply chains, technology decoupling, and financial systems.
- **Regional Power Shifts**: Rise of new blocs (BRICS+, SCO). Any news of currency de-dollarization, new trade pacts, or military alliances?
- **Energy as a Weapon**: How are energy-exporting nations (Russia, Saudi, Iran) using supply to exert influence? What does that mean for Europe, Asia, and energy security?
- **Economic Warfare**: Sanctions, export controls, and asset freezes. Analyze effectiveness and blowback. Are there signs of weaponized interdependence?
- **Systemic Control**: How are digital currencies, surveillance tech, and data localization reshaping state control over economies?
- **Fragile States & Proxy Conflicts**: Identify regions where state failure or proxy wars could disrupt global markets (e.g., Sahel, Horn of Africa, Myanmar).
- **Implications for Investors**: What sectors, regions, or asset classes are most exposed? Should portfolios tilt toward hard assets, defense, or commodities?

Provide a deep, nuanced analysis with historical context and forward-looking scenarios. Use structured sections and bullet points.
"""
    }

    user_prompt = f"""**Data for 2026 Analysis**
Market & Economic Data:
{market_context}

Latest Intelligence (News):
{news_context}

**Analysis Task:**
{prompts.get(prompt_type, prompts['general'])}"""

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"**Analysis failed:** {e}"

# ==========================================
# 5. INITIALISE SESSION STATE
# ==========================================
if "data_manager" not in st.session_state:
    st.session_state.data_manager = DataSourceManager(ALL_SOURCES)
if "fetched_results" not in st.session_state:
    st.session_state.fetched_results = None
if "analysis_in_progress" not in st.session_state:
    st.session_state.analysis_in_progress = False

# ==========================================
# 6. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # API Key input (DeepSeek)
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
    
    # Source selection
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
# 7. PROFESSIONAL DASHBOARD UI
# ==========================================

st.title("🌍 Macro-Risk Intelligence Hub")
st.markdown("#### Real‑time monitoring of economic, energy & geopolitical risks")
st.caption(f"Data updated live • Session started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if st.session_state.fetched_results:
    results = st.session_state.fetched_results

    # 1. Key Metrics Row
    st.subheader("📊 Key Market Snapshot")
    price_sources = [(name, data) for name, data in results.items()
                     if isinstance(data, dict) and "price" in data]

    if price_sources:
        metric_cols = st.columns(4)
        for i, (name, data) in enumerate(price_sources[:4]):
            with metric_cols[i]:
                st.metric(
                    label=name,
                    value=f"${data['price']:,.2f}",
                    delta=f"{data.get('change', 0):+.2f}",
                    delta_color="normal"
                )

        if len(price_sources) > 4:
            metric_cols2 = st.columns(4)
            for i, (name, data) in enumerate(price_sources[4:8]):
                with metric_cols2[i]:
                    st.metric(
                        label=name,
                        value=f"${data['price']:,.2f}",
                        delta=f"{data.get('change', 0):+.2f}",
                        delta_color="normal"
                    )
    else:
        st.info("Select commodity sources in the sidebar to see price snapshots.")

    st.divider()

    # 2. Categorized Data Expanders
    st.subheader("📂 Detailed Source Data")

    categories_in_results = {}
    for src_name, data in results.items():
        src = next((s for s in ALL_SOURCES if s["name"] == src_name), None)
        cat = src["category"] if src else "Other"
        categories_in_results.setdefault(cat, []).append((src_name, data))

    category_order = ["Energy", "Metals", "Agriculture", "Economic", "Monetary", "Currency", "Equities", "Crypto", "News", "Geopolitical", "Other"]

    for cat in category_order:
        if cat in categories_in_results:
            items = categories_in_results[cat]
            with st.expander(f"**{cat}** ({len(items)} sources)", expanded=cat in ["Energy", "Economic"]):
                cols = st.columns(3)
                for idx, (name, data) in enumerate(items):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.caption(name)
                            if "error" in data:
                                st.error(f"❌ {data['error']}")
                            elif "price" in data:
                                st.metric("Price", f"${data['price']}", delta=f"{data.get('change',0):+.2f}")
                            elif "headlines" in data:
                                for hl in data["headlines"][:2]:
                                    st.markdown(f"- {hl['title'][:60]}...")
                                if len(data["headlines"]) > 2:
                                    st.markdown(f"*+{len(data['headlines'])-2} more*")
                            elif "value" in data:
                                st.write(f"**Value:** {data['value']}")
                                st.caption(f"as of {data.get('date', 'N/A')}")
                            elif "data" in data:
                                st.write("Data available")
                                with st.popover("Preview"):
                                    st.json(data["data"])
                            else:
                                st.write("✓ Data received")

    st.divider()

    # 3. AI Analysis Section
    st.subheader("🧠 AI-Powered Strategic Analysis")
    st.markdown("Select a focus area to generate a forward-looking briefing based on **current 2026 data**.")

    analysis_type = st.selectbox(
        "Choose analysis lens:",
        ["General Macro", "Energy & Maritime", "LATAM/Caribbean Risk",
         "Tech & Digitalization", "Warehouse Ops", "PM Risk",
         "Crypto", "Geopolitical Power"],
        key="analysis_selector"
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

    if st.button("🚀 Generate Briefing", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ DeepSeek API key required. Please add it in the sidebar.")
        elif not st.session_state.fetched_results:
            st.warning("Please fetch data sources first.")
        else:
            st.session_state.analysis_in_progress = True

            with st.status("🔄 Generating comprehensive briefing...", expanded=True) as status:
                st.write("📊 Compiling market data...")
                market_lines = []
                news_lines = []
                for name, data in results.items():
                    if "error" in data:
                        continue
                    if "price" in data:
                        market_lines.append(f"- {name}: ${data['price']} (change: {data.get('change',0):+.2f})")
                    elif "headlines" in data:
                        for hl in data["headlines"][:2]:
                            news_lines.append(f"- {hl['title']}")
                    elif "value" in data:
                        market_lines.append(f"- {name}: {data['value']} (as of {data.get('date','N/A')})")

                market_context = "\n".join(market_lines[:25])
                news_context = "\n".join(news_lines[:12])

                st.write("🧠 Calling DeepSeek API for 2026 analysis...")
                report = analyze_with_deepseek(prompt_map[analysis_type], market_context, news_context, api_key)
                status.update(label="✅ Briefing ready", state="complete")

            with st.container(border=True):
                st.markdown("### Strategic Briefing for 2026")
                st.markdown(report)

            st.download_button(
                label="📥 Download Briefing (Markdown)",
                data=report,
                file_name=f"macro_briefing_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True
            )

            st.session_state.analysis_in_progress = False

else:
    st.info("👈 **Start here:** Select data sources in the sidebar and click 'Fetch Selected Sources' to populate the dashboard.")
    with st.container(border=True):
        st.markdown("**Dashboard Preview**")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Crude Oil", "$--.--", "--")
        with col2: st.metric("Gold", "$--.--", "--")
        with col3: st.metric("S&P 500", "--.--", "--")
        with col4: st.metric("VIX", "--.--", "--")
        st.caption("Select and fetch sources to see live data.")    
