"""
Base Repository Pattern Implementation
Generic repository with CRUD operations and query builders
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

# Type variables
TModel = TypeVar("TModel")  # SQLAlchemy model
TCreate = TypeVar("TCreate", bound=BaseModel)  # Pydantic create schema
TUpdate = TypeVar("TUpdate", bound=BaseModel)  # Pydantic update schema


@dataclass
class QueryResult(Generic[TModel]):
    """Query result with metadata"""

    items: list[TModel]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


@dataclass
class FilterCriteria:
    """Generic filter criteria"""

    field: str
    operator: str  # eq, ne, lt, le, gt, ge, in, like, ilike
    value: Any


@dataclass
class SortCriteria:
    """Sort criteria"""

    field: str
    direction: str = "asc"  # asc, desc


class IRepository(Generic[TModel], ABC):
    """Repository interface"""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> TModel | None:
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: list[FilterCriteria] | None = None,
        sort: list[SortCriteria] | None = None,
    ) -> QueryResult[TModel]:
        pass

    @abstractmethod
    async def create(self, entity: TModel) -> TModel:
        pass

    @abstractmethod
    async def update(self, entity: TModel) -> TModel:
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass


class BaseRepository(IRepository[TModel]):
    """
    Generic base repository with common CRUD operations

    Features:
    - Generic CRUD operations
    - Dynamic filtering and sorting
    - Pagination with metadata
    - Eager loading support
    - Query builder pattern
    - Soft delete support
    - Audit field management
    """

    def __init__(self, db: AsyncSession, model: type[TModel], soft_delete: bool = False):
        self.db = db
        self.model = model
        self.soft_delete = soft_delete

    # Basic CRUD Operations

    async def get_by_id(self, id: UUID, eager_load: list[str] | None = None) -> TModel | None:
        """Get entity by ID with optional eager loading"""
        query = select(self.model).where(self.model.id == id)

        # Add eager loading
        if eager_load:
            for relation in eager_load:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))

        # Apply soft delete filter
        if self.soft_delete and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: list[FilterCriteria] | None = None,
        sort: list[SortCriteria] | None = None,
        eager_load: list[str] | None = None,
    ) -> QueryResult[TModel]:
        """Get paginated list with filtering and sorting"""

        # Build base query
        query = select(self.model)
        count_query = select(func.count(self.model.id))

        # Apply soft delete filter
        if self.soft_delete and hasattr(self.model, "deleted_at"):
            base_filter = self.model.deleted_at.is_(None)
            query = query.where(base_filter)
            count_query = count_query.where(base_filter)

        # Apply filters
        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            query = query.where(and_(*filter_conditions))
            count_query = count_query.where(and_(*filter_conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        # Apply sorting
        if sort:
            for sort_criteria in sort:
                if hasattr(self.model, sort_criteria.field):
                    field = getattr(self.model, sort_criteria.field)
                    if sort_criteria.direction.lower() == "desc":
                        query = query.order_by(field.desc())
                    else:
                        query = query.order_by(field.asc())
        # Default sort by created_at if available
        elif hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())

        # Apply eager loading
        if eager_load:
            for relation in eager_load:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        items = result.scalars().all()

        # Calculate pagination metadata
        page = (skip // limit) + 1 if limit > 0 else 1
        has_next = skip + limit < total_count
        has_prev = skip > 0

        return QueryResult(
            items=items,
            total_count=total_count,
            page=page,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def create(self, entity: TModel) -> TModel:
        """Create new entity"""
        # Set audit fields if available
        if hasattr(entity, "created_at") and not entity.created_at:
            entity.created_at = datetime.utcnow()
        if hasattr(entity, "updated_at"):
            entity.updated_at = datetime.utcnow()

        self.db.add(entity)
        await self.db.flush()  # Flush to get ID
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: TModel) -> TModel:
        """Update existing entity"""
        # Set audit fields if available
        if hasattr(entity, "updated_at"):
            entity.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, id: UUID) -> bool:
        """Delete entity (soft delete if enabled)"""
        entity = await self.get_by_id(id)
        if not entity:
            return False

        if self.soft_delete and hasattr(entity, "deleted_at"):
            # Soft delete
            entity.deleted_at = datetime.utcnow()
            await self.db.flush()
        else:
            # Hard delete
            await self.db.delete(entity)
            await self.db.flush()

        return True

    # Query Builder Methods

    def query(self) -> "QueryBuilder[TModel]":
        """Get a query builder for complex queries"""
        return QueryBuilder(self.db, self.model, self.soft_delete)

    async def exists(self, filters: list[FilterCriteria]) -> bool:
        """Check if entity exists with given filters"""
        query = select(func.count(self.model.id))

        if self.soft_delete and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            query = query.where(and_(*filter_conditions))

        result = await self.db.execute(query)
        count = result.scalar()
        return count > 0

    async def count(self, filters: list[FilterCriteria] | None = None) -> int:
        """Count entities with optional filters"""
        query = select(func.count(self.model.id))

        if self.soft_delete and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            query = query.where(and_(*filter_conditions))

        result = await self.db.execute(query)
        return result.scalar()

    async def find_one(
        self, filters: list[FilterCriteria], eager_load: list[str] | None = None
    ) -> TModel | None:
        """Find single entity by filters"""
        query = select(self.model)

        if self.soft_delete and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        filter_conditions = self._build_filter_conditions(filters)
        query = query.where(and_(*filter_conditions))

        # Add eager loading
        if eager_load:
            for relation in eager_load:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def bulk_create(self, entities: list[TModel]) -> list[TModel]:
        """Bulk create entities"""
        for entity in entities:
            if hasattr(entity, "created_at") and not entity.created_at:
                entity.created_at = datetime.utcnow()
            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.utcnow()

        self.db.add_all(entities)
        await self.db.flush()

        # Refresh entities to get IDs
        for entity in entities:
            await self.db.refresh(entity)

        return entities

    async def bulk_update(self, filters: list[FilterCriteria], update_data: dict[str, Any]) -> int:
        """Bulk update entities matching filters"""
        if hasattr(self.model, "updated_at"):
            update_data["updated_at"] = datetime.utcnow()

        query = update(self.model)

        if self.soft_delete and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            query = query.where(and_(*filter_conditions))

        query = query.values(**update_data)
        result = await self.db.execute(query)
        await self.db.flush()

        return result.rowcount

    # Private helper methods

    def _build_filter_conditions(self, filters: list[FilterCriteria]) -> list:
        """Build SQLAlchemy filter conditions from filter criteria"""
        conditions = []

        for filter_criteria in filters:
            if not hasattr(self.model, filter_criteria.field):
                logger.warning(f"Field {filter_criteria.field} not found in {self.model.__name__}")
                continue

            field = getattr(self.model, filter_criteria.field)
            operator = filter_criteria.operator.lower()
            value = filter_criteria.value

            if operator == "eq":
                conditions.append(field == value)
            elif operator == "ne":
                conditions.append(field != value)
            elif operator == "lt":
                conditions.append(field < value)
            elif operator == "le":
                conditions.append(field <= value)
            elif operator == "gt":
                conditions.append(field > value)
            elif operator == "ge":
                conditions.append(field >= value)
            elif operator == "in":
                if isinstance(value, list | tuple):
                    conditions.append(field.in_(value))
            elif operator == "like":
                conditions.append(field.like(f"%{value}%"))
            elif operator == "ilike":
                conditions.append(field.ilike(f"%{value}%"))
            elif operator == "is_null":
                conditions.append(field.is_(None))
            elif operator == "is_not_null":
                conditions.append(field.is_not(None))
            else:
                logger.warning(f"Unknown operator: {operator}")

        return conditions


class QueryBuilder(Generic[TModel]):
    """Fluent query builder for complex queries"""

    def __init__(self, db: AsyncSession, model: type[TModel], soft_delete: bool = False):
        self.db = db
        self.model = model
        self.soft_delete = soft_delete
        self._query: Select = select(model)
        self._applied_soft_delete = False

        # Apply soft delete filter by default
        if self.soft_delete and hasattr(self.model, "deleted_at"):
            self._query = self._query.where(self.model.deleted_at.is_(None))
            self._applied_soft_delete = True

    def where(self, *conditions) -> "QueryBuilder[TModel]":
        """Add where conditions"""
        self._query = self._query.where(and_(*conditions))
        return self

    def filter_by(self, **kwargs) -> "QueryBuilder[TModel]":
        """Filter by field values"""
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                self._query = self._query.where(getattr(self.model, field) == value)
        return self

    def order_by(self, *fields) -> "QueryBuilder[TModel]":
        """Add ordering"""
        self._query = self._query.order_by(*fields)
        return self

    def limit(self, limit: int) -> "QueryBuilder[TModel]":
        """Add limit"""
        self._query = self._query.limit(limit)
        return self

    def offset(self, offset: int) -> "QueryBuilder[TModel]":
        """Add offset"""
        self._query = self._query.offset(offset)
        return self

    def join(self, *props, **kwargs) -> "QueryBuilder[TModel]":
        """Add join"""
        self._query = self._query.join(*props, **kwargs)
        return self

    def options(self, *opts) -> "QueryBuilder[TModel]":
        """Add query options (like eager loading)"""
        self._query = self._query.options(*opts)
        return self

    def eager_load(self, *relations) -> "QueryBuilder[TModel]":
        """Add eager loading for relations"""
        options = []
        for relation in relations:
            if hasattr(self.model, relation):
                options.append(selectinload(getattr(self.model, relation)))
        if options:
            self._query = self._query.options(*options)
        return self

    async def first(self) -> TModel | None:
        """Get first result"""
        result = await self.db.execute(self._query)
        return result.scalar_one_or_none()

    async def all(self) -> list[TModel]:
        """Get all results"""
        result = await self.db.execute(self._query)
        return result.scalars().all()

    async def count(self) -> int:
        """Get count of results"""
        count_query = select(func.count()).select_from(self._query.subquery())
        result = await self.db.execute(count_query)
        return result.scalar()

    async def exists(self) -> bool:
        """Check if any results exist"""
        count = await self.count()
        return count > 0

    def to_sql(self) -> str:
        """Get SQL representation (for debugging)"""
        return str(self._query.compile(compile_kwargs={"literal_binds": True}))
