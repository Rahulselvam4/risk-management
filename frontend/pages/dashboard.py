# frontend/pages/dashboard.py
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import requests
import yfinance as yf
import pandas as pd
import os

from components.navbar import get_navbar
from components.kpi_card import create_kpi_card
from theme import COLORS, get_base_layout

dash.register_page(__name__, path='/dashboard', title="Dashboard - Squilla Fund")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- INDIAN MARKET ASSETS (Matching the Setup Page) ---
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

# --- UI LAYOUT ---
layout = html.Div([
    get_navbar(),
    dbc.Container([
        # Header Row
        dbc.Row([
            dbc.Col([
                html.H2("Portfolio Command Center", style={"color": COLORS["dark_gray"], "fontWeight": "600"}),
                html.P("Analyze systemic risk and AI-driven asset forecasts.", className="text-muted")
            ], width=8),
            dbc.Col([
                dbc.Button("↻ Rebalance Portfolio", href="/rebalance", color="primary", className="float-end btn px-4 py-2 mt-2")
            ], width=4)
        ], className="mb-4"),

        # Top KPI Cards
        dbc.Row(id="dashboard-kpi-row", className="mb-4"),

        # MACRO VIEW: Allocation & Drawdown
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Graph(id="allocation-pie-chart", config={'displayModeBar': False})
            ]), className="shadow-sm card"), width=4),
            
            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Graph(id="drawdown-area-chart", config={'displayModeBar': False})
            ]), className="shadow-sm card"), width=8)
        ], className="mb-5"),

        html.Hr(style={"color": COLORS["light_gray"]}),

        # MICRO VIEW: Deep Dive AI & Moving Averages
        html.H3("Micro Asset Intelligence", className="mt-5 mb-4", style={"color": COLORS["dark_gray"], "fontWeight": "600"}),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.Label("Select Asset to Analyze:", className="fw-bold text-muted mb-2"),
                    # --- THE UPGRADE: Searchable Dropdown ---
                    dcc.Dropdown(
                        id="ai-ticker-input",
                        options=INDIAN_ASSETS,
                        placeholder="Search Indian Equities & Commodities...",
                        searchable=True,
                        clearable=True,
                        className="mb-3"
                    ),
                    dbc.Button("Run Explainable AI", id="btn-run-ai", color="dark", className="w-100 btn")
                ]), className="shadow-sm card border-0")
            ], width=3),
            
            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Loading(
                    dcc.Graph(id="ma-price-chart", config={'displayModeBar': False}), 
                    type="circle", color=COLORS["deep_teal"]
                )
            ]), className="shadow-sm card border-0"), width=5),
            
            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Loading(
                    dcc.Graph(id="shap-waterfall-chart", config={'displayModeBar': False}), 
                    type="circle", color=COLORS["alert_red"]
                )
            ]), className="shadow-sm card border-0"), width=4)
        ], className="mb-5")

    ], fluid=True, style={"maxWidth": "1400px"})
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC: MACRO DIAGNOSTICS ---
@callback(
    Output("dashboard-kpi-row", "children"),
    Output("allocation-pie-chart", "figure"),
    Output("drawdown-area-chart", "figure"),
    Input("session-store", "data")
)
def load_macro_dashboard(session):
    if not session or not session.get('user_id'):
        return [], go.Figure(), go.Figure()
        
    user_id = session['user_id']
    
    try:
        # 1. Fetch Allocation for Pie Chart
        port_res = requests.get(f"{API_URL}/portfolio/{user_id}")
        assets = port_res.json().get("assets", [])
        
        if not assets:
            return [], go.Figure().update_layout(get_base_layout("No Portfolio Data")), go.Figure()

        pie_fig = px.pie(
            assets, names='ticker', values='weight', hole=0.45, 
            title="Asset Allocation", 
            color_discrete_sequence=[COLORS['deep_teal'], COLORS['muted_aqua'], COLORS['dark_gray']]
        )
        pie_fig.update_layout(get_base_layout("Asset Allocation"))

        # 2. Fetch Diagnostics for KPIs and Drawdown
        diag_res = requests.get(f"{API_URL}/portfolio/{user_id}/diagnostics")
        if diag_res.status_code == 200:
            data = diag_res.json()
            
            # Create KPI Components
            kpis = [
                create_kpi_card("Total Historical Return", f"{data['total_return']}%"),
                create_kpi_card("Value at Risk (95%)", f"${data['var_95']}"),
                create_kpi_card("Maximum Drawdown", f"{data['current_drawdown']}%", is_alert=True)
            ]

            # Create Drawdown Area Chart
            draw_fig = go.Figure()
            draw_fig.add_trace(go.Scatter(
                x=data['dates'], y=data['drawdown_history'], 
                fill='tozeroy', mode='lines', 
                line=dict(color=COLORS['alert_red'], width=2),
                name="Drawdown"
            ))
            draw_fig.update_layout(get_base_layout("Systemic Portfolio Drawdown"))
            draw_fig.update_yaxes(tickformat=".1%")

            return kpis, pie_fig, draw_fig
            
    except Exception as e:
        print(f"Dashboard load error: {e}")
        
    return [], go.Figure(), go.Figure()


