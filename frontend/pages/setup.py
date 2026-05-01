# frontend/pages/setup.py
import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import requests
import os
from components.navbar import get_navbar
from theme import COLORS
import logging

dash.register_page(__name__, path='/setup', title="Initial Setup - Squilla Fund")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

INDIAN_ASSETS = [
    {"label": "Reliance Industries (RELIANCE.NS)", "value": "RELIANCE.NS"},
    {"label": "Tata Consultancy Services (TCS.NS)", "value": "TCS.NS"},
    {"label": "HDFC Bank (HDFCBANK.NS)", "value": "HDFCBANK.NS"},
    {"label": "Infosys (INFY.NS)", "value": "INFY.NS"},
    {"label": "ICICI Bank (ICICIBANK.NS)", "value": "ICICIBANK.NS"},
    {"label": "State Bank of India (SBIN.NS)", "value": "SBIN.NS"},
    {"label": "Bharti Airtel (BHARTIARTL.NS)", "value": "BHARTIARTL.NS"},
    {"label": "ITC Limited (ITC.NS)", "value": "ITC.NS"},
    {"label": "Hindustan Unilever (HINDUNILVR.NS)", "value": "HINDUNILVR.NS"},
    {"label": "Larsen & Toubro (LT.NS)", "value": "LT.NS"},
    {"label": "Bajaj Finance (BAJFINANCE.NS)", "value": "BAJFINANCE.NS"},
    {"label": "Tata Motors (TATAMOTORS.NS)", "value": "TATAMOTORS.NS"},
    {"label": "Mahindra & Mahindra (M&M.NS)", "value": "M&M.NS"},
    {"label": "Asian Paints (ASIANPAINT.NS)", "value": "ASIANPAINT.NS"},
    {"label": "Maruti Suzuki (MARUTI.NS)", "value": "MARUTI.NS"},
    {"label": "Sun Pharmaceuticals (SUNPHARMA.NS)", "value": "SUNPHARMA.NS"},
    {"label": "Kotak Mahindra Bank (KOTAKBANK.NS)", "value": "KOTAKBANK.NS"},
    {"label": "Titan Company (TITAN.NS)", "value": "TITAN.NS"},
    {"label": "Gold Benchmark - Nippon India ETF (GOLDBEES.NS)", "value": "GOLDBEES.NS"},
    {"label": "Silver Benchmark - Nippon India ETF (SILVERBEES.NS)", "value": "SILVERBEES.NS"},
    {"label": "Debt / Cash Equivalent - Liquid BeES (LIQUIDBEES.NS)", "value": "LIQUIDBEES.NS"},
    {"label": "Govt Bonds - Long Term Gilt ETF (GILTBEES.NS)", "value": "GILTBEES.NS"}
]

