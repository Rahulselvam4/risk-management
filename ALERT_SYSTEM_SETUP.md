# Email Alert System - Setup & Testing Guide

## 📋 Overview
This guide walks you through setting up and testing the email alert system that sends daily risk notifications to users.

---

## 🔧 Phase 1: Database Migration

### Step 1: Run the SQL Migration
```bash
# Connect to MySQL
mysql -u root -p

# Run the migration script
source database_migration_alerts.sql
```

### Step 2: Verify Changes
```sql
USE risk_management;
DESCRIBE users;

-- You should see these new columns:
-- email_alerts_enabled (BOOLEAN, DEFAULT FALSE)
-- alert_threshold (INT, DEFAULT 50)
-- last_alert_sent (DATETIME, NULL)
```

---

## 📧 Phase 2: Configure Email (Gmail)

### Step 1: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Enable "2-Step Verification"

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Click "Generate"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Update .env File
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # No spaces!
ALERT_FROM_EMAIL=noreply@riskdashboard.com
ALERT_FROM_NAME=Risk Dashboard Alerts
DASHBOARD_URL=http://localhost:8050
```

---

## 🧪 Phase 3: Testing

### Test 1: Email Service (SMTP Connection)
```bash
python test_email.py
```

**Expected Output:**
```
============================================================
EMAIL SERVICE TEST
============================================================

[Test 1] Testing SMTP connection...
✅ SMTP connection successful!

[Test 2] Sending test digest email...
Enter your email address to receive test alert: your-email@gmail.com
✅ Test email sent successfully to your-email@gmail.com

Check your inbox (and spam folder) for the alert email.
```

**If it fails:**
- Check SMTP_USER and SMTP_PASSWORD in .env
- Verify you're using App Password (not regular password)
- Check firewall/antivirus blocking port 587

---

### Test 2: Alert Worker (Portfolio Scan)

#### Step 2a: Enable Alerts for Test User
```sql
-- Enable alerts for user ID 1
UPDATE users SET email_alerts_enabled = TRUE WHERE id = 1;

-- Verify
SELECT id, email, email_alerts_enabled FROM users WHERE id = 1;
```

#### Step 2b: Run Manual Scan
```bash
python test_alert_worker.py 1
```

**Expected Output:**
```
============================================================
ALERT WORKER TEST - User ID: 1
============================================================

User Email: user@example.com
Alerts Enabled: True

[Step 1] Scanning user portfolio...
✅ Portfolio scan complete!

Results:
  Total Assets: 5
  Critical Risk: 1 assets
  Medium Risk: 2 assets
  Safe: 2 assets

🚨 CRITICAL ALERTS:
  - RELIANCE.NS: 68% risk (SELL)

⚠️  MEDIUM ALERTS:
  - TATAMOTORS.NS: 54% risk (SELL)
  - HDFCBANK.NS: 51% risk (HOLD)

[Step 2] Sending alert email to user@example.com...
✅ Alert email sent successfully!

Check inbox: user@example.com
```

---

### Test 3: Scheduler (Automated Daily Scan)

#### Step 3a: Modify Scheduler for Testing
Edit `backend/alert_worker.py` temporarily:

```python
# ORIGINAL (5 PM daily):
scheduler.add_job(
    daily_risk_scan,
    trigger=CronTrigger(
        day_of_week='mon-fri',
        hour=17,
        minute=0,
        timezone='Asia/Kolkata'
    ),
    ...
)

# TESTING (every 2 minutes):
scheduler.add_job(
    daily_risk_scan,
    trigger=CronTrigger(minute='*/2'),  # Every 2 minutes
    ...
)
```

#### Step 3b: Start FastAPI Server
```bash
cd backend
uvicorn main:app --reload
```

#### Step 3c: Monitor Logs
Watch the console output:
```
INFO:AlertWorker:✅ Alert scheduler started successfully (5 PM IST, Mon-Fri)
INFO:AlertWorker:Next scheduled run: 2024-03-15 17:00:00+05:30

# Wait 2 minutes...

