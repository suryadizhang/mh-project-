/**
 * TypeScript Types for Knowledge Sync System
 * Matches backend response schemas from /api/v1/knowledge/sync endpoints
 */

/**
 * Sync source types - must match TypeScript file names
 */
export type SyncSource = 'faqs' | 'packages' | 'business_charter';

/**
 * Sync type - auto (scheduled) or manual (user-triggered)
 */
export type SyncType = 'auto' | 'manual';

/**
 * Sync status states
 */
export type SyncStatus =
  | 'in_sync'           // Database matches TypeScript files
  | 'out_of_sync'       // Changes detected but not applied
  | 'syncing'           // Sync operation in progress
  | 'error'             // Sync failed
  | 'never_synced';     // No sync performed yet

/**
 * Individual file change detected during comparison
 */
export interface FileChange {
  field: string;
  source_value: string | number | null;
  db_value: string | number | null;
  change_type: 'added' | 'modified' | 'deleted';
}

/**
 * Changes detected for a specific source
 */
export interface SourceDiff {
  source: SyncSource;
  has_changes: boolean;
  changes_count: number;
  changes: FileChange[];
  last_checked: string; // ISO 8601 timestamp
}

/**
 * Overall sync differences for all sources
 */
export interface SyncDiff {
  faqs: SourceDiff;
  packages: SourceDiff;
  business_charter: SourceDiff;
  total_changes: number;
}

/**
 * Sync status for a single source
 */
export interface SourceStatus {
  source: SyncSource;
  status: SyncStatus;
  last_sync_at: string | null; // ISO 8601 timestamp
  last_sync_type: SyncType | null;
  changes_detected: number;
  changes_applied: number;
  error_message: string | null;
}

/**
 * Overall sync status response
 */
export interface SyncStatusResponse {
  faqs: SourceStatus;
  packages: SourceStatus;
  business_charter: SourceStatus;
  overall_status: SyncStatus;
  last_sync_at: string | null;
}

/**
 * Individual sync history record
 */
export interface SyncHistoryRecord {
  id: string;
  source: SyncSource;
  sync_type: SyncType;
  status: 'success' | 'partial' | 'failed';
  changes_detected: number;
  changes_applied: number;
  error_message: string | null;
  duration_ms: number;
  started_at: string; // ISO 8601 timestamp
  completed_at: string; // ISO 8601 timestamp
  created_at: string; // ISO 8601 timestamp
}

/**
 * Paginated sync history response
 */
export interface SyncHistoryResponse {
  records: SyncHistoryRecord[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/**
 * Sync operation request body
 */
export interface SyncRequest {
  sources?: SyncSource[]; // Optional: sync specific sources only
  force?: boolean;        // Force sync even if no changes detected
  dry_run?: boolean;      // Detect changes but don't apply them
}

/**
 * Sync operation result
 */
export interface SyncResult {
  source: SyncSource;
  success: boolean;
  changes_applied: number;
  error_message: string | null;
  duration_ms: number;
}

/**
 * Sync operation response
 */
export interface SyncOperationResponse {
  success: boolean;
  results: SyncResult[];
  total_changes: number;
  duration_ms: number;
  message: string;
}

/**
 * Health check response
 */
export interface SyncHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database_connected: boolean;
  files_accessible: boolean;
  last_successful_sync: string | null;
  errors: string[];
}

/**
 * API error response
 */
export interface SyncApiError {
  error: string;
  detail?: string;
  status_code: number;
}
