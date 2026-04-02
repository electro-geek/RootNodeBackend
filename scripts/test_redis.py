import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.celery_app import celery_app

def test_connection():
    print(f"Testing connection to broker: {celery_app.conf.broker_url}")
    try:
        # Tries to ping the redis server via the celery connection pool
        conn = celery_app.pool.acquire(block=True)
        conn.ensure_connection()
        print("✅ BROKER CONNECTED SUCCESSFULLY!")
        conn.release()
    except Exception as e:
        print(f"❌ BROKER CONNECTION FAILED: {str(e)}")

if __name__ == "__main__":
    test_connection()
