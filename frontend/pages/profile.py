# frontend/pages/profile.py
import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc

from components.navbar import get_navbar
from theme import COLORS

dash.register_page(__name__, path='/profile', title="Profile - Squilla Fund")

# --- UI LAYOUT ---
layout = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(html.H2("User Settings", className="mb-4 text-center", style={"color": COLORS["dark_gray"], "fontWeight": "600"}))),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Account Overview", style={"backgroundColor": COLORS["deep_teal"], "color": "white"}),
                    dbc.CardBody([
                        # Profile Icon
                        html.Div([
                            html.I(className="bi bi-person-circle", style={"fontSize": "4rem", "color": COLORS["muted_aqua"]}),
                        ], className="text-center mb-3"),
                        
                        html.H5("Portfolio Manager", className="text-center mb-1"),
                        html.P(id="profile-user-id-text", className="text-center text-muted mb-4"),
                        
                        html.Hr(className="my-4"),
                        
                        # Security Actions
                        html.H6("Security Management", className="mb-3 text-muted"),
                        dbc.Button("Change Password", color="outline-secondary", className="w-100 mb-3 btn"),
                        dbc.Button("Sign Out", id="btn-logout", color="danger", className="w-100 btn")
                    ])
                ], className="shadow-sm border-0")
            ], width=4, className="mx-auto") # Centers the column
        ]),
        
        # Invisible component to handle the redirect after logout
        dcc.Location(id="logout-redirect", refresh=True)
        
    ], fluid=True)
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC 1: Display Profile Data ---
@callback(
    Output("profile-user-id-text", "children"),
    Input("session-store", "data")
)
def load_profile(session):
    """Reads the secure session storage to display the active user's ID."""
    if session and session.get('user_id'):
        return f"System ID: {session['user_id']}"
    return "Status: Unauthenticated"


# --- LOGIC 2: Secure Session Teardown ---
@callback(
    Output("session-store", "data", allow_duplicate=True),
    Output("logout-redirect", "pathname"),
    Input("btn-logout", "n_clicks"),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    """Wipes the JWT Token and User ID from local memory and redirects to Login."""
    if n_clicks:
        # Returning a wiped dictionary destroys the session state
        wiped_session = {"user_id": None, "token": None}
        return wiped_session, "/login"
        
    return dash.no_update, dash.no_update