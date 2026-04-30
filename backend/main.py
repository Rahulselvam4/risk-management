# backend/main.py
import logging
import re
from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.ml_model import RiskPredictor
from backend.portfolio_engine import PortfolioCalculator
from backend.auth import create_access_token, get_password_hash, verify_password
from backend.kafka_producer import trigger_kafka_pipeline

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FastAPI-Main")
logger.setLevel(logging.INFO)

app = FastAPI(title="Enterprise Risk Platform API", version="2.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In strict production, restrict this to your frontend's exact URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA VALIDATION MODELS ---
class PortfolioItem(BaseModel):
    ticker: str
    weight: float

class RebalanceRequest(BaseModel):
    assets: List[PortfolioItem]

class StandardLoginItem(BaseModel):
    email: str
    password: str

class GoogleLoginItem(BaseModel):
    email: str
    google_id: str


# --- 1. AUTHENTICATION ENDPOINTS ---

@app.post("/auth/register", tags=["Authentication"])
def register_user(item: StandardLoginItem):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (item.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
            
        hashed_pwd = get_password_hash(item.password)
        cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (item.email, hashed_pwd))
        conn.commit()
        return {"message": "User successfully registered"}
    except Exception as e:
        logger.error(f"Registration Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")
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

@app.post("/auth/login/google", tags=["Authentication"])
def login_google(item: GoogleLoginItem):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM users WHERE google_id = %s", (item.google_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute("INSERT INTO users (email, google_id) VALUES (%s, %s)", (item.email, item.google_id))
            conn.commit()
            user_id = cursor.lastrowid
            is_new_user = True
        else:
            user_id = user['id']
            cursor.execute("SELECT COUNT(*) as count FROM portfolios WHERE user_id = %s", (user_id,))
            is_new_user = cursor.fetchone()['count'] == 0
            
        token = create_access_token(data={"sub": item.email, "user_id": user_id})
        return {"access_token": token, "token_type": "bearer", "user_id": user_id, "is_new_user": is_new_user}
    finally:
        cursor.close()
        conn.close()

# --- 2. PORTFOLIO CRUD OPERATIONS ---

@app.get("/portfolio/{user_id}", tags=["Portfolio Management"])
def get_user_portfolio(user_id: int):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT ticker, weight FROM portfolios WHERE user_id = %s", (user_id,))
        portfolio = cursor.fetchall()
        return {"user_id": user_id, "assets": portfolio}
    finally:
        cursor.close()
        conn.close()

@app.post("/portfolio/{user_id}", tags=["Portfolio Management"])
def add_or_update_asset(user_id: int, item: PortfolioItem, background_tasks: BackgroundTasks):
    """Adds a new ticker, updates weight, and TRIGGERS KAFKA PIPELINE."""
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO portfolios (user_id, ticker, weight) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE weight = %s
    """
    try:
        ticker_upper = item.ticker.upper()
        cursor.execute(sql, (user_id, ticker_upper, item.weight, item.weight))
        conn.commit()
        
        # Fire the Kafka background task immediately to ingest data
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
    """BULK UPDATE: Updates weights for all provided assets simultaneously."""
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    
    # Validation: Ensure weights sum up correctly (allow slight float variance)
    total_weight = sum(item.weight for item in request.assets)
    if not (0.99 <= total_weight <= 1.01): 
        raise HTTPException(status_code=400, detail="Total weights must sum to 1.0 (100%).")

    try:
        # Normalize and validate tickers before any DB operation
        def normalize_ticker(raw: str) -> str:
            if not raw:
                return raw
            s = raw.strip().upper()
            # If user provided a label like "Name (TICKER.NS)", extract the parentheses content
            m = re.search(r"\(([^)]+)\)", s)
            if m:
                s = m.group(1)
            # If still contains spaces, take the last token (commonly the ticker)
            if " " in s:
                s = s.split()[-1]
            return s

        for item in request.assets:
            item.ticker = normalize_ticker(item.ticker)
            if len(item.ticker) > 64:
                raise HTTPException(status_code=400, detail=f"Ticker too long: '{item.ticker}'. Use exchange ticker like 'RELIANCE.NS'. Max 64 chars.")

        # Proceed with DB replacement

        # Log normalized tickers for debugging
        logger.info(f"Rebalance request for user {user_id} with assets: {[{'ticker': a.ticker, 'weight': a.weight} for a in request.assets]}")

        # Replace the user's portfolio atomically: remove existing entries and insert the new set.
        cursor.execute("DELETE FROM portfolios WHERE user_id = %s", (user_id,))

        insert_sql = "INSERT INTO portfolios (user_id, ticker, weight) VALUES (%s, %s, %s)"
        for item in request.assets:
            ticker_upper = item.ticker.upper()
            logger.debug(f"Inserting ticker={repr(ticker_upper)} len={len(ticker_upper)} for user {user_id}")
            try:
                cursor.execute(insert_sql, (user_id, ticker_upper, item.weight))
            except Exception as db_e:
                logger.error(f"DB insert failed for ticker {repr(ticker_upper)} (len={len(ticker_upper)}): {db_e}")
                raise
            # Trigger ingestion for each inserted ticker
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
    
    if not assets:
        raise HTTPException(status_code=404, detail="No portfolio found for this user.")
        
    try:
        calc = PortfolioCalculator(assets)
        results = calc.get_portfolio_metrics()
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
            
        return results
    except Exception as e:
        logger.error(f"Diagnostics engine failure: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute portfolio macro diagnostics.")

# --- 4. MICRO RISK & ML PREDICTION ---

@app.get("/predict/{ticker}", tags=["Micro Analytics"])
def get_risk_forecast(ticker: str):
    try:
        predictor = RiskPredictor(ticker.upper())
        forecast = predictor.train_and_predict()
        
        if "error" in forecast:
            raise HTTPException(status_code=400, detail=forecast["error"])
            
        return forecast
    except Exception as e:
        logger.error(f"ML Model prediction failure for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal error during AI inference.")

# --- 5. SYSTEM DATA ---

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