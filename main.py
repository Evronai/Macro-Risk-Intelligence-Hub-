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
import pandas as pd

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Macro-Risk Intelligence Hub",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CUSTOM CSS FOR TERMINAL LOOK
# ==========================================
st.markdown("""
<style>
    /* Terminal dark theme */
    .stApp {
        background-color: #0a0a0a;
        color: #00ff00;
    }
    .stApp header, .stApp footer {
        background-color: #111;
    }
    .css-1d391kg, .css-1wrcr25 {
        background-color: #111 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00ff00 !important;
        font-family: 'Courier New', monospace;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #111;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #222;
        border-radius: 4px 4px 0 0;
        color: #0f0;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0a0a0a;
        border-bottom: 2px solid #00ff00;
    }
    .stDataFrame {
        font-family: 'Courier New', monospace;
        background-color: #111;
    }
    .stDataFrame td {
        color: #0f0;
    }
    .stDataFrame th {
        background-color: #222;
        color: #0f0;
        font-weight: bold;
    }
    .stMetric {
        background-color: #111;
        border: 1px solid #0f0;
        border-radius: 5px;
        padding: 10px;
        font-family: 'Courier New', monospace;
    }
    .stMetric label {
        color: #0f0 !important;
    }
    .stMetric .value {
        color: #0f0 !important;
    }
    .stAlert {
        background-color: #111 !important;
        color: #0f0 !important;
        border: 1px solid #0f0;
    }
    .stButton button {
        background-color: #111;
        color: #0f0;
        border: 1px solid #0f0;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #0f0;
        color: #111;
    }
    .sidebar .sidebar-content {
        background-color: #111;
        color: #0f0;
        font-family: 'Courier New', monospace;
    }
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #111;
    }
    ::-webkit-scrollbar-thumb {
        background: #0f0;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #0c0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SOURCE REGISTRY (unchanged)
# ==========================================
ALL_SOURCES = [
    # ... (keep all sources as provided)
    {"name": "Crude Oil (WTI)", "type": "yfinance", "symbol": "CL=F", "category": "Energy"},
    # ... etc. (I'll omit for brevity, but keep the full list)
]

# ==========================================
# 4. DATA SOURCE MANAGER (unchanged)
# ==========================================
class DataSourceManager:
    # ... (same as original)

# ==========================================
# 5. AI ANALYSIS FUNCTION (unchanged)
# ==========================================
def analyze_with_deepseek(...):
    # ... (same as original)

# ==========================================
# 6. HELPER: Format results for display
# ==========================================
def format_results_for_category(results: Dict, category: str) -> pd.DataFrame:
    """Return a DataFrame with columns: Source, Value, Change, Status"""
    rows = []
    for src_name, data in results.items():
        src = next((s for s in ALL_SOURCES if s["name"] == src_name), None)
        if src and src["category"] == category:
            if "error" in data:
                rows.append({
                    "Source": src_name,
                    "Value": "ERROR",
                    "Change": "",
                    "Status": "❌"
                })
            elif "price" in data:
                rows.append({
                    "Source": src_name,
                    "Value": f"${data['price']:,.2f}",
                    "Change": f"{data.get('change', 0):+.2f}",
                    "Status": "✓"
                })
            elif "headlines" in data:
                # For news, show headline count
                rows.append({
                    "Source": src_name,
                    "Value": f"{len(data['headlines'])} headlines",
                    "Change": "",
                    "Status": "📰"
                })
            elif "value" in data:
                rows.append({
                    "Source": src_name,
                    "Value": data['value'],
                    "Change": "",
                    "Status": "📊"
                })
            elif "data" in data:
                rows.append({
                    "Source": src_name,
                    "Value": "API data",
                    "Change": "",
                    "Status": "📡"
                })
            else:
                rows.append({
                    "Source": src_name,
                    "Value": "Received",
                    "Change": "",
                    "Status": "✓"
                })
    return pd.DataFrame(rows)

# ==========================================
# 7. INITIALISE SESSION STATE
# ==========================================
if "data_manager" not in st.session_state:
    st.session_state.data_manager = DataSourceManager(ALL_SOURCES)
if "fetched_results" not in st.session_state:
    st.session_state.fetched_results = None
if "analysis_in_progress" not in st.session_state:
    st.session_state.analysis_in_progress = False
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = None

# ==========================================
# 8. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.title("⚙️ CONFIG")
    
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
        st.success("✅ Key set")
    else:
        st.warning("⚠️ Key missing")
    
    st.markdown("---")
    
    # Source selection
    st.subheader("📡 SOURCES")
    categories = list(set(s["category"] for s in ALL_SOURCES))
    selected_category = st.selectbox("Filter", ["All"] + sorted(categories))
    
    filtered_sources = ALL_SOURCES
    if selected_category != "All":
        filtered_sources = [s for s in ALL_SOURCES if s["category"] == selected_category]
    
    source_names = [s["name"] for s in filtered_sources]
    selected_sources = st.multiselect(
        "Select sources",
        options=source_names,
        default=source_names[:10]
    )
    
    update_freq = st.slider("Cache (s)", 300, 7200, 3600, step=300)
    
    if st.button("🔄 FETCH", use_container_width=True):
        with st.spinner(f"Fetching {len(selected_sources)} sources..."):
            results = st.session_state.data_manager.fetch_selected(selected_sources)
            st.session_state.fetched_results = results
            st.session_state.last_fetch_time = time.time()
            success_count = sum(1 for v in results.values() if "error" not in v)
            st.success(f"Fetched {success_count}/{len(selected_sources)}")
    
    if st.session_state.last_fetch_time:
        st.caption(f"Last: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_fetch_time))}")
    
    st.markdown("---")
    st.caption("© 2026 Macro-Risk Terminal")

# ==========================================
# 9. MAIN DASHBOARD
# ==========================================
st.title("🌍 MACRO-RISK INTELLIGENCE TERMINAL")
st.markdown("#### Real‑time monitoring • 2026")

if st.session_state.fetched_results:
    results = st.session_state.fetched_results

    # ===== KEY METRICS ROW =====
    st.subheader("📊 SPOT PRICES")
    price_sources = [(name, data) for name, data in results.items()
                     if isinstance(data, dict) and "price" in data]
    if price_sources:
        cols = st.columns(4)
        for i, (name, data) in enumerate(price_sources[:8]):
            with cols[i % 4]:
                st.metric(
                    label=name,
                    value=f"${data['price']:,.2f}",
                    delta=f"{data.get('change', 0):+.2f}",
                    delta_color="normal"
                )
    else:
        st.info("No price data yet.")

    st.divider()

    # ===== CATEGORY TABS =====
    st.subheader("📂 DETAILED DATA")
    tab_names = ["Energy", "Metals", "Agriculture", "Economic", "Monetary", "Currency", "Equities", "Crypto", "News", "Geopolitical"]
    tabs = st.tabs([f"⚡{n}" if n=="Energy" else f"📈{n}" for n in tab_names])  # add icons

    for tab, category in zip(tabs, tab_names):
        with tab:
            df = format_results_for_category(results, category)
            if not df.empty:
                # Style the DataFrame
                styled_df = df.style.applymap(
                    lambda x: 'color: #0f0' if isinstance(x, str) and x.startswith('$') else '',
                    subset=['Value']
                ).applymap(
                    lambda x: 'color: #0f0' if isinstance(x, str) and x.startswith('+') else ('color: #f00' if isinstance(x, str) and x.startswith('-') else ''),
                    subset=['Change']
                )
                st.dataframe(styled_df, use_container_width=True, height=300)
            else:
                st.caption("No data in this category. Select sources in sidebar and fetch.")

    # ===== AI ANALYSIS SECTION =====
    st.divider()
    st.subheader("🧠 AI STRATEGIC ANALYSIS")
    st.markdown("Select a lens and generate a forward-looking briefing based on **current 2026 data**.")

    analysis_type = st.selectbox(
        "Analysis lens:",
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

    if st.button("🚀 GENERATE BRIEFING", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ DeepSeek API key required.")
        elif not st.session_state.fetched_results:
            st.warning("Please fetch data first.")
        else:
            st.session_state.analysis_in_progress = True

            with st.status("🔄 Generating...", expanded=True) as status:
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

                st.write("🧠 Calling DeepSeek...")
                report = analyze_with_deepseek(prompt_map[analysis_type], market_context, news_context, api_key)
                status.update(label="✅ Briefing ready", state="complete")

            with st.container(border=True):
                st.markdown("### Strategic Briefing for 2026")
                st.markdown(report)

            st.download_button(
                label="📥 Download (Markdown)",
                data=report,
                file_name=f"briefing_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True
            )

            st.session_state.analysis_in_progress = False

else:
    st.info("👈 **Start:** Select sources in sidebar and click 'FETCH'.")
    with st.container(border=True):
        st.markdown("**TERMINAL PREVIEW**")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Crude Oil", "$--.--", "--")
        with col2: st.metric("Gold", "$--.--", "--")
        with col3: st.metric("S&P 500", "--.--", "--")
        with col4: st.metric("VIX", "--.--", "--")
        st.caption("Awaiting data...")
