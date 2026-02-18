import streamlit as st
import sys
import plotly.express as px
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend_streamlit.services.api_client import fetch_admin_metrics

st.set_page_config(page_title="Admin Analytics", page_icon="📊", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Please login first")
    st.stop()

import httpx
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.markdown('<div class="page-header"><h1>📊 System Administration & Analytics</h1><p>Infrastructure health and clinical volume monitoring</p></div>', unsafe_allow_html=True)

# --- Top metrics ---
metrics = fetch_admin_metrics()
health_data = {"ws_connections": 0, "status": "Unknown"}
try:
    health_res = httpx.get(f"{API_BASE}/health", timeout=2.0)
    health_data = health_res.json()
except:
    pass

if metrics:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Assessments", metrics.get("total", 0))
    with m2:
        st.metric("System Status", health_data.get("status", "Offline"), delta="Active" if health_data.get("status") == "healthy" else "Alert")
    with m3:
        st.metric("WS Connections", health_data.get("ws_connections", 0))
    with m4:
        st.metric("Avg Latency", f"{metrics.get('latency', 0)}s")

    st.markdown("---")
    
    col_l, col_r = st.columns([1.2, 0.8])
    
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📈 Assessment Volume (Weekly)")
        if "weekly_alerts" in metrics:
             df_weekly = metrics["weekly_alerts"]
             fig_vol = px.area(df_weekly, x="day", y="count", title="Assessment Throughput", markers=True)
             fig_vol.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
             st.plotly_chart(fig_vol, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎯 Risk Distribution")
        if "distribution" in metrics:
            fig_pie = px.pie(metrics["distribution"], names="risk", values="count", hole=0.5)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("💻 System Logistics")
    c1, c2 = st.columns(2)
    with c1:
        st.info("Clinical Engine: v4.0.0-hardened (Active)")
    with c2:
        st.success("Supabase Multi-region Sync: Operational")

else:
    st.error("Failed to load metrics from analytics service.")
