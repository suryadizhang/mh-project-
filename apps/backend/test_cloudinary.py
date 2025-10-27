"""
Quick test of Cloudinary configuration
"""
import os
import cloudinary

# Load from .env
from dotenv import load_dotenv
load_dotenv()

# Configure
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

print("🔧 Cloudinary Configuration:")
print(f"   Cloud Name: {cloudinary.config().cloud_name}")
print(f"   API Key: {cloudinary.config().api_key[:10]}...")
print(f"   Secure: {cloudinary.config().secure}")

# Test connection
try:
    result = cloudinary.api.ping()
    print("\n✅ Cloudinary connection successful!")
    print(f"   Status: {result.get('status', 'ok')}")
except Exception as e:
    print(f"\n❌ Cloudinary connection failed: {e}")
