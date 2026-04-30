# frontend/app.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Initialize the app with Dash Pages enabled (The React-style router)
# We use the LUX theme as a high-end, clean Bootstrap baseline
app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "Enterprise Risk Platform"

# Global Session Storage
# This invisible component stores the user's ID and JWT Token securely in their browser session
session_store = dcc.Store(id='session-store', storage_type='session', data={"user_id": None, "token": None})

# The Master Layout
# dash.page_container dynamically injects the correct page (login, dashboard, etc.) based on the URL
app.layout = html.Div([
    session_store,
    dash.page_container 
])

if __name__ == '__main__':
    # In production (Docker), this will be bound to 0.0.0.0
    app.run(debug=True, port=8050, host="0.0.0.0")