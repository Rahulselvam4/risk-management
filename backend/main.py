# backend/main.py
import logging
import re
from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.ml_model import RiskPredictor, MultiThresholdPredictor
from backend.portfolio_engine import PortfolioCalculator
from backend.auth import create_access_token, get_password_hash, verify_password
from backend.kafka_producer import trigger_kafka_pipeline
from backend.alert_worker import start_alert_scheduler
from backend.otp_service import create_otp, verify_otp, cleanup_expired_otps

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FastAPI-Main")
logger.setLevel(logging.INFO)

app = FastAPI(title="Enterprise Risk Platform API", version="2.0.0")

# --- STARTUP EVENT: Initialize Alert Scheduler ---
@app.on_event("startup")
def startup_event():
    """Start background services on application startup."""
    logger.info("Starting background services...")
    start_alert_scheduler()
    cleanup_expired_otps()  # Clean up old OTPs on startup
    logger.info("Alert scheduler initialized successfully")

def ensure_risk_column(conn):
    """Ensure the portfolios table has a risk_threshold column (adds it if missing)."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'portfolios' AND COLUMN_NAME = 'risk_threshold'")
        exists = cur.fetchone()[0]
        if not exists:
            try:
                cur.execute("ALTER TABLE portfolios ADD COLUMN risk_threshold DECIMAL(5,2) DEFAULT 1.5")
                conn.commit()
                logger.info("Added missing column 'risk_threshold' to portfolios table.")
            except Exception as e:
                logger.error(f"Failed to add risk_threshold column: {e}")
        cur.close()
    except Exception as e:
        logger.error(f"ensure_risk_column failed: {e}")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA VALIDATION MODELS ---
class PortfolioItem(BaseModel):
    ticker: str
    weight: float
    risk_threshold: float = 1.5  

class RebalanceRequest(BaseModel):
    assets: List[PortfolioItem]
    total_capital: float = 100000.0  # NEW: Expect total_capital from the UI

class StandardLoginItem(BaseModel):
    email: str
    password: str

class AlertPreferences(BaseModel):
    enabled: bool

class OTPRequest(BaseModel):
    email: str
    purpose: str  # 'registration' or 'password_reset'

class OTPVerify(BaseModel):
    email: str
    otp_code: str
    purpose: str

class RegisterWithOTP(BaseModel):
    email: str
    password: str
    otp_code: str

class ResetPassword(BaseModel):
    email: str
    otp_code: str
    new_password: str


# --- 1. AUTHENTICATION ENDPOINTS ---

@app.post("/auth/send-otp", tags=["Authentication"])
def send_otp(item: OTPRequest):
    """Send OTP to email for registration or password reset."""
    result = create_otp(item.email, item.purpose)
    
    if result["success"]:
        return {"message": result["message"]}
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.post("/auth/verify-otp", tags=["Authentication"])
def verify_otp_endpoint(item: OTPVerify):
    """Verify OTP code."""
    result = verify_otp(item.email, item.otp_code, item.purpose)
    
    if result["success"]:
        return {"message": result["message"], "verified": True}
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.post("/auth/register", tags=["Authentication"])
def register_user(item: RegisterWithOTP):
    """Register user with OTP verification."""
    # First verify OTP
    otp_result = verify_otp(item.email, item.otp_code, "registration")
    
    if not otp_result["success"]:
        raise HTTPException(status_code=400, detail=otp_result["message"])
    
    conn = get_db_connection()
    if not conn: 
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (item.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
            
        hashed_pwd = get_password_hash(item.password)
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)", 
            (item.email, hashed_pwd)
        )
        conn.commit()
        
        logger.info(f"User registered successfully: {item.email}")
        return {"message": "User successfully registered"}
        
    except Exception as e:
        logger.error(f"Registration Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")
    finally:
        cursor.close()
        conn.close()

@app.post("/auth/reset-password", tags=["Authentication"])
def reset_password(item: ResetPassword):
    """Reset password with OTP verification."""
    # First verify OTP
    otp_result = verify_otp(item.email, item.otp_code, "password_reset")
    
    if not otp_result["success"]:
        raise HTTPException(status_code=400, detail=otp_result["message"])
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (item.email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        hashed_pwd = get_password_hash(item.new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (hashed_pwd, item.email)
        )
        conn.commit()
        
        logger.info(f"Password reset successfully for: {item.email}")
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cursor.close()
        conn.close()

@app.post("/auth/login/standard", tags=["Authentication"])
def login_standard(item: StandardLoginItem):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, password_hash FROM users WHERE email = %s", (item.email,))
        user = cursor.fetchone()
        
        if not user or not user['password_hash'] or not verify_password(item.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        cursor.execute("SELECT COUNT(*) as count FROM portfolios WHERE user_id = %s", (user['id'],))
        is_new_user = cursor.fetchone()['count'] == 0
        
        token = create_access_token(data={"sub": item.email, "user_id": user['id']})
        return {"access_token": token, "token_type": "bearer", "user_id": user['id'], "is_new_user": is_new_user}
    finally:
        cursor.close()
        conn.close()
 


# --- 2. PORTFOLIO CRUD OPERATIONS ---

@app.get("/portfolio/{user_id}", tags=["Portfolio Management"])
def get_user_portfolio(user_id: int):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    ensure_risk_column(conn)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Fetch the user's saved capital so Rebalance UI can pre-fill it
        cursor.execute("SELECT total_capital FROM users WHERE id = %s", (user_id,))
        user_row = cursor.fetchone()
        total_capital = user_row['total_capital'] if user_row and 'total_capital' in user_row and user_row['total_capital'] is not None else 100000.0

        cursor.execute("SELECT ticker, weight, risk_threshold FROM portfolios WHERE user_id = %s", (user_id,))
        portfolio = cursor.fetchall()
        
        try:
            for row in portfolio:
                if 'risk_threshold' not in row or row['risk_threshold'] is None:
                    cursor.execute("SELECT risk_threshold FROM portfolios WHERE user_id = %s AND ticker = %s", (user_id, row['ticker']))
                    thr = cursor.fetchone()
                    if thr and 'risk_threshold' in thr:
                        row['risk_threshold'] = thr['risk_threshold']
        except Exception:
            pass
            
        # Return both the assets AND the user's capital
        return {"user_id": user_id, "assets": portfolio, "total_capital": total_capital}
    finally:
        cursor.close()
        conn.close()

@app.post("/portfolio/{user_id}", tags=["Portfolio Management"])
def add_or_update_asset(user_id: int, item: PortfolioItem, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    ensure_risk_column(conn)
    
    sql = """
        INSERT INTO portfolios (user_id, ticker, weight, risk_threshold) 
        VALUES (%s, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE weight = %s, risk_threshold = %s
    """
    try:
        ticker_upper = item.ticker.upper()
        cursor.execute(sql, (user_id, ticker_upper, item.weight, item.risk_threshold, item.weight, item.risk_threshold))
        conn.commit()
        background_tasks.add_task(trigger_kafka_pipeline, ticker_upper)
        return {"message": f"Successfully saved {ticker_upper}. Data ingestion started."}
    except Exception as e:
        logger.error(f"Error saving asset: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while saving portfolio item.")
    finally:
        cursor.close()
        conn.close()

@app.put("/portfolio/{user_id}/rebalance", tags=["Portfolio Management"])
def rebalance_portfolio(user_id: int, request: RebalanceRequest, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    ensure_risk_column(conn)
    
    total_weight = sum(item.weight for item in request.assets)
    if not (0.99 <= total_weight <= 1.01): 
        raise HTTPException(status_code=400, detail="Total weights must sum to 1.0 (100%).")

    try:
        def normalize_ticker(raw: str) -> str:
            if not raw:
                return raw
            s = raw.strip().upper()
            m = re.search(r"\(([^)]+)\)", s)
            if m:
                s = m.group(1)
            if " " in s:
                s = s.split()[-1]
            return s

        for item in request.assets:
            item.ticker = normalize_ticker(item.ticker)
            if len(item.ticker) > 64:
                raise HTTPException(status_code=400, detail=f"Ticker too long: '{item.ticker}'. Use exchange ticker like 'RELIANCE.NS'. Max 64 chars.")

        # NEW: Save the user's updated total_capital to the users table
        try:
            cursor.execute("UPDATE users SET total_capital = %s WHERE id = %s", (request.total_capital, user_id))
        except Exception as e:
            logger.error(f"Could not update total_capital for user {user_id}: {e}")

        cursor.execute("DELETE FROM portfolios WHERE user_id = %s", (user_id,))
        insert_sql = "INSERT INTO portfolios (user_id, ticker, weight, risk_threshold) VALUES (%s, %s, %s, %s)"
        for item in request.assets:
            ticker_upper = item.ticker.upper()
            try:
                cursor.execute(insert_sql, (user_id, ticker_upper, item.weight, item.risk_threshold))
            except Exception as db_e:
                logger.error(f"DB insert failed for ticker {repr(ticker_upper)} (len={len(ticker_upper)}): {db_e}")
                try:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS portfolios (
                            user_id INT NOT NULL,
                            ticker VARCHAR(64) NOT NULL,
                            risk_threshold DECIMAL(5,2) DEFAULT 1.5,
                            PRIMARY KEY (user_id, ticker)
                        ) ENGINE=InnoDB
                        """
                    )
                    cursor.execute(
                        "INSERT INTO portfolios (user_id, ticker, weight) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE weight = %s",
                        (user_id, ticker_upper, item.weight, item.weight)
                    )
                    cursor.execute(
                        "INSERT INTO portfolios (user_id, ticker, risk_threshold) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE risk_threshold = %s",
                        (user_id, ticker_upper, item.risk_threshold, item.risk_threshold)
                    )
                except Exception as fallback_e:
                    logger.error(f"Fallback upsert also failed for {ticker_upper}: {fallback_e}")
                    raise
            background_tasks.add_task(trigger_kafka_pipeline, ticker_upper)

        conn.commit()
        return {"message": "Portfolio successfully rebalanced."}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error rebalancing portfolio for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply new portfolio weights.")
    finally:
        cursor.close()
        conn.close()

