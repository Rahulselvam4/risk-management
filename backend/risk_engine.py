# # backend/risk_engine.py
# import logging
# import pandas as pd
# import numpy as np
# import os
# from sqlalchemy import create_engine, exc
# from dotenv import load_dotenv

# # Initialize logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger("RiskEngine")

# # Load environment variables
# load_dotenv()

# class RiskCalculator:
#     def __init__(self, ticker: str):
#         self.ticker = ticker
#         self._engine = self._create_db_engine()
#         self.df = self._fetch_data()

#     def _create_db_engine(self):
#         """Creates an SQLAlchemy engine with enterprise connection pooling."""
#         try:
#             db_user = os.getenv("DB_USER", "root")
#             db_pass = os.getenv("DB_PASSWORD", "")
#             db_host = os.getenv("DB_HOST", "localhost")
#             db_name = os.getenv("DB_NAME", "risk_management")
            
#             # Connection string format: mysql+mysqlconnector://user:password@host/dbname
#             engine_url = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}"
            
#             # pool_recycle prevents "MySQL server has gone away" timeouts
#             return create_engine(engine_url, pool_recycle=3600)
#         except Exception as e:
#             logger.error(f"Failed to initialize database engine for {self.ticker}: {e}")
#             return None

#     def _fetch_data(self) -> pd.DataFrame:
#         """Fetches historical price data using SQLAlchemy safely."""
#         if not self._engine:
#             return pd.DataFrame()
            
#         try:
#             query = """
#                 SELECT date, close_price, volume
#                 FROM historical_prices 
#                 WHERE ticker = %(ticker)s 
#                 ORDER BY date ASC
#             """
#             df = pd.read_sql(query, self._engine, params={"ticker": self.ticker})
            
#             if df.empty:
#                 logger.warning(f"No historical data found in database for ticker: {self.ticker}")
#                 return pd.DataFrame()
            
#             df['close_price'] = df['close_price'].astype(float)
#             df['daily_return'] = df['close_price'].pct_change()
            
#             return df.dropna()
#         except exc.SQLAlchemyError as e:
#             logger.error(f"Database query failed for {self.ticker}: {e}")
#             return pd.DataFrame()
#         except Exception as e:
#             logger.error(f"Unexpected error fetching data for {self.ticker}: {e}")
#             return pd.DataFrame()

#     def calculate_volatility(self) -> float:
#         """Calculates the Annualized Volatility (Standard Deviation)."""
#         if self.df.empty: return None
#         daily_volatility = self.df['daily_return'].std()
#         annualized_volatility = daily_volatility * np.sqrt(252) # 252 trading days in a year
#         return float(round(annualized_volatility, 4))

#     def calculate_var_95(self) -> float:
#         """Calculates the 95% Confidence Value at Risk."""
#         if self.df.empty: return None
#         var_95 = np.percentile(self.df['daily_return'], 5)
#         return float(round(var_95, 4))

#     def calculate_max_drawdown(self) -> float:
#         """Calculates the Maximum Historical Drawdown."""
#         if self.df.empty: return None
#         cumulative_returns = (1 + self.df['daily_return']).cumprod()
#         running_max = cumulative_returns.cummax()
#         drawdown = (cumulative_returns - running_max) / running_max
#         return float(round(drawdown.min(), 4))

#     def get_all_metrics(self) -> dict:
#         """Compiles all single-asset metrics into a JSON-ready dictionary."""
#         try:
#             if self.df.empty:
#                 return {"error": f"Insufficient data to calculate metrics for {self.ticker}."}
                
#             return {
#                 "ticker": self.ticker,
#                 "annualized_volatility": self.calculate_volatility(),
#                 "value_at_risk_95": self.calculate_var_95(),
#                 "max_drawdown": self.calculate_max_drawdown()
#             }
#         except Exception as e:
#             logger.error(f"Failed to compile metrics for {self.ticker}: {e}")
#             return {"error": "Internal math engine failure."}


