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
    # Telecom
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
    # Retail & Consumer
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
    # Gold ETFs
    {"label": "Gold - Nippon India ETF (GOLDBEES.NS)", "value": "GOLDBEES.NS"},
    {"label": "Gold - SBI ETF (SETFGOLD.NS)", "value": "SETFGOLD.NS"},
    {"label": "Gold - HDFC Gold ETF (HDFCGOLD.NS)", "value": "HDFCGOLD.NS"},
    # Silver ETFs
    {"label": "Silver - Nippon India ETF (SILVERBEES.NS)", "value": "SILVERBEES.NS"},
    {"label": "Silver - SBI ETF (SETFSILV.NS)", "value": "SETFSILV.NS"},
    # Debt / Fixed Income
    {"label": "Liquid Fund - Nippon BeES (LIQUIDBEES.NS)", "value": "LIQUIDBEES.NS"},
    {"label": "Govt Bonds - Nippon Gilt ETF (GILTBEES.NS)", "value": "GILTBEES.NS"},
    {"label": "Nifty 50 Index ETF (NIFTYBEES.NS)", "value": "NIFTYBEES.NS"},
]

# ─── CHART PLACEHOLDER ────────────────────────────────────────────────────────
def _chart_placeholder(icon, title, subtitle):
    """Empty-state card shown before the user clicks PREDICT."""
    return html.Div(
        [
            html.Div(icon, style={
                "fontSize": "2.8rem",
                "lineHeight": "1",
                "marginBottom": "12px",
                "opacity": "0.55"
            }),
            html.P(title, style={
                "fontWeight": "600",
                "color": COLORS["dark_gray"],
                "marginBottom": "4px",
                "fontSize": "0.95rem"
            }),
            html.P(subtitle, style={
                "color": "#aaa",
                "fontSize": "0.8rem",
                "margin": "0"
            }),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "280px",
            "padding": "2rem",
            "textAlign": "center",
            "background": "repeating-linear-gradient("
                          "45deg, transparent, transparent 8px, "
                          "rgba(0,0,0,0.015) 8px, rgba(0,0,0,0.015) 9px)",
            "borderRadius": "8px",
        }
    )


# ─── INLINE STYLES ────────────────────────────────────────────────────────────
KPI_CARD_STYLE = {
    "borderRadius": "12px",
    "border": "none",
    "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
    "padding": "20px 24px",
    "minHeight": "110px",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "center",
}

KPI_LABEL_STYLE = {
    "fontSize": "0.7rem",
    "fontWeight": "700",
    "letterSpacing": "0.08em",
    "textTransform": "uppercase",
    "color": "#888",
    "marginBottom": "6px",
}

KPI_VALUE_STYLE_GREEN = {
    "fontSize": "1.9rem",
    "fontWeight": "700",
    "color": COLORS["deep_teal"],
    "lineHeight": "1.15",
    "whiteSpace": "nowrap",
}

KPI_VALUE_STYLE_NEUTRAL = {
    "fontSize": "1.9rem",
    "fontWeight": "700",
    "color": COLORS["dark_gray"],
    "lineHeight": "1.15",
    "whiteSpace": "nowrap",
}

KPI_VALUE_STYLE_RED = {
    "fontSize": "1.9rem",
    "fontWeight": "700",
    "color": COLORS["alert_red"],
    "lineHeight": "1.15",
    "whiteSpace": "nowrap",
}

