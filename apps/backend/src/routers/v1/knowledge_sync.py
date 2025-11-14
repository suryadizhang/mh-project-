"""
Knowledge Sync API Router - Admin endpoints for knowledge base synchronization
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.knowledge_sync_service import KnowledgeSyncService
from utils.auth import require_role, UserRole


router = APIRouter(prefix="/api/v1/ai/knowledge/sync", tags=["Knowledge Sync"])


# =====================================================================
# Request/Response Models
# =====================================================================

class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    menu: dict
    faqs: dict
    terms: dict
    overall_status: str = Field(..., description="synced | needs_sync | conflicts")
    timestamp: str


class SyncTriggerRequest(BaseModel):
    """Request model for triggering sync"""
    force: bool = Field(default=False, description="Override conflicts (superadmin only)")
    sources: Optional[list[str]] = Field(
        default=None,
        description="Specific sources to sync (menu, faqs, terms). If None, sync all."
    )


class SyncResultResponse(BaseModel):
    """Response model for sync operation result"""
    success: bool
    menu: Optional[dict] = None
    faqs: Optional[dict] = None
    terms: Optional[dict] = None
    overall_success: bool
    timestamp: str
    message: str


class DiffResponse(BaseModel):
    """Response model for detecting changes"""
    menu: dict
    faqs: dict
    terms: dict
    has_changes: bool
    has_conflicts: bool
    timestamp: str


class SyncHistoryResponse(BaseModel):
    """Response model for sync history"""
    records: list[dict]
    total: int
    page: int
    page_size: int
    timestamp: str


# =====================================================================
# API Endpoints
# =====================================================================

@router.get(
    "/status",
    response_model=SyncStatusResponse,
    summary="Get Knowledge Sync Status",
    description="Get current sync status for all knowledge sources (menu, FAQs, terms)",
)
async def get_sync_status(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """
    Get current synchronization status for all knowledge sources.
    
    Returns:
        - Current state of each source (synced, changed, conflicts)
        - Overall sync status
        - Timestamp of last check
    
    Requires: Admin or Superadmin role
    """
    try:
        sync_service = KnowledgeSyncService(session)
        status = sync_service.get_sync_status()
        
        return SyncStatusResponse(
            menu=status['menu'],
            faqs=status['faqs'],
            terms=status['terms'],
            overall_status=status['overall_status'],
            timestamp=status['timestamp']
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to get sync status",
                "error": str(e)
            }
        )


@router.get(
    "/diff",
    response_model=DiffResponse,
    summary="Get Knowledge Changes (Diff)",
    description="Detect changes between source files and database without syncing",
)
async def get_sync_diff(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """
    Get detailed diff of changes for all knowledge sources.
    
    Returns:
        - Detailed changes for each source
        - Added/modified/deleted items
        - Conflicts that need resolution
    
    Requires: Admin or Superadmin role
    """
    try:
        sync_service = KnowledgeSyncService(session)
        
        menu_changes = sync_service.detect_menu_changes()
        faq_changes = sync_service.detect_faq_changes()
        terms_changes = sync_service.detect_terms_changes()
        
        has_changes = any([
            menu_changes.get('changed'),
            faq_changes.get('changed'),
            terms_changes.get('changed')
        ])
        
        has_conflicts = any([
            len(menu_changes.get('conflicts', [])) > 0,
            len(faq_changes.get('conflicts', [])) > 0,
            len(terms_changes.get('conflicts', [])) > 0
        ])
        
        return DiffResponse(
            menu=menu_changes,
            faqs=faq_changes,
            terms=terms_changes,
            has_changes=has_changes,
            has_conflicts=has_conflicts,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to get sync diff",
                "error": str(e)
            }
        )


@router.post(
    "/trigger",
    response_model=SyncResultResponse,
    summary="Trigger Knowledge Sync",
    description="Manually trigger synchronization of knowledge sources",
)
async def trigger_sync(
    request: SyncTriggerRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """
    Manually trigger knowledge synchronization.
    
    Args:
        force: If True, override conflicts (requires superadmin)
        sources: Optional list of specific sources to sync
    
    Returns:
        - Sync results for each source
        - Overall success status
        - Timestamp of sync operation
    
    Requires: 
        - Admin role for normal sync
        - Superadmin role for force sync
    """
    try:
        # Force sync requires superadmin
        if request.force and current_user.get('role') != UserRole.SUPER_ADMIN.value:
            raise HTTPException(
                status_code=403,
                detail="Force sync requires superadmin role"
            )
        
        sync_service = KnowledgeSyncService(session)
        
        # If specific sources requested
        if request.sources:
            result = {
                'overall_success': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            for source in request.sources:
                if source == 'menu':
                    changes = sync_service.detect_menu_changes()
                    result['menu'] = sync_service.auto_sync_menu(changes, request.force)
                elif source == 'faqs':
                    changes = sync_service.detect_faq_changes()
                    result['faqs'] = sync_service.auto_sync_faqs(changes, request.force)
                elif source == 'terms':
                    changes = sync_service.detect_terms_changes()
                    result['terms'] = sync_service.auto_sync_terms(changes, request.force)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid source: {source}. Must be one of: menu, faqs, terms"
                    )
            
            # Check overall success
            result['overall_success'] = all([
                r.get('success', False) 
                for k, r in result.items() 
                if k in ['menu', 'faqs', 'terms']
            ])
        else:
            # Sync all sources
            result = sync_service.sync_all(force=request.force)
        
        return SyncResultResponse(
            success=result.get('overall_success', False),
            menu=result.get('menu'),
            faqs=result.get('faqs'),
            terms=result.get('terms'),
            overall_success=result.get('overall_success', False),
            timestamp=result.get('timestamp', datetime.utcnow().isoformat()),
            message="Sync completed successfully" if result.get('overall_success') else "Sync completed with errors"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to trigger sync",
                "error": str(e)
            }
        )


@router.get(
    "/history",
    response_model=SyncHistoryResponse,
    summary="Get Sync History",
    description="Get historical sync operations with pagination",
)
async def get_sync_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source (menu, faqs, terms)"),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """
    Get paginated history of sync operations.
    
    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        - source: Filter by specific source (optional)
    
    Returns:
        - List of sync history records
        - Pagination metadata
    
    Requires: Admin or Superadmin role
    """
    try:
        sync_service = KnowledgeSyncService(session)
        
        # Get sync history from database
        # Note: This is a placeholder - implement actual database query
        # based on your SyncHistory model
        
        # For now, return empty result with proper structure
        return SyncHistoryResponse(
            records=[],
            total=0,
            page=page,
            page_size=page_size,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to get sync history",
                "error": str(e)
            }
        )


@router.post(
    "/auto",
    response_model=SyncResultResponse,
    summary="Auto Sync (Safe Mode)",
    description="Automatically sync changes without conflicts (safe mode)",
)
async def auto_sync(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """
    Automatically sync changes in safe mode.
    
    - Only syncs additions and non-conflicting updates
    - Skips any items with conflicts
    - Safe for automated/scheduled execution
    
    Returns:
        - Sync results for each source
        - Overall success status
    
    Requires: Admin or Superadmin role
    """
    try:
        sync_service = KnowledgeSyncService(session)
        result = sync_service.sync_all(force=False)
        
        return SyncResultResponse(
            success=result.get('overall_success', False),
            menu=result.get('menu'),
            faqs=result.get('faqs'),
            terms=result.get('terms'),
            overall_success=result.get('overall_success', False),
            timestamp=result.get('timestamp', datetime.utcnow().isoformat()),
            message="Auto-sync completed successfully" if result.get('overall_success') else "Auto-sync completed with skipped conflicts"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to auto-sync",
                "error": str(e)
            }
        )


@router.post(
    "/force",
    response_model=SyncResultResponse,
    summary="Force Sync (Override Conflicts)",
    description="Force sync all changes, overriding conflicts (requires superadmin)",
)
async def force_sync(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """
    Force sync all changes, overriding conflicts.
    
    - Overwrites database with source file contents
    - Resolves all conflicts in favor of source files
    - Requires superadmin role for safety
    
    ⚠️ WARNING: This will override any manual database edits
    
    Returns:
        - Sync results for each source
        - Overall success status
    
    Requires: Superadmin role only
    """
    try:
        sync_service = KnowledgeSyncService(session)
        result = sync_service.sync_all(force=True)
        
        return SyncResultResponse(
            success=result.get('overall_success', False),
            menu=result.get('menu'),
            faqs=result.get('faqs'),
            terms=result.get('terms'),
            overall_success=result.get('overall_success', False),
            timestamp=result.get('timestamp', datetime.utcnow().isoformat()),
            message="Force sync completed successfully" if result.get('overall_success') else "Force sync completed with errors"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to force sync",
                "error": str(e)
            }
        )