# backend/risk_engine.py
import logging
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, exc
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RiskEngine")

load_dotenv()


class RiskCalculator:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self._engine = self._create_db_engine()
        self.df = self._fetch_data()

    def _create_db_engine(self):
        """Creates an SQLAlchemy engine with connection pooling."""
        try:
            db_user = os.getenv("DB_USER", "root")
            db_pass = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_name = os.getenv("DB_NAME", "risk_management")
            engine_url = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}"
            return create_engine(engine_url, pool_recycle=3600)
        except Exception as e:
            logger.error(f"Failed to initialize database engine for {self.ticker}: {e}")
            return None

    def _fetch_data(self) -> pd.DataFrame:
        """Fetches enriched OHLCV + fundamental columns from the database."""
        if not self._engine:
            return pd.DataFrame()

        try:
            query = """
                SELECT date,
                       open_price, high_price, low_price, close_price, volume,
                       pe_ratio, pb_ratio, beta,
                       week52_high, week52_low
                FROM historical_prices
                WHERE ticker = %(ticker)s
                ORDER BY date ASC
            """
            df = pd.read_sql(query, self._engine, params={"ticker": self.ticker})

            if df.empty:
                logger.warning(f"No historical data found for ticker: {self.ticker}")
                return pd.DataFrame()

            # Cast numeric columns safely
            price_cols = ['open_price', 'high_price', 'low_price', 'close_price']
            for col in price_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['volume']     = pd.to_numeric(df['volume'],     errors='coerce')
            df['pe_ratio']   = pd.to_numeric(df['pe_ratio'],   errors='coerce')
            df['pb_ratio']   = pd.to_numeric(df['pb_ratio'],   errors='coerce')
            df['beta']       = pd.to_numeric(df['beta'],       errors='coerce')
            df['week52_high']= pd.to_numeric(df['week52_high'],errors='coerce')
            df['week52_low'] = pd.to_numeric(df['week52_low'], errors='coerce')

            # Daily return is required by several metrics; computed from close only
            df['daily_return'] = df['close_price'].pct_change()

            return df.dropna(subset=['close_price', 'daily_return'])

        except exc.SQLAlchemyError as e:
            logger.error(f"Database query failed for {self.ticker}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {self.ticker}: {e}")
            return pd.DataFrame()

    # -----------------------------------------------------------------------
    # Risk metrics (unchanged logic, same API as before)
    # -----------------------------------------------------------------------

    def calculate_volatility(self) -> float:
        """Annualized volatility (std of daily returns × √252)."""
        if self.df.empty:
            return None
        return float(round(self.df['daily_return'].std() * np.sqrt(252), 4))

    def calculate_var_95(self) -> float:
        """95% Confidence Value at Risk (historical simulation)."""
        if self.df.empty:
            return None
        return float(round(np.percentile(self.df['daily_return'], 5), 4))

    def calculate_max_drawdown(self) -> float:
        """Maximum historical drawdown from peak to trough."""
        if self.df.empty:
            return None
        cumulative = (1 + self.df['daily_return']).cumprod()
        drawdown   = (cumulative - cumulative.cummax()) / cumulative.cummax()
        return float(round(drawdown.min(), 4))

    def get_all_metrics(self) -> dict:
        """Compiles all single-asset risk metrics into a JSON-ready dictionary."""
        try:
            if self.df.empty:
                return {"error": f"Insufficient data to calculate metrics for {self.ticker}."}
            return {
                "ticker":               self.ticker,
                "annualized_volatility": self.calculate_volatility(),
                "value_at_risk_95":      self.calculate_var_95(),
                "max_drawdown":          self.calculate_max_drawdown(),
            }
        except Exception as e:
            logger.error(f"Failed to compile metrics for {self.ticker}: {e}")
            return {"error": "Internal math engine failure."}