# ─── UI LAYOUT ────────────────────────────────────────────────────────────────
layout = html.Div([
    get_navbar(),
    dcc.Interval(id="dashboard-poll", interval=3000, n_intervals=0, max_intervals=20),
    dbc.Container([

        # ── Header ──────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.H2("Portfolio Command Center",
                        style={"color": COLORS["dark_gray"], "fontWeight": "700",
                               "letterSpacing": "-0.02em"}),
                html.P("Analyze systemic risk and AI-driven asset forecasts.",
                       className="text-muted mb-0")
            ], xs=12, md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-arrow-repeat me-2"), "Rebalance Portfolio"],
                    href="/rebalance",
                    color="primary",
                    className="float-end px-4 py-2 mt-2",
                    style={"borderRadius": "8px", "fontWeight": "600"}
                )
            ], xs=12, md=4)
        ], className="mb-4 mt-3"),

        # ── Loading banner ───────────────────────────────────────────────────
        html.Div(id="dashboard-loading-banner"),

        # ── KPI Cards ───────────────────────────────────────────────────────
        html.Div(id="dashboard-kpi-row", className="mb-4"),

        # ── Macro Charts ────────────────────────────────────────────────────
        html.Div(id="dashboard-charts-row", className="mb-5"),

        html.Hr(style={"borderColor": COLORS["light_gray"], "opacity": "0.5"}),

        # ── Micro Section Header ─────────────────────────────────────────────
        html.H3("Micro Asset Intelligence",
                className="mt-4 mb-1",
                style={"color": COLORS["dark_gray"], "fontWeight": "700",
                       "letterSpacing": "-0.02em"}),
        html.P("Select an asset from your portfolio to get AI-powered technical analysis and risk prediction.",
               className="text-muted mb-4", style={"fontSize": "0.9rem"}),

        # ── Asset Selector ───────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Label("Select Your Portfolio Asset:",
                                   className="fw-bold mb-2",
                                   style={"color": COLORS["dark_gray"], "fontSize": "0.85rem",
                                          "textTransform": "uppercase", "letterSpacing": "0.06em"}),
                        dcc.Dropdown(
                            id="ai-ticker-input",
                            options=[],
                            placeholder="Select from your portfolio...",
                            searchable=True,
                            clearable=True,
                            className="mb-3",
                            style={"fontSize": "0.9rem"}
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-cpu me-2"), "PREDICT"],
                            id="btn-run-ai",
                            color="dark",
                            className="w-100",
                            style={"borderRadius": "6px", "fontWeight": "700",
                                   "letterSpacing": "0.08em", "padding": "10px"}
                        )
                    ]),
                    className="border-0 shadow-sm",
                    style={"borderRadius": "12px"}
                ),
                xs=12, sm=10, md=8, lg=6,
                className="mx-auto"
            )
        ], className="mb-4"),

        # ── Technical + SHAP Charts ──────────────────────────────────────────
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        dcc.Loading(
                            html.Div(
                                id="ma-price-chart-container",
                                children=_chart_placeholder(
                                    "📈",
                                    "Price & Moving Averages",
                                    "Select an asset and click PREDICT to load the technical chart"
                                )
                            ),
                            type="circle",
                            color=COLORS["deep_teal"]
                        )
                    ),
                    className="border-0 shadow-sm h-100",
                    style={"borderRadius": "12px"}
                ),
                xs=12, md=6,
                className="mb-3 mb-md-0"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        dcc.Loading(
                            html.Div(
                                id="shap-waterfall-chart-container",
                                children=_chart_placeholder(
                                    "🧩",
                                    "AI Risk Explanation",
                                    "The SHAP waterfall chart will appear here after prediction"
                                )
                            ),
                            type="circle",
                            color=COLORS["alert_red"]
                        )
                    ),
                    className="border-0 shadow-sm h-100",
                    style={"borderRadius": "12px"}
                ),
                xs=12, md=6
            )
        ], className="mb-4"),

        # ── Explanation Box ──────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        [html.I(className="bi bi-info-circle me-2"),
                         "How to Read the AI Analysis"],
                        style={"backgroundColor": COLORS["muted_aqua"],
                               "color": "white", "fontWeight": "bold",
                               "borderRadius": "12px 12px 0 0"}
                    ),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Span("📈", style={"fontSize": "1.4rem"}),
                                    html.H6("The Technical Chart (Left)",
                                            className="d-inline ms-2 align-middle",
                                            style={"color": COLORS["dark_gray"]})
                                ], className="mb-2"),
                                html.P(
                                    "This graph shows recent price movements. Green candlesticks mean "
                                    "the price went up; red means it went down. The teal line is the "
                                    "short-term average and the red dotted line is the long-term average. "
                                    "When the short-term line falls below the long-term line, momentum is fading.",
                                    className="text-muted small mb-0"
                                )
                            ], xs=12, md=4, className="mb-3 mb-md-0"),
                            dbc.Col([
                                html.Div([
                                    html.Span("🧩", style={"fontSize": "1.4rem"}),
                                    html.H6("The AI Explanation (Right)",
                                            className="d-inline ms-2 align-middle",
                                            style={"color": COLORS["dark_gray"]})
                                ], className="mb-2"),
                                html.P(
                                    "This waterfall diagram is the AI explaining its reasoning. Each red "
                                    "block (e.g. high volatility, bad P/E ratio) increases the predicted "
                                    "crash risk. The blocks stack to show exactly how the AI reached its "
                                    "final risk percentage.",
                                    className="text-muted small mb-0"
                                )
                            ], xs=12, md=4, className="mb-3 mb-md-0"),
                            dbc.Col([
                                html.Div([
                                    html.Span("⚖️", style={"fontSize": "1.4rem"}),
                                    html.H6("The Verdict & Risk",
                                            className="d-inline ms-2 align-middle",
                                            style={"color": COLORS["dark_gray"]})
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("Risk: "),
                                    "Probability the stock drops beyond your custom threshold tomorrow. ",
                                    html.Strong("HOLD "),
                                    html.Span("(teal)", style={"color": COLORS["deep_teal"]}),
                                    " = crash unlikely. ",
                                    html.Strong("SELL "),
                                    html.Span("(red)", style={"color": COLORS["alert_red"]}),
                                    " = high probability of a severe drop — reconsider your position."
                                ], className="text-muted small mb-0")
                            ], xs=12, md=4),
                        ])
                    ])
                ],
                className="border-0 shadow-sm mb-5",
                style={"borderRadius": "12px"}
                )
            )
        ])

    ], fluid=True, style={"maxWidth": "1400px"})
], style={"backgroundColor": COLORS["off_white"], "minHeight": "100vh"})


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def _loading_banner(message="Building your portfolio dashboard, please wait..."):
    return dbc.Alert(
        [dbc.Spinner(size="sm", color="light", spinner_class_name="me-2"), message],
        color="info",
        className="d-flex align-items-center py-2",
        style={"borderRadius": "8px"}
    )


