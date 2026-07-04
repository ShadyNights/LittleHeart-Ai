import streamlit as st
import sys
import plotly.express as px
from pathlib import Path

# Fix relative import paths
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend_streamlit.services.api_client import fetch_alerts, fetch_admin_metrics

st.set_page_config(page_title="Healthcare Dashboard", page_icon="🏥", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Please login first")
    st.stop()

st.markdown('<div class="page-header"><h1>🏥 Healthcare Provider Dashboard</h1><p>Real-time patient monitoring and alert response system</p></div>', unsafe_allow_html=True)

# --- Live Alert Banner ---
st.subheader("🚨 Live Alerts Feed")
st.caption("Real-time WebSocket Push · Auto-refreshing every 5 seconds")


@st.fragment(run_every=5)
def live_alerts_section():
    """Auto-refreshing fragment for live alerts — replaces the blocking while-True loop."""
    alerts = fetch_alerts()

    if alerts:
        latest = alerts[0]
        alert_type = latest.get("alert_type", "ALERT").upper()
        risk = latest.get("risk", "HIGH")

        if risk in ["HIGH", "CRITICAL"]:
            st.markdown(f"""
            <div class="glass-card alert-glow">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:1.2rem; font-weight:700; color:#991b1b;">
                        🚨 {alert_type}: Patient {latest.get('patient_id', 'Unknown')}
                    </div>
                    <div style="background:#fee2e2; padding:4px 12px; border-radius:12px; color:#991b1b; font-weight:bold;">
                        LIVE
                    </div>
                </div>
                <div style="margin-top:8px; color:#7f1d1d;">
                    Immediate attention required. Risk assessment indicates {risk} probability of complications.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.dataframe(alerts, on_select="ignore", selection_mode="single-row")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:40px;">
            <div style="font-size:3rem; opacity:0.3;">✅</div>
            <h3 style="color:#166534;">All Systems Normal</h3>
            <p style="color:#64748b;">No active clinical alerts at this time.</p>
        </div>
        """, unsafe_allow_html=True)


@st.fragment(run_every=15)
def metrics_section():
    """Auto-refreshing fragment for department overview charts."""
    metrics = fetch_admin_metrics()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.caption("Current Risk Distribution")
        if "distribution" in metrics and metrics["distribution"]:
            fig_dist = px.pie(metrics["distribution"], names="risk", values="count", hole=0.4)
            fig_dist.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No assessment data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.caption("Weekly Alert Volume")
        if "weekly_alerts" in metrics and metrics["weekly_alerts"]:
            fig_weekly = px.bar(metrics["weekly_alerts"], x="day", y="count")
            fig_weekly.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_weekly, use_container_width=True)
        else:
            st.info("No alert data yet.")
        st.markdown('</div>', unsafe_allow_html=True)


# Render the auto-refreshing sections
live_alerts_section()

st.markdown("---")
st.subheader("📊 Department Overview")

metrics_section()
