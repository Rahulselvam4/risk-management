# test_email.py
"""
Test script for email service functionality.
Run this BEFORE starting the full application to verify SMTP configuration.

Usage:
    python test_email.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.email_service import test_smtp_connection, send_digest_email

def main():
    print("=" * 60)
    print("EMAIL SERVICE TEST")
    print("=" * 60)
    
    # Test 1: SMTP Connection
    print("\n[Test 1] Testing SMTP connection...")
    if test_smtp_connection():
        print("✅ SMTP connection successful!")
    else:
        print("❌ SMTP connection failed. Check your .env configuration:")
        print("   - SMTP_HOST")
        print("   - SMTP_PORT")
        print("   - SMTP_USER")
        print("   - SMTP_PASSWORD (use App Password for Gmail)")
        return
    
    # Test 2: Send Test Email
    print("\n[Test 2] Sending test digest email...")
    
    # IMPORTANT: Replace with your actual email address
    test_email = input("Enter your email address to receive test alert: ").strip()
    
    if not test_email:
        print("❌ No email provided. Test aborted.")
        return
    
    # Sample digest data
    test_digest = {
        "user_email": test_email,
        "scan_date": "March 15, 2024 at 5:00 PM IST",
        "total_assets": 5,
        "critical": [
            {
                "ticker": "RELIANCE.NS",
                "risk": 68,
                "recommendation": "SELL",
                "driver": "High RSI (78) - Overbought",
                "threshold": 1.5
            }
        ],
        "medium": [
            {
                "ticker": "TATAMOTORS.NS",
                "risk": 54,
                "recommendation": "SELL",
                "driver": "Negative Momentum (-3.2%)",
                "threshold": 2.0
            }
        ],
        "safe": [
            {"ticker": "TCS.NS", "risk": 23},
            {"ticker": "INFY.NS", "risk": 31},
            {"ticker": "HDFCBANK.NS", "risk": 42}
        ]
    }
    
    if send_digest_email(test_email, test_digest):
        print(f"✅ Test email sent successfully to {test_email}")
        print("\nCheck your inbox (and spam folder) for the alert email.")
    else:
        print("❌ Failed to send test email. Check logs above for details.")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