def _build_kpi_card(label, value, value_style):
    """Compact, single-line KPI card."""
    return dbc.Card(
        dbc.CardBody([
            html.P(label, style=KPI_LABEL_STYLE),
            html.P(value, style=value_style),
        ]),
        style=KPI_CARD_STYLE,
        className="h-100"
    )


# ─── CALLBACK: MACRO DASHBOARD ────────────────────────────────────────────────
@callback(
    Output("dashboard-kpi-row", "children"),
    Output("dashboard-charts-row", "children"),
    Output("dashboard-poll", "disabled"),
    Output("dashboard-loading-banner", "children"),
    Output("ai-ticker-input", "options"),
    Input("session-store", "data"),
    Input("dashboard-poll", "n_intervals")
)
def load_macro_dashboard(session, n_intervals):
    if not session or not session.get('user_id'):
        return (
            None,
            dbc.Row([
                dbc.Col(html.Div([
                    html.I(className="bi bi-graph-up",
                           style={"fontSize": "4rem", "color": "#ccc"}),
                    html.P("Please log in to view your portfolio",
                           className="text-muted mt-3")
                ], className="text-center py-5"), width=12)
            ]),
            True, None, []
        )

    user_id = session['user_id']

    try:
        port_res = requests.get(f"{API_URL}/portfolio/{user_id}", timeout=5)
        assets   = port_res.json().get("assets", [])

        if not assets:
            return (
                None,
                dbc.Row([
                    dbc.Col(html.Div([
                        dbc.Spinner(color="primary", size="lg"),
                        html.P("Loading your portfolio...", className="text-muted mt-3")
                    ], className="text-center py-5"), width=12)
                ]),
                False,
                _loading_banner("Setting up your portfolio..."),
                []
            )

        portfolio_options = [
            {"label": asset['ticker'], "value": asset['ticker']} for asset in assets
        ]

        pie_fig = px.pie(
            assets, names='ticker', values='weight', hole=0.45,
            title="Asset Allocation",
            color_discrete_sequence=[
                COLORS['deep_teal'], COLORS['muted_aqua'], COLORS['dark_gray']
            ]
        )
        pie_fig.update_layout(get_base_layout("Asset Allocation"))

        diag_res = requests.get(f"{API_URL}/portfolio/{user_id}/diagnostics", timeout=5)
        if diag_res.status_code == 200:
            data = diag_res.json()

            # ── KPI Row ──────────────────────────────────────────────────────
            kpis = dbc.Row([
                dbc.Col(_build_kpi_card(
                    "TOTAL RETURNS (3YRS)",
                    f"{data['total_return']}%",
                    KPI_VALUE_STYLE_GREEN
                ), xs=12, sm=4, className="mb-3 mb-sm-0"),
                dbc.Col(_build_kpi_card(
                    "VALUE AT RISK (95%)",
                    f"₹{data['var_95']:,.2f}",
                    KPI_VALUE_STYLE_NEUTRAL
                ), xs=12, sm=4, className="mb-3 mb-sm-0"),
                dbc.Col(_build_kpi_card(
                    "MAXIMUM DRAWDOWN",
                    f"{data['current_drawdown']}%",
                    KPI_VALUE_STYLE_RED
                ), xs=12, sm=4),
            ], className="g-3")

            draw_fig = go.Figure()
            draw_fig.add_trace(go.Scatter(
                x=data['dates'], y=data['drawdown_history'],
                fill='tozeroy', mode='lines',
                line=dict(color=COLORS['alert_red'], width=2),
                name="Drawdown"
            ))
            draw_fig.update_layout(get_base_layout("Systemic Portfolio Drawdown"))
            draw_fig.update_yaxes(tickformat=".1%")

            charts = dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(dcc.Graph(figure=pie_fig, config={'displayModeBar': False})),
                        className="border-0 shadow-sm",
                        style={"borderRadius": "12px"}
                    ),
                    xs=12, md=4, className="mb-3 mb-md-0"
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(dcc.Graph(figure=draw_fig, config={'displayModeBar': False})),
                        className="border-0 shadow-sm",
                        style={"borderRadius": "12px"}
                    ),
                    xs=12, md=8
                ),
            ], className="g-3")

            return kpis, charts, True, None, portfolio_options

        # assets exist but diagnostics not ready
        charts = dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(dcc.Graph(figure=pie_fig, config={'displayModeBar': False})),
                    className="border-0 shadow-sm",
                    style={"borderRadius": "12px"}
                ),
                xs=12, md=4, className="mb-3 mb-md-0"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(html.Div([
                        dbc.Spinner(color="primary", size="lg"),
                        html.P("Calculating portfolio metrics...", className="text-muted mt-3")
                    ], className="text-center py-5")),
                    className="border-0 shadow-sm",
                    style={"borderRadius": "12px"}
                ),
                xs=12, md=8
            ),
        ], className="g-3")

        return None, charts, False, _loading_banner("Crunching portfolio diagnostics..."), portfolio_options

    except Exception as e:
        print(f"Dashboard load error: {e}")

    return (
        None,
        dbc.Row([
            dbc.Col(html.Div([
                dbc.Spinner(color="primary", size="lg"),
                html.P("Loading portfolio data...", className="text-muted mt-3")
            ], className="text-center py-5"), width=12)
        ]),
        False,
        _loading_banner(),
        []
    )


