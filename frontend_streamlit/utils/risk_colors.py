RISK_CONFIG = {
    "LOW": {
        "emoji": "🟢",
        "color": "#22c55e",
        "bg": "rgba(34,197,94,0.15)",
        "label": "Low Risk",
        "numeric": 1,
    },
    "MEDIUM": {
        "emoji": "🟡",
        "color": "#eab308",
        "bg": "rgba(234,179,8,0.15)",
        "label": "Medium Risk",
        "numeric": 2,
    },
    "HIGH": {
        "emoji": "🔴",
        "color": "#ef4444",
        "bg": "rgba(239,68,68,0.15)",
        "label": "High Risk",
        "numeric": 3,
    },
    "CRITICAL": {
        "emoji": "🚨",
        "color": "#dc2626",
        "bg": "rgba(220,38,38,0.25)",
        "label": "Critical Risk",
        "numeric": 4,
    },
}


def risk_badge(level: str) -> str:
    cfg = RISK_CONFIG.get(level, RISK_CONFIG["LOW"])
    return (
        f'<span style="'
        f"display:inline-block;padding:6px 16px;border-radius:20px;"
        f"background:{cfg['bg']};color:{cfg['color']};"
        f"font-weight:700;font-size:14px;letter-spacing:0.5px;"
        f"border:1px solid {cfg['color']};"
        f'">{cfg["emoji"]} {level}</span>'
    )


def risk_numeric(level: str) -> int:
    return RISK_CONFIG.get(level, RISK_CONFIG["LOW"])["numeric"]


def risk_color(level: str) -> str:
    return RISK_CONFIG.get(level, RISK_CONFIG["LOW"])["color"]


def risk_emoji(level: str) -> str:
    return RISK_CONFIG.get(level, RISK_CONFIG["LOW"])["emoji"]
