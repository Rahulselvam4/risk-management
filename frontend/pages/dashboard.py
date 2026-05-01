
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

dash.register_page(__name__, path='/dashboard', title="RISK DASHBOARD", description="Your portfolio's health at a glance, with AI-driven insights and diagnostics.")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- INDIAN MARKET ASSETS ---
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
    dcc.Interval(id="dashboard-poll", interval=3000, n_intervals=0, max_intervals=20),
    dbc.Container([
        # Header Row
        dbc.Row([
            dbc.Col([
                html.H2("Portfolio Command Center",
                        style={"color": COLORS["dark_gray"], "fontWeight": "600"}),
                html.P("Analyze systemic risk and AI-driven asset forecasts.",
                       className="text-muted")
            ], width=8),
            dbc.Col([
                dbc.Button("↻ Rebalance Portfolio", href="/rebalance",
                           color="primary", className="float-end btn px-4 py-2 mt-2")
            ], width=4)
        ], className="mb-4"),

        # Loading banner — visible while data is being fetched
        html.Div(id="dashboard-loading-banner"),

        # Top KPI Cards
        dcc.Loading(
            dbc.Row(id="dashboard-kpi-row", className="mb-4"),
            type="dot", color=COLORS["deep_teal"]
        ),

        # MACRO VIEW: Allocation & Drawdown
        dcc.Loading(
          dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Graph(id="allocation-pie-chart", config={'displayModeBar': False})
            ]), className="shadow-sm card"), width=4),

            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Graph(id="drawdown-area-chart", config={'displayModeBar': False})
            ]), className="shadow-sm card"), width=8)
          ], className="mb-5"),
          type="circle", color=COLORS["deep_teal"]
        ),

        html.Hr(style={"color": COLORS["light_gray"]}),

        # MICRO VIEW: Deep Dive AI & Moving Averages
        html.H3("Micro Asset Intelligence", className="mt-5 mb-4",
                style={"color": COLORS["dark_gray"], "fontWeight": "600"}),
        
        # Selector Row: centered smaller selector above the charts
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Select Your Portfolio Asset:", className="fw-bold text-muted mb-2"),
                    dcc.Dropdown(
                        id="ai-ticker-input",
                        options=[],
                        placeholder="Select from your portfolio...",
                        searchable=True,
                        clearable=True,
                        className="mb-3"
                    ),
                    dbc.Button("PREDICT", id="btn-run-ai",
                               color="dark", className="w-100 btn")
                ]), className="shadow-sm card border-0 selector-card"),
            xs=12
            )
        ], className="mb-4"),

        # Charts Row: two technical graphs below the selector (equal width)
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Loading(
                    dcc.Graph(id="ma-price-chart", config={'displayModeBar': False}),
                    type="circle", color=COLORS["deep_teal"]
                )
            ]), className="shadow-sm card border-0 chart-card"), xs=12, md=6),

            dbc.Col(dbc.Card(dbc.CardBody([
                dcc.Loading(
                    dcc.Graph(id="shap-waterfall-chart", config={'displayModeBar': False}),
                    type="circle", color=COLORS["alert_red"]
                )
            ]), className="shadow-sm card border-0 chart-card"), xs=12, md=6)
        ], className="mb-4"),
        
        # NEW: Model Confidence Card
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.I(className="bi bi-shield-check me-2"), "Model Confidence Metrics"],
                               style={"backgroundColor": COLORS["deep_teal"], "color": "white", "fontWeight": "bold"}),
                dbc.CardBody(id="model-confidence-display")
            ], className="shadow-sm border-0"), width=12)
        ], className="mb-4"),

        # --- THE EXPLANATION BOX ---
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.I(className="bi bi-info-circle me-2"), "How to Read the AI Analysis (Plain English)"], 
                               style={"backgroundColor": COLORS["muted_aqua"], "color": "white", "fontWeight": "bold"}),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("📈 The Technical Chart (Left)", style={"color": COLORS["dark_gray"]}),
                            html.P("This graph shows recent price movements. The bars (candlesticks) show daily trading: Green means the price went up, Red means it went down. The Teal Line is the short-term average price, and the Red Dotted Line is the long-term average. If the short-term line drops below the long-term line, it indicates the stock is losing momentum.", className="text-muted small")
                        ], width=4),
                        dbc.Col([
                            html.H5("🧩 The AI Explanation (Right)", style={"color": COLORS["dark_gray"]}),
                            html.P("This 'waterfall' diagram is the AI explaining its math. Each red block is a clue (like high volatility or a bad P/E ratio) that increases the risk of a crash. The blocks stack diagonally to show you exactly how the AI arrived at its final risk percentage.", className="text-muted small")
                        ], width=4),
                        dbc.Col([
                            html.H5("⚖️ The Verdict & Risk", style={"color": COLORS["dark_gray"]}),
                            html.P([
                                html.Strong("What is the risk? "), "The AI predicts the probability that this stock will drop by ", html.Strong("more than your custom risk threshold tomorrow."), html.Br(),
                                html.Strong("Should I hold? "), "If the AI says ", html.Span("HOLD", style={"color": COLORS["deep_teal"], "fontWeight": "bold"}), ", it means a crash hitting your threshold is unlikely. If it says ", html.Span("SELL", style={"color": COLORS["alert_red"], "fontWeight": "bold"}), ", the AI detects a high probability of a severe drop, and you should reconsider your position."
                            ], className="text-muted small")
                        ], width=4),
                    ])
                ])
            ], className="shadow-sm border-0 mb-5"))
        ])

    ], fluid=True, style={"maxWidth": "1400px"})
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# --- LOGIC: MACRO DIAGNOSTICS ---
def _loading_banner(message="Building your portfolio dashboard, please wait..."):
    return dbc.Alert(
        [dbc.Spinner(size="sm", color="light", spinner_class_name="me-2"), message],
        color="info", className="d-flex align-items-center py-2"
    )


