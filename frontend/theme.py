# frontend/theme.py
import plotly.graph_objects as go

# Enterprise Color Palette
COLORS = {
    "deep_teal": "#388087",
    "muted_aqua": "#6FB3B8",
    "off_white": "#F6F6F2",
    "alert_red": "#E63946",
    "dark_gray": "#2C3E50",
    "light_gray": "#E5E7EB",
    "success_green": "#2ECC71"
}

def get_base_layout(title: str = ""):
    """Returns a standardized, high-end Plotly layout for all charts."""
    return go.Layout(
        title={"text": title, "font": {"color": COLORS["deep_teal"], "size": 20, "family": "Segoe UI"}},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Tahoma, sans-serif", "color": COLORS["dark_gray"]},
        margin={"l": 40, "r": 20, "t": 60, "b": 40},
        xaxis={
            "gridcolor": COLORS["light_gray"], 
            "zerolinecolor": COLORS["light_gray"],
            "showline": True,
            "linewidth": 1,
            "linecolor": COLORS["light_gray"]
        },
        yaxis={
            "gridcolor": COLORS["light_gray"], 
            "zerolinecolor": COLORS["light_gray"],
            "showline": True,
            "linewidth": 1,
            "linecolor": COLORS["light_gray"]
        },
        hovermode="x unified"
    )