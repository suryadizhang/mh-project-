"""
Customer management endpoints
Admin users get 100-200 requests/minute vs 20 for public
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from api.deps import get_current_admin_user, AdminUser
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class CustomerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$")
    address_line1: Optional[str] = Field(None, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5}(-\d{4})?$")
    dietary_restrictions: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)
    status: CustomerStatus = CustomerStatus.ACTIVE

class CustomerCreate(CustomerBase):
    sms_consent: bool = False
    email_consent: bool = False

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$")
    address_line1: Optional[str] = Field(None, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5}(-\d{4})?$")
    dietary_restrictions: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[CustomerStatus] = None

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    total_bookings: int = 0
    total_spent: float = 0.0
    last_booking_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CustomerSearchResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# Mock data storage (replace with actual database operations)
mock_customers = [
    {
        "id": 1,
        "first_name": "John",
        "last_name": "Smith", 
        "email": "john.smith@example.com",
        "phone": "+19165551234",
        "city": "Sacramento",
        "state": "CA",
        "status": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "total_bookings": 3,
        "total_spent": 1250.00,
        "last_booking_date": datetime.now()
    },
    {
        "id": 2,
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "sarah.j@example.com", 
        "phone": "+19165555678",
        "city": "Fremont",
        "state": "CA",
        "status": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "total_bookings": 1,
        "total_spent": 450.00,
        "last_booking_date": datetime.now()
    }
]

@router.get("/", response_model=CustomerSearchResponse)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[CustomerStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    List customers with pagination and search
    Admin rate limit: 100 requests/minute
    """
    try:
        # Apply search filters to mock data
        filtered_customers = mock_customers.copy()
        
        if search:
            search_lower = search.lower()
            filtered_customers = [
                c for c in filtered_customers
                if (search_lower in c["first_name"].lower() or 
                    search_lower in c["last_name"].lower() or
                    search_lower in (c["email"] or "").lower() or
                    search_lower in (c["phone"] or ""))
            ]
        
        if status:
            filtered_customers = [c for c in filtered_customers if c["status"] == status]
        
        # Apply pagination
        total = len(filtered_customers)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        customers_page = filtered_customers[start_idx:end_idx]
        
        total_pages = (total + per_page - 1) // per_page
        
        logger.info(f"Admin {current_admin.email} listed customers - page {page}, found {total} total")
        
        return CustomerSearchResponse(
            customers=[CustomerResponse(**c) for c in customers_page],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customers"
        )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get specific customer by ID
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find customer in mock data
        customer = next((c for c in mock_customers if c["id"] == customer_id), None)
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found"
            )
        
        logger.info(f"Admin {current_admin.email} retrieved customer {customer_id}")
        return CustomerResponse(**customer)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer"
        )

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Create new customer
    Admin rate limit: 100 requests/minute
    """
    try:
        # Create new customer (mock implementation)
        new_id = max([c["id"] for c in mock_customers], default=0) + 1
        new_customer = {
            "id": new_id,
            **customer.dict(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "total_bookings": 0,
            "total_spent": 0.0,
            "last_booking_date": None
        }
        
        mock_customers.append(new_customer)
        
        logger.info(f"Admin {current_admin.email} created customer {new_id}: {customer.first_name} {customer.last_name}")
        return CustomerResponse(**new_customer)
    
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Update existing customer
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find and update customer in mock data
        customer_idx = next((i for i, c in enumerate(mock_customers) if c["id"] == customer_id), None)
        
        if customer_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found"
            )
        
        # Update fields
        update_data = customer_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        mock_customers[customer_idx].update(update_data)
        
        logger.info(f"Admin {current_admin.email} updated customer {customer_id}")
        return CustomerResponse(**mock_customers[customer_idx])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Delete customer (soft delete)
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find customer in mock data
        customer_idx = next((i for i, c in enumerate(mock_customers) if c["id"] == customer_id), None)
        
        if customer_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found"
            )
        
        # Soft delete by setting status to inactive
        mock_customers[customer_idx]["status"] = "inactive"
        mock_customers[customer_idx]["updated_at"] = datetime.now()
        
        logger.info(f"Admin {current_admin.email} deleted customer {customer_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer"
        )

@router.get("/{customer_id}/bookings")
async def get_customer_bookings(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get all bookings for a specific customer
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find customer first
        customer = next((c for c in mock_customers if c["id"] == customer_id), None)
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found"
            )
        
        # Mock bookings data
        mock_bookings = [
            {
                "id": 1,
                "customer_id": customer_id,
                "event_date": "2025-10-15T18:00:00",
                "guest_count": 8,
                "menu_type": "Hibachi Dinner",
                "total_amount": 450.00,
                "status": "confirmed",
                "created_at": datetime.now()
            }
        ]
        
        logger.info(f"Admin {current_admin.email} retrieved bookings for customer {customer_id}")
        return mock_bookings
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer bookings {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer bookings"
        )