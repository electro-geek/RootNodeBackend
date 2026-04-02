import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.config import settings

def test_db_connection():
    print(f"Testing connection to DB: {settings.db_url}")
    try:
        engine = create_engine(settings.db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ DB CONNECTED SUCCESSFULLY! result: {result.fetchone()}")
    except Exception as e:
        print(f"❌ DB CONNECTION FAILED: {str(e)}")

if __name__ == "__main__":
    test_db_connection()
