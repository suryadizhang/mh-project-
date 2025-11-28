"""
CRUD API endpoints for addon items management
Supports Create, Read, Update, Delete operations for addon_items table
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import AddonItem

router = APIRouter(prefix="/addon-items", tags=["addon-items"])


# Pydantic schemas
class AddonItemCreate(BaseModel):
    """Schema for creating an addon item"""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: float = Field(..., ge=0)
    category: str = Field(
        ..., pattern="^(protein_upgrades|enhancements|equipment|entertainment|beverages)$"
    )
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)


class AddonItemUpdate(BaseModel):
    """Schema for updating an addon item"""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    price: float | None = Field(None, ge=0)
    category: str | None = Field(
        None, pattern="^(protein_upgrades|enhancements|equipment|entertainment|beverages)$"
    )
    is_active: bool | None = None
    display_order: int | None = Field(None, ge=0)


class AddonItemResponse(BaseModel):
    """Schema for addon item response"""

    id: UUID
    name: str
    description: str | None
    price: float
    category: str
    is_active: bool
    display_order: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[AddonItemResponse])
async def get_addon_items(
    active_only: bool = False, session: AsyncSession = Depends(get_async_session)
):
    """
    Get all addon items

    Args:
        active_only: If True, only return active items
        session: Database session

    Returns:
        List of addon items
    """
    query = select(AddonItem)

    if active_only:
        query = query.where(AddonItem.is_active == True)

    query = query.order_by(AddonItem.display_order, AddonItem.name)

    result = await session.execute(query)
    items = result.scalars().all()

    return [
        AddonItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            price=float(item.price),
            category=item.category,
            is_active=item.is_active,
            display_order=item.display_order,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
        )
        for item in items
    ]


@router.get("/{item_id}", response_model=AddonItemResponse)
async def get_addon_item(item_id: UUID, session: AsyncSession = Depends(get_async_session)):
    """
    Get a specific addon item by ID

    Args:
        item_id: Addon item UUID
        session: Database session

    Returns:
        Addon item details
    """
    result = await session.execute(select(AddonItem).where(AddonItem.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon item {item_id} not found"
        )

    return AddonItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=float(item.price),
        category=item.category,
        is_active=item.is_active,
        display_order=item.display_order,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


@router.post("", response_model=AddonItemResponse, status_code=status.HTTP_201_CREATED)
async def create_addon_item(
    data: AddonItemCreate, session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new addon item

    Args:
        data: Addon item creation data
        session: Database session

    Returns:
        Created addon item
    """
    item = AddonItem(
        name=data.name,
        description=data.description,
        price=data.price,
        category=data.category,
        is_active=data.is_active,
        display_order=data.display_order,
    )

    session.add(item)
    await session.commit()
    await session.refresh(item)

    return AddonItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=float(item.price),
        category=item.category,
        is_active=item.is_active,
        display_order=item.display_order,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


@router.put("/{item_id}", response_model=AddonItemResponse)
async def update_addon_item(
    item_id: UUID, data: AddonItemUpdate, session: AsyncSession = Depends(get_async_session)
):
    """
    Update an existing addon item

    Args:
        item_id: Addon item UUID
        data: Update data
        session: Database session

    Returns:
        Updated addon item
    """
    result = await session.execute(select(AddonItem).where(AddonItem.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon item {item_id} not found"
        )

    # Update only provided fields
    if data.name is not None:
        item.name = data.name
    if data.description is not None:
        item.description = data.description
    if data.price is not None:
        item.price = data.price
    if data.category is not None:
        item.category = data.category
    if data.is_active is not None:
        item.is_active = data.is_active
    if data.display_order is not None:
        item.display_order = data.display_order

    await session.commit()
    await session.refresh(item)

    return AddonItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=float(item.price),
        category=item.category,
        is_active=item.is_active,
        display_order=item.display_order,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_addon_item(item_id: UUID, session: AsyncSession = Depends(get_async_session)):
    """
    Delete an addon item

    Args:
        item_id: Addon item UUID
        session: Database session
    """
    result = await session.execute(select(AddonItem).where(AddonItem.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon item {item_id} not found"
        )

    await session.delete(item)
    await session.commit()
