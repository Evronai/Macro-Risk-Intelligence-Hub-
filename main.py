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
# 2. CUSTOM CSS — BIG 4 PROFESSIONAL THEME
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@300;400;500;600&family=Source+Code+Pro:wght@400;500&display=swap');

    /* ── CSS Variables ── */
    :root {
        --bg-primary: #f7f8fa;
        --bg-secondary: #ffffff;
        --bg-sidebar: #1a2340;
        --bg-sidebar-hover: #243058;
        --accent-navy: #1a2340;
        --accent-blue: #003087;
        --accent-gold: #c8960c;
        --accent-red: #c0392b;
        --accent-green: #1a7a4a;
        --text-primary: #0f1923;
        --text-secondary: #4a5568;
        --text-muted: #8a95a3;
        --text-sidebar: #b8c4d8;
        --text-sidebar-label: #7a8ba8;
        --border-light: #e2e6ed;
        --border-medium: #c8cfd9;
        --shadow-card: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
        --shadow-hover: 0 4px 20px rgba(0,0,0,0.12);
        --font-display: 'Playfair Display', Georgia, serif;
        --font-body: 'Source Sans 3', 'Helvetica Neue', sans-serif;
        --font-mono: 'Source Code Pro', 'Courier New', monospace;
    }

    /* ── Reset & Base ── */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: var(--font-body);
    }
    .stApp header {
        background-color: var(--bg-secondary) !important;
        border-bottom: 2px solid var(--accent-navy);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: none;
    }
    [data-testid="stSidebar"] > div {
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] * {
        font-family: var(--font-body) !important;
        color: var(--text-sidebar) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        font-size: 0.65rem !important;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--text-sidebar-label) !important;
        margin: 1.2rem 0 0.4rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] label {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        color: var(--text-sidebar-label) !important;
    }
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
        background-color: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #e0e7f0 !important;
        border-radius: 3px !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stSidebar"] .stSlider label {
        font-size: 0.75rem !important;
    }

    /* Sidebar title block */
    [data-testid="stSidebar"] h1 {
        font-family: var(--font-display) !important;
        font-size: 1.1rem !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
        padding: 1.4rem 0 0.2rem 0;
        border-bottom: 2px solid var(--accent-gold);
        margin-bottom: 0.5rem;
    }

    /* Sidebar button */
    [data-testid="stSidebar"] .stButton button {
        background-color: var(--accent-blue) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 3px !important;
        font-family: var(--font-body) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.55rem 1rem !important;
        transition: background-color 0.2s;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #004bb5 !important;
    }

    /* ── Main Headings ── */
    h1 {
        font-family: var(--font-display) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        color: var(--accent-navy) !important;
        letter-spacing: -0.01em;
        line-height: 1.2;
    }
    h2 {
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        font-size: 0.65rem !important;
        color: var(--text-muted) !important;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-top: 1.8rem;
        margin-bottom: 0.8rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-light);
    }
    h3 {
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        color: var(--accent-navy) !important;
    }
    h4 {
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        color: var(--text-secondary) !important;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* ── Subtitle / tagline ── */
    .report-tagline {
        font-family: var(--font-body);
        font-size: 0.85rem;
        color: var(--text-muted);
        font-weight: 400;
        letter-spacing: 0.02em;
        margin-top: -0.6rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .report-tagline .dot {
        width: 6px;
        height: 6px;
        background: var(--accent-gold);
        border-radius: 50%;
        display: inline-block;
    }

    /* ── Section divider ── */
    hr {
        border: none;
        border-top: 1px solid var(--border-light);
        margin: 1.5rem 0;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-top: 3px solid var(--accent-navy);
        border-radius: 3px;
        padding: 1rem 1.1rem;
        box-shadow: var(--shadow-card);
        transition: box-shadow 0.2s;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-hover);
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--font-body) !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--font-mono) !important;
        font-size: 1.35rem !important;
        font-weight: 500 !important;
        color: var(--accent-navy) !important;
        line-height: 1.2;
    }
    [data-testid="stMetricDelta"] {
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-secondary);
        border-bottom: 2px solid var(--border-light);
        gap: 0;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-muted);
        font-family: var(--font-body) !important;
        font-size: 0.78rem !important;
        font-weight: 500;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        border-bottom: 2px solid transparent;
        padding: 0.7rem 1.2rem;
        border-radius: 0;
        margin-bottom: -2px;
        transition: color 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-navy);
        background-color: rgba(0, 0, 0, 0.02);
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-navy) !important;
        border-bottom: 2px solid var(--accent-navy) !important;
        background-color: transparent !important;
        font-weight: 600 !important;
    }

    /* ── DataFrames / Tables ── */
    .stDataFrame {
        border: 1px solid var(--border-light) !important;
        border-radius: 3px !important;
        box-shadow: var(--shadow-card);
        font-family: var(--font-mono) !important;
        font-size: 0.8rem !important;
    }
    .stDataFrame thead tr th {
        background-color: var(--accent-navy) !important;
        color: #ffffff !important;
        font-family: var(--font-body) !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 0.6rem 0.8rem !important;
    }
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #f5f7fb !important;
    }
    .stDataFrame tbody tr:hover {
        background-color: #eef1f8 !important;
    }
    .stDataFrame tbody tr td {
        color: var(--text-primary) !important;
        padding: 0.5rem 0.8rem !important;
        border-bottom: 1px solid var(--border-light) !important;
    }

    /* ── Buttons (main) ── */
    .stButton button {
        background-color: var(--bg-secondary);
        color: var(--accent-navy);
        border: 1.5px solid var(--border-medium);
        border-radius: 3px;
        font-family: var(--font-body);
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: var(--accent-navy);
        color: #ffffff;
        border-color: var(--accent-navy);
    }
    /* Primary button */
    .stButton button[kind="primary"] {
        background-color: var(--accent-navy) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: var(--accent-blue) !important;
    }

    /* ── Alerts / Info boxes ── */
    .stAlert {
        border-radius: 3px !important;
        border-left: 4px solid var(--accent-navy) !important;
        background-color: #f0f3f9 !important;
        font-family: var(--font-body) !important;
        font-size: 0.82rem !important;
    }
    .stAlert p {
        color: var(--text-secondary) !important;
    }

    /* ── Success / Warning / Error ── */
    [data-testid="stNotification"][data-type="success"] {
        border-left-color: var(--accent-green) !important;
        background-color: #f0faf5 !important;
    }
    [data-testid="stNotification"][data-type="warning"] {
        border-left-color: var(--accent-gold) !important;
        background-color: #fdf8ee !important;
    }
    [data-testid="stNotification"][data-type="error"] {
        border-left-color: var(--accent-red) !important;
        background-color: #fdf0ef !important;
    }

    /* ── Status widget ── */
    [data-testid="stStatusWidget"] {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 3px !important;
        font-family: var(--font-body) !important;
    }

    /* ── Container with border ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--border-light) !important;
        border-radius: 3px !important;
        background-color: var(--bg-secondary) !important;
        box-shadow: var(--shadow-card);
        padding: 1.2rem !important;
    }

    /* ── Download button ── */
    .stDownloadButton button {
        background-color: transparent !important;
        color: var(--accent-blue) !important;
        border: 1.5px solid var(--accent-blue) !important;
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .stDownloadButton button:hover {
        background-color: var(--accent-blue) !important;
        color: #ffffff !important;
    }

    /* ── Selectbox ── */
    .stSelectbox [data-baseweb="select"] {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-medium) !important;
        border-radius: 3px !important;
        font-family: var(--font-body) !important;
        font-size: 0.82rem !important;
    }

    /* ── Text inputs ── */
    .stTextInput input {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-medium) !important;
        border-radius: 3px !important;
        font-family: var(--font-body) !important;
        color: var(--text-primary) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: var(--accent-navy) !important;
    }

    /* ── Caption / small text ── */
    .stCaption, caption {
        font-family: var(--font-body) !important;
        font-size: 0.72rem !important;
        color: var(--text-muted) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f0f2f5; }
    ::-webkit-scrollbar-thumb { background: #c0c8d4; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #a0aab8; }

    /* ── AI Briefing markdown output ── */
    .briefing-container {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-top: 3px solid var(--accent-navy);
        border-radius: 3px;
        padding: 2rem 2.4rem;
        box-shadow: var(--shadow-card);
        line-height: 1.7;
    }
    .briefing-container h3 {
        font-family: var(--font-display) !important;
        font-size: 1.3rem !important;
        color: var(--accent-navy) !important;
        border-bottom: 1px solid var(--border-light);
        padding-bottom: 0.6rem;
        margin-bottom: 1.2rem;
    }
    .briefing-container p {
        font-family: var(--font-body);
        font-size: 0.88rem;
        color: var(--text-secondary);
        margin-bottom: 0.8rem;
    }
    .briefing-container ul li {
        font-size: 0.87rem;
        color: var(--text-secondary);
        margin-bottom: 0.3rem;
    }
    .briefing-container strong {
        color: var(--accent-navy);
    }
    .briefing-container table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.82rem;
        margin: 1rem 0;
    }
    .briefing-container table th {
        background-color: var(--accent-navy);
        color: white;
        padding: 0.5rem 0.8rem;
        text-align: left;
    }
    .briefing-container table td {
        padding: 0.45rem 0.8rem;
        border-bottom: 1px solid var(--border-light);
    }
    .briefing-container table tr:nth-child(even) td {
        background-color: #f5f7fb;
    }

    /* ── Header bar ── */
    .page-header {
        background-color: var(--accent-navy);
        margin: -1rem -1rem 1.5rem -1rem;
        padding: 1.2rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* ── Preview placeholder cards ── */
    .placeholder-card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-top: 3px solid #e2e6ed;
        border-radius: 3px;
        padding: 1rem;
        text-align: center;
    }

    /* ── Multiselect tags ── */
    [data-baseweb="tag"] {
        background-color: var(--accent-navy) !important;
        border-radius: 2px !important;
    }
    [data-baseweb="tag"] span {
        color: #ffffff !important;
        font-family: var(--font-body) !important;
        font-size: 0.72rem !important;
    }

    /* ── Status badge ── */
    .status-badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 2px;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .badge-live {
        background-color: #e8f5f0;
        color: var(--accent-green);
        border: 1px solid #c0e0d0;
    }
    .badge-pending {
        background-color: #fdf8ee;
        color: #a07000;
        border: 1px solid #edd090;
    }

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. SOURCE REGISTRY (90+ FREE SOURCES)
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
# 4. DATA SOURCE MANAGER  (unchanged)
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
        url = "https://api.stlouisfed.org/fred/series/observations"
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
# 5. AI ANALYSIS FUNCTION  (unchanged)
# ==========================================
def analyze_with_deepseek(prompt_type: str, market_context: str, news_context: str, api_key: str) -> str:
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
""",
        'regional': """
