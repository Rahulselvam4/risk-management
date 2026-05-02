# frontend/pages/profile.py
import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import requests
import os

from components.navbar import get_navbar
from theme import COLORS

dash.register_page(__name__, path='/profile', title="Profile - RISK DASHBOARD")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

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
                        
                        # Email Alert Preferences Section
                        html.H6("Email Alert Preferences", className="mb-3 text-muted"),
                        html.P("Receive daily notifications when assets exceed your risk threshold", className="small text-muted mb-3"),
                        
                        dbc.Row([
                            dbc.Col(html.Label("Daily Risk Alerts:", className="fw-bold"), width=6, align="center"),
                            dbc.Col(dbc.Switch(id="alert-toggle", value=False, className="float-end"), width=6)
                        ], className="mb-3"),
                        
                        html.Div(id="alert-status-display", className="mb-3"),
                        
                        html.Hr(className="my-4"),
                        
                        # Security Actions
                        dbc.Button("Sign Out", id="btn-logout", color="danger", className="w-100 btn")
                    ])
                ], className="shadow-sm border-0")
            ], width=4, className="mx-auto") # Centers the column
        ]),
        
        # Invisible component to handle the redirect after logout
        dcc.Location(id="logout-redirect", refresh=True),
        dcc.Interval(id="profile-load-interval", interval=500, n_intervals=0, max_intervals=1)
        
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


# --- LOGIC 2: Load Alert Preferences ---
@callback(
    Output("alert-toggle", "value"),
    Output("alert-status-display", "children"),
    Input("profile-load-interval", "n_intervals"),
    State("session-store", "data")
)
def load_alert_preferences(n_intervals, session):
    """Load user's current alert preferences from backend."""
    if not session or not session.get('user_id'):
        return False, html.P("Please log in to manage alerts", className="text-muted small")
    
    user_id = session['user_id']
    
    try:
        response = requests.get(f"{API_URL}/user/{user_id}/alert-preferences", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            enabled = data.get('enabled', False)
            last_sent = data.get('last_alert_sent')
            
            status_text = "Enabled" if enabled else "Disabled"
            status_color = COLORS["success_green"] if enabled else COLORS["dark_gray"]
            
            last_alert_text = "Never" if not last_sent else last_sent.split("T")[0] if "T" in str(last_sent) else str(last_sent)
            
            status_display = html.Div([
                html.P([
                    html.Strong("Status: "),
                    html.Span(status_text, style={"color": status_color, "fontWeight": "bold"})
                ], className="mb-1 small"),
                html.P([
                    html.Strong("Last Alert: "),
                    html.Span(last_alert_text)
                ], className="mb-0 small text-muted")
            ])
            
            return enabled, status_display
        elif response.status_code == 404:
            return False, html.P("User not found", className="text-danger small")
        else:
            return False, html.P(f"Server error: {response.status_code}", className="text-danger small")
            
    except requests.exceptions.ConnectionError:
        return False, html.P("Cannot connect to server. Is backend running?", className="text-danger small")
    except requests.exceptions.Timeout:
        return False, html.P("Request timeout. Try again.", className="text-danger small")
    except Exception as e:
        return False, html.P(f"Error: {str(e)}", className="text-danger small")


# --- LOGIC 3: Update Alert Preferences ---
@callback(
    Output("alert-status-display", "children", allow_duplicate=True),
    Input("alert-toggle", "value"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def update_alert_preferences(enabled, session):
    """Update user's alert preferences when toggle is switched."""
    if not session or not session.get('user_id'):
        return html.P("Session expired", className="text-danger small")
    
    user_id = session['user_id']
    
    try:
        response = requests.put(
            f"{API_URL}/user/{user_id}/alert-preferences",
            json={"enabled": enabled},
            timeout=5
        )
        
        if response.status_code == 200:
            status_text = "Enabled" if enabled else "Disabled"
            status_color = COLORS["success_green"] if enabled else COLORS["dark_gray"]
            
            return html.Div([
                html.P([
                    html.Strong("Status: "),
                    html.Span(status_text, style={"color": status_color, "fontWeight": "bold"})
                ], className="mb-1 small"),
                html.P("✓ Preferences updated successfully", className="mb-0 small text-success")
            ])
        elif response.status_code == 404:
            return html.P("User not found", className="text-danger small")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response.headers.get('content-type') == 'application/json' else 'Server error'
            return html.P(f"Failed: {error_msg}", className="text-danger small")
            
    except requests.exceptions.ConnectionError:
        return html.P("Cannot connect to server. Is backend running?", className="text-danger small")
    except requests.exceptions.Timeout:
        return html.P("Request timeout. Try again.", className="text-danger small")
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger small")


# --- LOGIC 4: Secure Session Teardown ---
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