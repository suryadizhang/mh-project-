# 🚀 QUICK FIX: Circular Import Resolution

## Issue Identified

The main backend has a circular import between `app/main.py` and
`app/routers/webhooks.py`.

## Solution

Move the shared `chat_ingest` function to a separate service module.

## Implementation (30 seconds):

### 1. Create `app/services/chat_service.py`:

```python
"""
Shared chat processing service
"""
from app.schemas import ChatIngestRequest, ChatResponse
from app.services.ai_pipeline import ai_pipeline
from sqlalchemy.ext.asyncio import AsyncSession

async def process_chat_message(
    request: ChatIngestRequest,
    session: AsyncSession
) -> ChatResponse:
    """Process chat message through AI pipeline"""
    return await ai_pipeline.process_message(
        message=request.message,
        user_id=request.user_id,
        session_id=request.session_id,
        channel=request.channel,
        session=session
    )
```

### 2. Update imports in both files:

- **main.py:**
  `from app.services.chat_service import process_chat_message`
- **webhooks.py:**
  `from app.services.chat_service import process_chat_message`

### 3. Replace function calls:

Replace `chat_ingest()` with `process_chat_message()` in both files.

## Result

✅ Circular import resolved ✅ Main backend will start successfully ✅
All functionality preserved

**Estimated fix time:** 2-3 minutes
