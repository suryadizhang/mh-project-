"""
Quick Deepgram API Key Verification Test
Run this to verify your API key is valid before Week 3 testing
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()


def test_deepgram_key():
    """Test if Deepgram API key is valid"""

    print("\n" + "=" * 60)
    print("🎙️ DEEPGRAM API KEY VERIFICATION")
    print("=" * 60 + "\n")

    # Check if key exists
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found in .env file!")
        print("\nTo fix:")
        print("1. Go to https://console.deepgram.com/")
        print("2. Create an API key")
        print("3. Add to apps/backend/.env:")
        print("   DEEPGRAM_API_KEY=your-key-here")
        return False

    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]}\n")

    # Check if SDK is installed
    try:
        from deepgram import DeepgramClient

        print("✅ Deepgram SDK installed\n")
    except ImportError as e:
        print(f"❌ Deepgram SDK not installed! Error: {e}")
        print("\nTo fix:")
        print("   pip install deepgram-sdk")
        return False

    # Test API key with actual request
    print("🔄 Testing API key with Deepgram service...\n")

    try:
        import asyncio
        import httpx

        async def verify_key():
            """Test API key with simple transcription request"""

            # Use Deepgram's REST API directly
            url = "https://api.deepgram.com/v1/listen"
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

            # Use Deepgram's sample audio
            payload = {"url": "https://dpgr.am/spacewalk.wav"}

            params = {"model": "nova-2", "language": "en-US", "smart_format": "true"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload, params=params)

                if response.status_code != 200:
                    raise Exception(f"API returned status {response.status_code}: {response.text}")

                data = response.json()

                # Extract transcript
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                confidence = data["results"]["channels"][0]["alternatives"][0]["confidence"]

                print("✅ API Key is VALID!\n")
                print("📝 Sample Transcription:")
                print(f"   '{transcript[:100]}...'\n")
                print(f"📊 Confidence: {confidence * 100:.1f}%\n")

                return True

        # Run async test
        result = asyncio.run(verify_key())

        if result:
            print("=" * 60)
            print("✅ DEEPGRAM READY FOR WEEK 3 TESTING!")
            print("=" * 60)
            print("\nYour configuration:")
            print("  - API Key: Valid ✅")
            print(f"  - Model: {os.getenv('DEEPGRAM_MODEL', 'nova-2')}")
            print(f"  - Voice: {os.getenv('DEEPGRAM_TTS_MODEL', 'aura-asteria-en')}")
            print(f"  - Voice AI: {os.getenv('ENABLE_VOICE_AI', 'false')}")
            print("\n🚀 Ready to start Week 3!")
            return True

    except Exception as e:
        print("❌ API Key verification FAILED!\n")
        print(f"Error: {str(e)}\n")

        if "401" in str(e) or "Unauthorized" in str(e):
            print("💡 This means your API key is invalid or expired.")
            print("\nTo fix:")
            print("1. Go to https://console.deepgram.com/")
            print("2. Generate a new API key")
            print("3. Update apps/backend/.env:")
            print("   DEEPGRAM_API_KEY=your-new-key-here")

        elif "403" in str(e) or "credits" in str(e).lower():
            print("💡 Your account may be out of credits.")
            print("\nTo fix:")
            print("1. Go to https://console.deepgram.com/billing")
            print("2. Check your balance")
            print("3. Add payment method or purchase credits")

        else:
            print("💡 Unexpected error. Check your internet connection.")
            print("   Or contact Deepgram support at support@deepgram.com")

        return False


if __name__ == "__main__":
    try:
        success = test_deepgram_key()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
