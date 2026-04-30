# frontend/components/navbar.py
from dash import html
import dash_bootstrap_components as dbc
from theme import COLORS

def get_navbar():
    """Returns the master navigation bar used across authenticated pages."""
    return dbc.Navbar(
        dbc.Container([
            # Left Side: Brand Logo / Name
            dbc.Row([
                dbc.Col(html.I(className="bi bi-shield-lock-fill", style={"fontSize": "1.5rem", "color": COLORS["off_white"]})),
                dbc.Col(dbc.NavbarBrand("Squilla Risk Engine", className="ms-2 fs-4", style={"color": COLORS["off_white"]})),
            ], align="center", className="g-0"),

            # Right Side: Navigation Links & Profile
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard", style={"color": COLORS["off_white"]})),
                    dbc.NavItem(dbc.NavLink("Rebalance", href="/rebalance", style={"color": COLORS["off_white"]})),
                    dbc.DropdownMenu(
                        children=[
                            dbc.DropdownMenuItem("Profile Settings", href="/profile"),
                            dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem("Logout", href="/login", style={"color": COLORS["alert_red"]}),
                        ],
                        nav=True,
                        in_navbar=True,
                        label="User",
                        toggle_style={"color": COLORS["off_white"]}
                    ),
                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ], fluid=True),
        color=COLORS["deep_teal"],
        dark=True,
        className="mb-4 shadow-sm",
    )