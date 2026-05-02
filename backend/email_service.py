# backend/email_service.py
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmailService")


def test_smtp_connection() -> bool:
    """Test SMTP connection without sending email."""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured in .env file")
            return False
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.quit()
        
        logger.info("SMTP connection test successful")
        return True
    except Exception as e:
        logger.error(f"SMTP connection test failed: {e}")
        return False


def format_html_email(digest_data: dict) -> str:
    """Generate HTML email content from digest data."""
    
    critical = digest_data.get("critical", [])
    medium = digest_data.get("medium", [])
    safe = digest_data.get("safe", [])
    scan_date = digest_data.get("scan_date", datetime.now().strftime("%B %d, %Y at %I:%M %p IST"))
    total_assets = digest_data.get("total_assets", 0)
    dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:8050/dashboard")
    
    # Count high-risk assets
    high_risk_count = len(critical) + len(medium)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f6f6f2; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            .header {{ background-color: #388087; color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 6px; margin-bottom: 25px; }}
            .summary-item {{ display: inline-block; margin-right: 20px; }}
            .summary-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
            .summary-value {{ font-size: 20px; font-weight: bold; color: #2c3e50; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ font-size: 14px; font-weight: bold; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
            .asset-card {{ background-color: #fff; border-left: 4px solid #e63946; padding: 15px; margin-bottom: 15px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .asset-card.medium {{ border-left-color: #f4a261; }}
            .asset-ticker {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 8px; }}
            .asset-detail {{ font-size: 14px; color: #555; margin: 5px 0; }}
            .asset-detail strong {{ color: #2c3e50; }}
            .safe-assets {{ color: #2ecc71; font-size: 14px; line-height: 1.8; }}
            .cta-button {{ display: inline-block; background-color: #388087; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin-top: 20px; font-weight: bold; }}
            .footer {{ background-color: #f6f6f2; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            .footer a {{ color: #388087; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 Daily Risk Alert</h1>
                <p>{high_risk_count} High-Risk Asset{"s" if high_risk_count != 1 else ""} Detected</p>
            </div>
            
            <div class="content">
                <div class="summary">
                    <div class="summary-item">
                        <div class="summary-label">Scan Date</div>
                        <div class="summary-value">{scan_date}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Total Assets</div>
                        <div class="summary-value">{total_assets}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">High-Risk</div>
                        <div class="summary-value" style="color: #e63946;">{high_risk_count}</div>
                    </div>
                </div>
    """
    
    # Critical Alerts Section
    if critical:
        html += """
                <div class="section">
                    <div class="section-title">⚠️ Critical Alerts (Risk ≥ 65%)</div>
        """
        for asset in critical:
            html += f"""
                    <div class="asset-card">
                        <div class="asset-ticker">{asset['ticker']}</div>
                        <div class="asset-detail"><strong>Risk Probability:</strong> {asset['risk']}%</div>
                        <div class="asset-detail"><strong>Recommendation:</strong> {asset['recommendation']}</div>
                        <div class="asset-detail"><strong>Primary Driver:</strong> {asset['driver']}</div>
                        <div class="asset-detail"><strong>Your Threshold:</strong> {asset.get('threshold', 1.5)}% drop</div>
                    </div>
            """
        html += "</div>"
    
    # Medium Alerts Section
    if medium:
        html += """
                <div class="section">
                    <div class="section-title">⚠️ Medium Alerts (Risk 50-65%)</div>
        """
        for asset in medium:
            html += f"""
                    <div class="asset-card medium">
                        <div class="asset-ticker">{asset['ticker']}</div>
                        <div class="asset-detail"><strong>Risk Probability:</strong> {asset['risk']}%</div>
                        <div class="asset-detail"><strong>Recommendation:</strong> {asset['recommendation']}</div>
                        <div class="asset-detail"><strong>Primary Driver:</strong> {asset['driver']}</div>
                        <div class="asset-detail"><strong>Your Threshold:</strong> {asset.get('threshold', 1.5)}% drop</div>
                    </div>
            """
        html += "</div>"
    
    # Safe Assets Section
    if safe:
        safe_list = ", ".join([f"{s['ticker']} ({s['risk']}%)" for s in safe[:5]])
        if len(safe) > 5:
            safe_list += f" +{len(safe) - 5} more"
        
        html += f"""
                <div class="section">
                    <div class="section-title">✅ Safe Assets (Risk &lt; 50%)</div>
                    <div class="safe-assets">{safe_list}</div>
                </div>
        """
    
    html += f"""
                <div style="text-align: center;">
                    <a href="{dashboard_url}" class="cta-button">📊 View Full Analysis</a>
                </div>
            </div>
            
            <div class="footer">
                <p>This is an automated alert from your Risk Management Dashboard.</p>
                <p>To disable alerts, visit <a href="{dashboard_url.replace('/dashboard', '/profile')}">Profile Settings</a>.</p>
                <p style="margin-top: 10px; color: #999;">Do not reply to this email. Replies are not monitored.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_digest_email(user_email: str, digest_data: dict) -> bool:
    """Send digest email alert to user."""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("ALERT_FROM_EMAIL", smtp_user)
        from_name = os.getenv("ALERT_FROM_NAME", "Risk Dashboard Alerts")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 Risk Alert: {len(digest_data.get('critical', [])) + len(digest_data.get('medium', []))} Assets Require Attention"
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = user_email
        
        # Generate HTML content
        html_content = format_html_email(digest_data)
        
        # Attach HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Alert email sent successfully to {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {e}")
        return False


def send_otp_email(user_email: str, otp_code: str, purpose: str) -> bool:
    """Send OTP email for registration or password reset."""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("ALERT_FROM_EMAIL", smtp_user)
        from_name = os.getenv("ALERT_FROM_NAME", "Risk Dashboard")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        # Determine subject and content based on purpose
        if purpose == "registration":
            subject = "Verify Your Email - Risk Dashboard"
            title = "Email Verification"
            message = "Thank you for registering! Please use the OTP below to verify your email address."
        else:  # password_reset
            subject = "Reset Your Password - Risk Dashboard"
            title = "Password Reset"
            message = "You requested to reset your password. Use the OTP below to proceed."
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f6f6f2; margin: 0; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background-color: #388087; color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 40px 30px; text-align: center; }}
                .otp-box {{ background-color: #f0f0f0; padding: 20px; border-radius: 8px; margin: 30px 0; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #388087; letter-spacing: 8px; }}
                .message {{ color: #555; font-size: 14px; line-height: 1.6; margin-bottom: 20px; }}
                .warning {{ color: #e63946; font-size: 12px; margin-top: 20px; }}
                .footer {{ background-color: #f6f6f2; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                
                <div class="content">
                    <p class="message">{message}</p>
                    
                    <div class="otp-box">
                        <div style="font-size: 12px; color: #666; margin-bottom: 10px;">YOUR OTP CODE</div>
                        <div class="otp-code">{otp_code}</div>
                    </div>
                    
                    <p class="message">This OTP is valid for 10 minutes.</p>
                    <p class="warning">⚠️ If you didn't request this, please ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p>Risk Management Dashboard</p>
                    <p style="color: #999;">Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = user_email
        
        # Attach HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"OTP email sent successfully to {user_email} for {purpose}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user_email}: {e}")
        return False