@app.delete("/portfolio/{user_id}/{ticker}", tags=["Portfolio Management"])
def remove_asset(user_id: int, ticker: str):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM portfolios WHERE user_id = %s AND ticker = %s", (user_id, ticker.upper()))
        conn.commit()
        return {"message": f"Successfully removed {ticker.upper()}."}
    finally:
        cursor.close()
        conn.close()


# --- 3. MACRO PORTFOLIO DIAGNOSTICS ---

@app.get("/portfolio/{user_id}/diagnostics", tags=["Macro Analytics"])
def get_portfolio_diagnostics(user_id: int):
    portfolio_data = get_user_portfolio(user_id)
    assets = portfolio_data.get("assets", [])
    total_capital = portfolio_data.get("total_capital", 100000.0)
    
    if not assets:
        raise HTTPException(status_code=404, detail="No portfolio found for this user.")
        
    try:
        # NEW: Inject the user's specific total_capital into the math engine
        calc = PortfolioCalculator(assets, total_capital=total_capital)
        results = calc.get_portfolio_metrics()
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
            
        return results
    except Exception as e:
        logger.error(f"Diagnostics engine failure: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute portfolio macro diagnostics.")


# --- 4. MICRO RISK & ML PREDICTION ---

@app.get("/predict/{user_id}/{ticker}", tags=["Micro Analytics"])
def get_risk_forecast(user_id: int, ticker: str):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT risk_threshold FROM portfolios WHERE user_id = %s AND ticker = %s", (user_id, ticker.upper()))
        result = cursor.fetchone()

        user_threshold = None
        if result and 'risk_threshold' in result and result['risk_threshold'] is not None:
            user_threshold = result['risk_threshold']
        else:
            try:
                cursor.execute("SELECT risk_threshold FROM portfolios WHERE user_id = %s AND ticker = %s", (user_id, ticker.upper()))
                thr = cursor.fetchone()
                if thr and 'risk_threshold' in thr and thr['risk_threshold'] is not None:
                    user_threshold = thr['risk_threshold']
            except Exception:
                user_threshold = None

        if user_threshold is None:
            user_threshold = 1.5

        # Use multi-threshold ensemble for better performance
        predictor = MultiThresholdPredictor(ticker.upper(), user_threshold)
        forecast = predictor.predict()
        
        if "error" in forecast:
            raise HTTPException(status_code=400, detail=forecast["error"])
            
        return forecast
    except Exception as e:
        logger.error(f"ML Model prediction failure for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal error during AI inference.")
    finally:
        cursor.close()
        conn.close()
        
