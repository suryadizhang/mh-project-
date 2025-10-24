"""Quick API test to check endpoint responses"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from httpx import AsyncClient, ASGITransport
from api.app.main import app


async def test_api():
    """Test API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        # Test health endpoint
        print("Testing /health...")
        resp = await client.get('/health')
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:200]}\n")
        
        # Test API bookings endpoint with redirects
        print("Testing /api/bookings...")
        resp = await client.get('/api/bookings?limit=10', follow_redirects=True)
        print(f"  Status: {resp.status_code}")
        print(f"  URL: {resp.url}")
        print(f"  Body: {resp.text[:500]}\n")
        
        # Test without redirect
        print("Testing /api/bookings (no redirect)...")
        resp = await client.get('/api/bookings?limit=10', follow_redirects=False)
        print(f"  Status: {resp.status_code}")
        print(f"  Headers: {dict(resp.headers)}")
        if resp.status_code in [301, 302, 307, 308]:
            print(f"  Redirect to: {resp.headers.get('location')}")


if __name__ == "__main__":
    asyncio.run(test_api())
