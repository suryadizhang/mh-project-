# Quick Reference: Dynamic Knowledge Integration

## For Developers

### How It Works Now

**Every AI conversation**:
1. User sends message → Intent Router
2. Router calls `KnowledgeService.get_full_ai_context()`
3. Service queries database for current menu, FAQs, policies
4. Router injects `knowledge_context` into context dict
5. Agent receives context, injects into system prompt
6. AI responds with current database data

### Adding New Knowledge Domains

**1. Add to Database Schema** (`services/knowledge/models.py`)
```python
class NewKnowledgeDomain(Base):
    __tablename__ = "new_domain"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    # ... other fields
```

**2. Update KnowledgeService** (`services/knowledge/knowledge_service.py`)
```python
async def get_full_ai_context(
    self,
    include_menu: bool = True,
    include_charter: bool = True,
    include_faqs: bool = True,
    include_new_domain: bool = True,  # Add parameter
    # ... other params
) -> str:
    # ... existing code
    
    if include_new_domain:
        new_data = await self._get_new_domain_data()
        sections.append(new_data)
    
    return "\n\n".join(sections)

async def _get_new_domain_data(self) -> str:
    """Format new domain data for AI context"""
    items = self.db.query(NewKnowledgeDomain).all()
    
    formatted = "**New Domain Information:**\n\n"
    for item in items:
        formatted += f"- {item.content}\n"
    
    return formatted
```

**3. Update Intent Router Call** (optional - default True)
```python
knowledge_context = await knowledge_service.get_full_ai_context(
    include_menu=True,
    include_charter=True,
    include_faqs=True,
    include_new_domain=True,  # Add if needed
    # ... other params
)
```

**4. Agents Automatically Receive It** (no changes needed!)
- All agents already inject `knowledge_context`
- New domain data appears in their system prompts
- AI can use the new information immediately

### Testing Your Changes

**Run test suite**:
```bash
cd apps/backend
pytest src/tests/test_knowledge_integration.py -v
```

**Manual test**:
```python
from services.knowledge.knowledge_service import KnowledgeService
from core.database import get_db

db = next(get_db())
service = KnowledgeService(db, station_id=None)

context = await service.get_full_ai_context(
    include_menu=True,
    include_charter=True,
    include_faqs=True
)

print(context)  # Should include your new domain
```

---

## For Product/Admin Team

### How to Update AI Knowledge (No Code Changes!)

**Update Menu Prices**:
1. Update `packages.ts` or use Admin UI
2. Auto-sync detects change (or manual sync)
3. Database updates
4. AI immediately quotes new prices

**Update Policies**:
1. Update policy in Admin UI or database directly
2. Next AI conversation uses new policy
3. No deployment needed!

**Add New FAQs**:
1. Add to `faqs.ts` or Admin UI
2. Auto-sync detects change
3. Database updates
4. AI can answer new questions immediately

### Verifying AI Has Current Data

**Check Knowledge Sync Dashboard** (if built):
- View current menu items in database
- See last sync timestamp
- Preview what AI "knows"

**Test with Chat**:
1. Open chat interface
2. Ask: "What are your packages?"
3. Verify AI lists current menu from database
4. Update a price
5. Ask again
6. Verify AI quotes new price immediately

---

## Troubleshooting

### "AI giving old/wrong prices"

**Check**:
1. Is data synced to database?
   ```sql
   SELECT * FROM menu_items ORDER BY updated_at DESC LIMIT 10;
   ```
2. Is auto-sync running?
   ```bash
   curl http://localhost:8000/api/v1/knowledge-sync/status
   ```
3. Check logs for knowledge loading errors:
   ```bash
   grep "Failed to load knowledge context" backend.log
   ```

### "AI says it can't find information"

**Possible causes**:
1. Database empty - run menu seeding:
   ```bash
   python scripts/seed_menu.py
   ```
2. KnowledgeService failing - check logs
3. Station-specific data requested but not available

### "Performance issues / slow responses"

**Check**:
1. Knowledge context generation time:
   ```python
   # Check Intent Router logs
   # Look for: "Loaded knowledge context (N chars) in Xms"
   ```
2. Database query performance:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM menu_items;
   EXPLAIN ANALYZE SELECT * FROM faqs;
   ```
3. Consider caching if <100ms target not met

---

## Architecture Reference

### Data Flow

```
┌─────────────────┐
│ TypeScript Files│ packages.ts, faqs.ts
└────────┬────────┘
         │ Auto-sync detects changes
         ↓
┌─────────────────┐
│ Database        │ menu_items, faqs, business_charter
└────────┬────────┘
         │ KnowledgeService queries
         ↓
┌─────────────────┐
│ knowledge_context│ Formatted string
└────────┬────────┘
         │ Intent Router injects
         ↓
┌─────────────────┐
│ Agent Context   │ {knowledge_context: "..."}
└────────┬────────┘
         │ Agent.get_system_prompt()
         ↓
┌─────────────────┐
│ System Prompt   │ "You are an agent... [current data]"
└────────┬────────┘
         │ OpenAI API
         ↓
┌─────────────────┐
│ AI Response     │ Uses current database data
└─────────────────┘
```

### Files Involved

**Core Integration**:
- `services/knowledge/knowledge_service.py` - Fetches and formats data
- `api/ai/routers/intent_router.py` - Calls service, injects context
- `api/ai/agents/*.py` - All 4 agents receive and inject knowledge

**Supporting**:
- `services/knowledge/models.py` - Database models
- `services/knowledge/sync_api.py` - Manual sync endpoints
- `services/knowledge/auto_sync_service.py` - Auto-sync (818 lines)

**Testing**:
- `tests/test_knowledge_integration.py` - 9 comprehensive tests

---

## Performance Targets

| Metric | Target | How to Check |
|--------|--------|--------------|
| Knowledge loading | <100ms | Intent Router logs |
| Database query | <50ms | `EXPLAIN ANALYZE` |
| Context size | <10KB | `len(knowledge_context)` |
| Total overhead | <100ms | Test suite performance test |

---

## Best Practices

### ✅ Do
- Keep knowledge_context under 10KB (token limits)
- Use selective loading (only needed sections)
- Cache knowledge_context for 5-10 minutes
- Log knowledge loading failures
- Test after database schema changes

### ❌ Don't
- Don't hardcode data in agent prompts anymore
- Don't add business logic to agents (use tools)
- Don't skip testing after knowledge updates
- Don't forget to seed database in new environments
- Don't ignore performance warnings

---

## Migration Notes (For Historical Reference)

### What Changed
- **Before**: `business_charter = context.get("business_charter", {})`
- **After**: `knowledge_context = context.get("knowledge_context", "")`

### Why
- Simplified: Single string vs nested dict
- Dynamic: Fetched from database vs hardcoded
- Consistent: All agents use same pattern
- Maintainable: KnowledgeService centralizes formatting

### Breaking Changes
- ⚠️ Agents no longer accept `business_charter` in context
- ⚠️ Intent Router now requires database session
- ✅ Backward compatible: Agents handle empty knowledge_context

---

**Last Updated**: November 5, 2025  
**Integration Status**: ✅ Complete  
**Test Coverage**: 9 tests, all passing  
**Performance**: <100ms overhead target
