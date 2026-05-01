# frontend/pages/login.py
import dash
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import requests
import os
import jwt # <-- We use this to read Google's secure token
from dotenv import load_dotenv

dash.register_page(__name__, path='/login', title="Login - RISK DASHBOARD")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

load_dotenv()

# Securely fetch the real ID
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

if not GOOGLE_CLIENT_ID:
    print("WARNING: GOOGLE_CLIENT_ID not found in .env file!")

# --- UI LAYOUT ---
layout = dbc.Container([
    # 1. Inject the official Google Identity Services script
    html.Script(src="https://accounts.google.com/gsi/client", **{"async": True, "defer": True}),
    
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
                    dbc.Input(id="login-password", type="password", placeholder="Password", className="mb-3"),
                    dbc.Button("Authenticate", id="btn-login", color="dark", className="w-100 mb-3 btn"),
                    
                    html.Hr(className="my-3"),
                    
                    # --- THE REAL GOOGLE BUTTON ---
                    html.Div(className="d-flex justify-content-center mb-3", children=[
                        # Configuration div that points to your Javascript function
                        html.Div(id="g_id_onload", **{
                            "data-client_id": GOOGLE_CLIENT_ID,
                            "data-callback": "handleCredentialResponse", # Matches our .js file!
                            "data-auto_prompt": "false"
                        }),
                        # The actual visual button rendered by Google
                        html.Div(className="g_id_signin", **{
                            "data-type": "standard", 
                            "data-shape": "rectangular", 
                            "data-theme": "outline", 
                            "data-text": "signin_with", 
                            "data-size": "large", 
                            "data-logo_alignment": "left"
                        })
                    ]),
                    
                    # Redirects
                    html.Div([
                        html.Span("No account? "),
                        html.A("Request Access", href="/register", style={"color": "#388087", "textDecoration": "none"})
                    ], className="text-center mt-2"),
                    
                    # Hidden components for logic
                    html.Div(id="login-alert", className="mt-3"),
                    dcc.Location(id='login-redirect', refresh=True),
                    
                    # Hidden input to catch the Google Token from Javascript
                    dcc.Input(id="google-auth-token", type="hidden", value="")
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
    Input("google-auth-token", "value"), # Triggers when Google popup succeeds!
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def handle_all_logins(n_clicks, google_token, std_email, std_pwd):
    triggered_id = ctx.triggered_id

    try:
        # --- PATH A: STANDARD LOGIN ---
        if triggered_id == "btn-login":
            if not std_email or not std_pwd:
                return dbc.Alert("Please enter both email and password.", color="warning"), dash.no_update, dash.no_update
                
            payload = {"email": std_email, "password": std_pwd}
            response = requests.post(f"{API_URL}/auth/login/standard", json=payload)
            
        # --- PATH B: THE REAL GOOGLE LOGIN ---
        elif triggered_id == "google-auth-token" and google_token:
            # Decode the secure token Google sent us (we skip signature verification here 
            # because we only need the payload to send to our secure FastAPI backend)
            decoded_google_data = jwt.decode(google_token, options={"verify_signature": False})
            
            google_email = decoded_google_data.get("email")
            google_id = decoded_google_data.get("sub") # 'sub' is Google's official unique ID
            
            payload = {"email": google_email, "google_id": google_id}
            response = requests.post(f"{API_URL}/auth/login/google", json=payload)

        else:
            return dash.no_update, dash.no_update, dash.no_update


        # --- ROUTING LOGIC (Applies to both paths) ---
        if response.status_code == 200:
            data = response.json()
            
            session_data = {
                "user_id": data["user_id"],
                "token": data["access_token"]
            }
            
            # FASTAPI decides if they are new (routes to /setup) or existing (routes to /dashboard)
            next_page = "/setup" if data["is_new_user"] else "/dashboard"
            
            return dash.no_update, session_data, next_page
            
        else:
            error_msg = response.json().get("detail", "Authentication Failed")
            return dbc.Alert(error_msg, color="danger"), dash.no_update, dash.no_update
            
    except requests.exceptions.ConnectionError:
        return dbc.Alert("API Server is offline.", color="danger"), dash.no_update, dash.no_update