**LATAM & Caribbean Geopolitical Risk Assessment – 2026**

Focus on Trinidad & Tobago, the wider Caribbean, and key Latin American economies (Brazil, Mexico, Argentina, Venezuela, Colombia). Your analysis must address:

- **Political Stability & Governance**: Recent elections, protests, or policy shifts that could impact business operations.
- **Economic Vulnerability**: Currency volatility, inflation, debt levels, and reliance on commodity exports.
- **Shipping & Trade Chokepoints**: Assess risks to maritime routes (Panama Canal, Caribbean passages, Amazon River ports).
- **Energy & Mining Sector Focus**: For Trinidad (LNG, petrochemicals), Guyana (oil boom), Venezuela (sanctions), Chile/Peru (copper), Brazil (mining, agribusiness).
- **Social & Environmental Factors**: Climate change impacts (hurricanes, droughts), migration flows.
- **Risk Scenarios**: Develop two plausible scenarios for the region over the next 12 months and their implications.
- **Recommendations**: Contingency plans, diversification strategies, or partnerships to prioritize.
""",
        'tech': """
**Technology & Digitalization Macro Trends – 2026**

You are advising the CIO of a global logistics firm. Address:

- **Automation & AI in Operations**: Adoption of robotics and AI in warehouses, ports, and field operations.
- **IT Services & Cloud Demand**: Impact of geopolitical tensions on cloud infrastructure and IT outsourcing.
- **Cybersecurity Risk Landscape**: Increased attacks on critical infrastructure.
- **Digitalization of Supply Chains**: Blockchain, IoT, digital twins adoption.
- **Talent & Workforce**: Remote work trends, tech talent migration.
- **Strategic Recommendations**: Technology investments to prioritize, delay, or reconsider in 2026.
""",
        'warehouse': """