@callback(
    Output("dashboard-kpi-row",        "children"),
    Output("allocation-pie-chart",     "figure"),
    Output("drawdown-area-chart",      "figure"),
    Output("dashboard-poll",           "disabled"),
    Output("dashboard-loading-banner", "children"),
    Output("ai-ticker-input",          "options"),
    Input("session-store",             "data"),
    Input("dashboard-poll",            "n_intervals")
)
def load_macro_dashboard(session, n_intervals):
    empty_figs = (go.Figure().update_layout(get_base_layout("Waiting for data...")),
                  go.Figure().update_layout(get_base_layout("Waiting for data...")))

    if not session or not session.get('user_id'):
        return [], *empty_figs, True, None, []

    user_id = session['user_id']

    try:
        port_res = requests.get(f"{API_URL}/portfolio/{user_id}", timeout=5)
        assets   = port_res.json().get("assets", [])

        if not assets:
            return [], *empty_figs, False, _loading_banner(), []

        # Build dropdown options from user's portfolio
        portfolio_options = [{"label": f"{asset['ticker']}", "value": asset['ticker']} for asset in assets]

        pie_fig = px.pie(
            assets, names='ticker', values='weight', hole=0.45,
            title="Asset Allocation",
            color_discrete_sequence=[COLORS['deep_teal'], COLORS['muted_aqua'], COLORS['dark_gray']]
        )
        pie_fig.update_layout(get_base_layout("Asset Allocation"))

        diag_res = requests.get(f"{API_URL}/portfolio/{user_id}/diagnostics", timeout=5)
        if diag_res.status_code == 200:
            data = diag_res.json()

            kpis = [
                create_kpi_card("Total Returns (3yrs)", f"{data['total_return']}%"),
                create_kpi_card("Value at Risk (95%)",     f"₹{data['var_95']:,.2f}"),
                create_kpi_card("Maximum Drawdown",        f"{data['current_drawdown']}%", is_alert=True)
            ]

            draw_fig = go.Figure()
            draw_fig.add_trace(go.Scatter(
                x=data['dates'], y=data['drawdown_history'],
                fill='tozeroy', mode='lines',
                line=dict(color=COLORS['alert_red'], width=2),
                name="Drawdown"
            ))
            draw_fig.update_layout(get_base_layout("Systemic Portfolio Drawdown"))
            draw_fig.update_yaxes(tickformat=".1%")

            return kpis, pie_fig, draw_fig, True, None, portfolio_options  # data ready — stop polling

        # assets exist but diagnostics not ready yet
        return [], pie_fig, empty_figs[1], False, _loading_banner("Crunching portfolio diagnostics..."), portfolio_options

    except Exception as e:
        print(f"Dashboard load error: {e}")

    return [], *empty_figs, False, _loading_banner(), []  # keep polling on error


