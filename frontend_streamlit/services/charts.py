import plotly.graph_objects as go
import streamlit as st

def render_risk_gauge(risk_level, confidence):
    
    risk_map = {
        "LOW": 25,
        "MEDIUM": 50,
        "HIGH": 75,
        "CRITICAL": 100
    }

    value = risk_map.get(risk_level, 0)
    
    # Dynamic bar color based on value
    bar_color = "#2563EB"
    if value > 85: bar_color = "#DC2626"
    elif value > 60: bar_color = "#F97316"
    elif value > 30: bar_color = "#F59E0B"
    else: bar_color = "#16A34A"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': "%", 'font': {'size': 24, 'color': '#1e3a8a'}},
        title={'text': "Clinical Risk Level", 'font': {'size': 18, 'color': '#64748b'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
            'bar': {'color': bar_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#f1f5f9",
            'steps': [
                {'range': [0, 30], 'color': "rgba(22, 163, 74, 0.15)"},
                {'range': [30, 60], 'color': "rgba(245, 158, 11, 0.15)"},
                {'range': [60, 85], 'color': "rgba(249, 115, 22, 0.15)"},
                {'range': [85, 100], 'color': "rgba(220, 38, 38, 0.15)"},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'family': "Inter, sans-serif"}
    )
    return fig
