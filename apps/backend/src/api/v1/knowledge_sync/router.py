"""
Knowledge Sync Router - API endpoints for auto-sync functionality
================================================================

Endpoints:
  - GET  /api/v1/knowledge/sync/status - Check sync status for all sources
  - POST /api/v1/knowledge/sync/auto - Trigger auto-sync
  - POST /api/v1/knowledge/sync/force - Force override conflicts (superadmin)
  - GET  /api/v1/knowledge/sync/diff/{source} - Show differences for specific source

Security: All endpoints require superadmin role
"""

from datetime import datetime
from typing import Dict, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Dependencies
from core.database import get_db
from services.knowledge_sync_service import KnowledgeSyncService
# TODO: Import auth dependencies
# from api.v1.auth.dependencies import require_superadmin

router = APIRouter(
    prefix="/sync",
    tags=["Knowledge Sync"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    menu: Dict
    faqs: Dict
    terms: Dict
    overall_status: Literal['synced', 'needs_sync', 'conflicts']
    timestamp: str


class SyncActionRequest(BaseModel):
    """Request model for sync actions"""
    sources: list[Literal['menu', 'faqs', 'terms']] | None = None  # None = all sources
    force: bool = False


class SyncActionResponse(BaseModel):
    """Response model for sync actions"""
    success: bool
    menu: Dict | None = None
    faqs: Dict | None = None
    terms: Dict | None = None
    overall_success: bool
    message: str
    timestamp: str


class DiffResponse(BaseModel):
    """Response model for showing differences"""
    source: Literal['menu', 'faqs', 'terms']
    file_hash: str
    changed: bool
    added: list[Dict]
    modified: list[Dict]
    deleted: list[Dict]
    conflicts: list[Dict]
    summary: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: Session = Depends(get_db),
    # current_user = Depends(require_superadmin)  # TODO: Uncomment when auth ready
):
    """
    Check sync status for all three knowledge sources
    
    Returns:
        - Overall sync status (synced, needs_sync, conflicts)
        - Detailed status for each source (menu, FAQs, terms)
        - File hashes and change summaries
    
    Security: Requires superadmin role
    """
    try:
        # Get workspace root (go up from backend/src to repo root)
        import os
        from pathlib import Path
        import logging
        logger = logging.getLogger(__name__)
        
        workspace_root = Path(__file__).parent.parent.parent.parent.parent
        logger.info(f"🔍 DEBUG: workspace_root = {workspace_root}")
        logger.info(f"🔍 DEBUG: workspace_root.exists() = {workspace_root.exists()}")
        
        sync_service = KnowledgeSyncService(db, str(workspace_root))
        logger.info(f"🔍 DEBUG: KnowledgeSyncService created successfully")
        
        status = sync_service.get_sync_status()
        logger.info(f"🔍 DEBUG: get_sync_status() returned: {status}")
        
        return SyncStatusResponse(**status)
    except Exception as e:
        import traceback
        traceback.print_exc()  # Log full error for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/auto", response_model=SyncActionResponse)
async def trigger_auto_sync(
    request: SyncActionRequest,
    db: Session = Depends(get_db),
    # current_user = Depends(require_superadmin)  # TODO: Uncomment when auth ready
):
    """
    Trigger automatic sync for specified sources (or all)
    
    Args:
        request.sources: List of sources to sync ('menu', 'faqs', 'terms') or None for all
        request.force: If True, override conflicts (use with caution!)
    
    Returns:
        - Success status for each source
        - Number of items added/modified/deleted
        - Error messages if any
    
    Security: Requires superadmin role
    
    Notes:
        - Auto-sync will PAUSE if conflicts detected (unless force=True)
        - Conflicts occur when DB items were manually edited AND file changed
        - Use force=True carefully - it will overwrite manual DB edits
    """
    try:
        # Get workspace root
        from pathlib import Path
        workspace_root = Path(__file__).parent.parent.parent.parent.parent
        
        sync_service = KnowledgeSyncService(db, str(workspace_root))
        
        # Determine which sources to sync
        sources = request.sources or ['menu', 'faqs', 'terms']
        
        if len(sources) == 3:
            # Sync all sources at once
            result = sync_service.sync_all(force=request.force)
            return SyncActionResponse(
                success=result['overall_success'],
                menu=result['menu'],
                faqs=result['faqs'],
                terms=result['terms'],
                overall_success=result['overall_success'],
                message=f"Synced {len(sources)} sources",
                timestamp=result['timestamp']
            )
        else:
            # Sync specific sources
            results = {}
            overall_success = True
            
            for source in sources:
                if source == 'menu':
                    changes = sync_service.detect_menu_changes()
                    results['menu'] = sync_service.auto_sync_menu(changes, force=request.force)
                    overall_success = overall_success and results['menu']['success']
                    
                elif source == 'faqs':
                    changes = sync_service.detect_faq_changes()
                    results['faqs'] = sync_service.auto_sync_faqs(changes, force=request.force)
                    overall_success = overall_success and results['faqs']['success']
                    
                elif source == 'terms':
                    changes = sync_service.detect_terms_changes()
                    results['terms'] = sync_service.auto_sync_terms(changes, force=request.force)
                    overall_success = overall_success and results['terms']['success']
            
            return SyncActionResponse(
                success=overall_success,
                menu=results.get('menu'),
                faqs=results.get('faqs'),
                terms=results.get('terms'),
                overall_success=overall_success,
                message=f"Synced {len(sources)} sources",
                timestamp=datetime.utcnow().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger auto-sync: {str(e)}"
        )


@router.post("/force", response_model=SyncActionResponse)
async def force_sync_override(
    request: SyncActionRequest,
    db: Session = Depends(get_db),
    # current_user = Depends(require_superadmin)  # TODO: Uncomment when auth ready
):
    """
    Force sync with conflict override (SUPERADMIN ONLY - USE WITH CAUTION!)
    
    This endpoint will:
    1. Detect changes from TypeScript files
    2. OVERRIDE any manual DB edits (force=True)
    3. Apply file changes to database
    
    ⚠️ WARNING: This will OVERWRITE manual edits made via admin UI!
    
    Use cases:
        - File changes are authoritative (e.g., developer updated pricing)
        - Manual DB edits were mistakes
        - Need to reset DB to match source files
    
    Security: Requires superadmin role with additional confirmation
    """
    # Force the force flag to True for this endpoint
    request.force = True
    
    # Log this action for audit purposes
    # TODO: Add audit logging
    # logger.warning(f"Force sync triggered by superadmin {current_user.id}")
    
    return await trigger_auto_sync(request, db)


@router.get("/diff/{source}", response_model=DiffResponse)
async def get_sync_diff(
    source: Literal['menu', 'faqs', 'terms'],
    db: Session = Depends(get_db),
    # current_user = Depends(require_superadmin)  # TODO: Uncomment when auth ready
):
    """
    Get detailed differences for a specific source
    
    Shows:
        - Items added in file (not in DB)
        - Items modified (file differs from DB)
        - Items deleted (removed from file but still in DB)
        - Conflicts (manual DB edits + file changes)
    
    Useful for:
        - Reviewing changes before syncing
        - Debugging sync conflicts
        - Audit trail of what changed
    
    Security: Requires superadmin role
    """
    try:
        # Get workspace root
        from pathlib import Path
        workspace_root = Path(__file__).parent.parent.parent.parent.parent
        
        sync_service = KnowledgeSyncService(db, str(workspace_root))
        
        if source == 'menu':
            changes = sync_service.detect_menu_changes()
        elif source == 'faqs':
            changes = sync_service.detect_faq_changes()
        elif source == 'terms':
            changes = sync_service.detect_terms_changes()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source: {source}. Must be 'menu', 'faqs', or 'terms'"
            )
        
        return DiffResponse(source=source, **changes)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get diff for {source}: {str(e)}"
        )


# ============================================================================
# UTILITY ENDPOINTS (for debugging/monitoring)
# ============================================================================

@router.get("/health")
async def sync_service_health():
    """
    Health check for sync service
    
    Returns:
        - Service status
        - File paths being monitored
        - Last check timestamp
    """
    return {
        "status": "healthy",
        "service": "knowledge_sync",
        "monitored_files": {
            "menu": "apps/customer/src/app/menu/page.tsx",
            "faqs": "apps/customer/src/data/faqsData.ts",
            "terms": "apps/customer/src/app/terms/page.tsx"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