**Warehouse & Inventory Operations Manager Briefing – 2026**

Translate the macro data into operational impacts and recommendations:

- **Procurement Lead Times**: Based on commodity price trends and supply disruptions.
- **Inventory Holding Costs**: Rising interest rates increasing carrying costs.
- **Facility Resource Allocation**: Energy price volatility affecting utility costs and staffing.
- **Transportation & Inbound Logistics**: Fuel surcharges, trucking availability, port delays.
- **Risk Mitigation**: Contingency plan for a major disruption (port strike, energy blackout).
- **Action Items**: A checklist of 5 immediate actions for the next quarter.
""",
        'pm_risk': """
**Senior Project Manager Risk Assessment – 2026**

For large-scale infrastructure or industrial projects, analyze:

- **Scope Creep Risks**: Geopolitical events or commodity price swings forcing design changes.
- **Schedule Risks**: Supply chain delays for critical equipment.
- **Cost Escalation**: Inflation in raw materials, labor, and energy.
- **Labor & Workforce**: Strikes, skilled labor shortages.
- **Financing & Currency**: Interest rate and currency volatility impacts.
- **Mitigation Strategies**: Concrete mitigation for each top risk.
- **Monitoring Recommendations**: KPIs to track weekly.
""",
        'crypto': """
**Digital Assets & Crypto Market Analysis – 2026**

