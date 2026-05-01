-- -- init.sql
-- CREATE DATABASE IF NOT EXISTS risk_dashboard_db;
-- USE risk_dashboard_db;

-- -- 1. Table for storing user identities (Supports Standard & Google OAuth)
-- CREATE TABLE IF NOT EXISTS users (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     email VARCHAR(255) UNIQUE NOT NULL,
--     google_id VARCHAR(255) UNIQUE DEFAULT NULL,
--     password_hash VARCHAR(255) DEFAULT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- -- 2. Table for storing the user's selected stocks and weights
-- CREATE TABLE IF NOT EXISTS portfolios (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL,
--     ticker VARCHAR(64) NOT NULL,
--     weight DECIMAL(5,4) DEFAULT 0.0000,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     UNIQUE KEY unique_user_ticker (user_id, ticker) -- Prevents duplicate tickers per user
-- );

-- -- 3. Table for storing the Kafka data pipeline streams
-- CREATE TABLE IF NOT EXISTS historical_prices (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     ticker VARCHAR(64) NOT NULL,
--     date DATE NOT NULL,
--     close_price DECIMAL(15, 4),
--     volume BIGINT,
--     UNIQUE KEY unique_ticker_date (ticker, date) -- Prevents duplicate rows on same day
-- );

CREATE DATABASE IF NOT EXISTS risk_management;
USE risk_management;

-- 1. Table for storing user identities (Supports Standard & Google OAuth)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE DEFAULT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users 
ADD COLUMN total_capital FLOAT DEFAULT 100000;

-- 2. Table for storing the user's selected stocks and weights
CREATE TABLE IF NOT EXISTS portfolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ticker VARCHAR(64) NOT NULL,
    weight DECIMAL(5,4) DEFAULT 0.0000,
    risk_threshold FLOAT DEFAULT 1.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ticker (user_id, ticker)
);

-- 3. ENHANCED historical_prices table
--    Truncate old data first, then recreate with richer schema
TRUNCATE TABLE IF EXISTS historical_prices;
DROP TABLE IF EXISTS historical_prices;

CREATE TABLE historical_prices (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ticker        VARCHAR(64)     NOT NULL,
    date          DATE            NOT NULL,

    -- OHLCV (was only close + volume before)
    open_price    DECIMAL(15, 4)  DEFAULT NULL,
    high_price    DECIMAL(15, 4)  DEFAULT NULL,
    low_price     DECIMAL(15, 4)  DEFAULT NULL,
    close_price   DECIMAL(15, 4)  DEFAULT NULL,
    volume        BIGINT          DEFAULT NULL,

    -- Valuation ratios (fetched once per day from yfinance .info)
    pe_ratio      DECIMAL(10, 4)  DEFAULT NULL,  -- Price / Earnings  → valuation risk
    pb_ratio      DECIMAL(10, 4)  DEFAULT NULL,  -- Price / Book      → balance-sheet stress
    beta          DECIMAL(8, 4)   DEFAULT NULL,  -- Market sensitivity → systemic risk

    -- 52-week range (fetched from .info, same value repeated daily until refreshed)
    week52_high   DECIMAL(15, 4)  DEFAULT NULL,
    week52_low    DECIMAL(15, 4)  DEFAULT NULL,

    UNIQUE KEY unique_ticker_date (ticker, date)
);