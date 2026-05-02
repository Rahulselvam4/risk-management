# frontend/app.py
import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "Enterprise Risk Platform"

PUBLIC_ROUTES = {"/login", "/register", "/forgot-password"}

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id='session-store', storage_type='session', data={"user_id": None, "token": None}),
    dcc.Location(id="auth-redirect", refresh=True),
    dash.page_container 
])

@callback(
    Output("auth-redirect", "pathname"),
    Input("url", "pathname"),
    Input("session-store", "data")
)
def guard(pathname, session):
    if pathname in PUBLIC_ROUTES:
        return dash.no_update
    if not session or not session.get("user_id"):
        return "/login"
    return dash.no_update

if __name__ == '__main__':
    app.run(debug=True, port=8050, host="127.0.0.1")