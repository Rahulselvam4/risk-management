# backend/alert_worker.py
import time
import logging
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.database import get_db_connection
from backend.ml_model import RiskPredictor
from backend.email_service import send_risk_alert

# --- ENTERPRISE LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RiskWatchdog")

def run_daily_risk_scan():
    """Fetches all users, runs ML on their portfolios, and sends emails if needed."""
    logger.info("Starting Automated Daily Risk Scan")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Database offline. Skipping scan.")
        return
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Get all active users
        cursor.execute("SELECT id, email FROM users")
        users = cursor.fetchall()
        
        if not users:
            logger.info("No active users found. Scan complete.")
            return

        for user in users:
            # 2. Get this user's portfolio
            cursor.execute("SELECT ticker FROM portfolios WHERE user_id = %s", (user['id'],))
            portfolio = cursor.fetchall()
            
            if not portfolio:
                logger.debug(f"User {user['email']} has no assets. Skipping.")
                continue
                
            logger.info(f"Scanning portfolio for {user['email']}...")
            high_risk_alerts = []
            
            # 3. Run ML Prediction for every ticker they own
            for item in portfolio:
                ticker = item['ticker']
                try:
                    predictor = RiskPredictor(ticker)
                    forecast = predictor.train_and_predict()
                    
                    # 4. Check if the AI flagged it as dangerous
                    if forecast and forecast.get("is_high_risk_tomorrow") is True:
                        high_risk_alerts.append(forecast)
                except Exception as e:
                    logger.error(f"Error predicting {ticker} for {user['email']}: {e}")
                    
            # 5. Send Email if there are any red flags
            if high_risk_alerts:
                logger.warning(f"High risk detected for {user['email']}! Triggering SMTP email alert...")
                send_risk_alert(user['email'], high_risk_alerts)
            else:
                logger.info(f"Portfolio safe for {user['email']}.")

    except Exception as e:
        logger.error(f"Critical failure during scan: {e}")
    finally:
        # Safely close database connections even if crashes occur
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("Daily Scan Complete")

if __name__ == "__main__":
    # Ensure timezone is explicitly Indian Standard Time (IST)
    ist_tz = timezone('Asia/Kolkata')
    scheduler = BackgroundScheduler(timezone=ist_tz)
    
    # PRODUCTION ROUTINE: Run at 5:00 PM IST every weekday (Monday-Friday)
    scheduler.add_job(
        run_daily_risk_scan, 
        'cron', 
        day_of_week='mon-fri', 
        hour=17, 
        minute=0
    )
    
    scheduler.start()
    logger.info("Enterprise Background Watchdog Started. Scheduled for 17:00 IST (Mon-Fri).")
    
    try:
        # Keep the daemon alive efficiently (sleeps for 60 seconds instead of 2)
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Watchdog safely shut down.")