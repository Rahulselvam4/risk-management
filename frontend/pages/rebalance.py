# frontend/pages/rebalance.py
import dash
from dash import dcc, html, Input, Output, State, callback, ALL, ctx
import dash_bootstrap_components as dbc
import requests
import os

from components.navbar import get_navbar
from theme import COLORS

dash.register_page(__name__, path='/rebalance', title="Rebalance - Squilla Fund")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- INDIAN MARKET ASSETS (For the Add New Stock Dropdown) ---
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

# --- UI LAYOUT ---
layout = html.Div([
    get_navbar(),
    dcc.Location(id="rebalance-loc"), # Invisible trigger for initial page load
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Rebalancing Engine", style={"color": COLORS["dark_gray"], "fontWeight": "600"}),
                html.P("Rotate assets and adjust allocation. Total weights must sum exactly to 1.0 (100%).", className="text-muted"),
                
                dbc.Card([
                    dbc.CardBody([
                        # --- ADD NEW ASSET CONTROLS ---
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
                        
                        # --- DYNAMIC PORTFOLIO LIST ---
                        dcc.Loading(html.Div(id="rebalance-asset-container"), type="circle", color=COLORS["deep_teal"]),
                        
                        html.Hr(className="my-4", style={"color": COLORS["light_gray"]}),
                        
                        # --- VALIDATION BAR ---
                        dbc.Row([
                            dbc.Col(html.H5("Total Allocation:", className="mb-0"), width=4, align="center"),
                            dbc.Col(html.H4(id="rebalance-total-text", className="mb-0 text-end"), width=8)
                        ]),
                        
                        dbc.Progress(id="rebalance-progress-bar", value=0, className="mt-3 mb-4", style={"height": "10px"}),
                        
                        # --- ACTION BUTTONS ---
                        dbc.Row([
                            dbc.Col(dbc.Button("Cancel", href="/dashboard", color="light", className="w-100 btn text-dark")),
                            dbc.Col(dbc.Button("Apply New Weights", id="btn-submit-rebalance", color="primary", className="w-100 btn", disabled=True))
                        ]),
                        
                        html.Div(id="rebalance-alert", className="mt-3"),
                        dcc.Location(id="rebalance-redirect", refresh=True)
                    ])
                ], className="shadow-sm border-0 mt-4", style={"maxWidth": "700px", "margin": "0 auto"})
            ])
        ])
    ], fluid=True)
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC 1: MASTER UI GENERATOR (Handles Load, Add, and Delete) ---
@callback(
    Output("rebalance-asset-container", "children"),
    Input("rebalance-loc", "pathname"),
    Input("btn-add-asset", "n_clicks"),
    Input({'type': 'btn-delete-asset', 'index': ALL}, 'n_clicks'),
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'value'),
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'id'),
    State("new-asset-dropdown", "value"),
    State("session-store", "data"),
    prevent_initial_call=False
)
def render_rebalance_ui(pathname, add_clicks, delete_clicks, weights, weight_ids, new_ticker, session):
    if not session or not session.get('user_id'):
        return [dbc.Alert("Unauthorized. Please log in.", color="danger")]

    user_id = session['user_id']
    triggered_id = ctx.triggered_id

    # 1. Read the current screen state into a list
    current_portfolio = []
    if weights and weight_ids:
        for w, w_id in zip(weights, weight_ids):
            current_portfolio.append({"ticker": w_id['index'], "weight": w if w is not None else 0.0})

    # 2. Handle the specific action that triggered the callback
    if not triggered_id or triggered_id == "rebalance-loc":
        # Initial Page Load: Fetch from Database
        try:
            res = requests.get(f"{API_URL}/portfolio/{user_id}")
            current_portfolio = res.json().get("assets", [])
        except Exception as e:
            return [dbc.Alert(f"Database Error: {e}", color="danger")]

    elif triggered_id == "btn-add-asset":
        # User clicked "Add Stock"
        if new_ticker and not any(p['ticker'] == new_ticker for p in current_portfolio):
            current_portfolio.append({"ticker": new_ticker, "weight": 0.0})

    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'btn-delete-asset':
        # User clicked a Trash Can. The new ctx.triggered_id directly hands us the dictionary!
        deleted_ticker = triggered_id['index']
        current_portfolio = [p for p in current_portfolio if p['ticker'] != deleted_ticker]

    # 3. Generate the actual UI components
    if not current_portfolio:
        return [dbc.Alert("Your portfolio is empty. Add a stock using the search bar above.", color="info")]

    input_rows = []
    for a in current_portfolio:
        row = dbc.InputGroup([
            dbc.InputGroupText(a['ticker'], style={"width": "160px", "fontWeight": "bold", "backgroundColor": COLORS["deep_teal"], "color": "white"}),
            dbc.Input(
                id={'type': 'dynamic-weight-input', 'index': a['ticker']}, 
                type="number", 
                value=float(a['weight']), 
                step=0.01, min=0, max=1
            ),
            # The Trash Can delete button
            dbc.Button(html.I(className="bi bi-trash"), id={'type': 'btn-delete-asset', 'index': a['ticker']}, color="danger", outline=True)
        ], className="mb-3 shadow-sm")
        input_rows.append(row)

    return input_rows


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


# --- LOGIC 3: API Submission ---
@callback(
    Output("rebalance-alert", "children"),
    Output("rebalance-redirect", "pathname"),
    Input("btn-submit-rebalance", "n_clicks"),
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'value'),
    State({'type': 'dynamic-weight-input', 'index': ALL}, 'id'),
    State("session-store", "data"),
    prevent_initial_call=True
)
def submit_rebalance(n_clicks, weights, weight_ids, session):
    user_id = session.get('user_id')
    new_portfolio = [{"ticker": w_id['index'], "weight": w} for w, w_id in zip(weights, weight_ids)]
    
    try:
        res = requests.put(f"{API_URL}/portfolio/{user_id}/rebalance", json={"assets": new_portfolio})
        
        if res.status_code == 200:
            return dash.no_update, "/dashboard"
        else:
            error_detail = res.json().get("detail", "Database update failed.")
            return dbc.Alert(error_detail, color="danger"), dash.no_update
            
    except requests.exceptions.ConnectionError:
        return dbc.Alert("API Server is offline.", color="danger"), dash.no_update