# --- LOGIC: MICRO EXPLAINABLE AI ---
@callback(
    Output("ma-price-chart", "figure"),
    Output("shap-waterfall-chart", "figure"),
    Input("btn-run-ai", "n_clicks"),
    State("ai-ticker-input", "value"),
    prevent_initial_call=True
)
def run_micro_ai(n_clicks, ticker):
    if not ticker:
        return go.Figure(), go.Figure()
        
    ticker = ticker.upper()
    
    # 1. Generate Technical Chart (Moving Averages)
    try:
        # Fetch 3 months of data for UI rendering
        df = yf.download(ticker, period="3mo", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_30'] = df['Close'].rolling(window=30).mean()
            
            ma_fig = go.Figure()
            ma_fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Price', line=dict(color=COLORS['dark_gray'])))
            ma_fig.add_trace(go.Scatter(x=df.index, y=df['SMA_10'], mode='lines', name='10-Day MA', line=dict(color=COLORS['deep_teal'])))
            ma_fig.add_trace(go.Scatter(x=df.index, y=df['SMA_30'], mode='lines', name='30-Day MA', line=dict(color=COLORS['alert_red'], dash='dot')))
            ma_fig.update_layout(get_base_layout(f"{ticker} Technicals"))
            ma_fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        else:
            ma_fig = go.Figure().update_layout(get_base_layout("No Price Data"))
    except Exception:
        ma_fig = go.Figure().update_layout(get_base_layout("Error Fetching Chart Data"))

    # 2. Trigger Backend Random Forest for SHAP Explanation
    try:
        res = requests.get(f"{API_URL}/predict/{ticker}")
        if res.status_code == 200:
            data = res.json()
            shap_data = data.get("shap_breakdown", [])
            
            # Format data for Plotly Waterfall
            features = [item['feature'] for item in shap_data]
            impacts = [item['impact_percentage'] for item in shap_data]
            
            shap_fig = go.Figure(go.Waterfall(
                orientation="h",
                measure=["relative"] * len(features),
                y=features,
                x=impacts,
                connector={"line": {"color": COLORS["light_gray"]}},
                decreasing={"marker": {"color": COLORS["muted_aqua"]}},
                increasing={"marker": {"color": COLORS["alert_red"]}}
            ))
            
            risk_text = "HIGH RISK" if data['is_high_risk_tomorrow'] else "STABLE"
            title = f"AI Explanation ({risk_text}: {data['risk_probability']}%)"
            shap_fig.update_layout(get_base_layout(title))
            return ma_fig, shap_fig
            
    except Exception:
        pass
        
    return ma_fig, go.Figure().update_layout(get_base_layout("AI Request Failed"))