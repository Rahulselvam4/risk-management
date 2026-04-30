# # backend/kafka_producer.py
# import os
# import json
# import time
# import logging
# import yfinance as yf
# from kafka import KafkaProducer
# from kafka.errors import NoBrokersAvailable
# from dotenv import load_dotenv

# # Initialize logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger("DataPipeline-Producer")

# # Load environment variables
# load_dotenv()

# def get_producer():
#     """Establishes a connection to the Kafka broker with resilience."""
#     broker = os.getenv("KAFKA_BROKER", "localhost:29092")
#     logger.info(f"Connecting to Kafka broker at {broker}...")
    
#     max_retries = 5
#     for attempt in range(max_retries):
#         try:
#             producer = KafkaProducer(
#                 bootstrap_servers=[broker],
#                 value_serializer=lambda v: json.dumps(v).encode('utf-8')
#             )
#             logger.info("Successfully connected to Kafka!")
#             return producer
#         except NoBrokersAvailable:
#             logger.warning(f"Kafka broker not available. Retrying ({attempt + 1}/{max_retries})...")
#             time.sleep(5)
#         except Exception as e:
#             logger.error(f"Unexpected error connecting to Kafka: {e}. Retrying...")
#             time.sleep(5)
            
#     logger.error("CRITICAL: Failed to connect to Kafka after maximum retries.")
#     return None

# def fetch_data_with_retry(ticker: str, retries: int = 3):
#     """Fetches 3 years of historical data from Yahoo Finance with network retry logic."""
#     for attempt in range(retries):
#         try:
#             logger.info(f"Fetching data for {ticker} (Attempt {attempt + 1}/{retries})...")
#             # Fetch 3 years of data to ensure the ML model has enough training history
#             df = yf.download(ticker, period="3y", progress=False)
            
#             if df is not None and not df.empty:
#                 return df.dropna()
#         except Exception as e:
#             logger.warning(f"Network error fetching {ticker}: {e}")
#             time.sleep(3) # Wait 3 seconds before backing off and trying again
            
#     logger.error(f"Failed to fetch data for {ticker} after {retries} attempts. API may be blocking requests.")
#     return None

# def trigger_kafka_pipeline(ticker: str):
#     """
#     The main entry point for FastAPI Background Tasks.
#     Fetches data for a specific ticker and streams it into the Kafka topic.
#     """
#     logger.info(f"Background Task Started: Ingesting data for {ticker}")
    
#     producer = get_producer()
#     if not producer:
#         return # Abort if Kafka is entirely unreachable
        
#     topic = os.getenv("KAFKA_TOPIC", "market_data_topic")
#     df = fetch_data_with_retry(ticker)
    
#     if df is not None and not df.empty:
#         rows_streamed = 0
#         for index, row in df.iterrows():
#             try:
#                 # Safely extract values regardless of yfinance version (Series vs Float)
#                 close_val = row['Close']
#                 vol_val = row['Volume']
                
#                 close_price = float(close_val.iloc[0]) if hasattr(close_val, 'iloc') else float(close_val)
#                 volume = int(vol_val.iloc[0]) if hasattr(vol_val, 'iloc') else int(vol_val)

#                 payload = {
#                     "ticker": ticker,
#                     "date": index.strftime('%Y-%m-%d'),
#                     "close": close_price,
#                     "volume": volume
#                 }
                
#                 producer.send(topic, payload)
#                 rows_streamed += 1
                
#             except Exception as e:
#                 logger.error(f"Error parsing row for {ticker} on {index}: {e}")
#                 continue
                
#         # Ensure all messages are sent before closing the connection
#         producer.flush()
#         producer.close()
#         logger.info(f"Background Task Complete: {rows_streamed} days of historical data for {ticker} successfully streamed to Kafka!")
#     else:
#         logger.warning(f"No valid data returned for {ticker}. Kafka stream aborted.")

# backend/kafka_producer.py
import os
import json
import time
import logging
import yfinance as yf
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataPipeline-Producer")

# Load environment variables
load_dotenv()


def get_producer():
    """Establishes a connection to the Kafka broker with resilience."""
    broker = os.getenv("KAFKA_BROKER", "localhost:29092")
    logger.info(f"Connecting to Kafka broker at {broker}...")

    max_retries = 5
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[broker],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Successfully connected to Kafka!")
            return producer
        except NoBrokersAvailable:
            logger.warning(f"Kafka broker not available. Retrying ({attempt + 1}/{max_retries})...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error connecting to Kafka: {e}. Retrying...")
            time.sleep(5)

    logger.error("CRITICAL: Failed to connect to Kafka after maximum retries.")
    return None


