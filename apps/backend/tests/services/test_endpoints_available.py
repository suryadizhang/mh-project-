"""
Check what endpoints are available
"""
import requests

try:
    # Try health endpoint first
    response = requests.get("http://localhost:8000/api/v1/public/health")
    print(f"Health endpoint status: {response.status_code}")
    print(f"Response: {response.text}\n")
    
    # Try main health
    response = requests.get("http://localhost:8000/api/health")
    print(f"Main health status: {response.status_code}")
    print(f"Response: {response.text}\n")
    
    # Try docs
    response = requests.get("http://localhost:8000/docs")
    print(f"Docs status: {response.status_code}")
    
except Exception as e:
    print(f"Error: {e}")
