"""
Quick service connectivity test for MyHibachi system
"""
import requests
import asyncio
import websockets
import json
from datetime import datetime

def test_service(name, url, timeout=5):
    """Test if a service is accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        status = "✅ ONLINE" if response.status_code == 200 else f"⚠️ STATUS {response.status_code}"
        return f"{name:20} | {status:15} | {url}"
    except requests.exceptions.ConnectionError:
        return f"{name:20} | ❌ OFFLINE    | {url}"
    except requests.exceptions.Timeout:
        return f"{name:20} | ⏱️ TIMEOUT    | {url}"
    except Exception as e:
        return f"{name:20} | ❌ ERROR      | {url} - {str(e)[:30]}"

async def test_websocket(name, url):
    """Test WebSocket connectivity"""
    try:
        async with websockets.connect(url, timeout=5) as websocket:
            await websocket.send(json.dumps({
                "type": "ping",
                "content": "health_check"
            }))
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            return f"{name:20} | ✅ ONLINE     | {url}"
    except Exception as e:
        return f"{name:20} | ❌ ERROR      | {url} - {str(e)[:30]}"

async def main():
    """Run comprehensive service tests"""
    print("🔍 MyHibachi System Service Test")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 70)
    
    # Test backend services
    print("\n📡 Backend Services:")
    services = [
        ("Main API", "http://localhost:8003/health"),
        ("AI API", "http://localhost:8002/health"),
        ("AI Chat Health", "http://localhost:8002/api/chat/health"),
    ]
    
    for name, url in services:
        print(test_service(name, url))
    
    # Test frontend services
    print("\n🖥️ Frontend Services:")
    frontend_services = [
        ("Admin Panel", "http://localhost:3001"),
        ("Customer App", "http://localhost:3000"),
    ]
    
    for name, url in frontend_services:
        print(test_service(name, url))
    
    # Test WebSocket
    print("\n🔌 WebSocket Services:")
    ws_result = await test_websocket("AI Chat WebSocket", "ws://localhost:8002/ws/chat")
    print(ws_result)
    
    print("\n" + "=" * 70)
    print("✅ Service test complete!")

if __name__ == "__main__":
    asyncio.run(main())