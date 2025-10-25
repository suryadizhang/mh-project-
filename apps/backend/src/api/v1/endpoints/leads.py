"""
Lead management endpoints
Admin users get 100-200 requests/minute vs 20 for public
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from api.deps import get_current_admin_user, AdminUser
from api.app.services.lead_service import LeadService
from api.app.models.lead_newsletter import LeadStatus, LeadSource, LeadQuality
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from enum import Enum
from uuid import UUID

class LeadBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$")
    event_date: Optional[datetime] = None
    guest_count: Optional[int] = Field(None, ge=1, le=500)
    event_location: Optional[str] = Field(None, max_length=200)
    budget_range: Optional[str] = Field(None, max_length=50)
    message: Optional[str] = Field(None, max_length=1000)
    source: LeadSource = LeadSource.WEBSITE
    status: LeadStatus = LeadStatus.NEW
    notes: Optional[str] = Field(None, max_length=2000)

class LeadCreate(LeadBase):
    sms_consent: bool = False
    email_consent: bool = False

class LeadUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$")
    event_date: Optional[datetime] = None
    guest_count: Optional[int] = Field(None, ge=1, le=500)
    event_location: Optional[str] = Field(None, max_length=200)
    budget_range: Optional[str] = Field(None, max_length=50)
    message: Optional[str] = Field(None, max_length=1000)
    source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = Field(None, max_length=2000)

class LeadResponse(LeadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_contact_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    conversion_probability: int = 0  # 0-100%
    
    class Config:
        from_attributes = True

class LeadSearchResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class LeadPipelineStats(BaseModel):
    new: int = 0
    contacted: int = 0
    qualified: int = 0
    quoted: int = 0
    negotiating: int = 0
    won: int = 0
    lost: int = 0
    total_value: float = 0.0
    conversion_rate: float = 0.0

# Mock data storage (replace with actual database operations)
mock_leads = [
    {
        "id": 1,
        "first_name": "Mike",
        "last_name": "Davis",
        "email": "mike.davis@example.com",
        "phone": "+19165551111",
        "event_date": datetime(2025, 10, 20, 19, 0),
        "guest_count": 12,
        "event_location": "Sacramento, CA",
        "budget_range": "$800-1200",
        "source": "website",
        "status": "qualified",
        "message": "Looking for hibachi dinner for anniversary party",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "last_contact_date": datetime.now(),
        "assigned_to": "admin@myhibachichef.com",
        "conversion_probability": 75
    },
    {
        "id": 2,
        "first_name": "Jennifer",
        "last_name": "Wilson",
        "email": "jwilson@example.com",
        "phone": "+19165552222",
        "event_date": datetime(2025, 11, 5, 18, 30),
        "guest_count": 6,
        "event_location": "Fremont, CA",
        "budget_range": "$400-600",
        "source": "instagram",
        "status": "contacted",
        "message": "Birthday party for my husband",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "last_contact_date": None,
        "assigned_to": None,
        "conversion_probability": 50
    },
    {
        "id": 3,
        "first_name": "Robert",
        "last_name": "Kim",
        "email": "robert.kim@example.com",
        "phone": "+19165553333",
        "event_date": datetime(2025, 10, 25, 17, 0),
        "guest_count": 20,
        "event_location": "San Jose, CA", 
        "budget_range": "$1500-2000",
        "source": "referral",
        "status": "quoted",
        "message": "Corporate team building event",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "last_contact_date": datetime.now(),
        "assigned_to": "owner@myhibachichef.com",
        "conversion_probability": 85
    }
]

@router.get("/", response_model=LeadSearchResponse)
async def list_leads(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[LeadStatus] = Query(None, description="Filter by status"),
    source: Optional[LeadSource] = Query(None, description="Filter by source"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    List leads with pagination and search
    Admin rate limit: 100 requests/minute
    """
    try:
        # Apply search filters to mock data
        filtered_leads = mock_leads.copy()
        
        if search:
            search_lower = search.lower()
            filtered_leads = [
                l for l in filtered_leads
                if (search_lower in l["first_name"].lower() or 
                    search_lower in l["last_name"].lower() or
                    search_lower in (l["email"] or "").lower() or
                    search_lower in (l["phone"] or ""))
            ]
        
        if status:
            filtered_leads = [l for l in filtered_leads if l["status"] == status]
            
        if source:
            filtered_leads = [l for l in filtered_leads if l["source"] == source]
            
        if assigned_to:
            filtered_leads = [l for l in filtered_leads if l.get("assigned_to") == assigned_to]
        
        # Apply pagination
        total = len(filtered_leads)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        leads_page = filtered_leads[start_idx:end_idx]
        
        total_pages = (total + per_page - 1) // per_page
        
        logger.info(f"Admin {current_admin.email} listed leads - page {page}, found {total} total")
        
        return LeadSearchResponse(
            leads=[LeadResponse(**l) for l in leads_page],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve leads"
        )

