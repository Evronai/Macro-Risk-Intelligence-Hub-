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
import io
import re

# reportlab imports for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Macro-Risk Intelligence Hub",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CUSTOM CSS — BIG 4 PROFESSIONAL THEME
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@300;400;500;600&family=Source+Code+Pro:wght@400;500&display=swap');

    /* ── CSS Variables ── */
    :root {
        --bg-primary:        #f4f5f8;
        --bg-secondary:      #ffffff;
        --bg-tint-blue:      #eef2f9;
        --bg-tint-gold:      #fdf8ed;
        --bg-tint-green:     #edf7f2;
        --bg-tint-slate:     #f0f3f8;
        --bg-sidebar:        #1a2340;
        --bg-sidebar-hover:  #243058;
        --accent-navy:       #1a2340;
        --accent-blue:       #2655a3;
        --accent-blue-light: #dce8f7;
        --accent-gold:       #c8960c;
        --accent-gold-light: #fdefc8;
        --accent-teal:       #0e7490;
        --accent-teal-light: #cff0f8;
        --accent-indigo:     #4f46e5;
        --accent-indigo-light: #ede9fe;
        --accent-amber:      #b45309;
        --accent-amber-light:#fef3c7;
        --accent-red:        #b91c1c;
        --accent-red-light:  #fee2e2;
        --accent-green:      #166534;
        --accent-green-light:#dcfce7;
        --accent-rose:       #9f1239;
        --accent-rose-light: #ffe4e6;
        --text-primary:      #0f1923;
        --text-secondary:    #374151;
        --text-muted:        #6b7280;
        --text-sidebar:      #b8c4d8;
        --text-sidebar-label:#7a8ba8;
        --border-light:      #e2e6ed;
        --border-medium:     #c8cfd9;
        --shadow-card:       0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04);
        --shadow-hover:      0 4px 20px rgba(0,0,0,0.11);
        --font-display:      'Playfair Display', Georgia, serif;
        --font-body:         'Source Sans 3', 'Helvetica Neue', sans-serif;
        --font-mono:         'Source Code Pro', 'Courier New', monospace;
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

    /* ── Main content area — subtle warm tint ── */
    .main .block-container {
        background: linear-gradient(160deg, #f4f5f8 0%, #f0f4fb 100%);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2340 0%, #1e2a50 100%) !important;
        border-right: none;
    }
    [data-testid="stSidebar"] > div {
        padding-top: 0 !important;
    }

    /* Sidebar text styling — use specific selectors, NOT wildcard * */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span:not([data-baseweb="tag"] span),
    [data-testid="stSidebar"] div.stMarkdown,
    [data-testid="stSidebar"] .stCaption {
        font-family: var(--font-body) !important;
        color: var(--text-sidebar) !important;
    }

    /* Hide duplicate title on desktop only */
    @media (min-width: 769px) {
        [data-testid="stSidebarHeader"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
    }

    /* ── Mobile sidebar toggle button (hamburger) ── */
    /* Streamlit puts the open-sidebar button in the top toolbar */
    @media (max-width: 768px) {
        /* Ensure the toolbar that contains the hamburger is visible */
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        header[data-testid="stHeader"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: all !important;
        }
        /* The actual sidebar toggle/collapse button */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarNavItems"],
        button[kind="header"],
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: all !important;
            color: var(--accent-navy) !important;
            z-index: 9999 !important;
        }
        /* Sidebar itself — slide-over on mobile */
        [data-testid="stSidebar"] {
            min-width: 280px !important;
            max-width: 88vw !important;
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
            z-index: 9998 !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            overflow-y: auto !important;
            padding-bottom: 4rem !important;
        }
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
        background-color: #1d4494 !important;
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

    /* ── Section divider ── */
    hr {
        border: none;
        border-top: 1px solid var(--border-light);
        margin: 1.5rem 0;
    }

    /* ── Section label tint blocks ── */
    .section-market {
        background: linear-gradient(90deg, var(--bg-tint-blue) 0%, transparent 100%);
        border-left: 3px solid var(--accent-blue);
        padding: 0.5rem 0.9rem;
        margin-bottom: 1rem;
        border-radius: 0 3px 3px 0;
    }
    .section-data {
        background: linear-gradient(90deg, var(--bg-tint-slate) 0%, transparent 100%);
        border-left: 3px solid var(--accent-teal);
        padding: 0.5rem 0.9rem;
        margin-bottom: 1rem;
        border-radius: 0 3px 3px 0;
    }
    .section-ai {
        background: linear-gradient(90deg, var(--bg-tint-gold) 0%, transparent 100%);
        border-left: 3px solid var(--accent-gold);
        padding: 0.5rem 0.9rem;
        margin-bottom: 1rem;
        border-radius: 0 3px 3px 0;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-top: 3px solid var(--accent-blue);
        border-radius: 3px;
        padding: 1rem 1.1rem;
        box-shadow: var(--shadow-card);
        transition: box-shadow 0.2s, border-top-color 0.2s;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-hover);
        border-top-color: var(--accent-gold);
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
        transition: color 0.15s, background-color 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-blue);
        background-color: var(--bg-tint-blue);
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-blue) !important;
        border-bottom: 2px solid var(--accent-blue) !important;
        background-color: var(--bg-tint-blue) !important;
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
        background-color: #f0f4fb !important;
    }
    .stDataFrame tbody tr:hover {
        background-color: var(--bg-tint-blue) !important;
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
        background-color: var(--bg-tint-blue);
        color: var(--accent-blue);
        border-color: var(--accent-blue);
    }
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
        border-left: 4px solid var(--accent-blue) !important;
        background-color: var(--bg-tint-blue) !important;
        font-family: var(--font-body) !important;
        font-size: 0.82rem !important;
    }
    .stAlert p { color: var(--text-secondary) !important; }

    /* ── Success / Warning / Error ── */
    [data-testid="stNotification"][data-type="success"] {
        border-left-color: var(--accent-green) !important;
        background-color: var(--accent-green-light) !important;
    }
    [data-testid="stNotification"][data-type="warning"] {
        border-left-color: var(--accent-amber) !important;
        background-color: var(--accent-amber-light) !important;
    }
    [data-testid="stNotification"][data-type="error"] {
        border-left-color: var(--accent-red) !important;
        background-color: var(--accent-red-light) !important;
    }

    /* ── Status widget ── */
    [data-testid="stStatusWidget"] {
        background-color: var(--bg-tint-blue) !important;
        border: 1px solid var(--accent-blue-light) !important;
        border-left: 3px solid var(--accent-blue) !important;
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
        background-color: var(--bg-tint-blue) !important;
        color: var(--accent-blue) !important;
        border: 1.5px solid var(--accent-blue-light) !important;
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .stDownloadButton button:hover {
        background-color: var(--accent-blue) !important;
        color: #ffffff !important;
        border-color: var(--accent-blue) !important;
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
    .stTextInput input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px var(--accent-blue-light) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--accent-blue) !important; }

    /* ── Caption / small text ── */
    .stCaption, caption {
        font-family: var(--font-body) !important;
        font-size: 0.72rem !important;
        color: var(--text-muted) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #eef1f6; }
    ::-webkit-scrollbar-thumb { background: #b8c4d8; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #8a9ab8; }

    /* ── AI Briefing output ── */
    .briefing-container {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-top: 3px solid var(--accent-gold);
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
    .briefing-container strong { color: var(--accent-navy); }
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
        background-color: var(--bg-tint-blue);
    }

    /* ── Page header banner ── */
    .page-header {
        background: linear-gradient(90deg, #1a2340 0%, #2a3a60 100%);
        margin: -1rem -1rem 1.5rem -1rem;
        padding: 1.2rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* ── Placeholder cards ── */
    .placeholder-card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-light);
        border-top: 3px solid var(--border-medium);
        border-radius: 3px;
        padding: 1rem;
        text-align: center;
    }

    /* ── Multiselect tags ── */
    [data-baseweb="tag"] {
        background-color: var(--accent-blue) !important;
        border-radius: 2px !important;
    }
    [data-baseweb="tag"] span {
        color: #ffffff !important;
        font-family: var(--font-body) !important;
        font-size: 0.72rem !important;
    }

    /* ── Status badges ── */
    .badge-live {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        background-color: var(--accent-green-light);
        color: var(--accent-green);
        border: 1px solid #bbf7d0;
        border-radius: 2px;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .badge-pending {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        background-color: var(--accent-amber-light);
        color: var(--accent-amber);
        border: 1px solid #fde68a;
        border-radius: 2px;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    /* ══════════════════════════════════════
       MOBILE RESPONSIVE STYLES
       ══════════════════════════════════════ */

    /* ── Fluid base on small screens ── */
    @media (max-width: 768px) {

        /* Tighter page padding */
        .main .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.5rem !important;
        }

        /* Scale down page title */
        h1 {
            font-size: 1.3rem !important;
            line-height: 1.25 !important;
        }
        h2 {
            font-size: 0.6rem !important;
            margin-top: 1.2rem !important;
        }
        h3 {
            font-size: 0.95rem !important;
        }

        /* Page header banner — stack vertically */
        .page-header {
            flex-direction: column !important;
            align-items: flex-start !important;
            padding: 0.8rem 1rem !important;
            gap: 0.3rem;
        }

        /* Section tint strips — reduce padding */
        .section-market,
        .section-data,
        .section-ai {
            padding: 0.4rem 0.7rem !important;
            margin-bottom: 0.7rem !important;
        }

        /* Metric cards — smaller text on mobile */
        [data-testid="stMetric"] {
            padding: 0.7rem 0.8rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.05rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.6rem !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.7rem !important;
        }

        /* Tabs — smaller, allow scroll */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.65rem !important;
            padding: 0.55rem 0.7rem !important;
            white-space: nowrap !important;
            letter-spacing: 0.02em !important;
        }

        /* Price cards — tighter on mobile */
        div[style*="border-left:3px solid"] {
            padding: 0.7rem 0.75rem !important;
            margin-bottom: 0.6rem !important;
        }

        /* Tables — allow horizontal scroll */
        .stDataFrame, table {
            font-size: 0.72rem !important;
            display: block !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }
        .stDataFrame thead tr th {
            font-size: 0.6rem !important;
            padding: 0.4rem 0.5rem !important;
        }
        .stDataFrame tbody tr td {
            padding: 0.35rem 0.5rem !important;
        }

        /* News feed — reduce padding */
        div[style*="border-bottom:1px solid #e2e6ed"] {
            padding: 0.5rem 0.75rem !important;
        }

        /* Tab sub-header strip */
        div[style*="border-left:3px solid"] {
            font-size: 0.72rem !important;
        }

        /* Buttons — full width on mobile */
        .stButton button {
            font-size: 0.72rem !important;
            padding: 0.5rem 0.6rem !important;
        }

        /* Selectbox / inputs */
        .stSelectbox [data-baseweb="select"],
        .stTextInput input {
            font-size: 0.8rem !important;
        }

        /* Download button */
        .stDownloadButton button {
            font-size: 0.7rem !important;
            width: 100% !important;
        }

        /* AI briefing output */
        .briefing-container {
            padding: 1.2rem 1rem !important;
        }
        .briefing-container h3 {
            font-size: 1.05rem !important;
        }
        .briefing-container p,
        .briefing-container ul li {
            font-size: 0.82rem !important;
        }

        /* Inline HTML tables used in kv/geo sections */
        table[style*="border-collapse:collapse"] {
            font-size: 0.72rem !important;
            display: block !important;
            overflow-x: auto !important;
        }
        table[style*="border-collapse:collapse"] th,
        table[style*="border-collapse:collapse"] td {
            padding: 0.35rem 0.5rem !important;
            white-space: normal !important;
            word-break: break-word;
        }

        /* Empty state card */
        div[style*="text-align:center"][style*="padding:2.5rem"] {
            padding: 1.5rem 1rem !important;
        }
    }

    /* ── Extra small screens (≤480px) ── */
    @media (max-width: 480px) {
        h1 { font-size: 1.1rem !important; }

        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 0.95rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.58rem !important;
            padding: 0.5rem 0.55rem !important;
        }
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
    {"name": "US GDP (Current USD)", "type": "geo_worldbank", "indicator": "NY.GDP.MKTP.CD", "country": "USA", "category": "Economic"},
    {"name": "US GDP Growth Rate", "type": "geo_worldbank", "indicator": "NY.GDP.MKTP.KD.ZG", "country": "USA", "category": "Economic"},
    {"name": "US Unemployment Rate", "type": "geo_worldbank", "indicator": "SL.UEM.TOTL.ZS", "country": "USA", "category": "Economic"},
    {"name": "US CPI Inflation", "type": "geo_worldbank", "indicator": "FP.CPI.TOTL.ZG", "country": "USA", "category": "Economic"},
    {"name": "US Fed Funds Rate", "type": "yfinance", "symbol": "^IRX", "category": "Monetary"},
    {"name": "US 10-Year Treasury", "type": "yfinance", "symbol": "^TNX", "category": "Monetary"},
    {"name": "US 2-Year Treasury", "type": "yfinance", "symbol": "^FVX", "category": "Monetary"},
    {"name": "US Dollar Index", "type": "yfinance", "symbol": "DX-Y.NYB", "category": "Currency"},
    {"name": "EUR/USD", "type": "yfinance", "symbol": "EURUSD=X", "category": "Currency"},
    {"name": "GBP/USD", "type": "yfinance", "symbol": "GBPUSD=X", "category": "Currency"},
    {"name": "USD/JPY", "type": "yfinance", "symbol": "JPY=X", "category": "Currency"},
    {"name": "USD/CNY", "type": "yfinance", "symbol": "CNY=X", "category": "Currency"},
    {"name": "Bitcoin", "type": "yfinance", "symbol": "BTC-USD", "category": "Crypto"},
    {"name": "Ethereum", "type": "yfinance", "symbol": "ETH-USD", "category": "Crypto"},
    {"name": "Solana", "type": "yfinance", "symbol": "SOL-USD", "category": "Crypto"},
    {"name": "XRP", "type": "yfinance", "symbol": "XRP-USD", "category": "Crypto"},
    {"name": "S&P 500", "type": "yfinance", "symbol": "^GSPC", "category": "Equities"},
    {"name": "Dow Jones", "type": "yfinance", "symbol": "^DJI", "category": "Equities"},
    {"name": "NASDAQ", "type": "yfinance", "symbol": "^IXIC", "category": "Equities"},
    {"name": "Russell 2000", "type": "yfinance", "symbol": "^RUT", "category": "Equities"},
    {"name": "FTSE 100", "type": "yfinance", "symbol": "^FTSE", "category": "Equities"},
    {"name": "DAX", "type": "yfinance", "symbol": "^GDAXI", "category": "Equities"},
    {"name": "Nikkei 225", "type": "yfinance", "symbol": "^N225", "category": "Equities"},
    {"name": "Hang Seng", "type": "yfinance", "symbol": "^HSI", "category": "Equities"},
    {"name": "VIX", "type": "yfinance", "symbol": "^VIX", "category": "Equities"},
    {"name": "China PMI (Shanghai Comp)", "type": "yfinance", "symbol": "000001.SS", "category": "Economic"},
    {"name": "Eurozone GDP Growth", "type": "geo_worldbank", "indicator": "NY.GDP.MKTP.KD.ZG", "country": "EMU", "category": "Economic"},
    {"name": "Japan CPI Inflation", "type": "geo_worldbank", "indicator": "FP.CPI.TOTL.ZG", "country": "JPN", "category": "Economic"},
    {"name": "UK Unemployment Rate", "type": "geo_worldbank", "indicator": "SL.UEM.TOTL.ZS", "country": "GBR", "category": "Economic"},
    {"name": "Brazil Interest Rate (EWZ)", "type": "yfinance", "symbol": "EWZ", "category": "Monetary"},
    {"name": "India GDP Growth", "type": "geo_worldbank", "indicator": "NY.GDP.MKTP.KD.ZG", "country": "IND", "category": "Economic"},
    {"name": "Australia CPI Inflation", "type": "geo_worldbank", "indicator": "FP.CPI.TOTL.ZG", "country": "AUS", "category": "Economic"},

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
    # USGS: M5.5+ earthquakes in last 30 days (free, no key)
    {"name": "USGS Earthquakes (M5.5+)",
     "type": "geo_usgs",
     "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5.5&limit=10&orderby=time",
     "category": "Geopolitical"},

    # Open-Meteo: current global weather/climate indicators (free, no key)
    {"name": "Open-Meteo Climate (London)",
     "type": "geo_openmeteo",
     "url": "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current=temperature_2m,windspeed_10m,precipitation&timezone=UTC",
     "category": "Geopolitical"},
    {"name": "Open-Meteo Climate (New York)",
     "type": "geo_openmeteo",
     "url": "https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74.01&current=temperature_2m,windspeed_10m,precipitation&timezone=UTC",
     "category": "Geopolitical"},
    {"name": "Open-Meteo Climate (Singapore)",
     "type": "geo_openmeteo",
     "url": "https://api.open-meteo.com/v1/forecast?latitude=1.35&longitude=103.82&current=temperature_2m,windspeed_10m,precipitation&timezone=UTC",
     "category": "Geopolitical"},
    {"name": "Open-Meteo Climate (Dubai)",
     "type": "geo_openmeteo",
     "url": "https://api.open-meteo.com/v1/forecast?latitude=25.20&longitude=55.27&current=temperature_2m,windspeed_10m,precipitation&timezone=UTC",
     "category": "Geopolitical"},

    # World Bank: key development indicators (free, no key)
    {"name": "World Bank — Global GDP (current USD)",
     "type": "geo_worldbank",
     "indicator": "NY.GDP.MKTP.CD", "country": "WLD",
     "category": "Geopolitical"},
    {"name": "World Bank — Global Inflation",
     "type": "geo_worldbank",
     "indicator": "FP.CPI.TOTL.ZG", "country": "WLD",
     "category": "Geopolitical"},
    {"name": "World Bank — US Debt (% GDP)",
     "type": "geo_worldbank",
     "indicator": "GC.DOD.TOTL.GD.ZS", "country": "USA",
     "category": "Geopolitical"},
    {"name": "World Bank — China GDP Growth",
     "type": "geo_worldbank",
     "indicator": "NY.GDP.MKTP.KD.ZG", "country": "CHN",
     "category": "Geopolitical"},
    {"name": "World Bank — EU Unemployment",
     "type": "geo_worldbank",
     "indicator": "SL.UEM.TOTL.ZS", "country": "EUU",
     "category": "Geopolitical"},

    # REST Countries: regional summaries (free, no key) — fixed URL with fields
    {"name": "REST Countries — Americas",
     "type": "geo_restcountries",
     "region": "americas",
     "category": "Geopolitical"},
    {"name": "REST Countries — Asia",
     "type": "geo_restcountries",
     "region": "asia",
     "category": "Geopolitical"},
    {"name": "REST Countries — Europe",
     "type": "geo_restcountries",
     "region": "europe",
     "category": "Geopolitical"},

    # Nager.Date: upcoming US public holidays (free, no key)
    {"name": "US Public Holidays 2026",
     "type": "geo_holidays",
     "url": "https://date.nager.at/api/v3/publicholidays/2026/US",
     "category": "Geopolitical"},
    {"name": "UK Public Holidays 2026",
     "type": "geo_holidays",
     "url": "https://date.nager.at/api/v3/publicholidays/2026/GB",
     "category": "Geopolitical"},
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
            elif source["type"] == "geo_usgs":
                return self._fetch_geo_usgs(source)
            elif source["type"] == "geo_openmeteo":
                return self._fetch_geo_openmeteo(source)
            elif source["type"] == "geo_worldbank":
                return self._fetch_geo_worldbank(source)
            elif source["type"] == "geo_restcountries":
                return self._fetch_geo_restcountries(source)
            elif source["type"] == "geo_holidays":
                return self._fetch_geo_holidays(source)
            elif source["type"] == "csv":
                return {"note": "CSV source not fully implemented"}
            else:
                return {"error": f"Unknown type: {source['type']}"}
        except Exception as e:
            return {"error": str(e)}

    def _fetch_yfinance(self, source):
        ticker = yf.Ticker(source["symbol"])
        hist = ticker.history(period="30d")
        if hist.empty or len(hist) < 1:
            return {"error": "No data"}
        closes = [round(float(v), 4) for v in hist['Close'].tolist()]
        price = closes[-1]
        prev  = closes[-2] if len(closes) >= 2 else price
        change = round(price - prev, 4)
        return {
            "price":  round(price, 2),
            "change": round(change, 2),
            "spark":  closes,   # list of up to ~22 daily closes
        }

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

    def _fetch_geo_usgs(self, source: Dict) -> Dict:
        """USGS Earthquake Hazards — M5.5+ recent events."""
        resp = self.session.get(source["url"], timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json()
        features = data.get("features", [])
        events = []
        for f in features[:8]:
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [None, None, None])
            events.append({
                "place": props.get("place", "Unknown"),
                "magnitude": props.get("mag", "?"),
                "depth_km": round(coords[2], 1) if coords[2] is not None else "?",
                "time": time.strftime("%Y-%m-%d %H:%M", time.gmtime(props["time"] / 1000)) if props.get("time") else "?",
                "alert": props.get("alert") or "—",
            })
        return {
            "value": f"{len(features)} events",
            "date": "Last 30 days",
            "geo_type": "usgs",
            "events": events,
        }

    def _fetch_geo_openmeteo(self, source: Dict) -> Dict:
        """Open-Meteo current weather — free, no API key."""
        resp = self.session.get(source["url"], timeout=10)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json()
        current = data.get("current", {})
        units = data.get("current_units", {})
        temp = current.get("temperature_2m", "?")
        wind = current.get("windspeed_10m", "?")
        precip = current.get("precipitation", "?")
        temp_u = units.get("temperature_2m", "°C")
        wind_u = units.get("windspeed_10m", "km/h")
        return {
            "value": f"{temp}{temp_u}",
            "date": current.get("time", ""),
            "geo_type": "weather",
            "detail": f"Wind {wind} {wind_u} · Precip {precip} mm",
        }

    def _fetch_geo_worldbank(self, source: Dict) -> Dict:
        """World Bank Open Data — indicator for a country, most recent value."""
        indicator = source["indicator"]
        country = source["country"]
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&mrv=3&per_page=3"
        resp = self.session.get(url, timeout=12)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        try:
            payload = resp.json()
        except Exception:
            return {"error": "Invalid JSON response"}
        if not payload or len(payload) < 2 or not payload[1]:
            return {"error": "No data returned"}
        # Find first non-null value
        for obs in payload[1]:
            if obs.get("value") is not None:
                raw_val = obs["value"]
                # Format sensibly
                if isinstance(raw_val, float) and raw_val > 1_000_000_000:
                    display = f"${raw_val / 1e12:.2f}T"
                elif isinstance(raw_val, float):
                    display = f"{raw_val:.2f}"
                else:
                    display = str(raw_val)
                return {
                    "value": display,
                    "date": obs.get("date", ""),
                    "geo_type": "worldbank",
                }
        return {"error": "All recent values null"}

    def _fetch_geo_restcountries(self, source: Dict) -> Dict:
        """REST Countries v3.1 — summary stats for a region."""
        region = source["region"]
        url = f"https://restcountries.com/v3.1/region/{region}?fields=name,population,area,subregion"
        resp = self.session.get(url, timeout=12)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        try:
            countries = resp.json()
        except Exception:
            return {"error": "Invalid JSON response"}
        if not isinstance(countries, list):
            return {"error": "Unexpected response format"}
        total_pop = sum(c.get("population", 0) for c in countries)
        total_area = sum(c.get("area") or 0 for c in countries)
        return {
            "value": f"{len(countries)} countries",
            "date": f"Pop: {total_pop / 1e9:.2f}B · Area: {total_area / 1e6:.1f}M km²",
            "geo_type": "restcountries",
        }

    def _fetch_geo_holidays(self, source: Dict) -> Dict:
        """Nager.Date — upcoming public holidays."""
        resp = self.session.get(source["url"], timeout=10)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        try:
            holidays = resp.json()
        except Exception:
            return {"error": "Invalid JSON response"}
        today = time.strftime("%Y-%m-%d")
        upcoming = [h for h in holidays if h.get("date", "") >= today][:5]
        return {
            "value": f"{len(holidays)} holidays",
            "date": f"Next: {upcoming[0]['name']} ({upcoming[0]['date']})" if upcoming else "None upcoming",
            "geo_type": "holidays",
        }

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
        "headings, bullet points, and where appropriate, tables. Be concise but comprehensive. "
        "**CRITICAL — POLITICAL FACTS:** Your training data has a knowledge cutoff and WILL contain "
        "outdated or incorrect political information. Do NOT state specific electoral outcomes, "
        "ruling parties, or heads of government from memory unless they are explicitly stated in "
        "the data provided to you. Where political context is provided in the prompt, treat it as "
        "ground truth and use it as the basis for your analysis. If no current political data is "
        "provided for a country, acknowledge uncertainty rather than asserting stale facts."
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

**VERIFIED POLITICAL CONTEXT — USE AS GROUND TRUTH:**
- **Trinidad & Tobago (2026):** A general election was held in 2025. A new government came to power with a slim majority. Do NOT reference or name any specific political party as governing or in opposition — party names are omitted intentionally. Analyse T&T solely through its policy outlook, energy sector priorities, and economic implications.

Focus on Trinidad & Tobago, the wider Caribbean, and key Latin American economies (Brazil, Mexico, Argentina, Venezuela, Colombia). Your analysis must address:

- **Political Stability & Governance**: For T&T, analyse the new government's likely policy priorities (energy sector, cost of living, foreign investment, crime). For other countries, note recent elections, protests, or policy shifts that could impact business operations. Flag where political data is uncertain.
- **Economic Vulnerability**: Currency volatility, inflation, debt levels, and reliance on commodity exports.
- **Shipping & Trade Chokepoints**: Assess risks to maritime routes (Panama Canal, Caribbean passages, Amazon River ports).
- **Energy & Mining Sector Focus**: For Trinidad (LNG, petrochemicals — note new government in place since 2025), Guyana (oil boom), Venezuela (sanctions), Chile/Peru (copper), Brazil (mining, agribusiness).
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
                # Prefer 'detail' over 'date' for secondary column
                secondary = data.get("detail") or data.get("date") or "—"
                rows.append({"Source": src_name, "Value": data["value"], "Change": secondary, "Status": "Live"})
            elif "data" in data:
                rows.append({"Source": src_name, "Value": "API data received", "Change": "—", "Status": "Live"})
            elif "note" in data:
                rows.append({"Source": src_name, "Value": "—", "Change": data["note"], "Status": "Info"})
            else:
                rows.append({"Source": src_name, "Value": "Received", "Change": "—", "Status": "Live"})
    return pd.DataFrame(rows)


# ==========================================
# 7. SPARKLINE SVG GENERATOR
# ==========================================
def make_sparkline(values: list, color: str, width: int = 120, height: int = 36) -> str:
    """
    Generate an inline SVG sparkline from a list of price values.
    Returns an SVG string ready to embed in HTML.
    """
    if not values or len(values) < 2:
        return ""

    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1.0

    pad_x, pad_y = 2, 3
    uw = width  - pad_x * 2
    uh = height - pad_y * 2
    n  = len(values)

    # Build polyline points
    pts = []
    for i, v in enumerate(values):
        x = pad_x + (i / (n - 1)) * uw
        y = pad_y + (1 - (v - mn) / rng) * uh
        pts.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(pts)

    # Filled area path (close back to baseline)
    first_x = pad_x
    last_x  = pad_x + uw
    baseline = pad_y + uh
    area_pts = f"{first_x:.1f},{baseline:.1f} " + polyline + f" {last_x:.1f},{baseline:.1f}"

    # Determine fill/stroke opacity based on trend
    fill_opacity = "0.08"
    stroke_width = "1.5"

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        f'style="display:block; overflow:visible;">'
        # Area fill
        f'<polygon points="{area_pts}" '
        f'fill="{color}" fill-opacity="{fill_opacity}" stroke="none"/>'
        # Line
        f'<polyline points="{polyline}" '
        f'fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        # End dot
        f'<circle cx="{float(pts[-1].split(",")[0]):.1f}" '
        f'cy="{float(pts[-1].split(",")[1]):.1f}" '
        f'r="2.2" fill="{color}"/>'
        f'</svg>'
    )
    return svg


# ==========================================
# 8. PDF GENERATION FUNCTION (renumbered)
# ==========================================
def generate_pdf_report(markdown_text: str, analysis_type: str) -> bytes:
    """Convert a markdown AI briefing to a styled Big 4-quality PDF."""

    # ── Colour palette ──
    NAVY       = colors.HexColor("#1a2340")
    GOLD       = colors.HexColor("#c8960c")
    LIGHT_GREY = colors.HexColor("#f5f7fb")
    MID_GREY   = colors.HexColor("#e2e6ed")
    TEXT_MAIN  = colors.HexColor("#0f1923")
    TEXT_SEC   = colors.HexColor("#4a5568")
    TEXT_MUTED = colors.HexColor("#8a95a3")
    GREEN      = colors.HexColor("#1a7a4a")
    RED        = colors.HexColor("#c0392b")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"Macro-Risk Intelligence — {analysis_type}",
        author="Macro-Risk Intelligence Hub",
        subject="Strategic Briefing 2026",
    )

    # ── Styles ──
    styles = getSampleStyleSheet()

    cover_label = ParagraphStyle(
        "CoverLabel", fontSize=7, textColor=TEXT_MUTED,
        fontName="Helvetica-Bold", leading=10,
        spaceAfter=4, letterSpacing=1.8, alignment=TA_LEFT
    )
    cover_title = ParagraphStyle(
        "CoverTitle", fontSize=22, textColor=NAVY,
        fontName="Times-Bold", leading=28,
        spaceAfter=6, alignment=TA_LEFT
    )
    cover_sub = ParagraphStyle(
        "CoverSub", fontSize=9.5, textColor=TEXT_SEC,
        fontName="Helvetica", leading=14,
        spaceAfter=4, alignment=TA_LEFT
    )
    h1_style = ParagraphStyle(
        "H1", fontSize=14, textColor=NAVY,
        fontName="Times-Bold", leading=18,
        spaceBefore=16, spaceAfter=6
    )
    h2_style = ParagraphStyle(
        "H2", fontSize=10, textColor=NAVY,
        fontName="Helvetica-Bold", leading=14,
        spaceBefore=14, spaceAfter=4
    )
    h3_style = ParagraphStyle(
        "H3", fontSize=9, textColor=TEXT_SEC,
        fontName="Helvetica-Bold", leading=13,
        spaceBefore=10, spaceAfter=3
    )
    body_style = ParagraphStyle(
        "Body", fontSize=9, textColor=TEXT_MAIN,
        fontName="Helvetica", leading=14,
        spaceBefore=2, spaceAfter=4, alignment=TA_JUSTIFY
    )
    bullet_style = ParagraphStyle(
        "Bullet", fontSize=9, textColor=TEXT_MAIN,
        fontName="Helvetica", leading=14,
        spaceBefore=1, spaceAfter=2,
        leftIndent=16, bulletIndent=6,
        bulletFontName="Helvetica", bulletFontSize=9
    )
    footer_style = ParagraphStyle(
        "Footer", fontSize=7, textColor=TEXT_MUTED,
        fontName="Helvetica", leading=10, alignment=TA_CENTER
    )

    story = []

    # ── Cover block ──
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("MACRO-RISK INTELLIGENCE HUB", cover_label))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))
    story.append(Paragraph("Strategic Intelligence Report", cover_title))
    story.append(Paragraph(f"Framework: {analysis_type} &nbsp;·&nbsp; Period: 2026", cover_sub))
    story.append(Paragraph(
        f"Generated: {time.strftime('%d %B %Y, %H:%M UTC')}",
        cover_sub
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=18))

    # ── Disclaimer box ──
    disclaimer_data = [[
        Paragraph(
            "<b>CONFIDENTIAL — FOR INTERNAL USE ONLY.</b> This report is generated by an "
            "AI-assisted intelligence platform using publicly available data sources. It is "
            "intended for informational purposes only and does not constitute financial, "
            "legal, or investment advice.",
            ParagraphStyle("Disc", fontSize=7.5, textColor=TEXT_SEC,
                           fontName="Helvetica", leading=11)
        )
    ]]
    disclaimer_table = Table(disclaimer_data, colWidths=[doc.width])
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX",        (0, 0), (-1, -1), 0.5, MID_GREY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Parse & render markdown ──
    def escape_xml(text):
        """Escape special XML chars but preserve intentional tags."""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        return text

    def md_inline_to_rl(text):
        """Convert inline markdown bold/italic to ReportLab XML."""
        # Bold+italic
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        # Inline code
        text = re.sub(r'`(.*?)`', r'<font name="Courier" size="8">\1</font>', text)
        return text

    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()

        # Blank line
        if not raw.strip():
            story.append(Spacer(1, 0.15 * cm))
            i += 1
            continue

        # H1
        if raw.startswith("# "):
            text = md_inline_to_rl(escape_xml(raw[2:].strip()))
            story.append(Paragraph(text, h1_style))
            story.append(HRFlowable(width="100%", thickness=0.4, color=MID_GREY, spaceAfter=4))
            i += 1
            continue

        # H2
        if raw.startswith("## "):
            text = md_inline_to_rl(escape_xml(raw[3:].strip()))
            story.append(Paragraph(text, h2_style))
            i += 1
            continue

        # H3
        if raw.startswith("### "):
            text = md_inline_to_rl(escape_xml(raw[4:].strip()))
            story.append(Paragraph(text, h3_style))
            i += 1
            continue

        # Horizontal rule
        if raw.strip() in ("---", "***", "___"):
            story.append(HRFlowable(width="100%", thickness=0.4, color=MID_GREY,
                                    spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # Markdown table — collect all rows
        if raw.strip().startswith("|"):
            table_rows_raw = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_rows_raw.append(lines[i].strip())
                i += 1
            # Filter out separator row (|---|---|)
            table_rows_raw = [r for r in table_rows_raw
                              if not re.match(r'^\|[-| :]+\|$', r)]
            if table_rows_raw:
                parsed = []
                for row in table_rows_raw:
                    cells = [c.strip() for c in row.strip("|").split("|")]
                    parsed.append(cells)
                max_cols = max(len(r) for r in parsed)
                col_w = doc.width / max_cols

                tbl_data = []
                for row_idx, row in enumerate(parsed):
                    # Pad short rows
                    while len(row) < max_cols:
                        row.append("")
                    cell_style = ParagraphStyle(
                        "TC", fontSize=8, fontName="Helvetica-Bold" if row_idx == 0 else "Helvetica",
                        textColor=colors.white if row_idx == 0 else TEXT_MAIN,
                        leading=11, alignment=TA_LEFT
                    )
                    tbl_data.append([
                        Paragraph(md_inline_to_rl(escape_xml(c)), cell_style)
                        for c in row
                    ])

                tbl = Table(tbl_data, colWidths=[col_w] * max_cols, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
                    ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                    ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
                    ("INNERGRID",     (0, 0), (-1, -1), 0.3, MID_GREY),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                    ("TOPPADDING",    (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(KeepTogether([tbl, Spacer(1, 0.3 * cm)]))
            continue

        # Bullet point (- or *)
        if re.match(r'^(\s*[-*+])\s+', raw):
            indent_level = len(raw) - len(raw.lstrip())
            text = re.sub(r'^[\s\-\*\+]+\s*', '', raw)
            text = md_inline_to_rl(escape_xml(text))
            bullet_s = ParagraphStyle(
                "Bul", fontSize=9, textColor=TEXT_MAIN,
                fontName="Helvetica", leading=14,
                spaceBefore=1, spaceAfter=2,
                leftIndent=16 + indent_level * 8,
                bulletIndent=6 + indent_level * 8,
            )
            story.append(Paragraph(f"• {text}", bullet_s))
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.\s+', raw):
            num_match = re.match(r'^(\d+)\.\s+(.*)', raw)
            if num_match:
                num, text = num_match.groups()
                text = md_inline_to_rl(escape_xml(text))
                numbered_s = ParagraphStyle(
                    "Num", fontSize=9, textColor=TEXT_MAIN,
                    fontName="Helvetica", leading=14,
                    spaceBefore=1, spaceAfter=2,
                    leftIndent=20, bulletIndent=6,
                )
                story.append(Paragraph(f"{num}. {text}", numbered_s))
                i += 1
                continue

        # Bold-only line (acts as a sub-heading)
        if re.match(r'^\*\*.*\*\*$', raw.strip()):
            text = md_inline_to_rl(escape_xml(raw.strip()))
            story.append(Paragraph(text, h3_style))
            i += 1
            continue

        # Regular paragraph
        text = md_inline_to_rl(escape_xml(raw))
        story.append(Paragraph(text, body_style))
        i += 1

    # ── Footer ──
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=6))
    story.append(Paragraph(
        "Macro-Risk Intelligence Hub &nbsp;·&nbsp; 2026 &nbsp;·&nbsp; "
        "For informational purposes only. Not financial advice.",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ==========================================
# 8. SESSION STATE (renumbered)
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
# 8. CONFIGURATION PANEL (expander — mobile friendly)
# ==========================================

# Resolve API key from secrets/env first
api_key = os.environ.get("DEEPSEEK_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except:
        pass

# Default sources list
_DEFAULT_PER_CATEGORY = {
    "Energy":       ["Crude Oil (WTI)", "Brent Oil", "Natural Gas", "RBOB Gasoline", "Heating Oil"],
    "Metals":       ["Gold", "Silver", "Copper", "Platinum"],
    "Agriculture":  ["Wheat", "Corn", "Soybeans", "Coffee"],
    "Economic":     ["US GDP (Current USD)", "US GDP Growth Rate", "US Unemployment Rate",
                     "US CPI Inflation", "UK Unemployment Rate", "Eurozone GDP Growth",
                     "Japan CPI Inflation", "India GDP Growth", "Australia CPI Inflation",
                     "China PMI (Shanghai Comp)"],
    "Monetary":     ["US Fed Funds Rate", "US 10-Year Treasury", "US 2-Year Treasury",
                     "Brazil Interest Rate (EWZ)"],
    "Currency":     ["US Dollar Index", "EUR/USD", "GBP/USD", "USD/JPY", "USD/CNY"],
    "Equities":     ["S&P 500", "Dow Jones", "NASDAQ", "Russell 2000",
                     "FTSE 100", "DAX", "Nikkei 225", "Hang Seng", "VIX"],
    "Crypto":       ["Bitcoin", "Ethereum", "Solana", "XRP"],
    "News":         ["BBC Business", "BBC World", "Reuters Business",
                     "CNBC World News", "OilPrice.com", "gCaptain",
                     "The Guardian Economics", "Al Jazeera Business"],
    "Geopolitical": ["USGS Earthquakes (M5.5+)",
                     "Open-Meteo Climate (London)", "Open-Meteo Climate (New York)",
                     "World Bank — Global GDP (current USD)", "World Bank — Global Inflation",
                     "World Bank — US Debt (% GDP)", "World Bank — China GDP Growth",
                     "World Bank — EU Unemployment",
                     "REST Countries — Americas", "REST Countries — Europe",
                     "US Public Holidays 2026", "UK Public Holidays 2026"],
}
_all_defaults = [s for names in _DEFAULT_PER_CATEGORY.values() for s in names
                 if any(src["name"] == s for src in ALL_SOURCES)]

# ── Sidebar — live status & quick-reference panel (desktop) ──
with st.sidebar:
    st.markdown("""
    <div style="background:linear-gradient(180deg,#1a2340 0%,#1e2a50 100%);
                margin:-1rem -1rem 0 -1rem; padding:1.4rem 1.2rem 1rem 1.2rem;
                border-bottom:2px solid #c8960c;">
        <div style="font-family:'Source Sans 3',sans-serif; font-size:0.55rem; font-weight:600;
                    letter-spacing:0.2em; text-transform:uppercase; color:#7a8ba8; margin-bottom:0.3rem;">
            Intelligence Platform
        </div>
        <div style="font-family:'Playfair Display',Georgia,serif; font-size:1.05rem;
                    font-weight:700; color:#ffffff; line-height:1.2;">
            Macro-Risk Hub
        </div>
        <div style="font-size:0.65rem; color:#7a8ba8; margin-top:0.2rem;
                    font-family:'Source Sans 3',sans-serif;">
            2026 Edition
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Status block ──
    results = st.session_state.get("fetched_results")
    last_t  = st.session_state.get("last_fetch_time")

    if last_t:
        st.markdown(
            f"<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.62rem; "
            f"color:#7a8ba8; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.2rem;'>"
            f"Last updated</div>"
            f"<div style='font-family:\"Source Code Pro\",monospace; font-size:0.82rem; "
            f"color:#b8c4d8; margin-bottom:1rem;'>"
            f"{time.strftime('%H:%M:%S', time.localtime(last_t))}</div>",
            unsafe_allow_html=True
        )
        ok  = sum(1 for v in results.values() if "error" not in v)
        err = len(results) - ok
        st.markdown(
            f"<div style='display:flex; gap:0.5rem; margin-bottom:1rem;'>"
            f"<div style='flex:1; background:rgba(22,101,52,0.25); border:1px solid rgba(22,101,52,0.4); "
            f"border-radius:3px; padding:0.5rem 0.4rem; text-align:center;'>"
            f"<div style='font-size:1.1rem; font-weight:700; color:#4ade80;'>{ok}</div>"
            f"<div style='font-size:0.58rem; color:#7a8ba8; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Live</div></div>"
            f"<div style='flex:1; background:rgba(185,28,28,0.2); border:1px solid rgba(185,28,28,0.35); "
            f"border-radius:3px; padding:0.5rem 0.4rem; text-align:center;'>"
            f"<div style='font-size:1.1rem; font-weight:700; color:#f87171;'>{err}</div>"
            f"<div style='font-size:0.58rem; color:#7a8ba8; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Error</div></div>"
            f"<div style='flex:1; background:rgba(38,85,163,0.25); border:1px solid rgba(38,85,163,0.4); "
            f"border-radius:3px; padding:0.5rem 0.4rem; text-align:center;'>"
            f"<div style='font-size:1.1rem; font-weight:700; color:#93c5fd;'>{ok+err}</div>"
            f"<div style='font-size:0.58rem; color:#7a8ba8; text-transform:uppercase; "
            f"letter-spacing:0.1em;'>Total</div></div>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.78rem; "
            "color:#7a8ba8; padding:0.5rem 0 1rem 0; font-style:italic;'>"
            "No data fetched yet.<br>Use the Settings panel above to fetch data.</div>",
            unsafe_allow_html=True
        )

    # ── Divider ──
    st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.08); margin:0.5rem 0 1rem 0;'>",
                unsafe_allow_html=True)

    # ── Spot prices mini-ticker ──
    st.markdown(
        "<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.58rem; font-weight:600; "
        "letter-spacing:0.16em; text-transform:uppercase; color:#7a8ba8; margin-bottom:0.6rem;'>"
        "Spot Prices</div>",
        unsafe_allow_html=True
    )

    TICKER_SYMBOLS = [
        "Crude Oil (WTI)", "Brent Oil", "Natural Gas",
        "Gold", "Silver", "Copper",
        "S&P 500", "NASDAQ", "VIX",
        "Bitcoin", "Ethereum",
        "EUR/USD", "GBP/USD",
    ]

    if results:
        tickers_shown = 0
        for name in TICKER_SYMBOLS:
            data = results.get(name, {})
            if "price" in data:
                price  = data["price"]
                change = data.get("change", 0)
                color  = "#4ade80" if change >= 0 else "#f87171"
                arrow  = "▲" if change >= 0 else "▼"
                spark  = make_sparkline(data.get("spark", []), color, width=52, height=20)
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; align-items:center; "
                    f"padding:0.3rem 0; border-bottom:1px solid rgba(255,255,255,0.05); gap:0.3rem;'>"
                    f"<span style='font-family:\"Source Sans 3\",sans-serif; font-size:0.7rem; "
                    f"color:#b8c4d8; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; "
                    f"flex:1; min-width:0;'>{name}</span>"
                    f"<span style='flex-shrink:0;'>{spark}</span>"
                    f"<span style='font-family:\"Source Code Pro\",monospace; font-size:0.7rem; "
                    f"color:#e0e7f0; text-align:right; flex-shrink:0; white-space:nowrap;'>"
                    f"${price:,.2f} <span style='color:{color}; font-size:0.62rem;'>{arrow}{abs(change):.2f}</span>"
                    f"</span></div>",
                    unsafe_allow_html=True
                )
                tickers_shown += 1
        if tickers_shown == 0:
            st.markdown(
                "<div style='font-size:0.72rem; color:#4a5a70; font-style:italic;'>"
                "Fetch price sources to see ticker.</div>",
                unsafe_allow_html=True
            )
    else:
        for name in TICKER_SYMBOLS[:6]:
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; padding:0.28rem 0; "
                f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                f"<span style='font-size:0.72rem; color:#4a5a70;'>{name}</span>"
                f"<span style='font-size:0.72rem; color:#4a5a70; font-family:\"Source Code Pro\",monospace;'>—</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    # ── Footer ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.6rem; "
        "color:#3a4a60; line-height:1.6; border-top:1px solid rgba(255,255,255,0.06); "
        "padding-top:0.8rem;'>"
        "© 2026 Macro-Risk Intelligence Hub<br>"
        "All data from public APIs.<br>"
        "For informational purposes only."
        "</div>",
        unsafe_allow_html=True
    )


# ==========================================
# 9. MAIN DASHBOARD
# ==========================================

# ── Page header ──
st.markdown("""
<div style="border-bottom:2px solid #1a2340; padding-bottom:0.8rem; margin-bottom:1.2rem;">
    <div style="font-family:'Source Sans 3',sans-serif; font-size:0.6rem; font-weight:600;
                letter-spacing:0.18em; text-transform:uppercase; color:#8a95a3; margin-bottom:0.3rem;">
        Global Intelligence Report
    </div>
    <div style="font-family:'Playfair Display',Georgia,serif;
               font-size:clamp(1.2rem, 4vw, 2rem); font-weight:700; color:#1a2340;
               line-height:1.2; margin-bottom:0.3rem;">
        Macro-Risk Intelligence Hub
    </div>
    <div style="font-family:'Source Sans 3',sans-serif; font-size:clamp(0.72rem, 2vw, 0.85rem);
                color:#8a95a3; line-height:1.5;">
        Real-time monitoring &nbsp;·&nbsp; Multi-source aggregation &nbsp;·&nbsp; AI analysis &nbsp;·&nbsp; 2026
    </div>
</div>
""", unsafe_allow_html=True)

# ── Settings panel — expander works on all devices ──
with st.expander("⚙️ Settings & Data Sources", expanded=not bool(st.session_state.fetched_results)):

    # API Key row
    c1, c2 = st.columns([2, 1])
    with c1:
        _key_input = st.text_input("DeepSeek API Key", type="password",
                                   placeholder="sk-...", value=api_key or "",
                                   label_visibility="collapsed",
                                   help="Enter your DeepSeek API key for AI analysis")
        if _key_input:
            api_key = _key_input
    with c2:
        if api_key:
            st.success("✓ API key set")
        else:
            st.warning("API key required")

    st.divider()

    # Source filter + quick-select
    col_cat, col_a, col_b = st.columns([3, 1, 1])
    with col_cat:
        categories = list(set(s["category"] for s in ALL_SOURCES))
        selected_category = st.selectbox("Filter by category", ["All"] + sorted(categories),
                                         label_visibility="collapsed")
    with col_a:
        if st.button("✓ All", use_container_width=True, key="sel_all"):
            filtered = ALL_SOURCES if selected_category == "All" else [s for s in ALL_SOURCES if s["category"] == selected_category]
            st.session_state["_src_selection"] = [s["name"] for s in filtered]
    with col_b:
        if st.button("✕ Clear", use_container_width=True, key="sel_none"):
            st.session_state["_src_selection"] = []

    filtered_sources = ALL_SOURCES if selected_category == "All" else \
                       [s for s in ALL_SOURCES if s["category"] == selected_category]
    source_names = [s["name"] for s in filtered_sources]

    if "_src_selection" in st.session_state:
        _default = [s for s in st.session_state["_src_selection"] if s in source_names]
    else:
        _default = [s for s in _all_defaults if s in source_names] or source_names[:10]

    selected_sources = st.multiselect(
        "Active sources",
        options=source_names,
        default=_default,
        key="source_multiselect",
        label_visibility="collapsed"
    )
    st.session_state["_src_selection"] = selected_sources
    st.caption(f"{len(selected_sources)} of {len(source_names)} sources selected")

    st.divider()

    # Fetch row
    fc1, fc2 = st.columns([2, 1])
    with fc1:
        update_freq = st.slider("Cache (s)", 300, 7200, 3600, step=300, label_visibility="collapsed")
    with fc2:
        fetch_clicked = st.button("Fetch Data", use_container_width=True, type="primary")

    if fetch_clicked:
        with st.spinner(f"Fetching {len(selected_sources)} sources…"):
            _results = st.session_state.data_manager.fetch_selected(selected_sources)
            st.session_state.fetched_results = _results
            st.session_state.last_fetch_time = time.time()
            _ok = sum(1 for v in _results.values() if "error" not in v)
            st.success(f"{_ok} of {len(selected_sources)} sources retrieved")

    if st.session_state.last_fetch_time:
        st.caption(f"Last updated: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_fetch_time))}")

    st.markdown("""<div style="font-size:0.68rem; color:#8a95a3; margin-top:0.3rem;">
        © 2026 Macro-Risk Intelligence Hub · For informational purposes only.</div>""",
        unsafe_allow_html=True)


if st.session_state.fetched_results:
    results = st.session_state.fetched_results

    # ── Spot Prices ──
    st.markdown("""
    <div class="section-market">
        <span style="font-family:'Source Sans 3',sans-serif; font-size:0.65rem; font-weight:600;
                     letter-spacing:0.18em; text-transform:uppercase; color:#2655a3;">
            Market Snapshot
        </span>
    </div>
    """, unsafe_allow_html=True)

    price_sources = [(name, data) for name, data in results.items()
                     if isinstance(data, dict) and "price" in data]

    # Featured tickers for snapshot row
    SNAPSHOT_NAMES = [
        "Crude Oil (WTI)", "Brent Oil", "Natural Gas", "Gold",
        "Silver", "S&P 500", "NASDAQ", "VIX",
        "Bitcoin", "Ethereum", "EUR/USD", "GBP/USD",
    ]
    snapshot_sources = [(n, results[n]) for n in SNAPSHOT_NAMES
                        if n in results and "price" in results[n]]
    if not snapshot_sources:
        snapshot_sources = price_sources

    if snapshot_sources:
        cols = st.columns(4)
        for i, (name, data) in enumerate(snapshot_sources[:12]):
            price  = data["price"]
            change = data.get("change", 0)
            pct    = (change / (price - change) * 100) if (price - change) != 0 else 0
            color  = "#1a7a4a" if change >= 0 else "#c0392b"
            arrow  = "▲" if change >= 0 else "▼"
            spark  = make_sparkline(data.get("spark", []), color, width=100, height=28)
            with cols[i % 4]:
                st.markdown(f"""
                <div style="background:#ffffff; border:1px solid #e2e6ed;
                            border-top:3px solid {color};
                            border-radius:3px; padding:0.75rem 0.9rem 0.6rem 0.9rem;
                            margin-bottom:0.8rem; box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                    <div style="font-family:'Source Sans 3',sans-serif; font-size:0.62rem;
                                font-weight:600; letter-spacing:0.1em; text-transform:uppercase;
                                color:#8a95a3; margin-bottom:0.2rem; white-space:nowrap;
                                overflow:hidden; text-overflow:ellipsis;"
                         title="{name}">{name}</div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div style="font-family:'Source Code Pro',monospace; font-size:1.15rem;
                                        font-weight:500; color:#0f1923; line-height:1.1;">
                                ${price:,.2f}</div>
                            <div style="font-family:'Source Code Pro',monospace; font-size:0.72rem;
                                        font-weight:600; color:{color}; margin-top:0.15rem;">
                                {arrow} {change:+.2f}
                                <span style="font-weight:400; font-size:0.65rem;">({pct:+.2f}%)</span>
                            </div>
                        </div>
                        <div style="flex-shrink:0;">{spark}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No price data available. Select sources and fetch data.")

    st.divider()

    # ── Category Tabs ──
    st.markdown("""
    <div class="section-data">
        <span style="font-family:'Source Sans 3',sans-serif; font-size:0.65rem; font-weight:600;
                     letter-spacing:0.18em; text-transform:uppercase; color:#0e7490;">
            Data by Category
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Category metadata: icon, description, display mode
    CATEGORY_META = {
        "Energy":       {"icon": "⚡", "desc": "Crude, gas, refined products & renewables", "mode": "cards", "color": "#b45309", "bg": "#fef3c7"},
        "Metals":       {"icon": "🪙", "desc": "Precious & industrial metals",              "mode": "cards", "color": "#6b7280", "bg": "#f3f4f6"},
        "Agriculture":  {"icon": "🌾", "desc": "Grains, softs & livestock",                 "mode": "cards", "color": "#166534", "bg": "#dcfce7"},
        "Economic":     {"icon": "📈", "desc": "GDP, inflation, employment indicators",      "mode": "kv",    "color": "#1d4ed8", "bg": "#dbeafe"},
        "Monetary":     {"icon": "🏦", "desc": "Central bank rates & treasury yields",       "mode": "cards", "color": "#1a2340", "bg": "#e0e7ff"},
        "Currency":     {"icon": "💱", "desc": "Major FX pairs & dollar index",              "mode": "cards", "color": "#0e7490", "bg": "#cff0f8"},
        "Equities":     {"icon": "📊", "desc": "Equity indices & volatility",               "mode": "cards", "color": "#2655a3", "bg": "#dce8f7"},
        "Crypto":       {"icon": "₿",  "desc": "Digital asset prices",                      "mode": "cards", "color": "#7c3aed", "bg": "#ede9fe"},
        "News":         {"icon": "📰", "desc": "Real-time headlines from global sources",   "mode": "news",  "color": "#374151", "bg": "#f3f4f6"},
        "Geopolitical": {"icon": "🌐", "desc": "Risk indices, conflict & climate data",     "mode": "kv",    "color": "#9f1239", "bg": "#ffe4e6"},
    }

    tab_labels = list(CATEGORY_META.keys())
    tab_display = [f"{CATEGORY_META[c]['icon']} {c}" for c in tab_labels]
    tabs = st.tabs(tab_display)

    def _change_color(change_str):
        """Return CSS color for a change string."""
        try:
            val = float(change_str.replace(",", ""))
            if val > 0:
                return "#1a7a4a"
            elif val < 0:
                return "#c0392b"
        except Exception:
            pass
        return "#8a95a3"

    def _change_arrow(change_str):
        try:
            val = float(change_str.replace(",", ""))
            if val > 0:
                return "▲"
            elif val < 0:
                return "▼"
        except Exception:
            pass
        return "–"

    for tab, category in zip(tabs, tab_labels):
        meta = CATEGORY_META[category]
        with tab:
            # Tab sub-header
            st.markdown(
                f"<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.78rem; "
                f"color:#8a95a3; margin-bottom:1.2rem; padding:0.5rem 0.9rem; "
                f"background:linear-gradient(90deg,{meta['bg']} 0%,transparent 100%); "
                f"border-left:3px solid {meta['color']}; border-radius:0 3px 3px 0;'>"
                f"<span style='font-weight:600; color:{meta['color']};'>{meta['icon']} {category}</span>"
                f"&nbsp;·&nbsp;{meta['desc']}</div>",
                unsafe_allow_html=True
            )

            # ── CARD MODE (price data) ──
            if meta["mode"] == "cards":
                price_items = [
                    (name, data) for name, data in results.items()
                    if isinstance(data, dict) and "price" in data
                    and any(s["name"] == name and s["category"] == category for s in ALL_SOURCES)
                ]
                error_items = [
                    (name, data) for name, data in results.items()
                    if isinstance(data, dict) and "error" in data
                    and any(s["name"] == name and s["category"] == category for s in ALL_SOURCES)
                ]

                if price_items:
                    # Render as a tight card grid — 2 per row (mobile-friendly)
                    cols_per_row = 2
                    for row_start in range(0, len(price_items), cols_per_row):
                        row_items = price_items[row_start:row_start + cols_per_row]
                        cols = st.columns(cols_per_row)
                        for col, (name, data) in zip(cols, row_items):
                            price  = data["price"]
                            change = data.get("change", 0)
                            change_str = f"{change:+.2f}"
                            color  = _change_color(str(change))
                            arrow  = _change_arrow(str(change))
                            pct    = (change / (price - change) * 100) if (price - change) != 0 else 0
                            spark  = make_sparkline(data.get("spark", []), color, width=110, height=32)
                            with col:
                                st.markdown(f"""
                                <div style="background:#ffffff; border:1px solid #e2e6ed;
                                            border-left:3px solid {meta['color']}; border-radius:3px;
                                            padding:0.75rem 0.9rem 0.6rem 0.9rem; margin-bottom:0.8rem;
                                            box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                                    <div style="font-family:'Source Sans 3',sans-serif;
                                                font-size:0.63rem; font-weight:600; letter-spacing:0.12em;
                                                text-transform:uppercase; color:#8a95a3;
                                                margin-bottom:0.25rem; white-space:nowrap;
                                                overflow:hidden; text-overflow:ellipsis;"
                                         title="{name}">{name}</div>
                                    <div style="display:flex; justify-content:space-between;
                                                align-items:flex-end; gap:0.5rem;">
                                        <div>
                                            <div style="font-family:'Source Code Pro',monospace;
                                                        font-size:1.18rem; font-weight:500; color:#0f1923;
                                                        line-height:1.1; margin-bottom:0.2rem;">
                                                ${price:,.2f}
                                            </div>
                                            <div style="font-family:'Source Code Pro',monospace;
                                                        font-size:0.74rem; font-weight:600; color:{color};">
                                                {arrow} {change_str}
                                                <span style="font-weight:400; font-size:0.68rem;">
                                                    ({pct:+.2f}%)
                                                </span>
                                            </div>
                                        </div>
                                        <div style="flex-shrink:0; opacity:0.9;">
                                            {spark}
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                if error_items:
                    with st.expander(f"⚠️ {len(error_items)} source(s) unavailable", expanded=False):
                        for name, data in error_items:
                            st.markdown(
                                f"<div style='font-size:0.78rem; color:#c0392b; padding:0.2rem 0; "
                                f"font-family:\"Source Code Pro\",monospace;'>"
                                f"<b>{name}</b>: {data.get('error','Unknown error')}</div>",
                                unsafe_allow_html=True
                            )

                if not price_items and not error_items:
                    st.markdown(
                        "<div style='color:#8a95a3; font-size:0.82rem; padding:1.5rem 0; text-align:center;'>"
                        "No data available. Select these sources in the sidebar and fetch.</div>",
                        unsafe_allow_html=True
                    )

            # ── KEY-VALUE MODE (economic / geopolitical indicators) ──
            elif meta["mode"] == "kv":
                kv_items = []
                for name, data in results.items():
                    src = next((s for s in ALL_SOURCES if s["name"] == name), None)
                    if not src or src["category"] != category:
                        continue
                    if "error" in data:
                        kv_items.append((name, "—", data["error"], "error"))
                    elif "price" in data:
                        change_str = f"{data.get('change', 0):+.2f}"
                        kv_items.append((name, f"${data['price']:,.2f}", change_str, "price"))
                    elif "value" in data:
                        kv_items.append((name, data["value"], data.get("date", ""), "value"))
                    elif "note" in data:
                        kv_items.append((name, "—", data["note"], "note"))
                    elif "data" in data:
                        kv_items.append((name, "API data received", "", "api"))

                if kv_items:
                    # Render as a clean two-column table
                    st.markdown("""
                    <table style="width:100%; border-collapse:collapse;
                                  font-family:'Source Sans 3',sans-serif; font-size:0.83rem;">
                        <thead>
                            <tr style="background:#1a2340;">
                                <th style="padding:0.55rem 1rem; text-align:left; color:#ffffff;
                                           font-size:0.68rem; letter-spacing:0.12em; font-weight:600;
                                           text-transform:uppercase; width:40%;">Indicator</th>
                                <th style="padding:0.55rem 1rem; text-align:right; color:#ffffff;
                                           font-size:0.68rem; letter-spacing:0.12em; font-weight:600;
                                           text-transform:uppercase; width:25%;">Latest Value</th>
                                <th style="padding:0.55rem 1rem; text-align:left; color:#ffffff;
                                           font-size:0.68rem; letter-spacing:0.12em; font-weight:600;
                                           text-transform:uppercase; width:35%;">Note / Date</th>
                            </tr>
                        </thead>
                        <tbody>
                    """ + "".join([
                        f"""<tr style="background:{'#f5f7fb' if i % 2 == 0 else '#ffffff'};
                                      border-bottom:1px solid #e2e6ed;">
                            <td style="padding:0.55rem 1rem; color:#0f1923; font-weight:500;">{name}</td>
                            <td style="padding:0.55rem 1rem; text-align:right;
                                       font-family:'Source Code Pro',monospace; font-size:0.82rem;
                                       color:{'#c0392b' if kind == 'error' else '#1a2340'};
                                       font-weight:600;">{value}</td>
                            <td style="padding:0.55rem 1rem;
                                       font-size:0.75rem; color:#8a95a3;">{note}</td>
                        </tr>"""
                        for i, (name, value, note, kind) in enumerate(kv_items)
                    ]) + """
                        </tbody>
                    </table>
                    """, unsafe_allow_html=True)

                    # ── USGS Earthquake detail panel ──
                    usgs_data = next(
                        (data for name, data in results.items()
                         if "USGS" in name and isinstance(data, dict) and data.get("geo_type") == "usgs"),
                        None
                    )
                    if usgs_data and usgs_data.get("events"):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(
                            "<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.65rem; "
                            "font-weight:600; letter-spacing:0.14em; text-transform:uppercase; "
                            "color:#8a95a3; margin-bottom:0.5rem;'>Recent Significant Earthquakes (M5.5+)</div>",
                            unsafe_allow_html=True
                        )
                        rows_html = """
                        <table style="width:100%; border-collapse:collapse;
                                      font-family:'Source Sans 3',sans-serif; font-size:0.8rem;">
                            <thead>
                                <tr style="background:#1a2340;">
                                    <th style="padding:0.5rem 0.8rem; text-align:left; color:#fff;
                                               font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase;">Location</th>
                                    <th style="padding:0.5rem 0.8rem; text-align:center; color:#fff;
                                               font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase;">Magnitude</th>
                                    <th style="padding:0.5rem 0.8rem; text-align:center; color:#fff;
                                               font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase;">Depth (km)</th>
                                    <th style="padding:0.5rem 0.8rem; text-align:left; color:#fff;
                                               font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase;">Time (UTC)</th>
                                    <th style="padding:0.5rem 0.8rem; text-align:center; color:#fff;
                                               font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase;">Alert</th>
                                </tr>
                            </thead><tbody>"""
                        for idx, ev in enumerate(usgs_data["events"]):
                            mag = ev["magnitude"]
                            mag_color = "#c0392b" if mag and float(mag) >= 7.0 else ("#e67e22" if mag and float(mag) >= 6.0 else "#1a2340")
                            bg = "#f5f7fb" if idx % 2 == 0 else "#ffffff"
                            rows_html += f"""
                            <tr style="background:{bg}; border-bottom:1px solid #e2e6ed;">
                                <td style="padding:0.48rem 0.8rem; color:#0f1923;">{ev['place']}</td>
                                <td style="padding:0.48rem 0.8rem; text-align:center;
                                           font-family:'Source Code Pro',monospace; font-weight:700;
                                           color:{mag_color};">{mag}</td>
                                <td style="padding:0.48rem 0.8rem; text-align:center;
                                           font-family:'Source Code Pro',monospace; color:#4a5568;">{ev['depth_km']}</td>
                                <td style="padding:0.48rem 0.8rem; color:#8a95a3; font-size:0.75rem;">{ev['time']}</td>
                                <td style="padding:0.48rem 0.8rem; text-align:center; color:#8a95a3; font-size:0.75rem;">{ev['alert']}</td>
                            </tr>"""
                        rows_html += "</tbody></table>"
                        st.markdown(rows_html, unsafe_allow_html=True)

                else:
                    st.markdown(
                        "<div style='color:#8a95a3; font-size:0.82rem; padding:1.5rem 0; text-align:center;'>"
                        "No data available. Select these sources in the sidebar and fetch.</div>",
                        unsafe_allow_html=True
                    )

            # ── NEWS MODE ──
            elif meta["mode"] == "news":
                news_sources = [
                    (name, data) for name, data in results.items()
                    if isinstance(data, dict) and "headlines" in data
                    and any(s["name"] == name and s["category"] == "News" for s in ALL_SOURCES)
                ]
                error_news = [
                    (name, data) for name, data in results.items()
                    if isinstance(data, dict) and "error" in data
                    and any(s["name"] == name and s["category"] == "News" for s in ALL_SOURCES)
                ]

                if news_sources:
                    # Summary row
                    total_headlines = sum(len(d["headlines"]) for _, d in news_sources)
                    st.markdown(
                        f"<div style='font-size:0.78rem; color:#4a5568; margin-bottom:1rem; "
                        f"font-family:\"Source Sans 3\",sans-serif;'>"
                        f"<b style='color:#1a2340;'>{total_headlines}</b> headlines from "
                        f"<b style='color:#1a2340;'>{len(news_sources)}</b> sources</div>",
                        unsafe_allow_html=True
                    )

                    for src_name, data in news_sources:
                        headlines = data.get("headlines", [])
                        if not headlines:
                            continue

                        # Source header
                        st.markdown(f"""
                        <div style="background:#1a2340; padding:0.5rem 1rem;
                                    border-radius:3px 3px 0 0; margin-top:0.8rem;">
                            <span style="font-family:'Source Sans 3',sans-serif; font-size:0.72rem;
                                         font-weight:600; letter-spacing:0.1em; text-transform:uppercase;
                                         color:#b8c4d8;">{src_name}</span>
                            <span style="float:right; font-size:0.68rem; color:#7a8ba8;">
                                {len(headlines)} articles
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                        # Headlines list
                        rows_html = ""
                        for idx, hl in enumerate(headlines):
                            bg = "#ffffff" if idx % 2 == 0 else "#f5f7fb"
                            rows_html += f"""
                            <div style="background:{bg}; padding:0.65rem 1rem;
                                        border-bottom:1px solid #e2e6ed;
                                        border-left:1px solid #e2e6ed;
                                        border-right:1px solid #e2e6ed;">
                                <a href="{hl['link']}" target="_blank"
                                   style="font-family:'Source Sans 3',sans-serif; font-size:0.84rem;
                                          font-weight:500; color:#003087; text-decoration:none;
                                          line-height:1.4; display:block;">
                                    {hl['title']}
                                </a>
                                <div style="font-size:0.7rem; color:#8a95a3; margin-top:0.2rem;
                                            font-family:'Source Sans 3',sans-serif;">
                                    {hl.get('published', '')}
                                </div>
                            </div>"""

                        # Close with bottom border radius
                        rows_html += "<div style='border-bottom:1px solid #e2e6ed; border-left:1px solid #e2e6ed; border-right:1px solid #e2e6ed; border-radius:0 0 3px 3px; height:4px; background:#ffffff;'></div>"
                        st.markdown(rows_html, unsafe_allow_html=True)

                if error_news:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander(f"⚠️ {len(error_news)} news source(s) unavailable", expanded=False):
                        for name, data in error_news:
                            st.markdown(
                                f"<div style='font-size:0.78rem; color:#c0392b; padding:0.2rem 0; "
                                f"font-family:\"Source Code Pro\",monospace;'>"
                                f"<b>{name}</b>: {data.get('error','Unknown error')}</div>",
                                unsafe_allow_html=True
                            )

                if not news_sources and not error_news:
                    st.markdown(
                        "<div style='color:#8a95a3; font-size:0.82rem; padding:1.5rem 0; text-align:center;'>"
                        "No news sources fetched. Select news sources in the sidebar and fetch.</div>",
                        unsafe_allow_html=True
                    )

    # ── AI Analysis ──
    st.divider()
    st.markdown("""
    <div class="section-ai">
        <span style="font-family:'Source Sans 3',sans-serif; font-size:0.65rem; font-weight:600;
                     letter-spacing:0.18em; text-transform:uppercase; color:#b45309;">
            AI Strategic Analysis
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        "<div style='font-family:\"Source Sans 3\",sans-serif; font-size:0.85rem; color:#4a5568; "
        "margin-bottom:1rem;'>Select an analytical framework and generate a forward-looking "
        "briefing grounded in the current data environment.</div>",
        unsafe_allow_html=True
    )

    analysis_type = st.selectbox(
        "Analytical framework",
        ["General Macro", "Energy & Maritime", "LATAM/Caribbean Risk",
         "Tech & Digitalization", "Warehouse Ops", "PM Risk",
         "Crypto", "Geopolitical Power"],
        key="analysis_selector",
        label_visibility="collapsed"
    )
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
            with st.spinner("Preparing PDF…"):
                pdf_bytes = generate_pdf_report(report, analysis_type)
            st.download_button(
                label="Download Report (PDF)",
                data=pdf_bytes,
                file_name=f"macro_risk_briefing_{int(time.time())}.pdf",
                mime="application/pdf",
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
    placeholder_metrics = [
        ("Crude Oil (WTI)", "—", "—"),
        ("Gold", "—", "—"),
        ("S&P 500", "—", "—"),
        ("VIX", "—", "—"),
    ]
    cols = st.columns(2)
    for i, (label, val, delta) in enumerate(placeholder_metrics):
        with cols[i % 2]:
            st.metric(label=label, value=val, delta=delta)

    st.caption("Awaiting data fetch to populate dashboard.")