Advising a crypto hedge fund:

- **Macro Drivers**: Correlation of Bitcoin/Ethereum with equities, commodities, and the US dollar.
- **Regulatory News**: Crypto regulation mentions in news feeds and market impact.
- **Institutional Adoption**: Major companies adding crypto to balance sheets, ETF flows.
- **Energy & Mining**: Impact of energy prices on Bitcoin mining profitability.
- **Geopolitical Risk**: Use of crypto for sanctions evasion, capital flight.
- **Outlook & Positioning**: Tactical outlook for the next 3–6 months.
""",
        'power_structures': """
**Advanced Geopolitical Power Structures Analysis – 2026**

Advising a sovereign wealth fund:

- **US-China Rivalry**: Escalation or de-escalation signals and supply chain impact.
- **Regional Power Shifts**: Rise of BRICS+, SCO, currency de-dollarization.
- **Energy as a Weapon**: How energy-exporting nations exert influence.
- **Economic Warfare**: Sanctions, export controls, weaponized interdependence.
- **Systemic Control**: Digital currencies, surveillance tech, data localization.
- **Fragile States & Proxy Conflicts**: Regions where state failure could disrupt markets.
- **Implications for Investors**: Sectors, regions, or asset classes most exposed.
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
# 6. HELPER: Format results for display  (unchanged)
# ==========================================
def format_results_for_category(results: Dict, category: str) -> pd.DataFrame:
    rows = []
    for src_name, data in results.items():
        src = next((s for s in ALL_SOURCES if s["name"] == src_name), None)
        if src and src["category"] == category:
            if "error" in data:
                rows.append({"Source": src_name, "Value": "Error", "Change": "—", "Status": "Error"})
            elif "price" in data:
                rows.append({
                    "Source": src_name,
                    "Value": f"${data['price']:,.2f}",
                    "Change": f"{data.get('change', 0):+.2f}",
                    "Status": "Live"
                })
            elif "headlines" in data:
                rows.append({"Source": src_name, "Value": f"{len(data['headlines'])} headlines", "Change": "—", "Status": "Live"})
            elif "value" in data:
                rows.append({"Source": src_name, "Value": data['value'], "Change": "—", "Status": "Live"})
            elif "data" in data:
                rows.append({"Source": src_name, "Value": "API data received", "Change": "—", "Status": "Live"})
            else:
                rows.append({"Source": src_name, "Value": "Received", "Change": "—", "Status": "Live"})
    return pd.DataFrame(rows)


