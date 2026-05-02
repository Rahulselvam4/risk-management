# frontend/pages/forgot_password.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import requests
import os

dash.register_page(__name__, path='/forgot-password', title="Reset Password - RISK DASHBOARD")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- UI LAYOUT ---
layout = dbc.Container([
    dbc.Row([
        dbc.Col(width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-key text-center", style={"fontSize": "3rem", "color": "#388087"}),
                        html.H2("Reset Password", className="text-center mt-2 mb-4", style={"color": "#2C3E50"}),
                    ], className="text-center"),
                    
                    # Email Input
                    dbc.Input(id="forgot-email", type="email", placeholder="Corporate Email", className="mb-3"),
                    
                    # OTP Section
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(id="forgot-otp", type="text", placeholder="6-digit OTP", maxLength=6, className="mb-3")
                        ], width=7),
                        dbc.Col([
                            dbc.Button("Send OTP", id="btn-forgot-send-otp", color="info", className="w-100 mb-3", outline=True, size="md")
                        ], width=5)
                    ]),
                    
                    html.Div(id="forgot-otp-status", className="mb-3"),
                    
                    # New Password Fields
                    dbc.Input(id="forgot-new-password", type="password", placeholder="New Password", className="mb-3"),
                    dbc.Input(id="forgot-confirm-password", type="password", placeholder="Confirm New Password", className="mb-3"),
                    
                    dbc.Button("Reset Password", id="btn-reset-password", color="dark", className="w-100 mb-3 btn"),
                    
                    # Back to Login
                    html.Div([
                        html.Span("Remember your password? "),
                        html.A("Sign In", href="/login", style={"color": "#388087", "textDecoration": "none"})
                    ], className="text-center mt-3"),
                    
                    # Hidden components
                    html.Div(id="forgot-alert", className="mt-3"),
                    dcc.Location(id='forgot-redirect', refresh=True),
                    dcc.Store(id='forgot-otp-sent', data=False),
                    dcc.Store(id='forgot-otp-verified', data=False)
                ])
            ], className="card shadow mt-5")
        ], width=4),
        dbc.Col(width=4)
    ], className="vh-100 align-items-center")
], fluid=True, style={"backgroundColor": "#F6F6F2"})


# --- LOGIC 1: Send OTP ---
@callback(
    Output("forgot-otp-status", "children"),
    Output("forgot-otp-sent", "data"),
    Output("btn-forgot-send-otp", "children"),
    Output("btn-forgot-send-otp", "disabled"),
    Output("btn-forgot-send-otp", "color"),
    Input("btn-forgot-send-otp", "n_clicks"),
    State("forgot-email", "value"),
    State("forgot-otp-sent", "data"),
    prevent_initial_call=True
)
def send_reset_otp(n_clicks, email, otp_sent):
    if not email or "@" not in email:
        return (
            dbc.Alert("⚠️ Please enter a valid email address", color="warning", dismissable=True),
            False,
            "Send OTP",
            False,
            "info"
        )
    
    try:
        payload = {"email": email, "purpose": "password_reset"}
        response = requests.post(f"{API_URL}/auth/send-otp", json=payload, timeout=10)
        
        if response.status_code == 200:
            return (
                dbc.Alert(
                    [html.I(className="bi bi-check-circle me-2"), "OTP sent! Check your email (and spam folder)."],
                    color="success",
                    dismissable=True
                ),
                True,
                "Resend OTP",
                False,
                "secondary"
            )
        else:
            error_msg = response.json().get("detail", "Failed to send OTP")
            return (
                dbc.Alert(f"❌ {error_msg}", color="danger", dismissable=True),
                False,
                "Send OTP",
                False,
                "info"
            )
            
    except requests.exceptions.Timeout:
        return (
            dbc.Alert("⏱️ Request timeout. OTP may have been sent. Check your email.", color="warning", dismissable=True),
            True,
            "Resend OTP",
            False,
            "secondary"
        )
    except requests.exceptions.ConnectionError:
        return (
            dbc.Alert("❌ Cannot connect to server. Is backend running?", color="danger", dismissable=True),
            False,
            "Send OTP",
            False,
            "info"
        )
    except Exception as e:
        return (
            dbc.Alert(f"❌ Error: {str(e)}", color="danger", dismissable=True),
            False,
            "Send OTP",
            False,
            "info"
        )


