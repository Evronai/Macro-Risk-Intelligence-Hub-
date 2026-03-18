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
# 1. PAGE CONFIGURATION (with custom theme)
# ==========================================
st.set_page_config(
    page_title="Macro-Risk Intelligence Hub",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ CUSTOM CSS for pro look ------------------
st.markdown("""
<style>
    /* Import professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container background */
    .main > div {
        background: #0e1117;
        background: linear-gradient(145deg, #0b0e14 0%, #141a24 100%);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1f2b;
        border-right: 1px solid #2a3142;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: #2d3748;
        color: #e2e8f0;
        border: 1px solid #4a5568;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: #3f4a5e;
        border-color: #718096;
    }
    
    /* Metric tiles */
    div[data-testid="metric-container"] {
        background: #1e2532;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.7);
        border-color: #4a5a7a;
    }
    div[data-testid="metric-container"] label {
        color: #a0aec0 !important;
        font-weight: 500;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    div[data-testid="metric-container"] div[data-testid="metric-value"] {
        color: #f7fafc !important;
        font-weight: 700;
        font-size: 1.8rem;
    }
    div[data-testid="metric-container"] div[data-testid="metric-delta"] {
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1e2532 !important;
        border-radius: 8px !important;
        border: 1px solid #2d3748 !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        padding: 0.75rem 1rem !important;
    }
    .streamlit-expanderHeader:hover {
        background-color: #27303f !important;
        border-color: #4a5a7a !important;
    }
    .streamlit-expanderContent {
        background-color: #151b26;
        border: 1px solid #2d3748;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
    }
    
    /* Cards inside expanders */
    div[data-testid="column"] > div {
        background: #1e2532;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #2d3748;
        margin-bottom: 8px;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #f7fafc !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    .stMarkdown p, .stMarkdown li {
        color: #cbd5e0;
    }
    
    /* Buttons */
    .stButton button {
        background: #2d3748;
        color: #e2e8f0;
        border: 1px solid #4a5568;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: #3f4a5e;
        border-color: #718096;
    }
    .stButton button[data-baseweb="button"][kind="primary"] {
        background: #2563eb;
        border-color: #3b82f6;
        color: white;
    }
    .stButton button[data-baseweb="button"][kind="primary"]:hover {
        background: #1d4ed8;
        border-color: #2563eb;
    }
    
    /* Divider */
    hr {
        border-color: #2d3748;
        margin: 2rem 0;
    }
    
    /* Status messages */
    .stAlert {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border: 1px solid #3b4b62 !important;
        border-radius: 8px !important;
    }
    .stAlert-success {
        background-color: #0f2e1f !important;
        border-color: #2f6e4a !important;
    }
    .stAlert-error {
        background-color: #3b1e1e !important;
        border-color: #9b2c2c !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #3b82f6 transparent transparent transparent !important;
    }
    
    /* Download button */
    .stDownloadButton button {
        background: #2d3748;
        border: 1px solid #4a5568;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SOURCE REGISTRY (unchanged, 90+ sources)
# ==========================================
ALL_SOURCES = [
    # ... (same as original, omitted for brevity - keep as is)
    # In practice, you'd copy the full list from the original code.
]

# ==========================================
# 3. DATA SOURCE MANAGER (unchanged)
# ==========================================
class DataSourceManager:
    # ... (same as original, keep all methods)
    pass

# ==========================================
# 4. AI PROMPTS FUNCTION (unchanged)
# ==========================================
def analyze_with_deepseek(prompt_type: str, market_context: str, news_context: str, api_key: str) -> str:
    # ... (same as original)
    pass

# ==========================================
# 5. INITIALISE SESSION STATE (unchanged)
# ==========================================
if "data_manager" not in st.session_state:
    st.session_state.data_manager = DataSourceManager(ALL_SOURCES)
if "fetched_results" not in st.session_state:
    st.session_state.fetched_results = None
if "analysis_in_progress" not in st.session_state:
    st.session_state.analysis_in_progress = False

# ==========================================
# 6. SIDEBAR CONFIGURATION (with improved styling)
# ==========================================
with st.sidebar:
    # Logo/title area
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <span style="font-size: 3rem;">🌍</span>
        <h2 style="color: #e2e8f0; margin: 0;">Macro-Risk</h2>
        <p style="color: #718096; font-size: 0.9rem;">Intelligence Hub</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key input
    st.markdown("#### 🔑 Authentication")
    api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
        except:
            pass
    
    if api_key:
        st.markdown("<span style='color: #10b981;'>✅ DeepSeek key set</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: #f59e0b;'>⚠️ DeepSeek key missing</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Source selection
    st.markdown("#### 📡 Data Sources")
    categories = list(set(s["category"] for s in ALL_SOURCES))
    selected_category = st.selectbox("Filter by category", ["All"] + sorted(categories))
    
    filtered_sources = ALL_SOURCES
    if selected_category != "All":
        filtered_sources = [s for s in ALL_SOURCES if s["category"] == selected_category]
    
    source_names = [s["name"] for s in filtered_sources]
    selected_sources = st.multiselect(
        "Select sources to fetch",
        options=source_names,
        default=source_names[:10],
        help="Choose up to 10-15 for best performance"
    )
    
    update_freq = st.slider("Cache duration (seconds)", 300, 7200, 3600, step=300,
                            help="How long to keep data in memory before auto-refresh")
    
    if st.button("🔄 Fetch Selected Sources", use_container_width=True):
        with st.spinner(f"Fetching {len(selected_sources)} sources..."):
            results = st.session_state.data_manager.fetch_selected(selected_sources)
            st.session_state.fetched_results = results
            success_count = sum(1 for v in results.values() if "error" not in v)
            st.success(f"Fetched {success_count}/{len(selected_sources)} sources")
    
    st.markdown("---")
    st.caption("© 2026 Macro-Risk Intelligence • v2.0")

# ==========================================
# 7. PROFESSIONAL DASHBOARD UI
# ==========================================

# Header area with live timestamp
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🌍 Macro-Risk Intelligence Hub")
    st.markdown("#### Real‑time monitoring of economic, energy & geopolitical risks")
with col2:
    st.markdown(f"""
    <div style="background: #1e2532; border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #2d3748; margin-top: 20px;">
        <span style="color: #a0aec0; font-size: 0.8rem;">LAST UPDATE</span><br>
        <span style="color: #f7fafc; font-weight: 600; font-size: 1.2rem;">{time.strftime('%H:%M:%S')}</span><br>
        <span style="color: #718096; font-size: 0.8rem;">{time.strftime('%b %d, %Y')}</span>
    </div>
    """, unsafe_allow_html=True)

st.caption(f"Session started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if st.session_state.fetched_results:
    results = st.session_state.fetched_results

    # 1. Key Metrics Row - dynamic columns
    st.subheader("📊 Key Market Snapshot")
    price_sources = [(name, data) for name, data in results.items()
                     if isinstance(data, dict) and "price" in data]

    if price_sources:
        # Display metrics in a responsive grid
        num_metrics = len(price_sources[:8])  # show max 8
        cols = st.columns(min(num_metrics, 4))  # first row max 4
        for i, (name, data) in enumerate(price_sources[:4]):
            with cols[i]:
                st.metric(
                    label=name,
                    value=f"${data['price']:,.2f}",
                    delta=f"{data.get('change', 0):+.2f}",
                    delta_color="normal"
                )
        if num_metrics > 4:
            cols2 = st.columns(min(num_metrics-4, 4))
            for i, (name, data) in enumerate(price_sources[4:8]):
                with cols2[i]:
                    st.metric(
                        label=name,
                        value=f"${data['price']:,.2f}",
                        delta=f"{data.get('change', 0):+.2f}",
                        delta_color="normal"
                    )
        if num_metrics == 0:
            st.info("No price sources selected.")
    else:
        st.info("Select commodity/currency sources to see price snapshots.")

    st.divider()

    # 2. Categorized Data Expanders - professional card layout
    st.subheader("📂 Detailed Source Data")

    categories_in_results = {}
    for src_name, data in results.items():
        src = next((s for s in ALL_SOURCES if s["name"] == src_name), None)
        cat = src["category"] if src else "Other"
        categories_in_results.setdefault(cat, []).append((src_name, data))

    # Sort categories in a logical order
    category_order = ["Energy", "Metals", "Agriculture", "Economic", "Monetary", 
                      "Currency", "Equities", "Crypto", "News", "Geopolitical", "Other"]

    for cat in category_order:
        if cat in categories_in_results:
            items = categories_in_results[cat]
            with st.expander(f"**{cat}** ({len(items)} sources)", expanded=cat in ["Energy", "Economic"]):
                # Create 3-column grid of cards
                cols = st.columns(3)
                for idx, (name, data) in enumerate(items):
                    with cols[idx % 3]:
                        # Card container with border
                        with st.container():
                            st.markdown(f"**{name}**")
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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🚀 Generate Briefing", type="primary", use_container_width=True)

    if generate_button:
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

            # Report container with subtle border
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
    # Welcome screen with preview
    st.info("👈 **Start here:** Select data sources in the sidebar and click 'Fetch Selected Sources' to populate the dashboard.")
    with st.container(border=True):
        st.markdown("**Dashboard Preview**")
        cols = st.columns(4)
        preview_data = [
            ("Crude Oil", "$72.45", "+1.20"),
            ("Gold", "$2,345.10", "-8.30"),
            ("S&P 500", "5,234", "+12"),
            ("VIX", "15.2", "-0.8")
        ]
        for i, (label, val, delta) in enumerate(preview_data):
            with cols[i]:
                st.metric(label, val, delta)
        st.caption("Select and fetch sources to see live data.")
