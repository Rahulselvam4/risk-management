-- =========================================
-- DATABASE SETUP
-- =========================================
CREATE DATABASE IF NOT EXISTS risk_management;
USE risk_management;

-- =========================================
-- 1. USERS TABLE (Auth + Alerts + Capital)
-- =========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE DEFAULT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,

    total_capital FLOAT DEFAULT 100000,

    email_alerts_enabled BOOLEAN DEFAULT FALSE COMMENT 'User opt-in for daily risk alerts',
    alert_threshold INT DEFAULT 50 COMMENT 'Minimum risk percentage to trigger alert (50-100)',
    last_alert_sent DATETIME NULL COMMENT 'Timestamp of last alert email sent',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for alert system
CREATE INDEX idx_email_alerts 
ON users(email_alerts_enabled, last_alert_sent);


-- =========================================
-- 2. PORTFOLIOS TABLE (User Holdings)
-- =========================================
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


-- =========================================
-- 3. HISTORICAL PRICES TABLE (Enhanced)
-- =========================================

-- Safe cleanup
DROP TABLE IF EXISTS historical_prices;

CREATE TABLE historical_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(64) NOT NULL,
    date DATE NOT NULL,

    -- OHLCV Data
    open_price  DECIMAL(15,4) DEFAULT NULL,
    high_price  DECIMAL(15,4) DEFAULT NULL,
    low_price   DECIMAL(15,4) DEFAULT NULL,
    close_price DECIMAL(15,4) DEFAULT NULL,
    volume      BIGINT DEFAULT NULL,

    -- Valuation Metrics
    pe_ratio DECIMAL(10,4) DEFAULT NULL,
    pb_ratio DECIMAL(10,4) DEFAULT NULL,
    beta     DECIMAL(8,4)  DEFAULT NULL,

    -- 52-Week Range
    week52_high DECIMAL(15,4) DEFAULT NULL,
    week52_low  DECIMAL(15,4) DEFAULT NULL,

    -- Constraints
    UNIQUE KEY unique_ticker_date (ticker, date)
);