# --- LOGIC 2: Auto-verify OTP ---
@callback(
    Output("forgot-otp-verified", "data"),
    Output("forgot-otp-status", "children", allow_duplicate=True),
    Input("forgot-otp", "value"),
    State("forgot-email", "value"),
    State("forgot-otp-sent", "data"),
    State("forgot-otp-verified", "data"),
    prevent_initial_call=True
)
def verify_reset_otp(otp_code, email, otp_sent, already_verified):
    # Don't verify again if already verified
    if already_verified:
        return True, dash.no_update
    
    if not otp_sent or not otp_code or len(otp_code) != 6:
        return False, dash.no_update
    
    if not otp_code.isdigit():
        return False, dash.no_update
    
    # Just show that we're ready - DON'T verify yet
    # Verification will happen during password reset
    return (
        True,
        dbc.Alert(
            [html.I(className="bi bi-check-circle-fill me-2"), "✓ OTP ready! Now create your new password below."],
            color="success"
        )
    )


# --- LOGIC 3: Reset Password ---
@callback(
    Output("forgot-alert", "children"),
    Output("forgot-redirect", "pathname"),
    Output("btn-reset-password", "disabled"),
    Input("btn-reset-password", "n_clicks"),
    State("forgot-email", "value"),
    State("forgot-otp", "value"),
    State("forgot-new-password", "value"),
    State("forgot-confirm-password", "value"),
    State("forgot-otp-verified", "data"),
    prevent_initial_call=True
)
def reset_password(n_clicks, email, otp_code, new_password, confirm_password, otp_verified):
    # Validation
    if not email or not otp_code or not new_password or not confirm_password:
        return dbc.Alert("⚠️ All fields are required.", color="warning"), dash.no_update, False
    
    if not otp_verified:
        return dbc.Alert("⚠️ Please enter the OTP sent to your email.", color="warning"), dash.no_update, False
    
    if len(otp_code) != 6 or not otp_code.isdigit():
        return dbc.Alert("⚠️ OTP must be 6 digits.", color="warning"), dash.no_update, False
        
    if new_password != confirm_password:
        return dbc.Alert("❌ Passwords do not match.", color="danger"), dash.no_update, False
    
    if len(new_password) < 6:
        return dbc.Alert("⚠️ Password must be at least 6 characters.", color="warning"), dash.no_update, False

    try:
        # The backend will verify OTP and reset password in one step
        payload = {"email": email, "otp_code": otp_code, "new_password": new_password}
        response = requests.post(f"{API_URL}/auth/reset-password", json=payload, timeout=10)
        
        if response.status_code == 200:
            return (
                dbc.Alert(
                    [html.I(className="bi bi-check-circle-fill me-2"), "✓ Password reset successful! Redirecting to login..."],
                    color="success"
                ),
                "/login",
                True
            )
        else:
            error_msg = response.json().get("detail", "Password reset failed")
            # Check if it's an OTP error
            if "OTP" in error_msg or "Invalid" in error_msg or "expired" in error_msg.lower():
                return dbc.Alert(f"❌ {error_msg}. Please request a new OTP.", color="danger"), dash.no_update, False
            return dbc.Alert(f"❌ {error_msg}", color="danger"), dash.no_update, False
            
    except requests.exceptions.Timeout:
        return dbc.Alert("⏱️ Request timeout. Please try again.", color="warning"), dash.no_update, False
    except requests.exceptions.ConnectionError:
        return dbc.Alert("❌ Cannot connect to server. Contact support.", color="danger"), dash.no_update, False
    except Exception as e:
        return dbc.Alert(f"❌ Error: {str(e)}", color="danger"), dash.no_update, False