# ─── CALLBACK: MICRO AI ────────────────────────────────────────────────────────
@callback(
    Output("ma-price-chart-container", "children"),
    Output("shap-waterfall-chart-container", "children"),
    Input("btn-run-ai", "n_clicks"),
    State("ai-ticker-input", "value"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def run_micro_ai(n_clicks, ticker, session):
    if not ticker or not session or not session.get('user_id'):
        return (
            _chart_placeholder("📈", "Price & Moving Averages",
                                "Select an asset and click PREDICT"),
            _chart_placeholder("🧩", "AI Risk Explanation",
                                "The SHAP waterfall chart will appear here")
        )

    ticker  = ticker.upper()
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
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1)
            )
        else:
            ma_fig = go.Figure().update_layout(get_base_layout("No Price Data"))

    except Exception:
        ma_fig = go.Figure().update_layout(get_base_layout("Error Fetching Chart Data"))

    # 2. Backend ML Prediction + Confidence
    try:
        res = requests.get(f"{API_URL}/predict/{user_id}/{ticker}")
        if res.status_code == 200:
            data       = res.json()
            shap_data  = data.get("shap_breakdown", [])
            confidence = data.get("model_confidence", {})
            risk_prob  = data.get('risk_probability', 0)

            features = [item['feature'] for item in shap_data]
            impacts  = [item['impact_percentage'] for item in shap_data]

            # Convert impact_percentage to percentage of total risk
            # Backend sends scaled values, we need to show them as % of total risk
            total_impact = sum(impacts)
            if total_impact > 0:
                impact_percentages = [(imp / total_impact) * risk_prob for imp in impacts]
            else:
                impact_percentages = impacts

            shap_fig = go.Figure(go.Waterfall(
                orientation="h",
                measure=["relative"] * len(features),
                y=features,
                x=impact_percentages,
                connector={"line": {"color": COLORS["light_gray"]}},
                decreasing={"marker": {"color": COLORS["muted_aqua"]}},
                increasing={"marker": {"color": COLORS["alert_red"]}},
                textposition="outside",
                text=[f"{val:.1f}%" for val in impact_percentages]
            ))

            rec_text  = data.get('recommendation', 'HOLD')
            threshold = data.get('target_threshold', 1.5)

            shap_fig.update_layout(
                get_base_layout(
                    f"AI Decision: {rec_text} ({risk_prob}% chance of a >{threshold}% drop)"
                )
            )
            shap_fig.update_xaxes(
                title="Contribution to Risk (%)",
                tickformat=".1f",
                ticksuffix="%",
                showgrid=True,
                gridcolor="#e5e5e5"
            )
            shap_fig.update_yaxes(showgrid=True, gridcolor="#e5e5e5")

            return (
                dcc.Graph(figure=ma_fig,   config={'displayModeBar': False}),
                dcc.Graph(figure=shap_fig, config={'displayModeBar': False})
            )

    except Exception as e:
        print(f"Prediction error: {e}")

    return (
        dcc.Graph(figure=ma_fig, config={'displayModeBar': False}),
        html.Div(html.P("AI prediction failed. Please try again.",
                        className="text-center text-danger py-5"))
    )