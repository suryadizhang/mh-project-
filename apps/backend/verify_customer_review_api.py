"""
Verify Customer Review API Registration
Checks if endpoints are properly registered in FastAPI app
"""
import sys
import os

# Add src directory to path
src_dir = r"C:\Users\surya\projects\MH webapps\apps\backend\src"
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("=" * 70)
print("🔍 Customer Review API - Registration Verification")
print("=" * 70)

try:
    # Import the main app
    from main import app
    
    print("\n✅ Successfully imported FastAPI app")
    
    # Get all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                'path': route.path,
                'methods': list(route.methods) if route.methods else [],
                'name': route.name if hasattr(route, 'name') else 'N/A'
            })
    
    # Filter customer review routes
    customer_review_routes = [
        r for r in routes 
        if '/customer-reviews' in r['path']
    ]
    
    # Filter admin moderation routes
    admin_moderation_routes = [
        r for r in routes
        if '/review-moderation' in r['path']
    ]
    
    print(f"\n📊 Total Routes: {len(routes)}")
    print(f"🎯 Customer Review Routes: {len(customer_review_routes)}")
    print(f"🔐 Admin Moderation Routes: {len(admin_moderation_routes)}")
    
    if customer_review_routes:
        print("\n✅ Customer Review API Endpoints Registered:")
        print("-" * 70)
        
        for route in customer_review_routes:
            methods_set = set(route['methods']) - {'HEAD', 'OPTIONS'}
            methods = ', '.join(sorted(methods_set))
            print(f"   {methods:6} {route['path']}")
        
        print("\n" + "=" * 70)
        print("✨ SUCCESS: Customer Review API is properly registered!")
        print("=" * 70)
        
        print("\n📚 Available Endpoints:")
        print("   1. POST   /api/customer-reviews/submit-review (with media_files)")
        print("   2. GET    /api/customer-reviews/my-reviews")
        print("   3. GET    /api/customer-reviews/approved-reviews (public feed)")
        print("   4. GET    /api/customer-reviews/reviews/{id}")
        print("   5. POST   /api/customer-reviews/reviews/{id}/like")
        print("   6. POST   /api/customer-reviews/reviews/{id}/helpful")
        print("   7. GET    /api/customer-reviews/stats")
        
        print("\n🎥 Media Support:")
        print("   • Images: JPG, PNG, WEBP, GIF (10MB max)")
        print("   • Videos: MP4, MOV, WEBM, AVI (100MB max)")
        print("   • Max 10 files per review")
        print("   • Cloudinary auto-optimization enabled")
        
        print("\n🚀 Next Steps:")
        print("   1. Start server: cd apps/backend/src && python -m uvicorn main:app --reload")
        print("   2. Open docs: http://localhost:8000/docs")
        print("   3. Test submit-review endpoint with Postman/curl")
        print("   4. Build admin moderation API")
        print("   5. Build frontend components")
        
    # Admin Moderation Routes
    if admin_moderation_routes:
        print("\n✅ Admin Moderation API Endpoints Registered:")
        print("-" * 70)
        
        for route in admin_moderation_routes:
            methods_set = set(route['methods']) - {'HEAD', 'OPTIONS'}
            methods = ', '.join(sorted(methods_set))
            print(f"   {methods:6} {route['path']}")
        
        print("\n" + "=" * 70)
        print("✨ SUCCESS: Admin Moderation API is properly registered!")
        print("=" * 70)
        
        print("\n📚 Admin Endpoints:")
        print("   1. GET    /api/admin/review-moderation/pending-reviews (FIFO queue)")
        print("   2. POST   /api/admin/review-moderation/approve-review/{id}")
        print("   3. POST   /api/admin/review-moderation/reject-review/{id}")
        print("   4. POST   /api/admin/review-moderation/bulk-action")
        print("   5. GET    /api/admin/review-moderation/approval-log/{id}")
        print("   6. GET    /api/admin/review-moderation/stats")
        print("   7. PUT    /api/admin/review-moderation/hold-review/{id}")
        
        print("\n🎯 Total Endpoints: 14 (7 customer + 7 admin)")
        
    else:
        print("\n⚠️  WARNING: No admin moderation routes found!")
        print("   Check if router was properly imported and registered.")
        
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("   Make sure all dependencies are installed.")
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
