/**
 * useKeyboardShortcuts Hook
 * =========================
 * Gmail-style keyboard navigation for the inbox.
 *
 * Shortcuts:
 * - j/k: Navigate threads
 * - r: Reply
 * - e: Archive
 * - s: Star/Unstar
 * - u: Mark unread
 * - /: Focus search
 * - Escape: Close/unfocus
 */

import { useEffect, useCallback } from 'react';
import { KEYBOARD_SHORTCUTS } from '../constants';

interface UseKeyboardShortcutsOptions {
  threads: any[];
  selectedThread: any | null;
  isEmailChannel: boolean;
  onSelectThread: (thread: any) => void;
  onArchive: (thread: any) => void;
  onStar: (thread: any) => void;
  onMarkUnread: (thread: any) => void;
  onReply: () => void;
  onSelectAll?: () => void;
  enabled?: boolean;
}

export function useKeyboardShortcuts({
  threads,
  selectedThread,
  isEmailChannel,
  onSelectThread,
  onArchive,
  onStar,
  onMarkUnread,
  onReply,
  onSelectAll,
  enabled = true,
}: UseKeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      const target = e.target as HTMLElement;
      const isInputFocused =
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'INPUT' ||
        target.isContentEditable;

      // Allow Escape to close/unfocus from any element
      if (e.key === 'Escape') {
        target.blur();
        return;
      }

      // Don't trigger shortcuts when typing in input fields
      if (isInputFocused) return;

      // Get current thread index
      const currentIndex = selectedThread
        ? threads.findIndex(
            t =>
              t.thread_id === selectedThread.thread_id ||
              t.id === selectedThread.id
          )
        : -1;

      switch (e.key.toLowerCase()) {
        // j - Next thread
        case KEYBOARD_SHORTCUTS.NEXT_THREAD:
          e.preventDefault();
          if (currentIndex < threads.length - 1) {
            onSelectThread(threads[currentIndex + 1]);
          } else if (currentIndex === -1 && threads.length > 0) {
            onSelectThread(threads[0]);
          }
          break;

        // k - Previous thread
        case KEYBOARD_SHORTCUTS.PREV_THREAD:
          e.preventDefault();
          if (currentIndex > 0) {
            onSelectThread(threads[currentIndex - 1]);
          }
          break;

        // r - Reply (email only)
        case KEYBOARD_SHORTCUTS.REPLY:
          if (selectedThread && isEmailChannel) {
            e.preventDefault();
            onReply();
          }
          break;

        // e - Archive (email only)
        case KEYBOARD_SHORTCUTS.ARCHIVE:
          if (selectedThread && isEmailChannel) {
            e.preventDefault();
            onArchive(selectedThread);
          }
          break;

        // s - Star/Unstar (email only)
        case KEYBOARD_SHORTCUTS.STAR:
          if (selectedThread && isEmailChannel) {
            e.preventDefault();
            onStar(selectedThread);
          }
          break;

        // u - Mark as unread (email only)
        case KEYBOARD_SHORTCUTS.MARK_UNREAD:
          if (selectedThread && isEmailChannel) {
            e.preventDefault();
            onMarkUnread(selectedThread);
          }
          break;

        // / - Focus search
        case '/':
          e.preventDefault();
          document
            .querySelector<HTMLInputElement>('input[type="text"]')
            ?.focus();
          break;

        // Ctrl/Cmd + A - Select all
        case 'a':
          if ((e.ctrlKey || e.metaKey) && onSelectAll) {
            e.preventDefault();
            onSelectAll();
          }
          break;
      }
    },
    [
      enabled,
      threads,
      selectedThread,
      isEmailChannel,
      onSelectThread,
      onArchive,
      onStar,
      onMarkUnread,
      onReply,
      onSelectAll,
    ]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
