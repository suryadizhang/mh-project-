from core.config import Settings

def test_config():
    try:
        s = Settings()
        print(f"✅ Settings loaded - Environment: {s.ENVIRONMENT}")
        
        # Test rate limiting methods
        admin_limits = s.get_rate_limit_for_user(None)  # Public user
        print(f"✅ Public rate limits: {admin_limits['per_minute']}/min")
        
        ai_limits = s.get_ai_rate_limit()
        print(f"✅ AI rate limits: {ai_limits['per_minute']}/min")
        
        print(f"✅ Database URL: {s.DATABASE_URL[:30]}...")
        print(f"✅ Redis URL: {s.REDIS_URL}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_config()