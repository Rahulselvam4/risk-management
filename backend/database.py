# backend/database.py
import os
import time
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DatabaseConnector")

# Load environment variables
load_dotenv()

def get_db_connection(retries: int = 3, delay: int = 2):
    """
    Establishes a secure connection to the MySQL database with enterprise retry logic.
    """
    attempt = 0
    while attempt < retries:
        try:
            # Fetch credentials with safe defaults to prevent NoneType crashes
            host = os.getenv("DB_HOST", "localhost")
            database = os.getenv("DB_NAME", "risk_management")
            user = os.getenv("DB_USER", "root")
            password = os.getenv("DB_PASSWORD", "")

            if not password:
                logger.warning("SECURITY WARNING: DB_PASSWORD is empty. This is highly discouraged in production.")

            connection = mysql.connector.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                connect_timeout=10  # Drop the connection attempt after 10 seconds to prevent API hanging
            )
            
            if connection.is_connected():
                return connection
                
        except Error as e:
            attempt += 1
            logger.warning(f"Database connection attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
                
    logger.error("CRITICAL FAULT: Exhausted all retries. Could not connect to the MySQL database.")
    return None