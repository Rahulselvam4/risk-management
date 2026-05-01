# frontend/pages/rebalance.py
import dash
from dash import dcc, html, Input, Output, State, callback, ALL, ctx
import dash_bootstrap_components as dbc
import requests
import os

from components.navbar import get_navbar
from theme import COLORS

dash.register_page(__name__, path='/rebalance', title="Rebalance - RISK DASHBOARD")

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

# --- UI LAYOUT ---
layout = html.Div([
    get_navbar(),
    dcc.Location(id="rebalance-loc"), 
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Rebalancing Engine", style={"color": COLORS["dark_gray"], "fontWeight": "600"}),
                html.P("Rotate assets and adjust allocation and AI risk threshold. Total weights must sum exactly to 1.0 (100%).", className="text-muted"),
                
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id="new-asset-dropdown", 
                                    options=INDIAN_ASSETS, 
                                    placeholder="Search to add new stock...",
                                    searchable=True,
                                    clearable=True
                                ), 
                                width=9
                            ),
                            dbc.Col(dbc.Button("Add Stock", id="btn-add-asset", color="dark", className="w-100"), width=3)
                        ], className="mb-4"),
                        
                        html.Hr(style={"color": COLORS["light_gray"]}),
                        
                        dcc.Loading(html.Div(id="rebalance-asset-container"), type="circle", color=COLORS["deep_teal"]),
                        
                        html.Hr(className="my-4", style={"color": COLORS["light_gray"]}),
                        
                        dbc.Row([
                            dbc.Col(html.H5("Total Allocation:", className="mb-0"), width=4, align="center"),
                            dbc.Col(html.H4(id="rebalance-total-text", className="mb-0 text-end"), width=8)
                        ]),
                        
                        dbc.Progress(id="rebalance-progress-bar", value=0, className="mt-3 mb-4", style={"height": "10px"}),
                        
                        # --- NEW: TOTAL CAPITAL INPUT ---
                        dbc.InputGroup([
                            dbc.InputGroupText("Total Investment Capital (₹)", style={"fontWeight": "bold"}),
                            dbc.Input(id="rebalance-capital", type="number", min=1000, step=1000)
                        ], className="mb-4"),
                        
                        dbc.Row([
                            dbc.Col(dbc.Button("Cancel", href="/dashboard", color="light", className="w-100 btn text-dark")),
                            dbc.Col(dbc.Button("Apply New Setup", id="btn-submit-rebalance", color="primary", className="w-100 btn", disabled=True))
                        ]),
                        
                        html.Div(id="rebalance-alert", className="mt-3"),
                        dcc.Location(id="rebalance-redirect", refresh=True),
                        html.Pre(id='rebalance-debug', style={"whiteSpace": "pre-wrap", "fontSize": "13px", "color": "#2C3E50", "marginTop": "1rem"})
                    ])
                ], className="shadow-sm border-0 mt-4", style={"maxWidth": "800px", "margin": "0 auto"})
            ])
        ])
    ], fluid=True)
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC 1: MASTER UI GENERATOR ---
@callback(
    Output("rebalance-asset-container", "children"),
    Output("rebalance-capital", "value"),
    Input("rebalance-loc", "pathname"),
    Input("btn-add-asset", "n_clicks"),
    Input({'type': 'btn-delete-asset', 'index': ALL}, 'n_clicks'),
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'value'),
    State({'type': 'dynamic-threshold-input', 'index': ALL}, 'value'),
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'id'),
    State("new-asset-dropdown", "value"),
    State("session-store", "data"),
    prevent_initial_call=False
)
def render_rebalance_ui(pathname, add_clicks, delete_clicks, weights, thresholds, weight_ids, new_ticker, session):
    if not session or not session.get('user_id'):
        return [dbc.Alert("Unauthorized. Please log in.", color="danger")], dash.no_update

    user_id = session['user_id']
    triggered_id = ctx.triggered_id

    current_portfolio = []
    if weights and weight_ids and thresholds:
        for w, t, w_id in zip(weights, thresholds, weight_ids):
            current_portfolio.append({
                "ticker": w_id['index'], 
                "weight": w if w is not None else 0.0,
                "risk_threshold": t if t is not None else 1.5
            })

    capital_val = dash.no_update

    if not triggered_id or triggered_id == "rebalance-loc":
        try:
            res = requests.get(f"{API_URL}/portfolio/{user_id}")
            data = res.json()
            current_portfolio = data.get("assets", [])
            # NEW: Grab the total capital from the backend to pre-fill the box
            capital_val = data.get("total_capital", 100000.0)
        except Exception as e:
            return [dbc.Alert(f"Database Error: {e}", color="danger")], dash.no_update

    elif triggered_id == "btn-add-asset":
        if new_ticker and not any(p['ticker'] == new_ticker for p in current_portfolio):
            current_portfolio.append({"ticker": new_ticker, "weight": 0.0, "risk_threshold": 1.5})

    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'btn-delete-asset':
        deleted_ticker = triggered_id['index']
        current_portfolio = [p for p in current_portfolio if p['ticker'] != deleted_ticker]

    if not current_portfolio:
        return [dbc.Alert("Your portfolio is empty. Add a stock using the search bar above.", color="info")], capital_val

    input_rows = []
    for a in current_portfolio:
        row = dbc.InputGroup([
            dbc.InputGroupText(a['ticker'], style={"width": "150px", "fontWeight": "bold", "backgroundColor": COLORS["deep_teal"], "color": "white"}),
            dbc.InputGroupText("Wt:"),
            dbc.Input(
                id={'type': 'dynamic-weight-input', 'index': a['ticker']}, 
                type="number", value=float(a.get('weight', 0)), step=0.01, min=0, max=1,
                style={"color": "#2C3E50", "fontSize": "15px"}
            ),
            # Dynamic Threshold Input Field
            dbc.InputGroupText("Risk %:"),
            dbc.Input(
                id={'type': 'dynamic-threshold-input', 'index': a['ticker']}, 
                type="number", value=float(a.get('risk_threshold', 1.5)), step=0.1, min=0.1,
                style={"color": "#2C3E50", "fontSize": "15px"}
            ),
            dbc.Button(html.I(className="bi bi-trash"), id={'type': 'btn-delete-asset', 'index': a['ticker']}, color="danger", outline=True)
        ], className="mb-3 shadow-sm")
        input_rows.append(row)

    return input_rows, capital_val