# ==========================================
# 7. SESSION STATE
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
# 8. SIDEBAR
# ==========================================
with st.sidebar:
    # Firm-style header
    st.markdown("""
    <div style="background:#1a2340; margin:-1rem -1rem 0 -1rem; padding:1.4rem 1.2rem 1rem 1.2rem; border-bottom:2px solid #c8960c;">
        <div style="font-family:'Source Sans 3',sans-serif; font-size:0.6rem; font-weight:600; letter-spacing:0.2em; text-transform:uppercase; color:#7a8ba8; margin-bottom:0.3rem;">
            INTELLIGENCE PLATFORM
        </div>
        <div style="font-family:'Playfair Display',Georgia,serif; font-size:1.1rem; font-weight:700; color:#ffffff; line-height:1.2;">
            Macro-Risk Hub
        </div>
        <div style="font-size:0.68rem; color:#7a8ba8; margin-top:0.3rem; font-family:'Source Sans 3',sans-serif;">
            2026 Edition
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # API Key
    st.markdown("## API Configuration")
    api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
        except:
            pass

    if api_key:
        st.success("API key configured")
    else:
        st.warning("API key required for AI analysis")

    st.markdown("---")

    # Data Sources
    st.markdown("## Data Sources")
    categories = list(set(s["category"] for s in ALL_SOURCES))
    selected_category = st.selectbox("Filter by category", ["All"] + sorted(categories))

    filtered_sources = ALL_SOURCES
    if selected_category != "All":
        filtered_sources = [s for s in ALL_SOURCES if s["category"] == selected_category]

    source_names = [s["name"] for s in filtered_sources]
    selected_sources = st.multiselect(
        "Active sources",
        options=source_names,
        default=source_names[:10]
    )

    st.markdown("## Refresh Settings")
    update_freq = st.slider("Cache duration (seconds)", 300, 7200, 3600, step=300)

    st.markdown("<br>", unsafe_allow_html=True)

    fetch_clicked = st.button("Fetch Selected Sources", use_container_width=True, type="primary")
    if fetch_clicked:
        with st.spinner(f"Retrieving data from {len(selected_sources)} sources…"):
            results = st.session_state.data_manager.fetch_selected(selected_sources)
            st.session_state.fetched_results = results
            st.session_state.last_fetch_time = time.time()
            success_count = sum(1 for v in results.values() if "error" not in v)
            st.success(f"{success_count} of {len(selected_sources)} sources retrieved")

    if st.session_state.last_fetch_time:
        st.caption(f"Last updated: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_fetch_time))}")

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'Source Sans 3',sans-serif; font-size:0.65rem; color:#4a5a70; line-height:1.6; padding-bottom:0.5rem;">
        © 2026 Macro-Risk Intelligence Hub<br>
        All data sourced from public APIs.<br>
        For informational purposes only.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 9. MAIN DASHBOARD
# ==========================================

# ── Page header ──
st.markdown("""
<div style="border-bottom:2px solid #1a2340; padding-bottom:1rem; margin-bottom:1.5rem;">
    <div style="font-family:'Source Sans 3',sans-serif; font-size:0.62rem; font-weight:600;
                letter-spacing:0.2em; text-transform:uppercase; color:#8a95a3; margin-bottom:0.4rem;">
        Global Intelligence Report
    </div>
    <h1 style="margin:0 0 0.3rem 0; font-family:'Playfair Display',Georgia,serif;
               font-size:2rem; font-weight:700; color:#1a2340;">
        Macro-Risk Intelligence Hub
    </h1>
    <div style="font-family:'Source Sans 3',sans-serif; font-size:0.85rem; color:#8a95a3;">
        Real-time monitoring &nbsp;·&nbsp; Multi-source aggregation &nbsp;·&nbsp; AI-powered analysis &nbsp;·&nbsp; 2026
    </div>
</div>
""", unsafe_allow_html=True)


if st.session_state.fetched_results:
    results = st.session_state.fetched_results

    # ── Spot Prices ──
    st.markdown("## Market Snapshot")

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
        st.info("No price data available. Select sources and fetch data.")

    st.divider()

    # ── Category Tabs ──
    st.markdown("## Data by Category")

    tab_labels = ["Energy", "Metals", "Agriculture", "Economic", "Monetary",
                  "Currency", "Equities", "Crypto", "News", "Geopolitical"]
    tabs = st.tabs(tab_labels)

    for tab, category in zip(tabs, tab_labels):
        with tab:
            df = format_results_for_category(results, category)
            if not df.empty:
                # Colour the Change and Status columns
                def style_change(val):
                    if isinstance(val, str) and val.startswith('+'):
                        return 'color: #1a7a4a; font-weight:600'
                    elif isinstance(val, str) and val.startswith('-'):
                        return 'color: #c0392b; font-weight:600'
                    return ''

                def style_status(val):
                    if val == "Error":
                        return 'color: #c0392b'
                    elif val == "Live":
                        return 'color: #1a7a4a; font-weight:500'
                    return 'color: #8a95a3'

                styled_df = (
                    df.style
                    .applymap(style_change, subset=['Change'])
                    .applymap(style_status, subset=['Status'])
                )
                st.dataframe(styled_df, use_container_width=True, height=300)

                # News headlines expanded view
                if category == "News":
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("#### Recent Headlines")
                    for src_name, data in results.items():
                        src = next((s for s in ALL_SOURCES if s["name"] == src_name), None)
                        if src and src["category"] == "News" and "headlines" in data:
                            with st.expander(f"**{src_name}**", expanded=False):
                                for hl in data["headlines"]:
                                    st.markdown(
                                        f"<div style='font-size:0.83rem; padding:0.4rem 0; "
                                        f"border-bottom:1px solid #e2e6ed; font-family:\"Source Sans 3\",sans-serif;'>"
                                        f"<a href='{hl['link']}' target='_blank' "
                                        f"style='color:#003087; text-decoration:none; font-weight:500;'>"
                                        f"{hl['title']}</a>"
                                        f"<span style='color:#8a95a3; font-size:0.72rem; margin-left:0.8rem;'>"
                                        f"{hl['published']}</span></div>",
                                        unsafe_allow_html=True
                                    )
            else:
                st.markdown(
                    "<div style='color:#8a95a3; font-size:0.82rem; padding:1rem 0;'>"
                    "No data available in this category. Select relevant sources in the sidebar and fetch."
                    "</div>",
                    unsafe_allow_html=True
                )

    # ── AI Analysis ──
    st.divider()
    st.markdown("## AI Strategic Analysis")
    st.markdown(
        "<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.85rem; color:#4a5568; "
        "margin-bottom:1rem;'>Select an analytical framework and generate a forward-looking "
        "briefing grounded in the current data environment.</div>",
        unsafe_allow_html=True
    )

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        analysis_type = st.selectbox(
            "Analytical framework",
            ["General Macro", "Energy & Maritime", "LATAM/Caribbean Risk",
             "Tech & Digitalization", "Warehouse Ops", "PM Risk",
             "Crypto", "Geopolitical Power"],
            key="analysis_selector",
            label_visibility="collapsed"
        )
    with col_btn:
        generate_clicked = st.button("Generate Briefing", type="primary", use_container_width=True)

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

    if generate_clicked:
        if not api_key:
            st.error("A DeepSeek API key is required to generate analysis.")
        elif not st.session_state.fetched_results:
            st.warning("Please fetch data before generating a briefing.")
        else:
            st.session_state.analysis_in_progress = True

            with st.status("Generating strategic briefing…", expanded=True) as status:
                st.write("Compiling market data…")
                market_lines, news_lines = [], []
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

                st.write("Calling AI analysis engine…")
                report = analyze_with_deepseek(
                    prompt_map[analysis_type], market_context, news_context, api_key
                )
                status.update(label="Briefing complete", state="complete")

            # Render the briefing in a styled container
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #e2e6ed; border-top:3px solid #1a2340;
                        border-radius:3px; padding:2rem 2.4rem; box-shadow:0 1px 4px rgba(0,0,0,0.08);">
                <div style="font-family:'Source Sans 3',sans-serif; font-size:0.6rem; font-weight:600;
                            letter-spacing:0.18em; text-transform:uppercase; color:#8a95a3;
                            margin-bottom:0.6rem;">Strategic Intelligence Report · 2026</div>
            """, unsafe_allow_html=True)
            st.markdown(report)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="Download Report (Markdown)",
                data=report,
                file_name=f"macro_risk_briefing_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=False
            )
            st.session_state.analysis_in_progress = False