layout = html.Div([
    get_navbar(),
    dbc.Container([
        dbc.Row(dbc.Col(html.H2("Construct Your Portfolio", className="mb-4", style={"color": COLORS["dark_gray"]}))),
        
        dbc.Row([
            # Left Column: The Input Controls
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Add Asset", style={"backgroundColor": COLORS["deep_teal"], "color": "white"}),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id="setup-ticker",
                            options=INDIAN_ASSETS,
                            placeholder="Search Indian Equities & Commodities...",
                            searchable=True,
                            clearable=True,
                            className="mb-3"
                        ),
                        dbc.InputGroup([
                            dbc.InputGroupText("Weight (0.01 - 1.0)"),
                            dbc.Input(id="setup-weight", type="number", min=0.01, max=1.0, step=0.01)
                        ], className="mb-3"),
                        # --- NEW INPUT FOR RISK THRESHOLD ---
                        dbc.InputGroup([
                            dbc.InputGroupText("Risk Threshold (%)"),
                            dcc.Input(id="setup-threshold", type="number", min=0.001, max=50.0, step=0.1, value=1.5, debounce=False, className="form-control", style={"color": "#2C3E50", "fontSize": "15px", "padding": "0.25rem"})
                        ], className="mb-3"),
                        
                        dbc.Button("Add to Staging", id="btn-stage-asset", color="dark", className="w-100 btn")
                    ])
                ], className="shadow-sm mb-4")
            ], width=4),

            # Right Column: The Staged Portfolio
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Current Allocation", style={"backgroundColor": COLORS["muted_aqua"], "color": "white"}),
                    dbc.CardBody([
                        html.Div(id="staged-assets-list", className="mb-3"),
                        html.Hr(),
                        html.Div([
                            html.Strong("Total Allocated: "),
                            html.Span(id="total-weight-display", className="fs-5")
                        ], className="mb-3"),
                        
                        # --- NEW: TOTAL CAPITAL INPUT ---
                        dbc.InputGroup([
                            dbc.InputGroupText("Total Investment Capital (₹)", style={"fontWeight": "bold"}),
                            dbc.Input(id="setup-capital", type="number", min=1000, step=1000, value=100000)
                        ], className="mb-4"),
                        
                        dbc.Button("Finalize & Launch Workspace", id="btn-finalize-setup", color="success", className="w-100 btn", disabled=True),
                        html.Div(id="setup-alert", className="mt-3"),
                        dcc.Location(id="setup-redirect", refresh=True),
                        dcc.Interval(id="setup-poll", interval=2000, n_intervals=0, disabled=True)
                    ])
                ], className="shadow-sm")
            ], width=8)
        ]),
        
        dcc.Store(id='staged-portfolio', data=[])
    ])
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC ---
@callback(
    Output('staged-portfolio', 'data'),
    Output('setup-ticker', 'value'),
    Output('setup-weight', 'value'),
    Output('setup-threshold', 'value'), # Reset threshold
    Input('btn-stage-asset', 'n_clicks'),
    State('setup-ticker', 'value'),
    State('setup-weight', 'value'),
    State('setup-threshold', 'value'),
    State('staged-portfolio', 'data'),
    prevent_initial_call=True
)
def stage_asset(n_clicks, ticker, weight, threshold, current_portfolio):
    try:
        # Immediate server-side debug output (visible in the Dash terminal)
        print(f"stage_asset called - clicks={n_clicks}, ticker={ticker}, weight={weight}, threshold={threshold}, current_portfolio={current_portfolio}")
        import sys
        sys.stdout.flush()

        # Validate ticker and weight; default threshold to 1.5 if not provided
        if not ticker:
            print("stage_asset: validation failed - missing ticker")
            sys.stdout.flush()
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if weight is None:
            print("stage_asset: validation failed - missing weight")
            sys.stdout.flush
            ()
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if threshold is None:
            print("stage_asset: threshold missing from client — defaulting to 1.5")
            sys.stdout.flush()
            threshold = 1.5

        # Log via logger as well
        logger = logging.getLogger("frontend.setup")
        logger.info(f"stage_asset called - clicks={n_clicks}, ticker={ticker}, weight={weight}, threshold={threshold}, current_portfolio={current_portfolio}")

        ticker = ticker.upper()

        for item in current_portfolio:
            if item['ticker'] == ticker:
                item['weight'] = weight
                item['risk_threshold'] = threshold
                return current_portfolio, None, None, dash.no_update

        # Include risk threshold in the payload
        current_portfolio.append({"ticker": ticker, "weight": weight, "risk_threshold": threshold})
        return current_portfolio, None, None, dash.no_update
    except Exception as e:
        print(f"stage_asset: exception: {e}")
        sys.stdout.flush()
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@callback(
    Output('staged-assets-list', 'children'),
    Output('total-weight-display', 'children'),
    Output('total-weight-display', 'style'),
    Output('btn-finalize-setup', 'disabled'),
    Input('staged-portfolio', 'data')
)
def update_ui(portfolio):
    if not portfolio:
        return html.P("No assets added yet.", className="text-muted"), "0.0%", {"color": COLORS["dark_gray"]}, True
        
    items = []
    total_weight = 0.0
    for p in portfolio:
        total_weight += p['weight']
        # Show both weight and threshold in UI
        items.append(html.Div(f"{p['ticker']} : {p['weight']*100}% | Drop Target: {p.get('risk_threshold', 1.5)}%", className="mb-1 border-bottom pb-1"))
        
    total_weight = round(total_weight, 2)
    weight_str = f"{total_weight * 100}%"
    
    if total_weight == 1.0:
        return items, weight_str, {"color": COLORS["success_green"], "fontWeight": "bold"}, False
    else:
        return items, weight_str, {"color": COLORS["alert_red"], "fontWeight": "bold"}, True

@callback(
    Output('setup-alert', 'children', allow_duplicate=True),
    Output('setup-redirect', 'pathname'),
    Output('setup-poll', 'disabled'),
    Input('btn-finalize-setup', 'n_clicks'),
    State('setup-capital', 'value'),
    State('staged-portfolio', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def finalize_setup(n_clicks, capital, portfolio, session):
    user_id = session.get('user_id')
    if not user_id:
        return dbc.Alert("Session expired. Please log in again.", color="danger"), "/login", True

    try:
        payload = {
            "assets": portfolio,
            "total_capital": float(capital) if capital else 100000.0
        }
        res = requests.put(f"{API_URL}/portfolio/{user_id}/rebalance", json=payload)

        if res.status_code == 200:
            alert = html.Div([
                dbc.Spinner(size="sm", color="success", spinner_class_name="me-2"),
                html.Span("Portfolio saved! Waiting for market data pipeline...", className="text-success fw-bold")
            ], className="d-flex align-items-center")
            return alert, dash.no_update, False  # start polling
        else:
            try:
                detail = res.json().get('detail', 'Failed to save portfolio.')
            except Exception:
                detail = f"Failed to save portfolio (status {res.status_code})"
            return dbc.Alert(detail, color="danger"), dash.no_update, True
    except Exception as e:
        return dbc.Alert(f"API Error: {e}", color="danger"), dash.no_update, True


@callback(
    Output('setup-redirect', 'pathname', allow_duplicate=True),
    Output('setup-poll', 'disabled', allow_duplicate=True),
    Output('setup-alert', 'children', allow_duplicate=True),
    Input('setup-poll', 'n_intervals'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def poll_for_data(n_intervals, session):
    if not session or not session.get('user_id'):
        return dash.no_update, True, dash.no_update
    user_id = session['user_id']
    try:
        port_res = requests.get(f"{API_URL}/portfolio/{user_id}", timeout=3)
        if port_res.status_code == 200 and port_res.json().get('assets'):
            diag_res = requests.get(f"{API_URL}/portfolio/{user_id}/diagnostics", timeout=3)
            if diag_res.status_code == 200:
                return "/dashboard", True, dash.no_update  # fully ready — redirect
            # assets saved, waiting for Kafka + diagnostics
            dots = "." * ((n_intervals % 3) + 1)
            msg = html.Div([
                dbc.Spinner(size="sm", color="success", spinner_class_name="me-2"),
                html.Span(f"Portfolio saved! Building dashboard{dots}", className="text-success fw-bold")
            ], className="d-flex align-items-center")
            return dash.no_update, False, msg
    except Exception:
        pass
    return dash.no_update, False, dash.no_update  # keep polling