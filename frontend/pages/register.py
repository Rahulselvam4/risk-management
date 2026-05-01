# frontend/pages/register.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import requests
import os

# Register this file as a route in the application
dash.register_page(__name__, path='/register', title="Register -  RISK DASHBOARD")

# Use 127.0.0.1 since we are running the Hybrid Local setup
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- UI LAYOUT ---
layout = dbc.Container([
    dbc.Row([
        dbc.Col(width=4), # Left spacer
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-person-plus text-center", style={"fontSize": "3rem", "color": "#388087"}),
                        html.H2("Create Account", className="text-center mt-2 mb-4", style={"color": "#2C3E50"}),
                    ], className="text-center"),
                    
                    # Registration Form
                    dbc.Input(id="reg-email", type="email", placeholder="Corporate Email", className="mb-3"),
                    dbc.Input(id="reg-password", type="password", placeholder="Create Password", className="mb-3"),
                    dbc.Input(id="reg-confirm", type="password", placeholder="Confirm Password", className="mb-4"),
                    
                    dbc.Button("Create Account", id="btn-register", color="dark", className="w-100 mb-3 btn"),
                    
                    # Redirect back to Login
                    html.Div([
                        html.Span("Already have an account? "),
                        html.A("Sign In", href="/login", style={"color": "#388087", "textDecoration": "none"})
                    ], className="text-center mt-3"),
                    
                    # Hidden components for logic
                    html.Div(id="reg-alert", className="mt-3"),
                    dcc.Location(id='reg-redirect', refresh=True)
                ])
            ], className="card shadow mt-5")
        ], width=4), # Center column
        dbc.Col(width=4)  # Right spacer
    ], className="vh-100 align-items-center") # Vertically center the box
], fluid=True, style={"backgroundColor": "#F6F6F2"})


# --- LOGIC / API CONNECTION ---
@callback(
    Output("reg-alert", "children"),
    Output("reg-redirect", "pathname"),
    Input("btn-register", "n_clicks"),
    State("reg-email", "value"),
    State("reg-password", "value"),
    State("reg-confirm", "value"),
    prevent_initial_call=True
)
def handle_registration(n_clicks, email, password, confirm):
    # 1. Frontend Validation
    if not email or not password or not confirm:
        return dbc.Alert("All fields are required.", color="warning"), dash.no_update
        
    if password != confirm:
        return dbc.Alert("Passwords do not match.", color="danger"), dash.no_update

    try:
        # 2. Contact the FastAPI Registration endpoint you created
        payload = {"email": email, "password": password}
        response = requests.post(f"{API_URL}/auth/register", json=payload)
        
        if response.status_code == 200:
            # Registration successful! Redirect them back to the login page
            return dash.no_update, "/login"
            
        else:
            # Handle backend errors (e.g., "Email already registered")
            error_msg = response.json().get("detail", "Registration Failed")
            return dbc.Alert(error_msg, color="danger"), dash.no_update
            
    except requests.exceptions.ConnectionError:
        return dbc.Alert("API Server is offline. Contact engineering.", color="danger"), dash.no_update