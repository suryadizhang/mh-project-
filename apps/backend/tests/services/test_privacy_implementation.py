"""
Automated Privacy & Initials Testing Suite
Tests database, API endpoints, privacy filtering, and initials generation
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select
from api.app.database import AsyncSessionLocal
from models.review import CustomerReviewBlogPost


class PrivacyTestSuite:
    """Performance-optimized test suite using async and batch operations"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'total': 0
        }
    
    def test(self, name: str, condition: bool, expected: str = "", actual: str = ""):
        """Record test result"""
        self.results['total'] += 1
        if condition:
            self.results['passed'].append(name)
            print(f"  [PASS] {name}")
        else:
            self.results['failed'].append({
                'name': name,
                'expected': expected,
                'actual': actual
            })
            print(f"  [FAIL] {name}")
            if expected and actual:
                print(f"     Expected: {expected}")
                print(f"     Got: {actual}")
    
    async def test_initials_generation(self):
        """Test get_initials() method with various name patterns"""
        print("\n[TEST] Testing Initials Generation...")
        
        test_cases = {
            "John Doe": "JD",
            "Sarah": "S",
            "Mary Jane Watson": "MW",  # First + Last
            "A": "A",
            "": "?",
            "  ": "?",
            "John": "J",
            "Alice Bob Charlie": "AC",  # First + Last only
        }
        
        # Create temp review instances for testing (in-memory, no DB)
        for name, expected_initials in test_cases.items():
            review = CustomerReviewBlogPost(customer_name=name)
            actual = review.get_initials()
            self.test(
                f"Initials for '{name}'",
                actual == expected_initials,
                expected_initials,
                actual
            )
    
    async def test_display_name_logic(self):
        """Test get_display_name() method"""
        print("\n[TEST] Testing Display Name Logic...")
        
        # Test full name mode
        review1 = CustomerReviewBlogPost(
            customer_name="John Doe",
            show_initials_only=False
        )
        self.test(
            "Display full name when show_initials_only=False",
            review1.get_display_name() == "John Doe",
            "John Doe",
            review1.get_display_name()
        )
        
        # Test initials mode
        review2 = CustomerReviewBlogPost(
            customer_name="John Doe",
            show_initials_only=True
        )
        self.test(
            "Display initials when show_initials_only=True",
            review2.get_display_name() == "JD",
            "JD",
            review2.get_display_name()
        )
        
        # Test empty name
        review3 = CustomerReviewBlogPost(
            customer_name="",
            show_initials_only=False
        )
        self.test(
            "Handle empty name gracefully",
            review3.get_display_name() == "Anonymous",
            "Anonymous",
            review3.get_display_name()
        )
    
    async def test_database_schema(self):
        """Test that database has required columns"""
        print("\n[TEST] Testing Database Schema...")
        
        async with AsyncSessionLocal() as session:
            try:
                # Try to query with new fields
                result = await session.execute(
                    select(
                        CustomerReviewBlogPost.customer_name,
                        CustomerReviewBlogPost.customer_email,
                        CustomerReviewBlogPost.customer_phone,
                        CustomerReviewBlogPost.show_initials_only
                    ).limit(1)
                )
                
                self.test("customer_name column exists", True)
                self.test("customer_email column exists", True)
                self.test("customer_phone column exists", True)
                self.test("show_initials_only column exists", True)
                
            except Exception as e:
                self.test("Database schema", False, "All columns exist", f"Error: {e}")
    
    async def test_data_integrity(self):
        """Test that we can create and retrieve reviews with privacy fields"""
        print("\n[TEST] Testing Data Integrity...")
        
        async with AsyncSessionLocal() as session:
            try:
                # Create test review
                test_review = CustomerReviewBlogPost(
                    customer_id=999,
                    customer_name="Test User",
                    customer_email="test@example.com",
                    customer_phone="555-0000",
                    show_initials_only=True,
                    title="Test Review",
                    content="This is a test review for data integrity validation.",
                    rating=5,
                    status='pending'
                )
                
                session.add(test_review)
                await session.commit()
                await session.refresh(test_review)
                
                review_id = test_review.id
                
                # Retrieve and verify
                result = await session.execute(
                    select(CustomerReviewBlogPost).filter(
                        CustomerReviewBlogPost.id == review_id
                    )
                )
                retrieved = result.scalar_one_or_none()
                
                if retrieved:
                    self.test("Store customer_name", retrieved.customer_name == "Test User")
                    self.test("Store customer_email", retrieved.customer_email == "test@example.com")
                    self.test("Store customer_phone", retrieved.customer_phone == "555-0000")
                    self.test("Store show_initials_only", retrieved.show_initials_only == True)
                    self.test("get_initials() works", retrieved.get_initials() == "TU")
                    self.test("get_display_name() works", retrieved.get_display_name() == "TU")
                    
                    # Cleanup
                    await session.delete(retrieved)
                    await session.commit()
                else:
                    self.test("Data persistence", False, "Review saved and retrieved", "Review not found")
                    
            except Exception as e:
                self.test("Data integrity", False, "All operations succeed", f"Error: {e}")
    
    async def test_api_privacy_filtering(self):
        """Test that API methods properly filter privacy data"""
        print("\n[TEST] Testing API Privacy Filtering...")
        
        # This tests the model methods used by API endpoints
        review = CustomerReviewBlogPost(
            customer_id=1,
            customer_name="Alice Johnson",
            customer_email="alice@secret.com",
            customer_phone="555-1234",
            show_initials_only=True,
            title="Great Place",
            content="Amazing experience!",
            rating=5
        )
        
        # Public display should only show initials
        display_name = review.get_display_name()
        self.test(
            "Public API shows initials only",
            display_name == "AJ",
            "AJ",
            display_name
        )
        
        # Verify email/phone are not in display name
        self.test(
            "Email not in display name",
            "alice@secret.com" not in display_name
        )
        self.test(
            "Phone not in display name",
            "555-1234" not in display_name
        )
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("[SUMMARY] TEST SUMMARY")
        print("=" * 70)
        
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        total = self.results['total']
        
        print(f"\n[PASS] Passed: {passed}/{total}")
        print(f"[FAIL] Failed: {failed}/{total}")
        
        if failed > 0:
            print("\n[FAIL] Failed Tests:")
            for fail in self.results['failed']:
                if isinstance(fail, dict):
                    print(f"  * {fail['name']}")
                else:
                    print(f"  * {fail}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n[STATS] Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n[SUCCESS] ALL TESTS PASSED! Privacy implementation verified.")
        else:
            print("\n[WARNING] Some tests failed. Review implementation.")
        
        print("=" * 70)
        
        return success_rate == 100


async def run_all_tests():
    """Run complete test suite"""
    print("=" * 70)
    print("[START] PRIVACY & INITIALS AUTOMATED TEST SUITE")
    print("=" * 70)
    
    suite = PrivacyTestSuite()
    
    # Run all test groups
    await suite.test_initials_generation()
    await suite.test_display_name_logic()
    await suite.test_database_schema()
    await suite.test_data_integrity()
    await suite.test_api_privacy_filtering()
    
    # Print summary
    all_passed = suite.print_summary()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
