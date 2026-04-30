-- init.sql
CREATE DATABASE IF NOT EXISTS risk_dashboard_db;
USE risk_dashboard_db;

-- 1. Table for storing user identities (Supports Standard & Google OAuth)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE DEFAULT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table for storing the user's selected stocks and weights
CREATE TABLE IF NOT EXISTS portfolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ticker VARCHAR(64) NOT NULL,
    weight DECIMAL(5,4) DEFAULT 0.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ticker (user_id, ticker) -- Prevents duplicate tickers per user
);

-- 3. Table for storing the Kafka data pipeline streams
CREATE TABLE IF NOT EXISTS historical_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    close_price DECIMAL(15, 4),
    volume BIGINT,
    UNIQUE KEY unique_ticker_date (ticker, date) -- Prevents duplicate rows on same day
);