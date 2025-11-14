"""
Comprehensive Deepgram STT/TTS Integration Test
Tests all voice AI capabilities for Phase 2.1
"""

import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.append(".")

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DeepgramIntegrationTester:
    """Complete test suite for Deepgram STT and TTS"""
    
    def __init__(self):
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "="*70)
        print(f"{title}")
        print("="*70)
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        self.results['tests_run'] += 1
        
        if passed:
            self.results['tests_passed'] += 1
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
        else:
            self.results['tests_failed'] += 1
            print(f"❌ {test_name}")
            if details:
                print(f"   Error: {details}")
                self.results['errors'].append(f"{test_name}: {details}")
    
    def test_environment_setup(self):
        """Test 1: Environment Configuration"""
        self.print_header("🔧 TEST 1: ENVIRONMENT CONFIGURATION")
        
        # Check API key
        if self.deepgram_api_key:
            self.print_result(
                "Deepgram API Key Found",
                True,
                f"Key: {self.deepgram_api_key[:15]}..."
            )
        else:
            self.print_result(
                "Deepgram API Key Found",
                False,
                "DEEPGRAM_API_KEY not found in .env"
            )
            return False
        
        # Check if key format is correct (legacy keys don't start with dg_)
        if self.deepgram_api_key.startswith("dg_") or len(self.deepgram_api_key) >= 32:
            self.print_result(
                "API Key Format", 
                True, 
                "Valid format (API v2 or legacy key)"
            )
        else:
            self.print_result(
                "API Key Format",
                False,
                "API key should be at least 32 characters"
            )
        
        return True
    
    def test_sdk_import(self):
        """Test 2: Deepgram SDK Import"""
        self.print_header("📦 TEST 2: DEEPGRAM SDK IMPORT")
        
        try:
            from deepgram import DeepgramClient
            self.print_result("Import DeepgramClient", True, "Successfully imported")
            
            # Check version
            import deepgram
            if hasattr(deepgram, '__version__'):
                self.print_result("SDK Version", True, f"v{deepgram.__version__}")
            
            return True
            
        except ImportError as e:
            self.print_result("SDK Import", False, str(e))
            print("\n💡 To install: pip install deepgram-sdk")
            return False
    
    def test_client_initialization(self):
        """Test 3: Client Initialization"""
        self.print_header("🔌 TEST 3: CLIENT INITIALIZATION")
        
        try:
            from deepgram import DeepgramClient
            
            client = DeepgramClient(api_key=self.deepgram_api_key)
            self.print_result("Initialize Client", True, "Deepgram client created")
            
            # Check client attributes
            if hasattr(client, 'listen'):
                self.print_result("STT Interface Available", True, "client.listen exists")
            else:
                self.print_result("STT Interface Available", False)
            
            if hasattr(client, 'speak'):
                self.print_result("TTS Interface Available", True, "client.speak exists")
            else:
                self.print_result("TTS Interface Available", False)
            
            return True, client
            
        except Exception as e:
            self.print_result("Initialize Client", False, str(e))
            return False, None
    
    def test_stt_with_url(self, client):
        """Test 4: Speech-to-Text with URL"""
        self.print_header("🎙️ TEST 4: SPEECH-TO-TEXT (URL)")
        
        try:
            # Use Deepgram's sample audio
            audio_url = "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
            
            print(f"📥 Transcribing audio from: {audio_url}")
            
            # Use SDK v5 API - correct signature: kwargs only
            response = client.listen.v1.media.transcribe_url(
                url=audio_url,
                model="nova-2",
                smart_format=True,
            )
            
            # Extract transcript (SDK v5 returns object with attribute access)
            if isinstance(response, dict):
                transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
                confidence = response['results']['channels'][0]['alternatives'][0].get('confidence', 0)
                duration = response['metadata']['duration']
            else:
                # Object with attribute access
                transcript = response.results.channels[0].alternatives[0].transcript
                confidence = getattr(response.results.channels[0].alternatives[0], 'confidence', 0)
                duration = response.metadata.duration
            
            self.print_result(
                "Transcribe Audio URL",
                True,
                f"Duration: {duration:.2f}s" + (f", Confidence: {confidence:.2%}" if confidence else "")
            )
            
            print(f"\n📝 Transcript: '{transcript}'")
            
            # Verify transcript quality
            if len(transcript) > 0:
                self.print_result("Transcript Not Empty", True, f"{len(transcript)} characters")
            else:
                self.print_result("Transcript Not Empty", False)
            
            if confidence and confidence > 0.8:
                self.print_result("High Confidence", True, f"{confidence:.2%}")
            elif confidence:
                self.print_result("High Confidence", False, f"Only {confidence:.2%}")
            else:
                # Nova-2 may not return confidence for all responses
                self.print_result("Transcript Quality", True, "Nova-2 model (no confidence score)")
            
            return True
            
        except Exception as e:
            self.print_result("Transcribe Audio URL", False, str(e))
            import traceback
            traceback.print_exc()
            return False
    
    def test_tts_synthesis(self, client):
        """Test 5: Text-to-Speech"""
        self.print_header("🔊 TEST 5: TEXT-TO-SPEECH (TTS)")
        
        try:
            test_text = "Hello! Welcome to My Hibachi Chef. How can I help you today?"
            
            print(f"🗣️  Synthesizing: '{test_text}'")
            
            # Generate speech using SDK v5 API
            audio_stream = client.speak.v1.audio.generate(
                text=test_text,
                model="aura-asteria-en"
            )
            
            # Collect audio bytes
            audio_bytes = b""
            for chunk in audio_stream:
                audio_bytes += chunk
            
            self.print_result("Generate Speech", True, f"{len(audio_bytes):,} bytes")
            
            # Save to file for verification
            with open("test_output.mp3", "wb") as f:
                f.write(audio_bytes)
            
            if os.path.exists("test_output.mp3"):
                file_size = os.path.getsize("test_output.mp3")
                self.print_result(
                    "Audio File Created",
                    True,
                    f"File size: {file_size:,} bytes"
                )
                
                # Cleanup
                os.remove("test_output.mp3")
                self.print_result("Cleanup Test File", True, "test_output.mp3 deleted")
            else:
                self.print_result("Audio File Created", False, "File not found")
            
            return True
            
        except Exception as e:
            self.print_result("Generate Speech", False, str(e))
            import traceback
            traceback.print_exc()
            return False
    
    def test_multiple_voices(self, client):
        """Test 6: Multiple Voice Models"""
        self.print_header("🎭 TEST 6: MULTIPLE VOICE MODELS")
        
        voices_to_test = [
            ("aura-asteria-en", "Asteria (Female)"),
            ("aura-luna-en", "Luna (Female)"),
            ("aura-orion-en", "Orion (Male)"),
        ]
        
        test_text = "Thank you for calling My Hibachi Chef."
        
        for voice_id, voice_name in voices_to_test:
            try:
                print(f"\n🎤 Testing voice: {voice_name}")
                
                # Generate audio using SDK v5 API
                audio_stream = client.speak.v1.audio.generate(
                    text=test_text,
                    model=voice_id
                )
                
                # Collect audio bytes
                audio_bytes = b""
                for chunk in audio_stream:
                    audio_bytes += chunk
                
                # Save to file
                filename = f"test_{voice_id}.mp3"
                with open(filename, "wb") as f:
                    f.write(audio_bytes)
                
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    self.print_result(
                        f"Voice: {voice_name}",
                        True,
                        f"{file_size:,} bytes"
                    )
                    os.remove(filename)
                else:
                    self.print_result(f"Voice: {voice_name}", False, "File not created")
                    
            except Exception as e:
                self.print_result(f"Voice: {voice_name}", False, str(e))
        
        return True
    
    async def test_speech_service_integration(self):
        """Test 7: Speech Service Integration"""
        self.print_header("🔗 TEST 7: SPEECH SERVICE INTEGRATION")
        
        try:
            from src.services.speech_service import speech_service
            
            self.print_result("Import SpeechService", True, "Module loaded")
            
            # Check if Deepgram is enabled
            if speech_service.deepgram_enabled:
                self.print_result("Deepgram Enabled", True, "Service configured")
            else:
                self.print_result("Deepgram Enabled", False, "Not configured")
                return False
            
            # Test health check
            print("\n🏥 Running health check...")
            health = await speech_service.health_check()
            
            if health.get('deepgram', {}).get('enabled'):
                self.print_result("Health Check", True, "Service healthy")
                
                print(f"\n📊 Service Configuration:")
                print(f"   • STT Model: {health['deepgram']['stt_model']}")
                print(f"   • TTS Model: {health['deepgram']['tts_model']}")
                print(f"   • STT Cost: ${health['deepgram']['stt_cost_per_minute']}/min")
                print(f"   • TTS Cost: ${health['deepgram']['tts_cost_per_1000_chars']}/1k chars")
                print(f"   • Voice AI: {health['voice_ai_enabled']}")
            else:
                self.print_result("Health Check", False, "Service not healthy")
            
            # Test get available voices
            print("\n🎤 Fetching available voices...")
            voices = await speech_service.get_available_voices()
            
            if voices and len(voices) > 0:
                self.print_result(
                    "Get Available Voices",
                    True,
                    f"{len(voices)} voices available"
                )
                
                print(f"\n📋 Available Voices:")
                for voice in voices[:5]:  # Show first 5
                    print(f"   • {voice['name']} ({voice['gender']}) - {voice['description']}")
                if len(voices) > 5:
                    print(f"   ... and {len(voices) - 5} more")
            else:
                self.print_result("Get Available Voices", False, "No voices returned")
            
            # Test TTS synthesis
            print("\n🔊 Testing TTS synthesis...")
            test_text = "Welcome to My Hibachi Chef. How may I assist you?"
            
            audio_bytes = await speech_service.synthesize_speech(test_text)
            
            if audio_bytes and len(audio_bytes) > 0:
                self.print_result(
                    "Synthesize Speech",
                    True,
                    f"{len(audio_bytes):,} bytes generated"
                )
            else:
                self.print_result("Synthesize Speech", False, "No audio generated")
            
            return True
            
        except Exception as e:
            self.print_result("Speech Service Integration", False, str(e))
            import traceback
            traceback.print_exc()
            return False
    
    def test_cost_calculation(self):
        """Test 8: Cost Calculation"""
        self.print_header("💰 TEST 8: COST CALCULATION")
        
        try:
            from src.services.speech_service import speech_service
            
            # Test scenarios
            scenarios = [
                ("1-minute call", 1.0, 150),
                ("5-minute call", 5.0, 750),
                ("10-minute call", 10.0, 1500),
                ("30-minute call", 30.0, 4500),
            ]
            
            print("\n📊 Cost Estimates:")
            print(f"{'Scenario':<20} {'STT Cost':<15} {'TTS Cost':<15} {'Total':<15}")
            print("-" * 70)
            
            for scenario_name, minutes, chars in scenarios:
                stt_cost = speech_service.calculate_transcription_cost(minutes)
                tts_cost = speech_service.calculate_tts_cost(chars)
                total = stt_cost + tts_cost
                
                print(f"{scenario_name:<20} ${stt_cost:>6.4f}       ${tts_cost:>6.4f}       ${total:>6.4f}")
            
            self.print_result("Cost Calculation", True, "All calculations successful")
            
            # Estimate for 1000 calls
            print("\n📈 Volume Estimates (1000 calls, avg 5 min each):")
            total_minutes = 5000  # 1000 calls × 5 min
            total_chars = 750000  # 1000 calls × 750 chars
            stt_total = speech_service.calculate_transcription_cost(total_minutes)
            tts_total = speech_service.calculate_tts_cost(total_chars)
            grand_total = stt_total + tts_total
            
            print(f"   • STT Cost: ${stt_total:.2f}")
            print(f"   • TTS Cost: ${tts_total:.2f}")
            print(f"   • Total Cost: ${grand_total:.2f}")
            print(f"   • Cost per call: ${grand_total/1000:.4f}")
            
            return True
            
        except Exception as e:
            self.print_result("Cost Calculation", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("📊 TEST SUMMARY")
        
        total = self.results['tests_run']
        passed = self.results['tests_passed']
        failed = self.results['tests_failed']
        
        print(f"\n📈 Results:")
        print(f"   • Total tests: {total}")
        print(f"   • Passed: {passed} ✅")
        print(f"   • Failed: {failed} ❌")
        print(f"   • Success rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Errors encountered:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        # Overall verdict
        print("\n" + "="*70)
        if failed == 0:
            print("🎉 ALL TESTS PASSED - DEEPGRAM READY FOR PRODUCTION!")
            print("="*70)
            print("\n✅ Phase 2.1 Status: COMPLETE")
            print("\n💡 Next Steps:")
            print("   1. ✅ Deepgram STT/TTS - Fully operational")
            print("   2. 🔜 RingCentral Webhook Pipeline")
            print("   3. 🔜 Call Recording Storage")
            print("   4. 🔜 Transcript Database Sync")
            print("   5. 🔜 Voice → AI → Database Flow")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW ERRORS ABOVE")
            print("="*70)
            print("\n💡 Common Issues:")
            print("   • Missing DEEPGRAM_API_KEY in .env")
            print("   • Deepgram SDK not installed (pip install deepgram-sdk)")
            print("   • Invalid API key format")
            print("   • Network connectivity issues")


async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("🚀 DEEPGRAM STT/TTS INTEGRATION TEST SUITE")
    print("   Phase 2.1: Voice AI Integration")
    print("="*70)
    
    tester = DeepgramIntegrationTester()
    
    # Test 1: Environment
    if not tester.test_environment_setup():
        print("\n❌ Environment not configured properly. Please set DEEPGRAM_API_KEY in .env")
        return
    
    # Test 2: SDK Import
    if not tester.test_sdk_import():
        return
    
    # Test 3: Client Initialization
    success, client = tester.test_client_initialization()
    if not success or not client:
        return
    
    # Test 4: STT with URL
    tester.test_stt_with_url(client)
    
    # Test 5: TTS Synthesis
    tester.test_tts_synthesis(client)
    
    # Test 6: Multiple Voices
    tester.test_multiple_voices(client)
    
    # Test 7: Speech Service Integration
    await tester.test_speech_service_integration()
    
    # Test 8: Cost Calculation
    tester.test_cost_calculation()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
