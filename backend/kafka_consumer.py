# # backend/kafka_consumer.py
# import os
# import json
# import time
# import logging
# import signal
# import sys
# import mysql.connector
# from mysql.connector import Error
# from kafka import KafkaConsumer
# from kafka.errors import NoBrokersAvailable
# from dotenv import load_dotenv

# # Initialize logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger("DataPipeline-Consumer")

# # Load environment variables
# load_dotenv()

# # Global flag for graceful shutdown
# running = True

# def signal_handler(sig, frame):
#     """Intercepts server shutdown commands to safely flush data before exiting."""
#     global running
#     logger.info("Shutdown signal received. Finishing current batch...")
#     running = False

# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)

# def get_db_connection():
#     """Establishes a secure connection to the database using environment variables."""
#     while running: 
#         try:
#             conn = mysql.connector.connect(
#                 host=os.getenv("DB_HOST", "localhost"),
#                 database=os.getenv("DB_NAME", "risk_management"),
#                 user=os.getenv("DB_USER", "root"),
#                 password=os.getenv("DB_PASSWORD")
#             )
#             if conn.is_connected():
#                 return conn
#         except Error as e:
#             logger.error(f"Database connection failed: {e}. Retrying in 5 seconds...")
#             time.sleep(5)
#     return None

# def start_consumer():
#     topic = os.getenv("KAFKA_TOPIC", "market_data_topic")
#     broker = os.getenv("KAFKA_BROKER", "localhost:29092")
    
#     logger.info("Connecting consumer to Kafka broker...")
    
#     while running: 
#         try:
#             consumer = KafkaConsumer(
#                 topic,
#                 bootstrap_servers=[broker],
#                 auto_offset_reset='latest',
#                 consumer_timeout_ms=1000, # Allows checking the 'running' flag periodically
#                 value_deserializer=lambda x: json.loads(x.decode('utf-8'))
#             )
#             logger.info("Consumer successfully connected to Kafka!")
#             break
#         except NoBrokersAvailable:
#             logger.warning("Kafka broker not available. Retrying in 5 seconds...")
#             time.sleep(5)
            
#     if not running: return

#     logger.info("Listening for market data stream to persist to MySQL...")
    
#     conn = get_db_connection()
#     if not conn: return
#     cursor = conn.cursor()

#     # Highly optimized bulk insert query
#     sql = """
#         INSERT IGNORE INTO historical_prices (ticker, date, close_price, volume)
#         VALUES (%s, %s, %s, %s)
#     """

#     # Performance Optimization: Batch Processing
#     BATCH_SIZE = 500
#     buffer = []

#     while running:
#         for message in consumer:
#             if not running: break
            
#             data = message.value
#             values = (data['ticker'], data['date'], data['close'], data['volume'])
#             buffer.append(values)
            
#             # Execute batch insert when buffer is full
#             if len(buffer) >= BATCH_SIZE:
#                 try:
#                     # Connection health check
#                     if not conn.is_connected():
#                         logger.warning("MySQL connection lost. Reconnecting...")
#                         conn = get_db_connection()
#                         cursor = conn.cursor()
                        
#                     cursor.executemany(sql, buffer)
#                     conn.commit()
#                     logger.info(f"Batched {len(buffer)} rows successfully to database.")
#                     buffer.clear()
#                 except Exception as e:
#                     logger.error(f"Bulk insert failed: {e}")
                    
#     # --- GRACEFUL SHUTDOWN PROCEDURE ---
#     # Flush any remaining rows in the buffer that didn't hit the BATCH_SIZE limit
#     if buffer and conn.is_connected():
#         try:
#             cursor.executemany(sql, buffer)
#             conn.commit()
#             logger.info(f"Flushed final {len(buffer)} rows to database before shutdown.")
#         except Exception as e:
#             logger.error(f"Failed to flush final buffer: {e}")

#     if conn and conn.is_connected():
#         cursor.close()
#         conn.close()
    
#     consumer.close()
#     logger.info("Data Consumer safely shut down.")

# if __name__ == "__main__":
#     start_consumer()


# backend/kafka_consumer.py
import os
import json
import time
import logging
import signal
import mysql.connector
from mysql.connector import Error
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataPipeline-Consumer")

load_dotenv()

running = True


def signal_handler(sig, frame):
    """Intercepts shutdown to safely flush remaining buffer before exit."""
    global running
    logger.info("Shutdown signal received. Finishing current batch...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def get_db_connection():
    """Establishes a MySQL connection with retry logic."""
    while running:
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "risk_management"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD")
            )
            if conn.is_connected():
                return conn
        except Error as e:
            logger.error(f"Database connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    return None


def start_consumer():
    topic  = os.getenv("KAFKA_TOPIC",  "market_data_topic")
    broker = os.getenv("KAFKA_BROKER", "localhost:29092")

    logger.info("Connecting consumer to Kafka broker...")

    while running:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=[broker],
                auto_offset_reset='latest',
                consumer_timeout_ms=1000,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Consumer successfully connected to Kafka!")
            break
        except NoBrokersAvailable:
            logger.warning("Kafka broker not available. Retrying in 5 seconds...")
            time.sleep(5)

    if not running:
        return

    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()

    # --- UPDATED INSERT: now persists all OHLCV columns + fundamental ratios ---
    sql = """
        INSERT IGNORE INTO historical_prices
            (ticker, date, open_price, high_price, low_price, close_price, volume,
             pe_ratio, pb_ratio, beta, week52_high, week52_low)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    BATCH_SIZE = 500
    buffer = []

    logger.info("Listening for market data stream...")

    while running:
        for message in consumer:
            if not running:
                break

            d = message.value
            values = (
                d.get('ticker'),
                d.get('date'),
                d.get('open'),
                d.get('high'),
                d.get('low'),
                d.get('close'),
                d.get('volume'),
                d.get('pe_ratio'),
                d.get('pb_ratio'),
                d.get('beta'),
                d.get('week52_high'),
                d.get('week52_low'),
            )
            buffer.append(values)

            if len(buffer) >= BATCH_SIZE:
                try:
                    if not conn.is_connected():
                        logger.warning("MySQL connection lost. Reconnecting...")
                        conn   = get_db_connection()
                        cursor = conn.cursor()

                    cursor.executemany(sql, buffer)
                    conn.commit()
                    logger.info(f"Batched {len(buffer)} rows to database.")
                    buffer.clear()
                except Exception as e:
                    logger.error(f"Bulk insert failed: {e}")

    # --- GRACEFUL SHUTDOWN: flush remaining rows ---
    if buffer and conn.is_connected():
        try:
            cursor.executemany(sql, buffer)
            conn.commit()
            logger.info(f"Flushed final {len(buffer)} rows before shutdown.")
        except Exception as e:
            logger.error(f"Failed to flush final buffer: {e}")

    if conn and conn.is_connected():
        cursor.close()
        conn.close()

    consumer.close()
    logger.info("Data Consumer safely shut down.")


if __name__ == "__main__":
    start_consumer()