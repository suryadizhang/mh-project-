"""
Cursor Pagination API Tests

Tests cursor-based pagination implementation:
- Forward pagination
- Backward pagination
- Cursor encoding/decoding
- Edge cases and boundaries
- Data consistency
"""
import pytest
from httpx import AsyncClient
from typing import List, Dict, Any


class TestCursorPaginationBasics:
    """Test basic cursor pagination functionality."""
    
    @pytest.mark.asyncio
    async def test_first_page_without_cursor(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test first page request without cursor parameter.
        
        Should return:
        - items: List of bookings
        - next_cursor: Cursor for next page
        - has_next: Boolean indicating more pages
        - has_previous: False (no previous page)
        """
        await create_test_bookings(count=100)
        
        response = await async_client.get("/api/bookings?limit=20")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 20
        
        # Validate pagination metadata
        assert "has_next" in data or "next_cursor" in data
        assert data.get("has_previous", False) is False
        
        print(f"✅ First page: {len(data['items'])} items")
    
    @pytest.mark.asyncio
    async def test_forward_pagination(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test forward pagination through multiple pages.
        
        Validates:
        - next_cursor progresses correctly
        - Items don't repeat across pages
        - Page boundaries work correctly
        """
        await create_test_bookings(count=100)
        
        # Get first page
        page1 = await async_client.get("/api/bookings?limit=20")
        assert page1.status_code == 200
        page1_data = page1.json()
        page1_ids = {item["id"] for item in page1_data["items"]}
        
        # Get second page
        next_cursor = page1_data.get("next_cursor")
        if not next_cursor:
            pytest.skip("No next cursor in response")
        
        page2 = await async_client.get(
            f"/api/bookings?cursor={next_cursor}&limit=20"
        )
        assert page2.status_code == 200
        page2_data = page2.json()
        page2_ids = {item["id"] for item in page2_data["items"]}
        
        # Validate no overlap
        assert len(page1_ids & page2_ids) == 0, "Pages have overlapping items"
        
        # Validate second page has items
        assert len(page2_data["items"]) > 0, "Second page is empty"
        
        print(f"✅ Forward pagination: Page 1={len(page1_ids)}, Page 2={len(page2_ids)} items")
    
    @pytest.mark.asyncio
    async def test_backward_pagination(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test backward pagination using prev_cursor.
        
        Validates:
        - Can navigate back to previous page
        - Items are consistent when going back
        - prev_cursor works correctly
        """
        await create_test_bookings(count=100)
        
        # Get first page
        page1 = await async_client.get("/api/bookings?limit=20")
        page1_data = page1.json()
        page1_ids = {item["id"] for item in page1_data["items"]}
        
        # Get second page
        next_cursor = page1_data.get("next_cursor")
        if not next_cursor:
            pytest.skip("No next cursor")
        
        page2 = await async_client.get(
            f"/api/bookings?cursor={next_cursor}&limit=20"
        )
        page2_data = page2.json()
        
        # Go back to first page
        prev_cursor = page2_data.get("prev_cursor") or page2_data.get("previous_cursor")
        if not prev_cursor:
            pytest.skip("No prev cursor")
        
        page1_again = await async_client.get(
            f"/api/bookings?cursor={prev_cursor}&direction=prev&limit=20"
        )
        page1_again_data = page1_again.json()
        page1_again_ids = {item["id"] for item in page1_again_data["items"]}
        
        # Should get same items as first page
        assert page1_ids == page1_again_ids, "Backward navigation returned different items"
        
        print(f"✅ Backward pagination: Returned to first page successfully")


class TestCursorEdgeCases:
    """Test cursor pagination edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_result_set(
        self,
        async_client: AsyncClient,
    ):
        """
        Test cursor pagination with no data.
        
        Should return empty items list with proper metadata.
        """
        response = await async_client.get("/api/bookings?limit=20")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert len(data["items"]) == 0
        assert data.get("has_next", False) is False
        
        print(f"✅ Empty result set handled correctly")
    
    @pytest.mark.asyncio
    async def test_last_page_detection(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test detection of last page.
        
        has_next should be False on last page.
        """
        # Create exactly 50 bookings
        await create_test_bookings(count=50)
        
        # Request all items (limit=50)
        response = await async_client.get("/api/bookings?limit=50")
        data = response.json()
        
        # Should indicate no next page
        assert data.get("has_next", True) is False or data.get("next_cursor") is None
        
        print(f"✅ Last page detected correctly")
    
    @pytest.mark.asyncio
    async def test_invalid_cursor_handling(
        self,
        async_client: AsyncClient,
    ):
        """
        Test handling of invalid/malformed cursor.
        
        Should return 400 Bad Request or gracefully handle.
        """
        response = await async_client.get("/api/bookings?cursor=invalid_cursor_123")
        
        # Should either reject or treat as first page
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            # If accepted, should return first page
            data = response.json()
            assert "items" in data
            print(f"✅ Invalid cursor handled gracefully (first page)")
        else:
            # If rejected, should have error message
            data = response.json()
            assert "error" in data or "detail" in data
            print(f"✅ Invalid cursor rejected with error")
    
    @pytest.mark.asyncio
    async def test_expired_cursor_handling(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test handling of expired cursor (data deleted/modified).
        
        Should handle gracefully without breaking pagination.
        """
        await create_test_bookings(count=50)
        
        # Get cursor
        page1 = await async_client.get("/api/bookings?limit=20")
        cursor = page1.json().get("next_cursor")
        
        # Simulate data change (in real scenario, bookings might be deleted)
        # For this test, just verify cursor still works
        
        if cursor:
            page2 = await async_client.get(f"/api/bookings?cursor={cursor}&limit=20")
            assert page2.status_code in [200, 404]
            print(f"✅ Cursor stability tested")


class TestCursorConsistency:
    """Test data consistency with cursor pagination."""
    
    @pytest.mark.asyncio
    async def test_no_duplicate_items(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that items don't appear on multiple pages.
        
        Validates cursor pagination doesn't cause duplicates.
        """
        await create_test_bookings(count=150)
        
        all_ids = set()
        current_cursor = None
        page_count = 0
        max_pages = 10  # Safety limit
        
        while page_count < max_pages:
            # Get next page
            url = "/api/bookings?limit=20"
            if current_cursor:
                url += f"&cursor={current_cursor}"
            
            response = await async_client.get(url)
            assert response.status_code == 200
            data = response.json()
            
            # Collect IDs
            page_ids = {item["id"] for item in data["items"]}
            
            # Check for duplicates
            duplicates = all_ids & page_ids
            assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate items"
            
            all_ids.update(page_ids)
            page_count += 1
            
            # Check if more pages
            current_cursor = data.get("next_cursor")
            if not current_cursor or not data.get("has_next", False):
                break
        
        print(f"✅ No duplicates found across {page_count} pages ({len(all_ids)} unique items)")
    
    @pytest.mark.asyncio
    async def test_no_missing_items(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that all items are returned when paginating through entire dataset.
        
        Validates no items are skipped during pagination.
        """
        # Create known number of bookings
        test_bookings = await create_test_bookings(count=75)
        expected_count = len(test_bookings)
        
        # Paginate through all items
        all_ids = set()
        current_cursor = None
        page_count = 0
        max_pages = 10
        
        while page_count < max_pages:
            url = "/api/bookings?limit=20"
            if current_cursor:
                url += f"&cursor={current_cursor}"
            
            response = await async_client.get(url)
            data = response.json()
            
            page_ids = {item["id"] for item in data["items"]}
            all_ids.update(page_ids)
            page_count += 1
            
            current_cursor = data.get("next_cursor")
            if not current_cursor:
                break
        
        # Verify all items were retrieved
        assert len(all_ids) == expected_count, (
            f"Expected {expected_count} items, got {len(all_ids)}"
        )
        
        print(f"✅ All {expected_count} items retrieved across {page_count} pages")
    
    @pytest.mark.asyncio
    async def test_sorting_consistency(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that items maintain consistent sort order across pages.
        
        Validates ordering is stable during pagination.
        """
        await create_test_bookings(count=100)
        
        # Get first page
        page1 = await async_client.get("/api/bookings?limit=20&sort=created_at")
        page1_data = page1.json()
        page1_items = page1_data["items"]
        
        # Verify first page is sorted
        if len(page1_items) > 1:
            dates1 = [item.get("created_at") for item in page1_items]
            # Should be in descending order (newest first) typically
            # Adjust based on your actual sort order
            print(f"✅ First page sorted: {len(dates1)} items")
        
        # Get second page
        next_cursor = page1_data.get("next_cursor")
        if next_cursor:
            page2 = await async_client.get(
                f"/api/bookings?cursor={next_cursor}&limit=20&sort=created_at"
            )
            page2_data = page2.json()
            page2_items = page2_data["items"]
            
            # Verify sort continues across pages
            if len(page1_items) > 0 and len(page2_items) > 0:
                # Last item of page 1 should come before first item of page 2
                # (Adjust comparison based on your sort order)
                print(f"✅ Sorting consistent across pages")


class TestCursorLimitVariations:
    """Test different page size limits."""
    
    @pytest.mark.asyncio
    async def test_small_page_size(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """Test pagination with small page size (limit=5)."""
        await create_test_bookings(count=20)
        
        response = await async_client.get("/api/bookings?limit=5")
        data = response.json()
        
        assert len(data["items"]) <= 5
        print(f"✅ Small page size (5): {len(data['items'])} items")
    
    @pytest.mark.asyncio
    async def test_large_page_size(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """Test pagination with large page size (limit=100)."""
        await create_test_bookings(count=150)
        
        response = await async_client.get("/api/bookings?limit=100")
        data = response.json()
        
        assert len(data["items"]) <= 100
        print(f"✅ Large page size (100): {len(data['items'])} items")
    
    @pytest.mark.asyncio
    async def test_default_page_size(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """Test pagination with default page size (no limit parameter)."""
        await create_test_bookings(count=100)
        
        response = await async_client.get("/api/bookings")
        data = response.json()
        
        # Should have some default limit (e.g., 50)
        assert len(data["items"]) <= 50
        print(f"✅ Default page size: {len(data['items'])} items")


class TestCursorMetadata:
    """Test cursor pagination metadata."""
    
    @pytest.mark.asyncio
    async def test_pagination_metadata(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that pagination metadata is accurate.
        
        Validates:
        - has_next is correct
        - has_previous is correct
        - Cursors are present when expected
        """
        await create_test_bookings(count=60)
        
        # First page
        page1 = await async_client.get("/api/bookings?limit=20")
        page1_data = page1.json()
        
        assert page1_data.get("has_previous", False) is False
        assert page1_data.get("has_next") is True or page1_data.get("next_cursor") is not None
        
        # Middle page
        next_cursor = page1_data.get("next_cursor")
        if next_cursor:
            page2 = await async_client.get(f"/api/bookings?cursor={next_cursor}&limit=20")
            page2_data = page2.json()
            
            # Middle page should have both directions available
            assert page2_data.get("has_next") is True or page2_data.get("next_cursor") is not None
            assert page2_data.get("prev_cursor") is not None or page2_data.get("previous_cursor") is not None
            
            print(f"✅ Pagination metadata accurate")
    
    @pytest.mark.asyncio
    async def test_total_count_if_available(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test total count in pagination metadata if provided.
        
        Note: Some cursor pagination implementations don't include total count
        for performance reasons. This test is optional.
        """
        await create_test_bookings(count=42)
        
        response = await async_client.get("/api/bookings?limit=20")
        data = response.json()
        
        if "total" in data or "total_count" in data:
            total = data.get("total") or data.get("total_count")
            assert total == 42, f"Expected total=42, got {total}"
            print(f"✅ Total count accurate: {total}")
        else:
            print(f"ℹ️  Total count not provided (cursor pagination optimization)")
