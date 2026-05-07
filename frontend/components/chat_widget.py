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
            style={
                "position": "fixed",
                "bottom": "30px",
                "right": "30px",
                "width": "60px",
                "height": "60px",
                "zIndex": "1000",
                "border": "none",
                "backgroundColor": "#388087",
                "borderRadius": "50%"
            },
            className="shadow-lg"
        ),
        
        # Chat Modal
        dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle([
                    html.I(className="bi bi-robot me-2", style={"color": "#388087"}),
                    "Portfolio Assistant",
                    html.Small(" - AI-Powered Risk Analysis", 
                             style={"color": "#000000", "fontSize": "0.8rem", "marginLeft": "8px"})
                ], style={"color": "#2c3e50"})
            ], style={"borderBottom": "2px solid #C2EDCE", "backgroundColor": "#fafafa"}),
            dbc.ModalBody([
                # Chat History Container
                html.Div(
                    id="chat-history",
                    style={
                        "height": "450px",
                        "overflowY": "auto",
                        "padding": "20px",
                        "backgroundColor": "#fafafa",
                        "borderRadius": "12px",
                        "marginBottom": "15px",
                        "border": "1px solid #e9ecef"
                    },
                    children=[
                        create_bot_message("Hello! I'm your portfolio assistant. I can help you with:\n\n• Understanding your portfolio composition\n• Explaining risk metrics and analysis\n• Suggesting portfolio improvements\n• Answering questions about your investments\n\nWhat would you like to know about your portfolio?")
                    ]
                ),
                
                # Loading Indicator
                html.Div([
                    dbc.Spinner(
                        html.Div(id="chat-loading"),
                        size="sm",
                        color="primary",
                        type="border"
                    ),
                    html.Div(id="typing-indicator", style={"display": "none"})
                ], style={"textAlign": "center", "marginBottom": "10px"}),
                
                # Input Area
                html.Div([
                    dbc.InputGroup([
                        dbc.Input(
                            id="chat-input",
                            placeholder="Ask about your portfolio, risk metrics, or investment strategy...",
                            type="text",
                            style={
                                "borderRadius": "25px 0 0 25px",
                                "border": "2px solid #C2EDCE",
                                "fontSize": "0.95rem"
                            }
                        ),
                        dbc.Button(
                            html.I(className="bi bi-send-fill"),
                            id="send-chat-btn",
                            style={
                                "borderRadius": "0 25px 25px 0",
                                "border": "2px solid #388087",
                                "backgroundColor": "#388087",
                                "paddingLeft": "15px",
                                "paddingRight": "15px"
                            }
                        )
                    ], className="mb-0")
                ], style={"marginTop": "10px"})
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
    """Creates an enhanced user message bubble."""
    return html.Div([
        html.Div([
            html.Div([
                html.I(className="bi bi-person-fill me-2", style={"fontSize": "1rem"}),
                "You"
            ], style={"fontSize": "0.85rem", "marginBottom": "4px", "color": "rgba(255,255,255,0.8)"}),
            html.Div(text, style={"lineHeight": "1.4"})
        ],
        style={
            "backgroundColor": "#388087",
            "color": "white",
            "padding": "12px 16px",
            "borderRadius": "12px 12px 4px 12px",
            "maxWidth": "75%",
            "marginLeft": "auto",
            "marginBottom": "15px",
            "wordWrap": "break-word",
            "boxShadow": "0 2px 4px rgba(56,128,135,0.3)"
        },
        className="user-message")
    ], style={"textAlign": "right"})


def create_typing_indicator():
    """Creates a typing indicator for when AI is processing."""
    return html.Div([
        html.Div([
            html.I(className="bi bi-robot me-2", style={"fontSize": "1.2rem", "color": "#388087"}),
            html.Strong("Portfolio Assistant", style={"color": "#388087"})
        ], style={"marginBottom": "8px"}),
        html.Div([
            html.Span("AI is analyzing", style={"marginRight": "8px"}),
            html.Span(".", className="typing-dot", style={"animation": "blink 1.4s infinite"}),
            html.Span(".", className="typing-dot", style={"animation": "blink 1.4s infinite 0.2s"}),
            html.Span(".", className="typing-dot", style={"animation": "blink 1.4s infinite 0.4s"})
        ], style={"color": "#6c757d", "fontStyle": "italic"})
    ], style={
        "backgroundColor": "#f8f9fa",
        "border": "1px solid #e9ecef",
        "borderLeft": "4px solid #388087",
        "padding": "15px",
        "borderRadius": "8px",
        "maxWidth": "85%",
        "marginRight": "auto",
        "marginBottom": "15px",
        "textAlign": "left"
    })


def create_bot_message(text):
    """Creates an enhanced bot message with structured formatting."""
    # Parse and format the response
    formatted_content = _format_ai_response(text)
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className="bi bi-robot me-2", style={"fontSize": "1.2rem", "color": "#388087"}),
                html.Strong("Portfolio Assistant", style={"color": "#388087"})
            ], style={"marginBottom": "8px"}),
            formatted_content
        ],
        style={
            "backgroundColor": "#ffffff",
            "border": "1px solid #C2EDCE",
            "borderLeft": "4px solid #388087",
            "color": "#212529",
            "padding": "15px",
            "borderRadius": "8px",
            "maxWidth": "85%",
            "marginRight": "auto",
            "marginBottom": "15px",
            "boxShadow": "0 2px 4px rgba(56,128,135,0.1)"
        },
        className="bot-message")
    ], style={"textAlign": "left"})


