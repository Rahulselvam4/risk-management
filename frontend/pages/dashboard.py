
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

# --- INDIAN MARKET ASSETS ---
INDIAN_ASSETS = [
    # Nifty 50 & Nifty 100 Heavyweights
    {"label": "Reliance Industries (RELIANCE.NS)",       "value": "RELIANCE.NS"},
    {"label": "Tata Consultancy Services (TCS.NS)",      "value": "TCS.NS"},
    {"label": "HDFC Bank (HDFCBANK.NS)",                 "value": "HDFCBANK.NS"},
    {"label": "Infosys (INFY.NS)",                       "value": "INFY.NS"},
    {"label": "ICICI Bank (ICICIBANK.NS)",               "value": "ICICIBANK.NS"},
    {"label": "State Bank of India (SBIN.NS)",           "value": "SBIN.NS"},
    {"label": "Bharti Airtel (BHARTIARTL.NS)",           "value": "BHARTIARTL.NS"},
    {"label": "ITC Limited (ITC.NS)",                    "value": "ITC.NS"},
    {"label": "Hindustan Unilever (HINDUNILVR.NS)",      "value": "HINDUNILVR.NS"},
    {"label": "Larsen & Toubro (LT.NS)",                 "value": "LT.NS"},
    {"label": "Bajaj Finance (BAJFINANCE.NS)",           "value": "BAJFINANCE.NS"},
    {"label": "Tata Motors (TATAMOTORS.NS)",             "value": "TATAMOTORS.NS"},
    {"label": "Mahindra & Mahindra (M&M.NS)",            "value": "M&M.NS"},
    {"label": "Asian Paints (ASIANPAINT.NS)",            "value": "ASIANPAINT.NS"},
    {"label": "Maruti Suzuki (MARUTI.NS)",               "value": "MARUTI.NS"},
    {"label": "Sun Pharmaceuticals (SUNPHARMA.NS)",      "value": "SUNPHARMA.NS"},
    {"label": "Kotak Mahindra Bank (KOTAKBANK.NS)",      "value": "KOTAKBANK.NS"},
    {"label": "Titan Company (TITAN.NS)",                "value": "TITAN.NS"},
    # Commodities
    {"label": "Gold Benchmark - Nippon India ETF (GOLDBEES.NS)",   "value": "GOLDBEES.NS"},
    {"label": "Silver Benchmark - Nippon India ETF (SILVERBEES.NS)","value": "SILVERBEES.NS"},
    # Debt / Fixed Income
    {"label": "Debt / Cash Equivalent - Liquid BeES (LIQUIDBEES.NS)", "value": "LIQUIDBEES.NS"},
    {"label": "Govt Bonds - Long Term Gilt ETF (GILTBEES.NS)",        "value": "GILTBEES.NS"},
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
                    html.Label("Select Asset to Analyze:", className="fw-bold text-muted mb-2"),
                    dcc.Dropdown(
                        id="ai-ticker-input",
                        options=INDIAN_ASSETS,
                        placeholder="Search Indian Equities & Commodities...",
                        searchable=True,
                        clearable=True,
                        className="mb-3"
                    ),
                    dbc.Button("Run Explainable AI", id="btn-run-ai",
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
    Input("session-store",             "data"),
    Input("dashboard-poll",            "n_intervals")
)
def load_macro_dashboard(session, n_intervals):
    empty_figs = (go.Figure().update_layout(get_base_layout("Waiting for data...")),
                  go.Figure().update_layout(get_base_layout("Waiting for data...")))

    if not session or not session.get('user_id'):
        return [], *empty_figs, True, None

    user_id = session['user_id']

    try:
        port_res = requests.get(f"{API_URL}/portfolio/{user_id}", timeout=5)
        assets   = port_res.json().get("assets", [])

        if not assets:
            return [], *empty_figs, False, _loading_banner()

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
                create_kpi_card("Total Historical Return", f"{data['total_return']}%"),
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

            return kpis, pie_fig, draw_fig, True, None  # data ready — stop polling

        # assets exist but diagnostics not ready yet
        return [], pie_fig, empty_figs[1], False, _loading_banner("Crunching portfolio diagnostics...")

    except Exception as e:
        print(f"Dashboard load error: {e}")

    return [], *empty_figs, False, _loading_banner()  # keep polling on error


# --- LOGIC: MICRO EXPLAINABLE AI ---
@callback(
    Output("ma-price-chart",      "figure"),
    Output("shap-waterfall-chart","figure"),
    Input("btn-run-ai",           "n_clicks"),
    State("ai-ticker-input",      "value"),
    State("session-store",        "data"), # Inject session to retrieve user_id
    prevent_initial_call=True
)
def run_micro_ai(n_clicks, ticker, session):
    if not ticker or not session or not session.get('user_id'):
        return go.Figure(), go.Figure()

    ticker = ticker.upper()
    user_id = session['user_id']

    # 1. Technical Chart — now uses High/Low for a candlestick + MA overlay
    try:
        df = yf.download(ticker, period="3mo", progress=False)

        if not df.empty:
            # Flatten MultiIndex columns if present (yfinance ≥ 0.2)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_30'] = df['Close'].rolling(window=30).mean()

            ma_fig = go.Figure()

            # Candlestick gives more price-risk context than a plain line
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

    # 2. Backend Random Forest → SHAP waterfall
    try:
        # Pings the new backend route, passing the user_id to look up the custom threshold
        res = requests.get(f"{API_URL}/predict/{user_id}/{ticker}")
        if res.status_code == 200:
            data      = res.json()
            shap_data = data.get("shap_breakdown", [])

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
            return ma_fig, shap_fig

    except Exception:
        pass

    return ma_fig, go.Figure().update_layout(get_base_layout("AI Request Failed"))