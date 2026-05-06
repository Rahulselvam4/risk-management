# frontend/components/chat_widget.py
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def create_chat_widget():
    """Creates a chat widget modal component."""
    return html.Div([
        # Chat Button (Floating)
        dbc.Button(
            html.I(className="bi bi-chat-dots-fill", style={"fontSize": "1.5rem"}),
            id="open-chat-btn",
            color="primary",
            className="rounded-circle shadow-lg",
            style={
                "position": "fixed",
                "bottom": "30px",
                "right": "30px",
                "width": "60px",
                "height": "60px",
                "zIndex": "1000",
                "border": "none"
            }
        ),
        
        # Chat Modal
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle([
                    html.I(className="bi bi-robot me-2"),
                    "Portfolio Assistant"
                ]),
                close_button=True
            ),
            dbc.ModalBody([
                # Chat History Container
                html.Div(
                    id="chat-history",
                    style={
                        "height": "400px",
                        "overflowY": "auto",
                        "padding": "15px",
                        "backgroundColor": "#f8f9fa",
                        "borderRadius": "8px",
                        "marginBottom": "15px"
                    },
                    children=[
                        create_bot_message("Hello! I'm your portfolio assistant. I can help you understand your portfolio, explain risk metrics, and suggest improvements. How can I assist you today?")
                    ]
                ),
                
                # Loading Indicator
                dbc.Spinner(
                    html.Div(id="chat-loading"),
                    size="sm",
                    color="primary",
                    type="border"
                ),
                
                # Input Area
                dbc.InputGroup([
                    dbc.Input(
                        id="chat-input",
                        placeholder="Ask about your portfolio...",
                        type="text",
                        style={"borderRadius": "20px 0 0 20px"}
                    ),
                    dbc.Button(
                        html.I(className="bi bi-send-fill"),
                        id="send-chat-btn",
                        color="primary",
                        style={"borderRadius": "0 20px 20px 0"}
                    )
                ], className="mb-0")
            ]),
        ],
        id="chat-modal",
        size="lg",
        is_open=False,
        backdrop=True,
        scrollable=True
        ),
        
        # Hidden store for conversation history
        dcc.Store(id="conversation-history", data=[])
    ])


def create_user_message(text):
    """Creates a user message bubble."""
    return html.Div([
        html.Div(
            text,
            style={
                "backgroundColor": "#007bff",
                "color": "white",
                "padding": "10px 15px",
                "borderRadius": "18px 18px 0 18px",
                "maxWidth": "70%",
                "marginLeft": "auto",
                "marginBottom": "10px",
                "wordWrap": "break-word"
            }
        )
    ], style={"textAlign": "right"})


def create_bot_message(text):
    """Creates a bot message bubble."""
    return html.Div([
        html.Div([
            html.I(className="bi bi-robot me-2", style={"fontSize": "1.2rem"}),
            html.Span(text)
        ],
        style={
            "backgroundColor": "#e9ecef",
            "color": "#212529",
            "padding": "10px 15px",
            "borderRadius": "18px 18px 18px 0",
            "maxWidth": "70%",
            "marginRight": "auto",
            "marginBottom": "10px",
            "wordWrap": "break-word"
        })
    ], style={"textAlign": "left"})


# Callbacks
@callback(
    Output("chat-modal", "is_open"),
    Input("open-chat-btn", "n_clicks"),
    Input("chat-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_chat_modal(n_clicks, is_open):
    """Toggle chat modal open/close."""
    if ctx.triggered_id == "open-chat-btn":
        return not is_open
    return is_open


@callback(
    Output("chat-history", "children"),
    Output("chat-input", "value"),
    Output("conversation-history", "data"),
    Output("chat-loading", "children"),
    Input("send-chat-btn", "n_clicks"),
    Input("chat-input", "n_submit"),
    State("chat-input", "value"),
    State("chat-history", "children"),
    State("conversation-history", "data"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def handle_chat_message(n_clicks, n_submit, message, current_history, conversation_history, session):
    """Handle sending and receiving chat messages."""
    if not message or not message.strip():
        return current_history, "", conversation_history, ""
    
    user_id = session.get("user_id") if session else None
    if not user_id:
        error_msg = create_bot_message("Please log in to use the chat assistant.")
        return current_history + [error_msg], "", conversation_history, ""
    
    # Add user message to display
    user_bubble = create_user_message(message)
    current_history.append(user_bubble)
    
    # Show loading
    loading_indicator = "..."
    
    try:
        # Call backend API
        response = requests.post(
            f"{API_URL}/chat/{user_id}",
            json={
                "message": message,
                "conversation_history": conversation_history
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get("response", "I couldn't process that request.")
            
            # Update conversation history
            conversation_history.append({"role": "user", "parts": [message]})
            conversation_history.append({"role": "model", "parts": [bot_response]})
            
            # Add bot message to display
            bot_bubble = create_bot_message(bot_response)
            current_history.append(bot_bubble)
        else:
            error_bubble = create_bot_message("Sorry, I encountered an error. Please try again.")
            current_history.append(error_bubble)
    
    except requests.exceptions.Timeout:
        error_bubble = create_bot_message("Request timed out. Please try again.")
        current_history.append(error_bubble)
    except Exception as e:
        error_bubble = create_bot_message("An error occurred. Please try again later.")
        current_history.append(error_bubble)
    
    return current_history, "", conversation_history, ""
