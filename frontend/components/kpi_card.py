# frontend/components/kpi_card.py
from dash import html
import dash_bootstrap_components as dbc
from theme import COLORS

def create_kpi_card(title, value, is_alert=False):
    """
    Generates a clean, enterprise metric card.
    If is_alert is True, the text turns red (e.g., for Drawdown).
    """
    value_color = COLORS["alert_red"] if is_alert else COLORS["deep_teal"]
    
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.P(title.upper(), className="mb-1 text-muted", style={"fontSize": "0.85rem", "letterSpacing": "1px", "fontWeight": "600"}),
                html.H3(value, style={"color": value_color, "fontWeight": "700", "margin": "0"})
            ]),
            className="shadow-sm card", style={"borderLeft": f"4px solid {value_color}"}
        ),
        width=4, className="mb-4"
    )