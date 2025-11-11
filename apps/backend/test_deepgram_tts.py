"""
Test Deepgram Text-to-Speech (TTS)
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_deepgram_tts():
    """Test Deepgram TTS"""
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    
    if not api_key:
        print("❌ ERROR: DEEPGRAM_API_KEY not found")
        return False
    
    print("="*60)
    print("Deepgram Text-to-Speech Test")
    print("="*60)
    print(f"✓ Found API key: {api_key[:10]}...")
    
    try:
        from deepgram import DeepgramClient
        
        print("\n1. Initializing Deepgram client...")
        deepgram = DeepgramClient(api_key=api_key)
        print("   ✓ Client initialized")
        
        print("\n2. Testing TTS synthesis...")
        text = "Thank you for calling MyHibachi Chef! How can I help you today?"
        
        # Test TTS - correct v5 API
        response = deepgram.speak.v1.audio.generate(
            text=text,
            model="aura-asteria-en"  # Natural female voice
        )
        
        # Save audio to file
        with open("test_tts_output.mp3", "wb") as f:
            for chunk in response:
                f.write(chunk)
        
        print(f"   ✓ TTS successful!")
        print(f"   Text: '{text}'")
        print(f"   Audio saved to: test_tts_output.mp3")
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Deepgram TTS is working!")
        print("="*60)
        print("\n✅ You can use Deepgram for BOTH:")
        print("  • Speech-to-Text (STT)")
        print("  • Text-to-Speech (TTS)")
        print("\n💡 This means:")
        print("  • NO NEED for ElevenLabs!")
        print("  • Single API key for voice AI")
        print("  • Lower latency (same provider)")
        print("  • Simpler billing ($0.015/1000 chars)")
        print("\n🎯 Your Voice AI stack:")
        print("  • Deepgram STT: $0.0125/min")
        print("  • Deepgram TTS: $0.015/1000 chars")
        print("  • Total for 5min call: ~$0.10")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_deepgram_tts()
    exit(0 if success else 1)
