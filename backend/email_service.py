# backend/email_service.py
import smtplib
import os
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

# Initialize logging
logger = logging.getLogger("EmailService")
load_dotenv()

def send_risk_alert(user_email: str, portfolio_alerts: list) -> bool:
    """
    Sends an HTML-formatted, branded email alert containing ML risk breakdowns.
    """
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    # Graceful defaults for Gmail if not specified in .env
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        logger.warning("Invalid SMTP_PORT in .env. Defaulting to 587.")
        smtp_port = 587
    
    if not sender_email or not sender_password:
        logger.error("CRITICAL: Email credentials (SENDER_EMAIL / SENDER_PASSWORD) missing in .env file.")
        return False

    msg = EmailMessage()
    msg['Subject'] = "⚠️ HIGH RISK ALERT: Portfolio Action Required"
    msg['From'] = f"Enterprise Risk Platform <{sender_email}>"
    msg['To'] = user_email

    # --- HTML EMAIL GENERATION (SQUILLA FUND THEME) ---
    html_content = """
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F6F6F2; padding: 20px; color: #2c3e50; margin: 0;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); max-width: 600px; margin: 0 auto;">
                <h2 style="color: #388087; border-bottom: 2px solid #BADFE7; padding-bottom: 10px; margin-top: 0;">System Risk Diagnostics</h2>
                <p style="font-size: 16px; line-height: 1.5;">Our automated Machine Learning pipelines have flagged the following assets in your portfolio as <strong>High Risk</strong> for the upcoming trading session:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 25px; margin-bottom: 25px;">
                    <thead>
                        <tr style="background-color: #6FB3B8; color: #ffffff; text-align: left;">
                            <th style="padding: 12px; border-radius: 6px 0 0 0;">Asset</th>
                            <th style="padding: 12px;">Crash Probability</th>
                            <th style="padding: 12px; border-radius: 0 6px 0 0;">Primary AI Driver</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Dynamically inject the ML alerts into the HTML table
    for alert in portfolio_alerts:
        # Fallbacks in case the ML model outputs missing keys
        ticker = alert.get('ticker', 'UNKNOWN')
        prob = alert.get('risk_probability', 'N/A')
        driver = alert.get('top_risk_driver', 'Complex Interaction')
        
        html_content += f"""
                        <tr style="border-bottom: 1px solid #BADFE7;">
                            <td style="padding: 12px; font-weight: bold; color: #388087;">{ticker}</td>
                            <td style="padding: 12px; color: #E63946; font-weight: bold;">{prob}%</td>
                            <td style="padding: 12px; color: #4A4A4A;">{driver}</td>
                        </tr>
        """
        
    html_content += """
                    </tbody>
                </table>
                <p style="font-size: 14px; color: #6FB3B8; border-top: 1px solid #BADFE7; padding-top: 15px;">
                    Please log in to your Enterprise Risk Dashboard to view the full SHAP waterfall analysis and assess your portfolio drawdown impact.
                </p>
            </div>
        </body>
    </html>
    """
    
    msg.set_content("Please enable HTML in your email client to view this security alert.")
    msg.add_alternative(html_content, subtype='html')

    # --- SMTP TRANSMISSION ---
    try:
        # 10 second timeout prevents the worker from freezing if network drops
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        logger.info(f"Alert email successfully dispatched to {user_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Auth Error: The username or password in .env is incorrect, or an App Password is required.")
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {e}")
        return False