import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any
from frontend_streamlit.utils.risk_colors import RISK_CONFIG, risk_color

RISK_COLOR_MAP = {k: v["color"] for k, v in RISK_CONFIG.items()}


def risk_timeline_chart(history: List[Dict[str, Any]]):
    if not history:
        return None
    df = pd.DataFrame(history)
    df["risk_numeric"] = df["final_risk"].map(lambda r: RISK_CONFIG.get(r, {}).get("numeric", 0))
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df = df.sort_values("recorded_at")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["recorded_at"],
        y=df["risk_numeric"],
        mode="lines+markers",
        marker=dict(
            size=10,
            color=[risk_color(r) for r in df["final_risk"]],
            line=dict(width=2, color="white"),
        ),
        line=dict(color="#6366f1", width=2),
        hovertemplate="<b>%{text}</b><br>%{x|%b %d, %H:%M}<extra></extra>",
        text=df["final_risk"],
    ))

    fig.update_layout(
        title=None,
        yaxis=dict(
            tickvals=[1, 2, 3, 4],
            ticktext=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            gridcolor="rgba(255,255,255,0.1)",
        ),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=300,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    return fig


def risk_distribution_pie(history: List[Dict[str, Any]]):
    if not history:
        return None
    df = pd.DataFrame(history)
    counts = df["final_risk"].value_counts().reset_index()
    counts.columns = ["risk", "count"]

    colors = [RISK_COLOR_MAP.get(r, "#888") for r in counts["risk"]]

    fig = px.pie(
        counts,
        values="count",
        names="risk",
        color="risk",
        color_discrete_map=RISK_COLOR_MAP,
        hole=0.4,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=300,
        margin=dict(l=20, r=20, t=10, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    return fig


def ml_probabilities_bar(probs: Dict[str, float]):
    if not probs:
        return None
    labels = list(probs.keys())
    values = list(probs.values())
    colors = [RISK_COLOR_MAP.get(l, "#6366f1") for l in labels]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1%}" for v in values],
        textposition="auto",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=200,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
    )
    return fig


def alert_frequency_bar(alerts: List[Dict[str, Any]]):
    if not alerts:
        return None
    df = pd.DataFrame(alerts)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    daily = df.groupby("date").size().reset_index(name="count")

    fig = px.bar(
        daily,
        x="date",
        y="count",
        color_discrete_sequence=["#ef4444"],
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=300,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
    )
    return fig


def model_drift_chart(drift_logs: List[Dict[str, Any]]):
    if not drift_logs:
        return None
    df = pd.DataFrame(drift_logs)
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])

    fig = go.Figure()
    if "accuracy" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["recorded_at"], y=df["accuracy"],
            mode="lines+markers", name="Accuracy",
            line=dict(color="#22c55e"),
        ))
    if "ece" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["recorded_at"], y=df["ece"],
            mode="lines+markers", name="ECE",
            line=dict(color="#ef4444"),
        ))

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=300,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    return fig
