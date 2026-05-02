# backend/alert_worker.py
import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.database import get_db_connection
from backend.ml_model import MultiThresholdPredictor
from backend.email_service import send_digest_email

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AlertWorker")

scheduler = BackgroundScheduler()


def scan_user_portfolio(user_id: int, user_email: str, alert_threshold: int = 50) -> dict:
    """
    Scan a single user's portfolio and return categorized risk data.
    
    Returns:
        dict with keys: critical, medium, safe, total_assets
    """
    conn = get_db_connection()
    if not conn:
        logger.error(f"Database connection failed for user {user_id}")
        return None
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Fetch user's portfolio
        cursor.execute(
            "SELECT ticker, risk_threshold FROM portfolios WHERE user_id = %s",
            (user_id,)
        )
        portfolio = cursor.fetchall()
        
        if not portfolio:
            logger.info(f"User {user_id} has no portfolio assets")
            return None
        
        critical_assets = []
        medium_assets = []
        safe_assets = []
        
        # Run ML prediction for each asset
        for asset in portfolio:
            ticker = asset['ticker']
            user_threshold = asset.get('risk_threshold', 1.5)
            
            try:
                # Use MultiThresholdPredictor for better accuracy
                predictor = MultiThresholdPredictor(ticker, user_threshold)
                prediction = predictor.predict()
                
                if "error" in prediction:
                    logger.warning(f"Prediction failed for {ticker}: {prediction['error']}")
                    continue
                
                risk_prob = prediction['risk_probability']
                
                asset_data = {
                    'ticker': ticker,
                    'risk': risk_prob,
                    'recommendation': prediction['recommendation'],
                    'driver': prediction['top_risk_driver'],
                    'threshold': user_threshold
                }
                
                # Categorize by risk level
                if risk_prob >= 65:
                    critical_assets.append(asset_data)
                elif risk_prob >= alert_threshold:
                    medium_assets.append(asset_data)
                else:
                    safe_assets.append(asset_data)
                    
            except Exception as e:
                logger.error(f"Error predicting risk for {ticker} (user {user_id}): {e}")
                continue
        
        # Build digest data
        digest_data = {
            "user_email": user_email,
            "scan_date": datetime.now().strftime("%B %d, %Y at %I:%M %p IST"),
            "total_assets": len(portfolio),
            "critical": critical_assets,
            "medium": medium_assets,
            "safe": safe_assets
        }
        
        logger.info(
            f"User {user_id} scan complete: "
            f"{len(critical_assets)} critical, "
            f"{len(medium_assets)} medium, "
            f"{len(safe_assets)} safe"
        )
        
        return digest_data
        
    except Exception as e:
        logger.error(f"Error scanning portfolio for user {user_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def daily_risk_scan():
    """
    Main scheduled job: Scan all users with alerts enabled and send digest emails.
    Runs daily at 5 PM IST (Mon-Fri).
    """
    logger.info("=" * 60)
    logger.info("Daily risk scan started")
    logger.info("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection failed. Aborting scan.")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Fetch all users with alerts enabled
        cursor.execute(
            """
            SELECT id, email, alert_threshold 
            FROM users 
            WHERE email_alerts_enabled = TRUE 
            AND email IS NOT NULL
            """
        )
        users = cursor.fetchall()
        
        if not users:
            logger.info("No users have email alerts enabled. Scan complete.")
            return
        
        logger.info(f"Found {len(users)} users with alerts enabled")
        
        success_count = 0
        error_count = 0
        
        # Scan each user's portfolio
        for user in users:
            user_id = user['id']
            user_email = user['email']
            alert_threshold = user.get('alert_threshold', 50)
            
            try:
                logger.info(f"Scanning portfolio for user {user_id} ({user_email})")
                
                # Scan portfolio
                digest_data = scan_user_portfolio(user_id, user_email, alert_threshold)
                
                if not digest_data:
                    logger.warning(f"No digest data for user {user_id}")
                    continue
                
                # Only send email if there are high-risk assets
                high_risk_count = len(digest_data['critical']) + len(digest_data['medium'])
                
                if high_risk_count > 0:
                    logger.info(f"Sending alert email to {user_email} ({high_risk_count} high-risk assets)")
                    
                    if send_digest_email(user_email, digest_data):
                        # Update last_alert_sent timestamp
                        cursor.execute(
                            "UPDATE users SET last_alert_sent = NOW() WHERE id = %s",
                            (user_id,)
                        )
                        conn.commit()
                        success_count += 1
                        logger.info(f"✅ Alert sent successfully to user {user_id}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to send alert to user {user_id}")
                else:
                    logger.info(f"No high-risk assets for user {user_id}. Skipping email.")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing user {user_id}: {e}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"Daily risk scan complete: {success_count} emails sent, {error_count} errors")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Critical error in daily_risk_scan: {e}")
    finally:
        cursor.close()
        conn.close()


def start_alert_scheduler():
    """
    Initialize and start the background scheduler.
    Runs daily at 5:00 PM IST (Mon-Fri).
    """
    try:
        # Schedule daily scan at 5 PM IST (11:30 AM UTC)
        scheduler.add_job(
            daily_risk_scan,
            trigger=CronTrigger(
                day_of_week='mon-fri',
                hour=17,
                minute=0,
                timezone='Asia/Kolkata'
            ),
            id='daily_risk_alert',
            name='Daily Portfolio Risk Scanner',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ Alert scheduler started successfully (5 PM IST, Mon-Fri)")
        
        # Log next run time
        job = scheduler.get_job('daily_risk_alert')
        if job:
            logger.info(f"Next scheduled run: {job.next_run_time}")
        
    except Exception as e:
        logger.error(f"Failed to start alert scheduler: {e}")


def stop_alert_scheduler():
    """Stop the scheduler gracefully."""
    try:
        scheduler.shutdown()
        logger.info("Alert scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
