# frontend/pages/setup.py
import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import requests
import os
from components.navbar import get_navbar
from theme import COLORS

dash.register_page(__name__, path='/setup', title="Initial Setup - Squilla Fund")

# Pointing to your local FastAPI backend
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- INDIAN MARKET ASSETS (Nifty 100, Commodities, Debt) ---
INDIAN_ASSETS = [
    # Nifty 50 & Nifty 100 Heavyweights
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
    
    # Commodities (Traded as ETFs on NSE)
    {"label": "Gold Benchmark - Nippon India ETF (GOLDBEES.NS)", "value": "GOLDBEES.NS"},
    {"label": "Silver Benchmark - Nippon India ETF (SILVERBEES.NS)", "value": "SILVERBEES.NS"},
    
    # Debt / Fixed Income (Traded as ETFs on NSE)
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
                        # Searchable Dropdown with India-specific assets
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
                        
                        dbc.Button("Finalize & Launch Workspace", id="btn-finalize-setup", color="success", className="w-100 btn", disabled=True),
                        html.Div(id="setup-alert", className="mt-3"),
                        dcc.Location(id="setup-redirect", refresh=True)
                    ])
                ], className="shadow-sm")
            ], width=8)
        ]),
        
        # Invisible storage for the staged assets before they hit the database
        dcc.Store(id='staged-portfolio', data=[])
    ])
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC ---
@callback(
    Output('staged-portfolio', 'data'),
    Output('setup-ticker', 'value'),
    Output('setup-weight', 'value'),
    Input('btn-stage-asset', 'n_clicks'),
    State('setup-ticker', 'value'),
    State('setup-weight', 'value'),
    State('staged-portfolio', 'data'),
    prevent_initial_call=True
)
def stage_asset(n_clicks, ticker, weight, current_portfolio):
    """Adds a ticker and weight to the local browser memory."""
    if not ticker or not weight:
        return dash.no_update, dash.no_update, dash.no_update
        
    ticker = ticker.upper()
    
    # Update if exists, otherwise append
    for item in current_portfolio:
        if item['ticker'] == ticker:
            item['weight'] = weight
            return current_portfolio, None, "" 
            
    current_portfolio.append({"ticker": ticker, "weight": weight})
    return current_portfolio, None, "" 

@callback(
    Output('staged-assets-list', 'children'),
    Output('total-weight-display', 'children'),
    Output('total-weight-display', 'style'),
    Output('btn-finalize-setup', 'disabled'),
    Input('staged-portfolio', 'data')
)
def update_ui(portfolio):
    """Renders the staged portfolio and checks if total weight equals 1.0 (100%)."""
    if not portfolio:
        return html.P("No assets added yet.", className="text-muted"), "0.0%", {"color": COLORS["dark_gray"]}, True
        
    # Build list UI
    items = []
    total_weight = 0.0
    for p in portfolio:
        total_weight += p['weight']
        items.append(html.Div(f"{p['ticker']} : {p['weight']*100}%", className="mb-1 border-bottom pb-1"))
        
    total_weight = round(total_weight, 2)
    weight_str = f"{total_weight * 100}%"
    
    # Validation Logic
    if total_weight == 1.0:
        return items, weight_str, {"color": COLORS["success_green"], "fontWeight": "bold"}, False
    else:
        return items, weight_str, {"color": COLORS["alert_red"], "fontWeight": "bold"}, True

@callback(
    Output('setup-alert', 'children'),
    Output('setup-redirect', 'pathname'),
    Input('btn-finalize-setup', 'n_clicks'),
    State('staged-portfolio', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def finalize_setup(n_clicks, portfolio, session):
    """Fires the new portfolio to the FastAPI backend, triggering the Kafka pipeline."""
    user_id = session.get('user_id')
    if not user_id:
        return dbc.Alert("Session expired. Please log in again.", color="danger"), "/login"
        
    try:
        # We use the bulk Rebalance endpoint to set the initial portfolio atomically
        res = requests.put(f"{API_URL}/portfolio/{user_id}/rebalance", json={"assets": portfolio})
        if res.status_code == 200:
            return dash.no_update, "/dashboard"
        else:
            return dbc.Alert("Failed to save portfolio.", color="danger"), dash.no_update
    except Exception as e:
        return dbc.Alert(f"API Error: {e}", color="danger"), dash.no_update