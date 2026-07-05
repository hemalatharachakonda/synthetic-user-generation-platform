"""
Theme constants and Plotly template for the "Field Research Lab" visual identity.
Import PLOTLY_LAYOUT and apply it to every chart via fig.update_layout(**PLOTLY_LAYOUT)
so all visualizations share one consistent look.
"""

# ── Core palette (kept in sync with styles/custom.css) ───────────────────────
PAPER = "#EDF0EA"
PAPER_ALT = "#E3E7DE"
INK = "#1E2A26"
INK_SOFT = "#4B5A54"
SAGE = "#4F7568"
SAGE_DARK = "#34473F"
SAGE_TINT = "#DCE6DE"
AMBER = "#D98E3F"
AMBER_TINT = "#F6E3C4"
BRICK = "#B5533C"
BRICK_TINT = "#F3DAD2"
CARD_BG = "#FFFFFF"
BORDER = "#D2D9CB"

FONT_DISPLAY = "Fraunces, Georgia, serif"
FONT_BODY = "Inter, -apple-system, sans-serif"
FONT_MONO = "IBM Plex Mono, SFMono-Regular, monospace"

# Sentiment / status colors used across dashboard + charts
SENTIMENT_COLORS = {
    "Positive": SAGE,
    "Neutral": AMBER,
    "Negative": BRICK,
}

SCORE_TIER_COLORS = {
    "high": SAGE,   # >= 7
    "mid": AMBER,   # 4 - 6.9
    "low": BRICK,   # < 4
}

# Discrete colorway used for multi-series/categorical charts
COLORWAY = [SAGE, AMBER, BRICK, SAGE_DARK, INK_SOFT, "#8FAF9E"]

# Continuous scale used for adoption-score bar charts
CONTINUOUS_SCALE = [[0, BRICK_TINT], [0.5, AMBER_TINT], [1, SAGE_TINT]]

# Shared Plotly layout — spread this into fig.update_layout(**PLOTLY_LAYOUT)
PLOTLY_LAYOUT = dict(
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family=FONT_BODY, color=INK, size=13),
    title_font=dict(family=FONT_DISPLAY, color=INK, size=17),
    colorway=COLORWAY,
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def score_tier(score: float) -> str:
    """Returns 'high' | 'mid' | 'low' for a 0-10 adoption score."""
    if score >= 7:
        return "high"
    if score >= 4:
        return "mid"
    return "low"


def load_css(path: str = "styles/custom.css") -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""
