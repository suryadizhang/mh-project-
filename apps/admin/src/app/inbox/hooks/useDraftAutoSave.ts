/**
 * useDraftAutoSave Hook
 * =====================
 * Auto-saves draft replies to localStorage with debouncing.
 *
 * Features:
 * - Debounced save (3 seconds after last change)
 * - Restore draft when selecting a thread
 * - Clear draft after sending
 * - Track last saved timestamp
 */

import { useState, useEffect, useCallback } from 'react';
import { DRAFT_AUTOSAVE_DELAY_MS, DRAFT_STORAGE_PREFIX } from '../constants';

interface UseDraftAutoSaveOptions {
  threadId: string | null;
  content: string;
  onRestore?: (content: string) => void;
}

interface DraftState {
  lastSaved: Date | null;
  isSaving: boolean;
}

export function useDraftAutoSave({
  threadId,
  content,
  onRestore,
}: UseDraftAutoSaveOptions): DraftState & {
  clearDraft: () => void;
  restoreDraft: () => string | null;
} {
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const getStorageKey = useCallback(
    (id: string) => `${DRAFT_STORAGE_PREFIX}${id}`,
    []
  );

  // Restore draft when thread changes
  useEffect(() => {
    if (!threadId) {
      setLastSaved(null);
      return;
    }

    const key = getStorageKey(threadId);
    const savedDraft = localStorage.getItem(key);

    if (savedDraft && onRestore) {
      onRestore(savedDraft);
      setLastSaved(new Date());
    }
  }, [threadId, getStorageKey, onRestore]);

  // Auto-save with debounce
  useEffect(() => {
    if (!threadId || !content.trim()) {
      return;
    }

    setIsSaving(true);

    const timeoutId = setTimeout(() => {
      const key = getStorageKey(threadId);
      localStorage.setItem(key, content);
      setLastSaved(new Date());
      setIsSaving(false);
    }, DRAFT_AUTOSAVE_DELAY_MS);

    return () => {
      clearTimeout(timeoutId);
      setIsSaving(false);
    };
  }, [threadId, content, getStorageKey]);

  const clearDraft = useCallback(() => {
    if (threadId) {
      const key = getStorageKey(threadId);
      localStorage.removeItem(key);
      setLastSaved(null);
    }
  }, [threadId, getStorageKey]);

  const restoreDraft = useCallback((): string | null => {
    if (!threadId) return null;
    const key = getStorageKey(threadId);
    return localStorage.getItem(key);
  }, [threadId, getStorageKey]);

  return {
    lastSaved,
    isSaving,
    clearDraft,
    restoreDraft,
  };
}

/**
 * Format the "Draft saved X ago" message
 */
export function formatDraftSavedTime(date: Date | null): string | null {
  if (!date) return null;

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);

  if (diffSecs < 5) return 'just now';
  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
  return `${Math.floor(diffSecs / 3600)}h ago`;
}
