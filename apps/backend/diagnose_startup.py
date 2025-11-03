# Diagnostic script to identify startup hang
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

print("=" * 60)
print("BACKEND STARTUP DIAGNOSTIC")
print("=" * 60)

async def test_components():
    print("\n[1/5] Testing Redis Connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=3)
        result = await asyncio.wait_for(
            asyncio.to_thread(r.ping), 
            timeout=3.0
        )
        if result:
            print("✅ Redis: CONNECTED")
        else:
            print("❌ Redis: NO RESPONSE")
    except asyncio.TimeoutError:
        print("⚠️ Redis: TIMEOUT (server will use memory fallback)")
    except Exception as e:
        print(f"❌ Redis: ERROR - {e}")

    print("\n[2/5] Testing Cache Service...")
    try:
        from core.cache import CacheService
        cache = CacheService("redis://localhost:6379/0")
        await asyncio.wait_for(cache.connect(), timeout=3.0)
        print("✅ Cache Service: INITIALIZED")
        await cache.disconnect()
    except asyncio.TimeoutError:
        print("⚠️ Cache Service: TIMEOUT")
    except Exception as e:
        print(f"❌ Cache Service: ERROR - {e}")

    print("\n[3/5] Testing Rate Limiter...")
    try:
        from core.rate_limiting import RateLimiter
        limiter = RateLimiter()
        await asyncio.wait_for(limiter._init_redis(), timeout=3.0)
        print("✅ Rate Limiter: INITIALIZED")
    except asyncio.TimeoutError:
        print("⚠️ Rate Limiter: TIMEOUT (will use memory fallback)")
    except Exception as e:
        print(f"❌ Rate Limiter: ERROR - {e}")

    print("\n[4/5] Testing Database Connection...")
    try:
        from core.database import get_database_url
        db_url = get_database_url()
        print(f"✅ Database URL: {db_url[:30]}...")
    except Exception as e:
        print(f"❌ Database: ERROR - {e}")

    print("\n[5/5] Testing FastAPI App Creation...")
    try:
        from fastapi import FastAPI
        test_app = FastAPI()
        print("✅ FastAPI: APP CREATED")
    except Exception as e:
        print(f"❌ FastAPI: ERROR - {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    print("\nStarting diagnostics...\n")
    asyncio.run(test_components())
    print("\nIf all tests passed, the server should start successfully.")
    print("If any test shows TIMEOUT or ERROR, that's the issue.\n")