# --- 5. EMAIL ALERT PREFERENCES ---

@app.get("/user/{user_id}/alert-preferences", tags=["User Settings"])
def get_alert_preferences(user_id: int):
    """Get user's email alert preferences."""
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT email_alerts_enabled, alert_threshold, last_alert_sent FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "enabled": bool(result.get('email_alerts_enabled', False)),
            "threshold": result.get('alert_threshold', 50),
            "last_alert_sent": result.get('last_alert_sent')
        }
    finally:
        cursor.close()
        conn.close()

@app.put("/user/{user_id}/alert-preferences", tags=["User Settings"])
def update_alert_preferences(user_id: int, preferences: AlertPreferences):
    """Update user's email alert preferences."""
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET email_alerts_enabled = %s WHERE id = %s",
            (preferences.enabled, user_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        status = "enabled" if preferences.enabled else "disabled"
        logger.info(f"Email alerts {status} for user {user_id}")
        
        return {"message": f"Email alerts successfully {status}", "enabled": preferences.enabled}
    except Exception as e:
        logger.error(f"Error updating alert preferences for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert preferences")
    finally:
        cursor.close()
        conn.close()

# --- 6. SYSTEM DATA ---

@app.get("/available-tickers", tags=["System"])
def get_available_tickers():
    conn = get_db_connection()
    if not conn: return {"tickers": []}
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT ticker FROM historical_prices")
        tickers = [row[0] for row in cursor.fetchall()]
        return {"tickers": tickers}
    finally:
        cursor.close()
        conn.close()