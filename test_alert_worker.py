# test_alert_worker.py
"""
Test script for alert worker functionality.
This manually triggers the alert scan for a specific user.

Usage:
    python test_alert_worker.py <user_id>
    
Example:
    python test_alert_worker.py 1
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.alert_worker import scan_user_portfolio
from backend.database import get_db_connection
from backend.email_service import send_digest_email

def test_user_scan(user_id: int):
    """Test alert scan for a specific user."""
    print("=" * 60)
    print(f"ALERT WORKER TEST - User ID: {user_id}")
    print("=" * 60)
    
    # Fetch user email
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT email, email_alerts_enabled FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        print(f"❌ User {user_id} not found in database")
        return
    
    user_email = user['email']
    alerts_enabled = user.get('email_alerts_enabled', False)
    
    print(f"\nUser Email: {user_email}")
    print(f"Alerts Enabled: {alerts_enabled}")
    
    if not alerts_enabled:
        print("\n⚠️  WARNING: Email alerts are DISABLED for this user.")
        print("   Enable alerts in Profile Settings or manually in database:")
        print(f"   UPDATE users SET email_alerts_enabled = TRUE WHERE id = {user_id};")
        
        proceed = input("\nProceed with test anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Test aborted.")
            return
    
    # Run portfolio scan
    print("\n[Step 1] Scanning user portfolio...")
    digest_data = scan_user_portfolio(user_id, user_email)
    
    if not digest_data:
        print("❌ Portfolio scan failed or returned no data")
        return
    
    print("✅ Portfolio scan complete!")
    print(f"\nResults:")
    print(f"  Total Assets: {digest_data['total_assets']}")
    print(f"  Critical Risk: {len(digest_data['critical'])} assets")
    print(f"  Medium Risk: {len(digest_data['medium'])} assets")
    print(f"  Safe: {len(digest_data['safe'])} assets")
    
    # Display high-risk assets
    if digest_data['critical']:
        print("\n🚨 CRITICAL ALERTS:")
        for asset in digest_data['critical']:
            print(f"  - {asset['ticker']}: {asset['risk']}% risk ({asset['recommendation']})")
    
    if digest_data['medium']:
        print("\n⚠️  MEDIUM ALERTS:")
        for asset in digest_data['medium']:
            print(f"  - {asset['ticker']}: {asset['risk']}% risk ({asset['recommendation']})")
    
    # Send email if high-risk assets exist
    high_risk_count = len(digest_data['critical']) + len(digest_data['medium'])
    
    if high_risk_count > 0:
        print(f"\n[Step 2] Sending alert email to {user_email}...")
        
        if send_digest_email(user_email, digest_data):
            print("✅ Alert email sent successfully!")
            print(f"\nCheck inbox: {user_email}")
        else:
            print("❌ Failed to send alert email")
    else:
        print("\n✅ No high-risk assets detected. No email sent.")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_alert_worker.py <user_id>")
        print("Example: python test_alert_worker.py 1")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        test_user_scan(user_id)
    except ValueError:
        print("❌ Invalid user_id. Must be an integer.")
        sys.exit(1)

if __name__ == "__main__":
    main()