def _format_ai_response(text):
    """Format AI response with better structure and readability."""
    if not text:
        return html.Div("No response available.")
    
    # Split text into sections based on common patterns
    sections = []
    lines = text.split('\n')
    current_section = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_section:
                sections.append(current_section)
                current_section = []
            continue
        
        # Check if line is a header (contains keywords like "PORTFOLIO", "ANALYSIS", etc.)
        if any(keyword in line.upper() for keyword in ['PORTFOLIO', 'ANALYSIS', 'RECOMMENDATION', 'SUMMARY', 'DETAILS']):
            if current_section:
                sections.append(current_section)
                current_section = []
            current_section.append(('header', line))
        # Check if line starts with bullet point or dash
        elif line.startswith(('-', '•', '*')) or line.startswith(tuple('123456789')):
            current_section.append(('bullet', line))
        # Check if line contains currency or percentage (likely metrics)
        elif '₹' in line or '%' in line or any(word in line.lower() for word in ['ratio', 'beta', 'price', 'risk']):
            current_section.append(('metric', line))
        else:
            current_section.append(('text', line))
    
    if current_section:
        sections.append(current_section)
    
    # If no clear structure found, treat as simple text with better formatting
    if len(sections) == 1 and all(item[0] == 'text' for item in sections[0]):
        return _format_simple_text(text)
    
    # Create formatted sections
    formatted_sections = []
    for section in sections:
        section_content = []
        
        for item_type, content in section:
            if item_type == 'header':
                section_content.append(
                    html.H6(content, style={
                        "color": "#388087", 
                        "marginBottom": "8px", 
                        "fontWeight": "600",
                        "borderBottom": "1px solid #C2EDCE",
                        "paddingBottom": "4px"
                    })
                )
            elif item_type == 'bullet':
                section_content.append(
                    html.Li(content.lstrip('-•* '), style={
                        "marginBottom": "4px",
                        "listStyleType": "disc",
                        "marginLeft": "20px"
                    })
                )
            elif item_type == 'metric':
                section_content.append(
                    html.Div(content, style={
                        "backgroundColor": "#f8f9fa",
                        "padding": "6px 10px",
                        "borderRadius": "4px",
                        "marginBottom": "6px",
                        "fontFamily": "monospace",
                        "fontSize": "0.9rem",
                        "border": "1px solid #e9ecef"
                    })
                )
            else:
                section_content.append(
                    html.P(content, style={
                        "marginBottom": "8px",
                        "lineHeight": "1.5"
                    })
                )
        
        if section_content:
            formatted_sections.append(
                html.Div(section_content, style={"marginBottom": "12px"})
            )
    
    return html.Div(formatted_sections)


def _format_simple_text(text):
    """Format simple text with better readability."""
    # Split into paragraphs and format
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if len(paragraphs) <= 1:
        # Single paragraph - check for sentences
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        if len(sentences) > 1:
            return html.Div([
                html.P(sentence, style={
                    "marginBottom": "6px",
                    "lineHeight": "1.5"
                }) for sentence in sentences
            ])
        else:
            return html.P(text, style={"lineHeight": "1.5", "marginBottom": "0"})
    
    return html.Div([
        html.P(para, style={
            "marginBottom": "10px",
            "lineHeight": "1.5"
        }) for para in paragraphs
    ])


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
    """Handle sending and receiving chat messages with enhanced UI."""
    if not message or not message.strip():
        return current_history, "", conversation_history, ""
    
    user_id = session.get("user_id") if session else None
    if not user_id:
        error_msg = create_bot_message("Please log in to use the chat assistant.")
        return current_history + [error_msg], "", conversation_history, ""
    
    # Add user message to display
    user_bubble = create_user_message(message)
    updated_history = current_history + [user_bubble]
    
    # Add typing indicator
    typing_indicator = create_typing_indicator()
    updated_history_with_typing = updated_history + [typing_indicator]
    
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
            
            # Add bot message to display (remove typing indicator)
            bot_bubble = create_bot_message(bot_response)
            final_history = updated_history + [bot_bubble]
        else:
            error_bubble = create_bot_message("Sorry, I encountered an error. Please try again later.")
            final_history = updated_history + [error_bubble]
    
    except requests.exceptions.Timeout:
        error_bubble = create_bot_message("Request timed out. Please try a shorter question or try again.")
        final_history = updated_history + [error_bubble]
    except Exception as e:
        error_bubble = create_bot_message("An error occurred. Please check your connection and try again.")
        final_history = updated_history + [error_bubble]
    
    return final_history, "", conversation_history, ""
