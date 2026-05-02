# backend/otp_service.py
import random
import logging
from datetime import datetime, timedelta
from backend.database import get_db_connection
from backend.email_service import send_otp_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OTPService")


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def create_otp(email: str, purpose: str) -> dict:
    """
    Create and send OTP to user's email.
    
    Args:
        email: User's email address
        purpose: 'registration' or 'password_reset'
    
    Returns:
        dict with success status and message
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}
    
    cursor = conn.cursor()
    
    try:
        # Delete any existing OTPs for this email and purpose
        cursor.execute(
            "DELETE FROM otp WHERE email = %s AND purpose = %s",
            (email, purpose)
        )
        
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)
        
        # Store OTP in database
        cursor.execute(
            """
            INSERT INTO otp (email, otp_code, purpose, expires_at) 
            VALUES (%s, %s, %s, %s)
            """,
            (email, otp_code, purpose, expires_at)
        )
        conn.commit()
        
        # Send OTP via email
        if send_otp_email(email, otp_code, purpose):
            logger.info(f"OTP created and sent to {email} for {purpose}")
            return {
                "success": True,
                "message": "OTP sent successfully to your email"
            }
        else:
            # Rollback if email fails
            cursor.execute(
                "DELETE FROM otp WHERE email = %s AND otp_code = %s",
                (email, otp_code)
            )
            conn.commit()
            return {
                "success": False,
                "message": "Failed to send OTP email"
            }
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating OTP for {email}: {e}")
        return {
            "success": False,
            "message": "Internal server error"
        }
    finally:
        cursor.close()
        conn.close()


def verify_otp(email: str, otp_code: str, purpose: str) -> dict:
    """
    Verify OTP code for given email and purpose.
    
    Args:
        email: User's email address
        otp_code: 6-digit OTP code
        purpose: 'registration' or 'password_reset'
    
    Returns:
        dict with success status and message
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed"}
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Find valid OTP
        cursor.execute(
            """
            SELECT id, expires_at, is_used 
            FROM otp 
            WHERE email = %s AND otp_code = %s AND purpose = %s
            """,
            (email, otp_code, purpose)
        )
        
        otp_record = cursor.fetchone()
        
        if not otp_record:
            return {
                "success": False,
                "message": "Invalid OTP code"
            }
        
        # Check if already used
        if otp_record['is_used']:
            return {
                "success": False,
                "message": "OTP already used"
            }
        
        # Check if expired
        if datetime.now() > otp_record['expires_at']:
            # Delete expired OTP
            cursor.execute("DELETE FROM otp WHERE id = %s", (otp_record['id'],))
            conn.commit()
            return {
                "success": False,
                "message": "OTP expired. Please request a new one"
            }
        
        # Mark OTP as used and delete it
        cursor.execute("DELETE FROM otp WHERE id = %s", (otp_record['id'],))
        conn.commit()
        
        logger.info(f"OTP verified successfully for {email} ({purpose})")
        return {
            "success": True,
            "message": "OTP verified successfully"
        }
        
    except Exception as e:
        logger.error(f"Error verifying OTP for {email}: {e}")
        return {
            "success": False,
            "message": "Internal server error"
        }
    finally:
        cursor.close()
        conn.close()


def cleanup_expired_otps():
    """Delete all expired or used OTPs from database."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM otp WHERE expires_at < NOW() OR is_used = TRUE"
        )
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired/used OTPs")
            
    except Exception as e:
        logger.error(f"Error cleaning up OTPs: {e}")
    finally:
        cursor.close()
        conn.close()
