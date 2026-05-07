# frontend/pages/login.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import requests
import os
from dotenv import load_dotenv

dash.register_page(__name__, path='/login', title="Login - RISK DASHBOARD")

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- UI LAYOUT ---
layout = dbc.Container([
    dbc.Row([
        dbc.Col(width=4), 
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-shield-lock text-center", style={"fontSize": "3rem", "color": "#388087"}),
                        html.H2("RISK DASHBOARD", className="text-center mt-2 mb-4", style={"color": "#2C3E50"}),
                    ], className="text-center"),
                    
                    # Standard Login Form
                    dbc.Input(id="login-email", type="email", placeholder="Corporate Email", className="mb-3"),
                    dbc.Input(id="login-password", type="password", placeholder="Password", className="mb-2"),
                    
                    # Forgot Password Link
                    html.Div([
                        html.A("Forgot Password?", href="/forgot-password", style={"color": "#388087", "textDecoration": "none", "fontSize": "14px"})
                    ], className="text-end mb-3"),
                    
                    dbc.Button("Authenticate", id="btn-login", color="dark", className="w-100 mb-3 btn"),
                    
                    # Redirects
                    html.Div([
                        html.Span("No account? "),
                        html.A("Sign Up", href="/register", style={"color": "#388087", "textDecoration": "none"})
                    ], className="text-center mt-2"),
                    
                    # Hidden components for logic
                    html.Div(id="login-alert", className="mt-3"),
                    dcc.Location(id='login-redirect', refresh=True)
                ])
            ], className="card shadow mt-5")
        ], width=4), 
        dbc.Col(width=4)  
    ], className="vh-100 align-items-center") 
], fluid=True, style={"backgroundColor": "#F6F6F2"})


# --- LOGIC / API CONNECTION ---
@callback(
    Output("login-alert", "children"),
    Output("session-store", "data"),
    Output("login-redirect", "pathname"),
    Input("btn-login", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, std_email, std_pwd):
    if not std_email or not std_pwd:
        return dbc.Alert("Please enter both email and password.", color="warning"), dash.no_update, dash.no_update
    
    try:
        payload = {"email": std_email, "password": std_pwd}
        response = requests.post(f"{API_URL}/auth/login/standard", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            session_data = {
                "user_id": data["user_id"],
                "token": data["access_token"]
            }
            
            next_page = "/setup" if data["is_new_user"] else "/dashboard"
            
            return dash.no_update, session_data, next_page
        else:
            error_msg = response.json().get("detail", "Authentication Failed")
            return dbc.Alert(error_msg, color="danger"), dash.no_update, dash.no_update
            
    except requests.exceptions.ConnectionError:
        return dbc.Alert("API Server is offline.", color="danger"), dash.no_update, dash.no_update