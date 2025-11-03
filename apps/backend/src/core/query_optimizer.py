"""
Query Optimization Utilities - N+1 Prevention & Performance
Utilities for optimizing SQLAlchemy queries and preventing N+1 problems
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import Select


class QueryOptimizer:
    """Utilities for query optimization and N+1 prevention"""

    @staticmethod
    def eager_load_relationships(
        query: Select, relationships: list[str], strategy: str = "selectinload"
    ) -> Select:
        """
        Add eager loading to prevent N+1 queries

        Args:
            query: Base SQLAlchemy query
            relationships: List of relationship names to eager load
            strategy: "selectinload" (separate query) or "joinedload" (single query with JOIN)

        Returns:
            Modified query with eager loading

        Example:
            query = select(Booking)
            query = QueryOptimizer.eager_load_relationships(
                query,
                ["customer", "menu_items", "reviews"],
                strategy="selectinload"
            )
        """
        if strategy == "selectinload":
            for rel in relationships:
                query = query.options(selectinload(rel))
        elif strategy == "joinedload":
            for rel in relationships:
                query = query.options(joinedload(rel))
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Use 'selectinload' or 'joinedload'")

        return query

    @staticmethod
    def add_nested_eager_loading(query: Select, nested_paths: list[str]) -> Select:
        """
        Add nested eager loading for deep relationships

        Args:
            query: Base SQLAlchemy query
            nested_paths: List of dot-separated paths like "customer.reviews.response"

        Returns:
            Modified query with nested eager loading

        Example:
            query = select(Booking)
            query = QueryOptimizer.add_nested_eager_loading(
                query,
                ["customer.reviews", "menu_items.ingredients"]
            )
        """
        for path in nested_paths:
            parts = path.split(".")
            if len(parts) == 2:
                query = query.options(selectinload(parts[0]).selectinload(parts[1]))
            elif len(parts) == 3:
                query = query.options(
                    selectinload(parts[0]).selectinload(parts[1]).selectinload(parts[2])
                )

        return query

    @staticmethod
    async def count_optimized(session: AsyncSession, query: Select) -> int:
        """
        Optimized count query that doesn't load all rows

        Args:
            session: Database session
            query: Base query to count

        Returns:
            Total count of rows
        """
        count_query = select(func.count()).select_from(query.subquery())
        result = await session.execute(count_query)
        return result.scalar() or 0

    @staticmethod
    def optimize_pagination(
        query: Select, page: int = 1, page_size: int = 20, max_page_size: int = 100
    ) -> Select:
        """
        Add pagination with safety limits

        Args:
            query: Base query
            page: Page number (1-indexed)
            page_size: Items per page
            max_page_size: Maximum allowed page size

        Returns:
            Paginated query
        """
        # Validate and limit page size
        page_size = min(page_size, max_page_size)
        page = max(1, page)  # Ensure page is at least 1

        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)


class QueryAnalyzer:
    """Analyze queries for performance issues"""

    @staticmethod
    def detect_n_plus_one(query: Select) -> dict:
        """
        Analyze query for potential N+1 issues

        Returns:
            Dictionary with analysis results
        """
        has_eager_loading = False
        relationships_loaded = []

        # Check if query has any eager loading options
        if hasattr(query, "_with_options"):
            for option in query._with_options:
                if hasattr(option, "path"):
                    has_eager_loading = True
                    relationships_loaded.append(str(option.path))

        return {
            "has_eager_loading": has_eager_loading,
            "relationships_loaded": relationships_loaded,
            "recommendation": (
                "Add eager loading if accessing relationships"
                if not has_eager_loading
                else "Good - using eager loading"
            ),
        }


# Convenience functions for common patterns
async def fetch_with_relationships(
    session: AsyncSession,
    model: type[Any],
    filters: dict,
    relationships: list[str],
    strategy: str = "selectinload",
) -> list[Any]:
    """
    Fetch entities with relationships in a single optimized query

    Example:
        bookings = await fetch_with_relationships(
            session,
            Booking,
            {"status": "confirmed"},
            ["customer", "menu_items"],
            strategy="selectinload"
        )
    """
    query = select(model)

    # Apply filters
    for key, value in filters.items():
        query = query.where(getattr(model, key) == value)

    # Add eager loading
    query = QueryOptimizer.eager_load_relationships(query, relationships, strategy)

    result = await session.execute(query)
    return list(result.scalars().all())


async def fetch_paginated_with_relationships(
    session: AsyncSession,
    model: type[Any],
    relationships: list[str],
    page: int = 1,
    page_size: int = 20,
    filters: dict | None = None,
) -> dict:
    """
    Fetch paginated results with relationships

    Returns:
        Dictionary with items, total, page, page_size

    Example:
        result = await fetch_paginated_with_relationships(
            session,
            Booking,
            ["customer", "reviews"],
            page=2,
            page_size=10,
            filters={"status": "confirmed"}
        )
    """
    # Build base query
    query = select(model)

    # Apply filters
    if filters:
        for key, value in filters.items():
            query = query.where(getattr(model, key) == value)

    # Get total count (before pagination)
    total = await QueryOptimizer.count_optimized(session, query)

    # Add eager loading
    query = QueryOptimizer.eager_load_relationships(query, relationships)

    # Add pagination
    query = QueryOptimizer.optimize_pagination(query, page, page_size)

    # Execute query
    result = await session.execute(query)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# Decorator for automatic query optimization
def optimize_query(relationships: list[str] | None = None, strategy: str = "selectinload"):
    """
    Decorator to automatically optimize queries in repository methods

    Example:
        @optimize_query(relationships=["customer", "menu_items"])
        async def get_bookings(self):
            return await self.session.execute(select(Booking))
    """

    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)

            # If result is a query, optimize it
            if isinstance(result, Select) and relationships:
                result = QueryOptimizer.eager_load_relationships(result, relationships, strategy)

            return result

        return wrapper

    return decorator
