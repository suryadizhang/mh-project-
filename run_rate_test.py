#!/usr/bin/env python3

"""
Direct Python execution test for rate limiting
This runs in the same Python environment without stopping the server
"""

import subprocess
import sys
import os

def run_test():
    """Run the rate limiting test without interfering with the server"""
    
    print("🧪 RUNNING RATE LIMITING TEST")
    print("=" * 50)
    print("Note: Server should be running on http://127.0.0.1:8001")
    print("=" * 50)
    
    # Get the correct Python executable
    python_exe = r"C:/Users/surya/projects/MH webapps/.venv/Scripts/python.exe"
    test_file = r"C:\Users\surya\projects\MH webapps\test_server_direct.py"
    
    # Change to the project directory
    project_dir = r"C:\Users\surya\projects\MH webapps"
    
    try:
        # Run the test in a separate process
        result = subprocess.run(
            [python_exe, test_file],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        print("📋 TEST OUTPUT:")
        print("-" * 50)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ ERRORS/WARNINGS:")
            print("-" * 50)
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Rate limiting test completed successfully!")
        else:
            print(f"\n❌ Test failed with exit code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    
    if success:
        print("\n🎉 RATE LIMITING SYSTEM VALIDATED!")
        print("✅ Admin users have proper higher limits for CRM operations")
    else:
        print("\n⚠️ Rate limiting test had issues")
        print("🔧 Check if the server is running on http://127.0.0.1:8001")