# backend/portfolio_engine.py
import logging
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, exc, text
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PortfolioEngine")

# Load environment variables securely
load_dotenv()

class PortfolioCalculator:
    # NEW: Added total_capital parameter (defaulting to 100,000 for safety)
    def __init__(self, user_portfolio: list, total_capital: float = 100000.0):
        """
        Expects a list of dictionaries mapping assets to weights.
        Example: [{'ticker': 'AAPL', 'weight': 0.6}, {'ticker': 'MSFT', 'weight': 0.4}]
        """
        self.user_portfolio = user_portfolio
        self.total_capital = total_capital
        self._engine = self._create_db_engine()
        self.portfolio_df = self._build_combined_timeseries()

    def _create_db_engine(self):
        """Creates the secure SQLAlchemy engine with connection error handling."""
        try:
            db_user = os.getenv("DB_USER", "root")
            db_pass = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_name = os.getenv("DB_NAME", "risk_management")
            
            engine_url = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}"
            return create_engine(engine_url, pool_recycle=3600)
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return None

    def _build_combined_timeseries(self) -> pd.DataFrame:
        """Merges multiple stock histories into a single, weighted portfolio timeline."""
        if not self.user_portfolio or not self._engine:
            return pd.DataFrame()

        all_data = []
        
        for asset in self.user_portfolio:
            ticker = asset.get('ticker')
            weight = float(asset.get('weight', 0))
            
            if weight <= 0:
                continue

            try:
                # Try several sensible ticker formats to be resilient to exchange suffixes
                def fetch_for(tk: str) -> pd.DataFrame:
                    q = text("SELECT date, close_price FROM historical_prices WHERE ticker = :ticker ORDER BY date ASC")
                    with self._engine.connect() as conn:
                        res = conn.execute(q, {"ticker": tk})
                        rows = res.fetchall()
                        if not rows:
                            return pd.DataFrame()
                        cols = res.keys()
                        return pd.DataFrame(rows, columns=cols)

                # Primary attempt: exact ticker as provided
                df = fetch_for(ticker)

                # Fallback: strip common exchange suffix (e.g. ".NS") if present
                if df.empty and "." in ticker:
                    base = ticker.split(".")[0]
                    df = fetch_for(base)

                # Fallback: try uppercased base ticker
                if df.empty and "." in ticker:
                    base = ticker.split(".")[0].upper()
                    df = fetch_for(base)

                if df.empty:
                    logger.warning(f"No historical data found for {ticker}. Skipping in portfolio calculation.")
                    continue
                    
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df['close_price'] = df['close_price'].astype(float)
                
                # Calculate the daily return, then multiply by the user's weight allocation
                df[f'{ticker}_return'] = df['close_price'].pct_change()
                df[f'{ticker}_weighted'] = df[f'{ticker}_return'] * weight
                
                # Save only the weighted column for merging
                all_data.append(df[[f'{ticker}_weighted']])
                
            except exc.SQLAlchemyError as e:
                logger.error(f"Database error while fetching data for {ticker}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {ticker}: {e}")
                continue
            
        if not all_data:
            logger.warning("No valid asset data could be processed. Returning empty dataframe.")
            return pd.DataFrame()
            
        # Merge all individual stock timelines into one master dataframe
        # outer join is default, dropna() ensures we only calculate days where ALL assets traded
        portfolio_df = pd.concat(all_data, axis=1).dropna()
        
        # Sum the weighted returns across all columns for each day
        portfolio_df['total_daily_return'] = portfolio_df.sum(axis=1)
        
        # Calculate cumulative growth (If you started with $1, what is the multiplier today?)
        portfolio_df['portfolio_value'] = (1 + portfolio_df['total_daily_return']).cumprod()
        
        # Calculate Drawdown (How far are we currently from the all-time high?)
        running_max = portfolio_df['portfolio_value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - running_max) / running_max
        
        return portfolio_df

    def get_portfolio_metrics(self) -> dict:
        """Extracts the exact data arrays and metrics the frontend Dash requires."""
        if self.portfolio_df.empty:
            return {"error": "Could not calculate portfolio data. Ensure assets have historical data."}
            
        try:
            # 1. Base Arrays for the UI Graph
            dates = self.portfolio_df.index.strftime('%Y-%m-%d').tolist()
            
            # 2. Value at Risk (VaR) 95% Calculation
            # Finds the 5th percentile worst daily drop. 
            daily_returns = self.portfolio_df['total_daily_return'].dropna()
            var_95_percent = np.percentile(daily_returns, 5)
            
            # NEW: Multiply by the user's specific total capital instead of a hardcoded value
            var_95_currency = round(abs(var_95_percent) * self.total_capital, 2)
            
            # 3. Macro Metrics
            current_drawdown = round(self.portfolio_df['drawdown'].iloc[-1] * 100, 2)
            total_return = round((self.portfolio_df['portfolio_value'].iloc[-1] - 1) * 100, 2)
            
            return {
                "dates": dates,
                "portfolio_value_history": self.portfolio_df['portfolio_value'].round(4).tolist(),
                "drawdown_history": self.portfolio_df['drawdown'].round(4).tolist(),
                "current_drawdown": current_drawdown,
                "total_return": total_return,
                "var_95": var_95_currency # Output the real, personalized VaR!
            }
        except Exception as e:
            logger.error(f"Error extracting portfolio metrics: {e}")
            return {"error": "Math engine failed to process portfolio metrics."}