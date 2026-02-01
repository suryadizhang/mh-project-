'use client';

import { useState } from 'react';
import {
  Search,
  Star,
  Archive,
  Trash2,
  Mail,
  MailOpen,
  Filter,
  MoreHorizontal,
  RefreshCw,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { BulkAction } from '../types';

interface EmailToolbarProps {
  // Selection
  selectedCount: number;
  onClearSelection: () => void;

  // Bulk actions
  onBulkAction: (action: BulkAction) => void;
  isBulkProcessing?: boolean;
  canDelete?: boolean; // Super admin only

  // Filters
  searchQuery: string;
  onSearchChange: (query: string) => void;
  showUnreadOnly: boolean;
  onToggleUnread: () => void;
  showStarredOnly: boolean;
  onToggleStarred: () => void;

  // Refresh
  onRefresh: () => void;
  isRefreshing?: boolean;
}

/**
 * EmailToolbar - Bulk actions and filters for email management
 *
 * Features:
 * - Bulk selection indicator with clear button
 * - Bulk actions (mark read/unread, star, archive, delete)
 * - Search input
 * - Filter toggles (unread, starred)
 * - Refresh button
 */
export function EmailToolbar({
  selectedCount,
  onClearSelection,
  onBulkAction,
  isBulkProcessing = false,
  canDelete = false,
  searchQuery,
  onSearchChange,
  showUnreadOnly,
  onToggleUnread,
  showStarredOnly,
  onToggleStarred,
  onRefresh,
  isRefreshing = false,
}: EmailToolbarProps) {
  const [showFilters, setShowFilters] = useState(false);

  // Show bulk actions bar when items selected
  if (selectedCount > 0) {
    return (
      <div className="flex items-center justify-between px-4 py-3 bg-indigo-50 border-b border-indigo-100">
        <div className="flex items-center gap-4">
          {/* Selection count */}
          <div className="flex items-center gap-2">
            <button
              onClick={onClearSelection}
              className="p-1 hover:bg-indigo-100 rounded"
              title="Clear selection"
            >
              <X className="h-4 w-4 text-indigo-600" />
            </button>
            <span className="text-sm font-medium text-indigo-700">
              {selectedCount} selected
            </span>
          </div>

          {/* Bulk action buttons */}
          <div className="flex items-center gap-1 border-l border-indigo-200 pl-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onBulkAction('mark_read')}
              disabled={isBulkProcessing}
              title="Mark as read"
            >
              <MailOpen className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onBulkAction('mark_unread')}
              disabled={isBulkProcessing}
              title="Mark as unread"
            >
              <Mail className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onBulkAction('star')}
              disabled={isBulkProcessing}
              title="Star"
            >
              <Star className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onBulkAction('archive')}
              disabled={isBulkProcessing}
              title="Archive"
            >
              <Archive className="h-4 w-4" />
            </Button>

            {/* Delete - Super Admin only */}
            {canDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onBulkAction('delete')}
                disabled={isBulkProcessing}
                className="text-red-600 hover:bg-red-50"
                title="Delete permanently"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Processing indicator */}
        {isBulkProcessing && (
          <span className="text-sm text-indigo-600 animate-pulse">
            Processing...
          </span>
        )}
      </div>
    );
  }

  // Normal toolbar (no selection)
  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
      {/* Search */}
      <div className="flex-1 max-w-md relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={e => onSearchChange(e.target.value)}
          placeholder="Search messages..."
          className="
            w-full pl-10 pr-4 py-2 text-sm
            border border-gray-300 rounded-lg
            focus:ring-2 focus:ring-indigo-500 focus:border-transparent
            placeholder-gray-400
          "
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 hover:bg-gray-100 rounded"
          >
            <X className="h-3.5 w-3.5 text-gray-400" />
          </button>
        )}
      </div>

      {/* Filters and Refresh */}
      <div className="flex items-center gap-2 ml-4">
        {/* Filter Toggle */}
        <div className="relative">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className={
              showUnreadOnly || showStarredOnly
                ? 'border-indigo-300 text-indigo-600'
                : ''
            }
          >
            <Filter className="h-4 w-4 mr-1.5" />
            Filters
            {(showUnreadOnly || showStarredOnly) && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded">
                {(showUnreadOnly ? 1 : 0) + (showStarredOnly ? 1 : 0)}
              </span>
            )}
          </Button>

          {/* Filter dropdown */}
          {showFilters && (
            <div className="absolute right-0 top-full mt-1 z-20 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1">
              <button
                onClick={() => {
                  onToggleUnread();
                }}
                className={`
                  w-full flex items-center justify-between px-4 py-2 text-sm
                  ${
                    showUnreadOnly
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'hover:bg-gray-50'
                  }
                `}
              >
                <span>Unread only</span>
                {showUnreadOnly && <span>✓</span>}
              </button>

              <button
                onClick={() => {
                  onToggleStarred();
                }}
                className={`
                  w-full flex items-center justify-between px-4 py-2 text-sm
                  ${
                    showStarredOnly
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'hover:bg-gray-50'
                  }
                `}
              >
                <span>Starred only</span>
                {showStarredOnly && <span>✓</span>}
              </button>

              {/* Clear filters */}
              {(showUnreadOnly || showStarredOnly) && (
                <>
                  <div className="border-t border-gray-100 my-1" />
                  <button
                    onClick={() => {
                      if (showUnreadOnly) onToggleUnread();
                      if (showStarredOnly) onToggleStarred();
                      setShowFilters(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-500 hover:bg-gray-50"
                  >
                    Clear filters
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Refresh */}
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw
            className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`}
          />
        </Button>
      </div>
    </div>
  );
}

export default EmailToolbar;
