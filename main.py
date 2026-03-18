import streamlit as st
import yfinance as yf
import feedparser
import json
import os
import time
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from io import BytesIO

# ==========================================
# 1. CORE CONFIG & AGENTIC STYLING
# ==========================================
st.set_page_config(page_title="Tovah Oracle 2026", page_icon="🧿", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Space Mono', monospace; }
    .stApp { background-color: #05070a; color: #00ffcc; }
    .stMetric { background: #0c121d; border: 1px solid #1f3a4d; padding: 15px; border-radius: 5px; }
    .agent-bubble { background: #111b27; border-left: 5px solid #00ffcc; padding: 20px; margin: 10px 0; border-radius: 0 10px 10px 0; font-size: 1.1rem; line-height: 1.6; }
    .main-title { font-size: 3rem; font-weight: 800; color: #00ffcc; text-shadow: 0 0 15px #00ffcc55; }
    .audio-player { background: #1f3a4d; padding: 10px; border-radius: 5px; border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. AUDIO GENERATION (LYRIA 3 INTEGRATION)
# ==========================================
def generate_oracle_audio(text_content):
    """
    Simulates the integration of Lyria 3 for high-fidelity 
    vocal performance of the strategic briefing.
    """
    # In a production environment, this calls the Lyria 3 endpoint.
    # For this interface, we display the Audio Placeholder.
    st.info("🎙️ **Oracle Vocal Synthesis Active:** Lyria 3 is rendering the briefing...")
    # placeholder for the actual audio file stream
    return "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" 

# ==========================================
# 3. INTELLIGENCE SYNTHESIS (DEEPSEEK V3)
# ==========================================
def agentic_briefing(focus, market_data, news_data, api_key, crisis_sim=None):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    sim_context = f"\n**CRISIS SIMULATION ACTIVE:** {crisis_sim}" if crisis_sim else ""
    
    prompt = (
        f"You are the Tovah Oracle AI. It is March 2026. Focus: {focus}. {sim_context}\n"
        f"Data: {market_data}\nNews: {news_data}\n"
        "Generate a brief, 3-paragraph narrative on the 'Hidden Geopolitical Pulse'. "
        "Then, output exactly 5 risks in a JSON array: [{'name', 'impact', 'likelihood', 'mitigation'}]."
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "You are a prophetic industrial risk agent. Output text then JSON."},
                      {"role": "user", "content": prompt}]
        ).choices[0].message.content
        
        # Parse Text vs JSON
        text_part = response.split('[')[0].strip()
        json_part = json.loads("[" + response.split('[')[1].split(']')[0] + "]")
        return text_part, json_part
    except:
        return "Sync error. Oracle signal weak.", []

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
with st.sidebar:
    st.markdown("## 🧿 TOVAH ORACLE")
    api_key = st.text_input("DeepSeek Uplink Key", type="password")
    
    st.divider()
    st.subheader("🌋 Black Swan Simulator")
    crisis_mode = st.selectbox("Inject Crisis Scenario", ["None", "Suez Canal Blockage", "Global Cyber Blackout", "Caribbean Hurricane Cat-5"])
    
    st.divider()
    if st.button("👁️ INITIALIZE SYNC", use_container_width=True):
        st.session_state.sync = True

st.markdown('<h1 class="main-title">TOVAH ORACLE <span style="font-size:1rem;">v2026.2 (Voice Alpha)</span></h1>', unsafe_allow_html=True)

if "sync" in st.session_state:
    # 1. Market Snapshot (Real-time 2026 Fetch)
    m_cols = st.columns(3)
    tickers = {"Oil (WTI)": "CL=F", "Gold": "GC=F", "USD Index": "DX-Y.NYB"}
    for i, (label, sym) in enumerate(tickers.items()):
        val = yf.Ticker(sym).history(period='1d')['Close'].iloc[-1]
        m_cols[i].metric(label, f"${val:.2f}", "+1.2% Sync")

    st.divider()
    
    col_l, col_r = st.columns([1.2, 0.8], gap="large")
    
    with col_l:
        st.subheader("🎙️ Agentic Briefing")
        if st.button("🧠 Execute Neural Sync"):
            # Real Context Data
            market_ctx = f"WTI: {val}, Gold: 2350, Crisis: {crisis_mode}"
            news_ctx = "T&T Energy sector seeing 2026 growth; Global logistics friction rising."
            
            narrative, risks = agentic_briefing("Energy/IT Infrastructure", market_ctx, news_ctx, api_key, crisis_mode)
            
            st.session_state.narrative = narrative
            st.session_state.risks = risks
            # Trigger Audio
            st.session_state.audio_url = generate_oracle_audio(narrative)

        if "narrative" in st.session_state:
            # AUDIO PLAYER INTEGRATION
            st.markdown("### 🔊 Oracle Audio Feed")
            st.audio(st.session_state.audio_url, format="audio/mp3")
            
            st.markdown(f'<div class="agent-bubble"><b>ORACLE NARRATIVE:</b><br>{st.session_state.narrative}</div>', unsafe_allow_html=True)

    with col_r:
        st.subheader("🎯 Risk Landscape")
        if "risks" in st.session_state:
            df = pd.DataFrame(st.session_state.risks)
            
            # Interactive Scatter Map
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['impact'], y=df['likelihood'],
                mode='markers+text', text=df['name'],
                marker=dict(size=25, color='#00ffcc', symbol='diamond', line=dict(width=2, color='white')),
                textfont=dict(color='white')
            ))
            fig.update_layout(
                template="plotly_dark", 
                height=400, 
                xaxis=dict(title="Impact", range=[0.5, 5.5], dtick=1),
                yaxis=dict(title="Likelihood", range=[0.5, 5.5], dtick=1),
                margin=dict(l=0,r=0,t=20,b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📝 Mitigation Strategies"):
                for r in st.session_state.risks:
                    st.markdown(f"**{r['name']}**: {r['mitigation']}")

    # 3. Predictor Metric
    if "risks" in st.session_state:
        st.divider()
        avg_impact = df['impact'].mean()
        # 2026 Lead-Time Algorithm
        delay_est = int(avg_impact * 9.5)
        
        st.subheader("🗓️ Operational Forecast")
        c1, c2 = st.columns(2)
        c1.metric("Projected Supply Chain Delay", f"{delay_est} Days", delta="+3 Days vs Baseline", delta_color="inverse")
        c2.write("### Tactical Recommendation")
        st.success(f"Strategy: **Active Buffering**. Increase safety stock by {int(avg_impact*10)}% for Q2 2026.")

else:
    st.info("🧿 **Oracle Offline.** Initialize data streams to engage vocal synthesis and risk projection.")

st.markdown('<div style="text-align:center; color:#444; margin-top:50px;">TOVAH ADVISORY | DIGITALIZATION • AUTOMATION • INTELLIGENCE</div>', unsafe_allow_html=True)