@router.get("/pipeline/stats", response_model=LeadPipelineStats)
async def get_pipeline_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get lead pipeline statistics
    Admin rate limit: 100 requests/minute
    """
    try:
        # Calculate stats from mock data
        stats = LeadPipelineStats()
        
        for lead in mock_leads:
            status = lead["status"]
            if status == "new":
                stats.new += 1
            elif status == "contacted":
                stats.contacted += 1
            elif status == "qualified":
                stats.qualified += 1
            elif status == "quoted":
                stats.quoted += 1
            elif status == "negotiating":
                stats.negotiating += 1
            elif status == "won":
                stats.won += 1
            elif status == "lost":
                stats.lost += 1
        
        # Calculate total value and conversion rate
        total_leads = len(mock_leads)
        if total_leads > 0:
            stats.conversion_rate = (stats.won / total_leads) * 100
        
        # Mock total value calculation
        stats.total_value = 5750.00  # Sum of potential values
        
        logger.info(f"Admin {current_admin.email} retrieved pipeline stats")
        return stats
    
    except Exception as e:
        logger.error(f"Error getting pipeline stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline stats"
        )

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get specific lead by ID
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find lead in mock data
        lead = next((l for l in mock_leads if l["id"] == lead_id), None)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        logger.info(f"Admin {current_admin.email} retrieved lead {lead_id}")
        return LeadResponse(**lead)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lead"
        )

@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Create new lead
    Admin rate limit: 100 requests/minute
    """
    try:
        # Create new lead (mock implementation)
        new_id = max([l["id"] for l in mock_leads], default=0) + 1
        new_lead = {
            "id": new_id,
            **lead.dict(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_contact_date": None,
            "assigned_to": current_admin.email,
            "conversion_probability": 25  # Default for new leads
        }
        
        mock_leads.append(new_lead)
        
        logger.info(f"Admin {current_admin.email} created lead {new_id}: {lead.first_name} {lead.last_name}")
        return LeadResponse(**new_lead)
    
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead"
        )

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Update existing lead
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find and update lead in mock data
        lead_idx = next((i for i, l in enumerate(mock_leads) if l["id"] == lead_id), None)
        
        if lead_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Update fields
        update_data = lead_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        # Update conversion probability based on status
        if "status" in update_data:
            status_probabilities = {
                "new": 25,
                "contacted": 40,
                "qualified": 60,
                "quoted": 75,
                "negotiating": 85,
                "won": 100,
                "lost": 0
            }
            update_data["conversion_probability"] = status_probabilities.get(update_data["status"], 25)
        
        mock_leads[lead_idx].update(update_data)
        
        logger.info(f"Admin {current_admin.email} updated lead {lead_id}")
        return LeadResponse(**mock_leads[lead_idx])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead"
        )

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Delete lead
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find and remove lead from mock data
        lead_idx = next((i for i, l in enumerate(mock_leads) if l["id"] == lead_id), None)
        
        if lead_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        mock_leads.pop(lead_idx)
        
        logger.info(f"Admin {current_admin.email} deleted lead {lead_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lead"
        )

@router.post("/{lead_id}/assign")
async def assign_lead(
    lead_id: int,
    assigned_to: str = Query(..., description="Email of admin to assign to"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Assign lead to admin user
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find lead in mock data
        lead_idx = next((i for i, l in enumerate(mock_leads) if l["id"] == lead_id), None)
        
        if lead_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {lead_id} not found"
            )
        
        # Update assignment
        mock_leads[lead_idx]["assigned_to"] = assigned_to
        mock_leads[lead_idx]["updated_at"] = datetime.now()
        
        logger.info(f"Admin {current_admin.email} assigned lead {lead_id} to {assigned_to}")
        
        return {"message": f"Lead {lead_id} assigned to {assigned_to}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign lead"
        )