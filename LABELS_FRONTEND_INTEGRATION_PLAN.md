# Labels/Tags System - Frontend Integration Plan

**Date:** November 25, 2025 **Status:** Backend ✅ Complete | Frontend
⏳ In Progress **Related:** `LABELS_TAGS_SYSTEM_COMPLETE.md`

---

## 🎯 Integration Strategy

### Approach: Extend Existing Unified Inbox

Instead of creating a separate email page, we'll **enable the disabled
"Email" tab** in the existing `/inbox` page. This provides:

- ✅ Consistent UX with SMS/Facebook/Instagram tabs
- ✅ Reuses existing components (StatsCard, FilterBar, Modal)
- ✅ Unified inbox experience (one place for all communications)
- ✅ Minimal code duplication

**File to Modify:** `apps/admin/src/app/inbox/page.tsx`

---

## 📋 Implementation Checklist

### Phase 1: Enable Email Tab ✅

- [x] Remove `disabled` prop from Email tab button
- [x] Add email stats to dashboard (total, unread, labeled counts)
- [x] Create email service API client
- [x] Fetch email threads from backend

### Phase 2: Email Thread Display ⏳

- [ ] Display email threads in left sidebar
- [ ] Show email preview (subject, from, snippet)
- [ ] Show read/unread status
- [ ] Show starred status
- [ ] Display label badges on threads

### Phase 3: Email Conversation View ⏳

- [ ] Display full email content (HTML/text)
- [ ] Show email headers (from, to, date)
- [ ] Display attachments list
- [ ] Show conversation thread history
- [ ] Add reply/forward buttons

### Phase 4: Labels UI ⏳

- [ ] Add label filter dropdown in FilterBar
- [ ] Display label badges on email list items
- [ ] Create label picker modal
- [ ] Bulk label operations (apply/remove)
- [ ] Label badge click to filter

### Phase 5: Label Management ⏳

- [ ] Create settings page: `/settings/labels`
- [ ] List all labels with colors
- [ ] Create new label form
- [ ] Edit label (name, color, icon)
- [ ] Archive/delete label
- [ ] Drag-and-drop reorder (sort_order)

### Phase 6: Bulk Actions ⏳

- [ ] Checkbox selection in email list
- [ ] Select all button
- [ ] Bulk mark read/unread
- [ ] Bulk star/unstar
- [ ] Bulk archive
- [ ] Bulk apply label
- [ ] Bulk remove label
- [ ] Bulk delete

---

## 🛠️ Components to Create

### 1. Email Service (`apps/admin/src/services/email-api.ts`)

```typescript
export const emailService = {
  // Emails
  getEmails: (params: EmailListParams) =>
    api.get('/admin/emails/customer-support', { params }),
  getEmailThread: (threadId: string) =>
    api.get(`/admin/emails/customer-support/${threadId}`),
  updateEmail: (messageId: string, data: EmailUpdate) =>
    api.put(`/admin/emails/customer-support/${messageId}`, data),
  deleteEmail: (messageId: string) =>
    api.delete(`/admin/emails/customer-support/${messageId}`),
  bulkUpdate: (data: BulkEmailUpdate) =>
    api.post('/admin/emails/customer-support/bulk', data),

  // Labels
  getLabels: (includeArchived?: boolean) =>
    api.get('/admin/emails/labels', {
      params: { include_archived: includeArchived },
    }),
  createLabel: (data: LabelCreate) =>
    api.post('/admin/emails/labels', data),
  updateLabel: (labelId: string, data: LabelUpdate) =>
    api.put(`/admin/emails/labels/${labelId}`, data),
  deleteLabel: (labelId: string) =>
    api.delete(`/admin/emails/labels/${labelId}`),
};
```

### 2. Email Types (`apps/admin/src/types/email.ts`)

```typescript
export interface Email {
  message_id: string;
  thread_id: string;
  from_address: string;
  from_name?: string;
  subject: string;
  text_body?: string;
  html_body?: string;
  received_at: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  has_attachments: boolean;
  labels: string[]; // Array of label slugs
}

export interface EmailThread {
  thread_id: string;
  subject: string;
  participants: EmailAddress[];
  messages: Email[];
  message_count: number;
  unread_count: number;
  last_message_at: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  labels: string[];
}

export interface Label {
  id: string;
  name: string;
  slug: string;
  description?: string;
  color: string;
  icon?: string;
  is_system: boolean;
  is_archived: boolean;
  email_count: number;
  sort_order: number;
}

export interface BulkEmailUpdate {
  message_ids: string[];
  action?:
    | 'mark_read'
    | 'mark_unread'
    | 'star'
    | 'unstar'
    | 'archive'
    | 'unarchive'
    | 'delete'
    | 'apply_label'
    | 'remove_label';
  label_slug?: string;
}
```