# --- LOGIC: MICRO EXPLAINABLE AI ---
@callback(
    Output("ma-price-chart",      "figure"),
    Output("shap-waterfall-chart","figure"),
    Output("model-confidence-display", "children"),
    Input("btn-run-ai",           "n_clicks"),
    State("ai-ticker-input",      "value"),
    State("session-store",        "data"),
    prevent_initial_call=True
)
def run_micro_ai(n_clicks, ticker, session):
    if not ticker or not session or not session.get('user_id'):
        return go.Figure(), go.Figure(), html.P("No prediction run yet.", className="text-muted")

    ticker = ticker.upper()
    user_id = session['user_id']

    # 1. Technical Chart
    try:
        df = yf.download(ticker, period="3mo", progress=False)

        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_30'] = df['Close'].rolling(window=30).mean()

            ma_fig = go.Figure()
            ma_fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'],   close=df['Close'],
                name='OHLC',
                increasing_line_color=COLORS['deep_teal'],
                decreasing_line_color=COLORS['alert_red'],
                showlegend=False
            ))
            ma_fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_10'],
                mode='lines', name='10-Day MA',
                line=dict(color=COLORS['deep_teal'], width=1.5)
            ))
            ma_fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_30'],
                mode='lines', name='30-Day MA',
                line=dict(color=COLORS['alert_red'], dash='dot', width=1.5)
            ))
            ma_fig.update_layout(get_base_layout(f"{ticker} Technicals"))
            ma_fig.update_layout(
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
        else:
            ma_fig = go.Figure().update_layout(get_base_layout("No Price Data"))

    except Exception:
        ma_fig = go.Figure().update_layout(get_base_layout("Error Fetching Chart Data"))

    # 2. Backend ML Prediction + Model Confidence
    try:
        res = requests.get(f"{API_URL}/predict/{user_id}/{ticker}")
        if res.status_code == 200:
            data      = res.json()
            shap_data = data.get("shap_breakdown", [])
            confidence = data.get("model_confidence", {})

            features = [item['feature']           for item in shap_data]
            impacts  = [item['impact_percentage']  for item in shap_data]

            shap_fig = go.Figure(go.Waterfall(
                orientation="h",
                measure=["relative"] * len(features),
                y=features,
                x=impacts,
                connector={"line": {"color": COLORS["light_gray"]}},
                decreasing={"marker": {"color": COLORS["muted_aqua"]}},
                increasing={"marker": {"color": COLORS["alert_red"]}}
            ))

            rec_text = data.get('recommendation', 'HOLD')
            threshold = data.get('target_threshold', 1.5)
            
            shap_fig.update_layout(
                get_base_layout(f"AI Decision: {rec_text} ({data['risk_probability']}% chance of a >{threshold}% drop)")
            )
            
            # Build confidence display
            if confidence:
                trust_score = confidence.get('trust_score', 'UNKNOWN')
                trust_colors = {"HIGH": "success", "MEDIUM": "warning", "LOW": "danger"}
                trust_icons = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
                
                confidence_ui = dbc.Row([
                    dbc.Col([
                        html.H4([trust_icons.get(trust_score, "⚪"), f" {trust_score} CONFIDENCE"], 
                                className=f"text-{trust_colors.get(trust_score, 'secondary')}"),
                        html.P(confidence.get('explanation', ''), className="text-muted small")
                    ], width=12, className="mb-3"),
                    
                    dbc.Col([
                        html.Strong("Recall (Crash Detection):"),
                        html.P(f"{confidence.get('recall', 0):.1f}%", className="mb-0 text-success" if confidence.get('recall', 0) >= 65 else "mb-0")
                    ], width=3),
                    dbc.Col([
                        html.Strong("Precision (Accuracy):"),
                        html.P(f"{confidence.get('precision', 0):.1f}%", className="mb-0")
                    ], width=3),
                    dbc.Col([
                        html.Strong("F2-Score:"),
                        html.P(f"{confidence.get('f2_score', 0):.1f}%", className="mb-0")
                    ], width=3),
                    dbc.Col([
                        html.Strong("ROC-AUC:"),
                        html.P(f"{confidence.get('roc_auc', 0):.2f}", className="mb-0")
                    ], width=3),
                    
                    dbc.Col([
                        html.Hr(className="my-3"),
                        html.Small([
                            html.Strong("Validated on: "),
                            f"{confidence.get('validation_days', 0)} days of hidden test data"
                        ], className="text-muted")
                    ], width=12)
                ])
            else:
                confidence_ui = html.P("Model confidence metrics not available.", className="text-muted")
            
            return ma_fig, shap_fig, confidence_ui

    except Exception as e:
        print(f"Prediction error: {e}")

    return ma_fig, go.Figure().update_layout(get_base_layout("AI Request Failed")), html.P("Prediction failed.", className="text-danger")