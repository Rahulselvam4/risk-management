# frontend/pages/setup.py
import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import requests
import os
from components.navbar import get_navbar
from theme import COLORS
import logging

dash.register_page(__name__, path='/setup', title="Initial Setup - RISK DASHBOARD")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

INDIAN_ASSETS = [
    # Nifty 50 Blue Chips - Banking & Financial Services
    {"label": "HDFC Bank (HDFCBANK.NS)", "value": "HDFCBANK.NS"},
    {"label": "ICICI Bank (ICICIBANK.NS)", "value": "ICICIBANK.NS"},
    {"label": "State Bank of India (SBIN.NS)", "value": "SBIN.NS"},
    {"label": "Kotak Mahindra Bank (KOTAKBANK.NS)", "value": "KOTAKBANK.NS"},
    {"label": "Axis Bank (AXISBANK.NS)", "value": "AXISBANK.NS"},
    {"label": "Bajaj Finance (BAJFINANCE.NS)", "value": "BAJFINANCE.NS"},
    {"label": "Bajaj Finserv (BAJAJFINSV.NS)", "value": "BAJAJFINSV.NS"},
    {"label": "HDFC Life Insurance (HDFCLIFE.NS)", "value": "HDFCLIFE.NS"},
    {"label": "SBI Life Insurance (SBILIFE.NS)", "value": "SBILIFE.NS"},
    
    # IT & Technology
    {"label": "Tata Consultancy Services (TCS.NS)", "value": "TCS.NS"},
    {"label": "Infosys (INFY.NS)", "value": "INFY.NS"},
    {"label": "HCL Technologies (HCLTECH.NS)", "value": "HCLTECH.NS"},
    {"label": "Wipro (WIPRO.NS)", "value": "WIPRO.NS"},
    {"label": "Tech Mahindra (TECHM.NS)", "value": "TECHM.NS"},
    
    # Energy & Oil
    {"label": "Reliance Industries (RELIANCE.NS)", "value": "RELIANCE.NS"},
    {"label": "ONGC (ONGC.NS)", "value": "ONGC.NS"},
    {"label": "NTPC (NTPC.NS)", "value": "NTPC.NS"},
    {"label": "Power Grid Corporation (POWERGRID.NS)", "value": "POWERGRID.NS"},
    {"label": "Coal India (COALINDIA.NS)", "value": "COALINDIA.NS"},
    
    # Automobiles
    {"label": "Tata Motors (TATAMOTORS.NS)", "value": "TATAMOTORS.NS"},
    {"label": "Maruti Suzuki (MARUTI.NS)", "value": "MARUTI.NS"},
    {"label": "Mahindra & Mahindra (M%26M.NS)", "value": "M%26M.NS"},
    {"label": "Bajaj Auto (BAJAJ-AUTO.NS)", "value": "BAJAJ-AUTO.NS"},
    {"label": "Hero MotoCorp (HEROMOTOCO.NS)", "value": "HEROMOTOCO.NS"},
    {"label": "Eicher Motors (EICHERMOT.NS)", "value": "EICHERMOT.NS"},
    
    # FMCG & Consumer
    {"label": "Hindustan Unilever (HINDUNILVR.NS)", "value": "HINDUNILVR.NS"},
    {"label": "ITC Limited (ITC.NS)", "value": "ITC.NS"},
    {"label": "Nestle India (NESTLEIND.NS)", "value": "NESTLEIND.NS"},
    {"label": "Britannia Industries (BRITANNIA.NS)", "value": "BRITANNIA.NS"},
    {"label": "Dabur India (DABUR.NS)", "value": "DABUR.NS"},
    {"label": "Godrej Consumer (GODREJCP.NS)", "value": "GODREJCP.NS"},
    
    # Pharmaceuticals
    {"label": "Sun Pharmaceuticals (SUNPHARMA.NS)", "value": "SUNPHARMA.NS"},
    {"label": "Dr. Reddy's Laboratories (DRREDDY.NS)", "value": "DRREDDY.NS"},
    {"label": "Cipla (CIPLA.NS)", "value": "CIPLA.NS"},
    {"label": "Divi's Laboratories (DIVISLAB.NS)", "value": "DIVISLAB.NS"},
    {"label": "Biocon (BIOCON.NS)", "value": "BIOCON.NS"},
    
    # Telecom & Media
    {"label": "Bharti Airtel (BHARTIARTL.NS)", "value": "BHARTIARTL.NS"},
    
    # Metals & Mining
    {"label": "Tata Steel (TATASTEEL.NS)", "value": "TATASTEEL.NS"},
    {"label": "JSW Steel (JSWSTEEL.NS)", "value": "JSWSTEEL.NS"},
    {"label": "Hindalco Industries (HINDALCO.NS)", "value": "HINDALCO.NS"},
    {"label": "Vedanta (VEDL.NS)", "value": "VEDL.NS"},
    
    # Cement & Construction
    {"label": "Larsen & Toubro (LT.NS)", "value": "LT.NS"},
    {"label": "UltraTech Cement (ULTRACEMCO.NS)", "value": "ULTRACEMCO.NS"},
    {"label": "Grasim Industries (GRASIM.NS)", "value": "GRASIM.NS"},
    {"label": "Ambuja Cements (AMBUJACEM.NS)", "value": "AMBUJACEM.NS"},
    
    # Retail & Consumer Durables
    {"label": "Titan Company (TITAN.NS)", "value": "TITAN.NS"},
    {"label": "Asian Paints (ASIANPAINT.NS)", "value": "ASIANPAINT.NS"},
    {"label": "Havells India (HAVELLS.NS)", "value": "HAVELLS.NS"},
    
    # Diversified
    {"label": "Adani Enterprises (ADANIENT.NS)", "value": "ADANIENT.NS"},
    {"label": "Adani Ports (ADANIPORTS.NS)", "value": "ADANIPORTS.NS"},
    {"label": "Tata Power (TATAPOWER.NS)", "value": "TATAPOWER.NS"},
    {"label": "IndusInd Bank (INDUSINDBK.NS)", "value": "INDUSINDBK.NS"},
    {"label": "Shree Cement (SHREECEM.NS)", "value": "SHREECEM.NS"},
    {"label": "Bajaj Holdings (BAJAJHLDNG.NS)", "value": "BAJAJHLDNG.NS"},
    
    # Commodities - Gold (Multiple Options)
    {"label": "Gold - Nippon India ETF (GOLDBEES.NS)", "value": "GOLDBEES.NS"},
    {"label": "Gold - SBI ETF (SETFGOLD.NS)", "value": "SETFGOLD.NS"},
    {"label": "Gold - HDFC Gold ETF (HDFCGOLD.NS)", "value": "HDFCGOLD.NS"},
    
    # Commodities - Silver
    {"label": "Silver - Nippon India ETF (SILVERBEES.NS)", "value": "SILVERBEES.NS"},
    {"label": "Silver - SBI ETF (SETFSILV.NS)", "value": "SETFSILV.NS"},
    
    # Debt / Fixed Income
    {"label": "Liquid Fund - Nippon BeES (LIQUIDBEES.NS)", "value": "LIQUIDBEES.NS"},
    {"label": "Govt Bonds - Nippon Gilt ETF (GILTBEES.NS)", "value": "GILTBEES.NS"},
    {"label": "Nifty 50 Index ETF (NIFTYBEES.NS)", "value": "NIFTYBEES.NS"},
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
                            dbc.Input(id="setup-threshold", type="number", min=0.1, max=50.0, step=0.1, value=1.5, className="form-control")
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