# --- LOGIC 2: Real-Time Math Validation ---
@callback(
    Output("rebalance-total-text", "children"),
    Output("rebalance-total-text", "style"),
    Output("rebalance-progress-bar", "value"),
    Output("rebalance-progress-bar", "color"),
    Output("btn-submit-rebalance", "disabled"),
    Input({'type': 'dynamic-weight-input', 'index': ALL}, 'value')
)
def validate_weights(weights):
    if not weights:
        return "0.00", {}, 0, "secondary", True
        
    clean_weights = [w if w is not None else 0 for w in weights]
    total = sum(clean_weights)
    total_rounded = round(total, 2)
    
    if total_rounded == 1.00:
        return "1.00 (100%)", {"color": COLORS["success_green"], "fontWeight": "bold"}, 100, "success", False
    elif total_rounded > 1.00:
        return f"{total_rounded} (Overallocated)", {"color": COLORS["alert_red"], "fontWeight": "bold"}, 100, "danger", True
    else:
        progress = int(total_rounded * 100)
        return f"{total_rounded} (Need {round(1.0 - total_rounded, 2)} more)", {"color": COLORS["muted_aqua"], "fontWeight": "bold"}, progress, "info", True


@callback(
    Output('rebalance-debug', 'children'),
    Input({'type': 'dynamic-weight-input', 'index': ALL}, 'value'),
    Input({'type': 'dynamic-threshold-input', 'index': ALL}, 'value')
)
def show_debug(weights, thresholds):
    return f"weights: {weights}\nthresholds: {thresholds}"


# --- LOGIC 3: API Submission ---
@callback(
    Output("rebalance-alert", "children"),
    Output("rebalance-redirect", "pathname"),
    Input("btn-submit-rebalance", "n_clicks"),
    State('rebalance-capital', 'value'), # NEW: Capture the capital input
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'value'),
    State({'type': 'dynamic-threshold-input', 'index': ALL}, 'value'),
    State({'type': 'dynamic-threshold-input', 'index': ALL}, 'id'),
    State("session-store", "data"),
    prevent_initial_call=True
)
def submit_rebalance(n_clicks, capital, weights, thresholds, threshold_ids, session):
    user_id = session.get('user_id')
    print(f"submit_rebalance called - weights={weights}, thresholds={thresholds}, threshold_ids={threshold_ids}")
    import sys
    sys.stdout.flush()
    
    new_portfolio = []
    for w, t, t_id in zip(weights, thresholds, threshold_ids):
        try:
            weight_val = float(w) if w is not None else 0.0
        except Exception:
            weight_val = 0.0
        try:
            thresh_val = float(t) if t is not None else 1.5
        except Exception:
            thresh_val = 1.5
        new_portfolio.append({"ticker": t_id['index'], "weight": weight_val, "risk_threshold": thresh_val})
    
    try:
        # NEW: Construct the new payload including the user's capital
        payload = {
            "assets": new_portfolio,
            "total_capital": float(capital) if capital else 100000.0
        }
        res = requests.put(f"{API_URL}/portfolio/{user_id}/rebalance", json=payload)
        
        if res.status_code == 200:
            return dash.no_update, "/dashboard"
        else:
            error_detail = res.json().get("detail", "Database update failed.")
            return dbc.Alert(error_detail, color="danger"), dash.no_update
            
    except requests.exceptions.ConnectionError:
        return dbc.Alert("API Server is offline.", color="danger"), dash.no_update