def fetch_fundamentals(ticker_obj) -> dict:
    """
    Fetches slow-changing fundamental ratios once per ingestion run.
    These values (PE, PB, Beta, 52w range) are the same for the whole day
    so we fetch them once and stamp every row with them.
    Returns a dict with safe fallback None values if the API doesn't provide them.
    """
    try:
        info = ticker_obj.info
        return {
            "pe_ratio":   info.get("trailingPE"),        # trailing P/E
            "pb_ratio":   info.get("priceToBook"),        # price / book
            "beta":       info.get("beta"),               # 1-year beta vs market
            "week52_high": info.get("fiftyTwoWeekHigh"),
            "week52_low":  info.get("fiftyTwoWeekLow"),
        }
    except Exception as e:
        logger.warning(f"Could not fetch fundamentals: {e}. Proceeding with nulls.")
        return {
            "pe_ratio": None, "pb_ratio": None, "beta": None,
            "week52_high": None, "week52_low": None,
        }


def fetch_data_with_retry(ticker: str, retries: int = 3):
    """
    Fetches 3 years of OHLCV history from Yahoo Finance + fundamental ratios.
    Returns (DataFrame, fundamentals_dict) or (None, None) on failure.
    """
    for attempt in range(retries):
        try:
            logger.info(f"Fetching data for {ticker} (Attempt {attempt + 1}/{retries})...")
            ticker_obj = yf.Ticker(ticker)

            # --- 3 years of daily OHLCV ---
            df = ticker_obj.history(period="3y")

            if df is not None and not df.empty:
                df = df.dropna(subset=["Close"])   # Close is mandatory; others may be NaN

                # Fetch fundamentals once for the whole batch
                fundamentals = fetch_fundamentals(ticker_obj)
                return df, fundamentals

        except Exception as e:
            logger.warning(f"Network error fetching {ticker}: {e}")
            time.sleep(3)

    logger.error(f"Failed to fetch data for {ticker} after {retries} attempts.")
    return None, None


def trigger_kafka_pipeline(ticker: str):
    """
    Main entry point for FastAPI Background Tasks.
    Fetches enriched OHLCV + fundamental data and streams it into Kafka.
    """
    logger.info(f"Background Task Started: Ingesting data for {ticker}")

    producer = get_producer()
    if not producer:
        return

    topic = os.getenv("KAFKA_TOPIC", "market_data_topic")
    df, fundamentals = fetch_data_with_retry(ticker)

    if df is not None and not df.empty:
        rows_streamed = 0

        for index, row in df.iterrows():
            try:
                # --- Safe extraction regardless of yfinance version ---
                def safe_float(val):
                    try:
                        return float(val.iloc[0]) if hasattr(val, 'iloc') else float(val)
                    except Exception:
                        return None

                def safe_int(val):
                    try:
                        return int(val.iloc[0]) if hasattr(val, 'iloc') else int(val)
                    except Exception:
                        return None

                payload = {
                    "ticker":     ticker,
                    "date":       index.strftime('%Y-%m-%d'),

                    # Full OHLCV — Open/High/Low enable ATR and gap features in ML
                    "open":       safe_float(row.get("Open")),
                    "high":       safe_float(row.get("High")),
                    "low":        safe_float(row.get("Low")),
                    "close":      safe_float(row.get("Close")),
                    "volume":     safe_int(row.get("Volume")),

                    # Fundamental ratios — same value for every row in this batch
                    "pe_ratio":    fundamentals.get("pe_ratio"),
                    "pb_ratio":    fundamentals.get("pb_ratio"),
                    "beta":        fundamentals.get("beta"),
                    "week52_high": fundamentals.get("week52_high"),
                    "week52_low":  fundamentals.get("week52_low"),
                }

                producer.send(topic, payload)
                rows_streamed += 1

            except Exception as e:
                logger.error(f"Error parsing row for {ticker} on {index}: {e}")
                continue

        producer.flush()
        producer.close()
        logger.info(
            f"Background Task Complete: {rows_streamed} days of enriched data "
            f"for {ticker} successfully streamed to Kafka!"
        )
    else:
        logger.warning(f"No valid data returned for {ticker}. Kafka stream aborted.")