else:
    # ── Empty state ──
    st.markdown("""
    <div style="background:#ffffff; border:1px solid #e2e6ed; border-radius:3px;
                padding:2.5rem 2rem; text-align:center; margin-top:1rem;
                box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="font-size:2rem; margin-bottom:0.8rem;">📊</div>
        <div style="font-family:'Playfair Display',Georgia,serif; font-size:1.2rem;
                    font-weight:600; color:#1a2340; margin-bottom:0.5rem;">
            No Data Loaded
        </div>
        <div style="font-family:'Source Sans 3',sans-serif; font-size:0.85rem; color:#8a95a3;
                    max-width:380px; margin:0 auto; line-height:1.6;">
            Select your data sources in the sidebar and click <strong>Fetch Selected Sources</strong>
            to begin your analysis session.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## Preview")
    col1, col2, col3, col4 = st.columns(4)
    placeholder_metrics = [
        ("Crude Oil (WTI)", "—", "—"),
        ("Gold", "—", "—"),
        ("S&P 500", "—", "—"),
        ("VIX", "—", "—"),
    ]
    for col, (label, val, delta) in zip([col1, col2, col3, col4], placeholder_metrics):
        with col:
            st.metric(label=label, value=val, delta=delta)

    st.caption("Awaiting data fetch to populate dashboard.")