### 3. Label Picker Component (`apps/admin/src/components/emails/LabelPicker.tsx`)

```tsx
interface LabelPickerProps {
  selectedLabels: string[];
  onToggle: (labelSlug: string) => void;
  onClose: () => void;
}

export function LabelPicker({
  selectedLabels,
  onToggle,
  onClose,
}: LabelPickerProps) {
  const { data: labels } = useLabels();

  return (
    <div className="absolute z-10 mt-2 w-64 bg-white rounded-lg shadow-lg border">
      <div className="p-2 space-y-1">
        {labels?.map(label => (
          <button
            key={label.slug}
            onClick={() => onToggle(label.slug)}
            className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 rounded"
          >
            <input
              type="checkbox"
              checked={selectedLabels.includes(label.slug)}
              readOnly
            />
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: label.color }}
            />
            <span className="flex-1 text-left text-sm">
              {label.name}
            </span>
            <span className="text-xs text-gray-500">
              ({label.email_count})
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### 4. Label Badge Component (`apps/admin/src/components/emails/LabelBadge.tsx`)

```tsx
interface LabelBadgeProps {
  label: Label;
  onRemove?: () => void;
  onClick?: () => void;
}

export function LabelBadge({
  label,
  onRemove,
  onClick,
}: LabelBadgeProps) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium cursor-pointer"
      style={{
        backgroundColor: `${label.color}20`,
        color: label.color,
        border: `1px solid ${label.color}40`,
      }}
      onClick={onClick}
    >
      {label.icon && <span>{label.icon}</span>}
      <span>{label.name}</span>
      {onRemove && (
        <button
          onClick={e => {
            e.stopPropagation();
            onRemove();
          }}
          className="hover:bg-black/10 rounded-full p-0.5"
        >
          ×
        </button>
      )}
    </span>
  );
}
```

### 5. Label Management Page (`apps/admin/src/app/settings/labels/page.tsx`)

```tsx
export default function LabelsSettingsPage() {
  const { data: labels, refetch } = useLabels();
  const [isCreating, setIsCreating] = useState(false);

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Email Labels</h1>
        <Button onClick={() => setIsCreating(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Label
        </Button>
      </div>

      {/* Labels List */}
      <div className="bg-white rounded-lg shadow border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="px-4 py-3 text-left">Label</th>
              <th className="px-4 py-3 text-left">Color</th>
              <th className="px-4 py-3 text-left">Emails</th>
              <th className="px-4 py-3 text-left">System</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {labels?.map(label => (
              <tr
                key={label.id}
                className="border-b hover:bg-gray-50"
              >
                <td className="px-4 py-3">
                  <LabelBadge label={label} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-6 h-6 rounded border"
                      style={{ backgroundColor: label.color }}
                    />
                    <span className="text-sm text-gray-600">
                      {label.color}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">{label.email_count}</td>
                <td className="px-4 py-3">
                  {label.is_system ? <Badge>System</Badge> : null}
                </td>
                <td className="px-4 py-3 text-right">
                  <Button variant="outline" size="sm">
                    Edit
                  </Button>
                  {!label.is_system && (
                    <Button variant="outline" size="sm">
                      Delete
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Label Modal */}
      {isCreating && (
        <LabelCreateModal onClose={() => setIsCreating(false)} />
      )}
    </div>
  );
}
```

---

## 🎨 UI/UX Design

### Label Badge Colors (Default Palette)

```tsx
const DEFAULT_LABEL_COLORS = [
  '#EF4444', // Red
  '#F59E0B', // Orange
  '#10B981', // Green
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#6B7280', // Gray
];
```

### Label Icons (Lucide React)

```tsx
import {
  Star,
  Flag,
  AlertCircle,
  Clock,
  CheckCircle,
  Zap,
} from 'lucide-react';

const DEFAULT_LABEL_ICONS = {
  star: Star,
  flag: Flag,
  alert: AlertCircle,
  clock: Clock,
  check: CheckCircle,
  zap: Zap,
};
```

---

## 🔌 API Integration

### Backend Endpoints (Already Implemented)

```
✅ GET    /admin/emails/customer-support               - List emails (with ?label=slug filter)
✅ GET    /admin/emails/customer-support/{thread_id}   - Get email thread
✅ POST   /admin/emails/customer-support/bulk          - Bulk operations
✅ GET    /admin/emails/labels                         - List labels
✅ POST   /admin/emails/labels                         - Create label
✅ PUT    /admin/emails/labels/{label_id}              - Update label
✅ DELETE /admin/emails/labels/{label_id}              - Archive label
```

### Frontend API Client Pattern

```typescript
// apps/admin/src/services/api-client.ts
import axios from 'axios';

const api = axios.create({
  baseURL:
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor
api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## 🧪 Testing Plan

### Unit Tests

- [ ] Label service methods
- [ ] Label badge component rendering
- [ ] Label picker selection logic
- [ ] Bulk operations validation

### Integration Tests

- [ ] Fetch emails with labels
- [ ] Apply label to email
- [ ] Remove label from email
- [ ] Filter emails by label
- [ ] Create new label
- [ ] Edit label color/name
- [ ] Archive label

### E2E Tests (Playwright)

- [ ] Navigate to inbox email tab
- [ ] Select email and apply label
- [ ] Filter by label
- [ ] Bulk select and label multiple emails
- [ ] Create label from settings
- [ ] Edit label from settings

---

## 📱 Mobile Responsiveness

### Breakpoints

- **Mobile (< 640px):** Single column, compact labels
- **Tablet (640px - 1024px):** Two columns (list + detail)
- **Desktop (> 1024px):** Three columns (list + detail + sidebar)

### Mobile Optimizations

- [ ] Swipe gestures for quick actions
- [ ] Bottom sheet for label picker
- [ ] Collapsible email headers
- [ ] Horizontal scroll for label badges
- [ ] Touch-friendly tap targets (44x44px minimum)

---

## 🚀 Deployment Plan

### Phase 1: Staging (Week 1)

1. Deploy backend (already complete)
2. Enable email tab in admin inbox
3. Test with real customer support emails
4. Gather team feedback

### Phase 2: Label Management (Week 2)

1. Create 5-10 default labels (VIP, Follow-up, Bug, Feature Request,
   Urgent)
2. Add label settings page
3. Train team on label usage
4. Document label best practices

### Phase 3: Production (Week 3)

1. Enable feature flag in production
2. Monitor performance (API response times)
3. Track label usage analytics
4. Iterate based on team feedback

---

## 🎓 Training Materials

### Admin Team Guide

```markdown
# How to Use Email Labels

## Quick Start

1. Open any email in the inbox
2. Click the "Labels" button
3. Select labels to apply
4. Use label filters to find emails faster

## Best Practices

- **VIP:** High-value customers
- **Follow-up:** Needs response within 24h
- **Bug Report:** Technical issues
- **Feature Request:** Product suggestions
- **Urgent:** Requires immediate attention

## Keyboard Shortcuts

- `L`: Open label picker
- `1-9`: Quick apply labels 1-9
- `Ctrl+L`: Toggle label filter
```

---

## 📊 Success Metrics

### Key Performance Indicators (KPIs)

1. **Email Response Time:** Target < 2 hours for labeled emails
2. **Label Usage Rate:** % of emails with at least one label (target:
   80%)
3. **Search Efficiency:** Time to find email (with labels vs without)
4. **Team Adoption:** % of team members using labels regularly
   (target: 100%)

### Analytics to Track

- Most used labels
- Average labels per email
- Label filter usage frequency
- Time saved with label filtering

---

## 🐛 Known Limitations

### Current Constraints

1. **No nested labels:** Flat structure only (no parent/child)
2. **No label sharing:** All labels global to organization
3. **No label permissions:** All admins can manage all labels
4. **No auto-labeling:** Manual application only (AI auto-label in
   Phase 2)
5. **No label rules:** Can't create filters (e.g., "auto-label emails
   from @gmail.com")

### Future Enhancements (V2)

- [ ] Nested label hierarchies
- [ ] Role-based label access
- [ ] AI-powered auto-labeling
- [ ] Label rules engine
- [ ] Label templates
- [ ] Label analytics dashboard

---

## 📝 Next Immediate Steps

1. **Create Email API Service**
   (`apps/admin/src/services/email-api.ts`)
2. **Add Email Types** (`apps/admin/src/types/email.ts`)
3. **Enable Email Tab** in `/inbox` page
4. **Fetch Emails** from backend API
5. **Display Email List** with labels
6. **Add Label Filter** to FilterBar
7. **Create Label Picker** component
8. **Test Label Operations** (apply/remove)

---

**Estimated Development Time:**

- Phase 1 (Enable Tab): 2 hours
- Phase 2 (Email Display): 4 hours
- Phase 3 (Conversation View): 3 hours
- Phase 4 (Labels UI): 6 hours
- Phase 5 (Label Management): 4 hours
- Phase 6 (Bulk Actions): 3 hours

**Total:** ~22 hours (3 days)

---

**Status:** Ready to begin frontend implementation **Next Action:**
Create email API service and enable email tab
