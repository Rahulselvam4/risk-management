import yfinance as yf

# Test current tickers
current_tickers = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 
    'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'HINDUNILVR.NS', 'LT.NS',
    'BAJFINANCE.NS', 'TATAMOTORS.NS', 'M&M.NS', 'ASIANPAINT.NS', 
    'MARUTI.NS', 'SUNPHARMA.NS', 'KOTAKBANK.NS', 'TITAN.NS',
    'GOLDBEES.NS', 'SILVERBEES.NS', 'LIQUIDBEES.NS', 'GILTBEES.NS'
]

print("Testing current tickers...")
for ticker in current_tickers:
    try:
        data = yf.download(ticker, period='5d', progress=False)
        status = "✓ OK" if not data.empty else "✗ EMPTY"
        print(f"{ticker:20s} {status}")
    except Exception as e:
        print(f"{ticker:20s} ✗ ERROR: {e}")
