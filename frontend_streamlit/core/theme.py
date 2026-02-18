import streamlit as st
from pathlib import Path

RISK_COLORS = {
    "LOW": {"color": "#3b82f6", "bg": "#eff6ff", "badge": "badge-low", "card": "low-risk", "emoji": "🟢"},
    "MEDIUM": {"color": "#f59e0b", "bg": "#fffbeb", "badge": "badge-medium", "card": "medium-risk", "emoji": "🟡"},
    "HIGH": {"color": "#ef4444", "bg": "#fef2f2", "badge": "badge-high", "card": "high-risk", "emoji": "🔴"},
    "CRITICAL": {"color": "#991b1b", "bg": "#fef2f2", "badge": "badge-critical", "card": "critical-risk", "emoji": "🚨"},
}


def load_css():
    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def metric_card(value, label, color=None):
    style = f'color: {color};' if color else 'color: #1e40af;'
    return f"""
    <div class="metric-card">
        <div class="metric-value" style="{style}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def risk_badge(level: str) -> str:
    cfg = RISK_COLORS.get(level, RISK_COLORS["LOW"])
    return f'<span class="risk-badge {cfg["badge"]}">{cfg["emoji"]} {level}</span>'


def risk_card_html(level: str, content: str) -> str:
    cfg = RISK_COLORS.get(level, RISK_COLORS["LOW"])
    return f'<div class="risk-card {cfg["card"]}">{content}</div>'


def risk_numeric(level: str) -> int:
    mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return mapping.get(level, 0)
