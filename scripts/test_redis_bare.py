import redis
import sys

URL = "rediss://default:gQAAAAAAASSqAAIncDJhZTdiNThiZTI4NTg0MzkyYTk2OWEwZjhjOGNhYmNhNHAyNzQ5MjI@charmed-cod-74922.upstash.io:6379"

def test_bare_redis():
    print(f"Testing bare redis connection to: {URL}")
    try:
        # Standard Upstash SSL check usually works without extra certs in modern envs
        r = redis.Redis.from_url(URL)
        ping = r.ping()
        if ping:
            print("✅ BARE REDIS PING SUCCESSFUL!")
        else:
            print("❌ BARE REDIS PING FAILED.")
    except Exception as e:
        print(f"❌ BARE REDIS CONNECTION FAILED: {str(e)}")

if __name__ == "__main__":
    test_bare_redis()