INFO:AlertWorker:============================================================
INFO:AlertWorker:Daily risk scan started
INFO:AlertWorker:============================================================
INFO:AlertWorker:Found 1 users with alerts enabled
INFO:AlertWorker:Scanning portfolio for user 1 (user@example.com)
INFO:AlertWorker:User 1 scan complete: 1 critical, 2 medium, 2 safe
INFO:AlertWorker:Sending alert email to user@example.com (3 high-risk assets)
INFO:EmailService:Alert email sent successfully to user@example.com
INFO:AlertWorker:✅ Alert sent successfully to user 1
INFO:AlertWorker:============================================================
INFO:AlertWorker:Daily risk scan complete: 1 emails sent, 0 errors
INFO:AlertWorker:============================================================
```

#### Step 3d: Revert to Production Schedule
After testing, change back to:
```python
trigger=CronTrigger(
    day_of_week='mon-fri',
    hour=17,
    minute=0,
    timezone='Asia/Kolkata'
)
```

---

## 🎨 Phase 4: Test Dashboard UI

### Step 1: Start Frontend
```bash
cd frontend
python app.py
```

### Step 2: Navigate to Profile
1. Open browser: http://localhost:8050
2. Login with test user
3. Click "User" → "Profile Settings"

### Step 3: Test Toggle
1. Toggle "Daily Risk Alerts" to **ON**
2. Verify status shows "Enabled" in green
3. Toggle to **OFF**
4. Verify status shows "Disabled" in gray

### Step 4: Verify Database
```sql
SELECT id, email, email_alerts_enabled, last_alert_sent 
FROM users 
WHERE id = 1;
```

---

## 🚀 Phase 5: Production Deployment

### Checklist Before Going Live:

- [ ] Database migration completed
- [ ] SMTP credentials configured (use production email)
- [ ] Scheduler set to 5 PM IST (not test interval)
- [ ] Test scripts removed or secured
- [ ] Email deliverability tested (check spam folder)
- [ ] Logs monitored for 1 week
- [ ] User documentation updated

### Production SMTP Options:

**Option 1: Gmail (Free)**
- Limit: 500 emails/day
- Good for: Small user base (<100 users)

**Option 2: AWS SES (Recommended)**
- Limit: 62,000 emails/month free
- Better deliverability
- Requires domain verification
- Setup: https://aws.amazon.com/ses/

**Option 3: SendGrid**
- Limit: 100 emails/day free
- Easy API integration
- Good documentation

---

## 🐛 Troubleshooting

### Issue: "SMTP connection failed"
**Solution:**
- Verify SMTP_USER and SMTP_PASSWORD in .env
- Use App Password for Gmail (not regular password)
- Check port 587 is not blocked by firewall

### Issue: "No users have email alerts enabled"
**Solution:**
```sql
UPDATE users SET email_alerts_enabled = TRUE WHERE id = 1;
```

### Issue: "Prediction failed for ticker"
**Solution:**
- Ensure Kafka consumer has ingested data
- Check `historical_prices` table has data for ticker
- Verify ticker format (e.g., RELIANCE.NS not RELIANCE)

### Issue: Email goes to spam
**Solution:**
- Use production email domain (not Gmail)
- Set up SPF/DKIM records
- Use AWS SES or SendGrid for better deliverability

### Issue: Scheduler not running
**Solution:**
- Check FastAPI startup logs for errors
- Verify timezone: `Asia/Kolkata`
- Test with 1-minute interval first

---

## 📊 Monitoring

### Check Alert Status
```sql
-- Users with alerts enabled
SELECT id, email, email_alerts_enabled, last_alert_sent 
FROM users 
WHERE email_alerts_enabled = TRUE;

-- Recent alerts sent
SELECT id, email, last_alert_sent 
FROM users 
WHERE last_alert_sent IS NOT NULL 
ORDER BY last_alert_sent DESC 
LIMIT 10;
```

### View Logs
```bash
# FastAPI logs (alert worker)
tail -f logs/fastapi.log

# Check for errors
grep "ERROR" logs/fastapi.log
grep "AlertWorker" logs/fastapi.log
```

---

## 📝 Next Steps

1. ✅ Complete all testing phases
2. ✅ Enable alerts for real users
3. ✅ Monitor email deliverability for 1 week
4. ✅ Collect user feedback
5. ✅ Consider adding SMS alerts (Twilio) for critical risks
6. ✅ Add user preference for alert threshold (50%, 60%, 70%)

---

## 🆘 Support

If you encounter issues:
1. Check logs in console output
2. Verify .env configuration
3. Test SMTP connection with `test_email.py`
4. Check database migration completed
5. Review this guide's troubleshooting section

---

**System Status:** ✅ Ready for Production
**Last Updated:** March 2024
