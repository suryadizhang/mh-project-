'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Command, Search, X } from 'lucide-react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  description: string;
  action: () => void;
  category?: string;
}

interface KeyboardShortcutsContextValue {
  registerShortcut: (id: string, shortcut: KeyboardShortcut) => void;
  unregisterShortcut: (id: string) => void;
  toggleCommandPalette: () => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextValue | null>(null);

export function useKeyboardShortcuts() {
  const context = useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error('useKeyboardShortcuts must be used within KeyboardShortcutsProvider');
  }
  return context;
}

/**
 * Keyboard Shortcuts Provider
 * Manages global keyboard shortcuts and command palette
 */
export function KeyboardShortcutsProvider({ children }: { children: React.ReactNode }) {
  const [shortcuts, setShortcuts] = useState<Map<string, KeyboardShortcut>>(new Map());
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const registerShortcut = useCallback((id: string, shortcut: KeyboardShortcut) => {
    setShortcuts((prev) => {
      const next = new Map(prev);
      next.set(id, shortcut);
      return next;
    });
  }, []);

  const unregisterShortcut = useCallback((id: string) => {
    setShortcuts((prev) => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const toggleCommandPalette = useCallback(() => {
    setShowCommandPalette((prev) => !prev);
  }, []);

  // Global keyboard event handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Command palette (Cmd+K or Ctrl+K)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleCommandPalette();
        return;
      }

      // ESC to close command palette
      if (e.key === 'Escape' && showCommandPalette) {
        e.preventDefault();
        setShowCommandPalette(false);
        return;
      }

      // Match shortcuts
      for (const shortcut of shortcuts.values()) {
        const ctrlMatch = shortcut.ctrl ? e.ctrlKey : !e.ctrlKey;
        const altMatch = shortcut.alt ? e.altKey : !e.altKey;
        const shiftMatch = shortcut.shift ? e.shiftKey : !e.shiftKey;
        const metaMatch = shortcut.meta ? e.metaKey : !e.metaKey;
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();

        if (ctrlMatch && altMatch && shiftMatch && metaMatch && keyMatch) {
          e.preventDefault();
          shortcut.action();
          return;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, showCommandPalette, toggleCommandPalette]);

  return (
    <KeyboardShortcutsContext.Provider
      value={{ registerShortcut, unregisterShortcut, toggleCommandPalette }}
    >
      {children}
      {mounted && showCommandPalette && (
        <CommandPalette
          shortcuts={Array.from(shortcuts.values())}
          onClose={() => setShowCommandPalette(false)}
        />
      )}
    </KeyboardShortcutsContext.Provider>
  );
}

/**
 * Hook to register a keyboard shortcut
 */
export function useShortcut(
  id: string,
  shortcut: Omit<KeyboardShortcut, 'action'>,
  action: () => void,
  deps: React.DependencyList = []
) {
  const { registerShortcut, unregisterShortcut } = useKeyboardShortcuts();

  useEffect(() => {
    registerShortcut(id, { ...shortcut, action });
    return () => unregisterShortcut(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, ...deps]);
}

/**
 * Command Palette Component
 */
function CommandPalette({
  shortcuts,
  onClose,
}: {
  shortcuts: KeyboardShortcut[];
  onClose: () => void;
}) {
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Group shortcuts by category
  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || 'General';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);

  // Filter shortcuts based on search
  const filteredShortcuts = Object.entries(groupedShortcuts).reduce((acc, [category, items]) => {
    const filtered = items.filter((shortcut) =>
      shortcut.description.toLowerCase().includes(search.toLowerCase())
    );
    if (filtered.length > 0) {
      acc[category] = filtered;
    }
    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);

  const allFilteredShortcuts = Object.values(filteredShortcuts).flat();

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < allFilteredShortcuts.length - 1 ? prev + 1 : prev
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const selected = allFilteredShortcuts[selectedIndex];
        if (selected) {
          selected.action();
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIndex, allFilteredShortcuts, onClose]);

  const palette = (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/50 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[600px] flex flex-col animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 p-4 border-b border-gray-200">
          <Search className="h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Type a command or search..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelectedIndex(0);
            }}
            className="flex-1 outline-none text-sm"
            autoFocus
          />
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Shortcuts List */}
        <div className="overflow-y-auto flex-1 p-2">
          {Object.keys(filteredShortcuts).length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              <p>No commands found</p>
            </div>
          ) : (
            Object.entries(filteredShortcuts).map(([category, items]) => (
              <div key={category} className="mb-4">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                  {category}
                </div>
                {items.map((shortcut, index) => {
                  const globalIndex = allFilteredShortcuts.indexOf(shortcut);
                  const isSelected = globalIndex === selectedIndex;

                  return (
                    <button
                      key={index}
                      onClick={() => {
                        shortcut.action();
                        onClose();
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-left transition-colors ${
                        isSelected
                          ? 'bg-blue-50 text-blue-900'
                          : 'hover:bg-gray-50 text-gray-900'
                      }`}
                    >
                      <span className="text-sm">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.meta && <Kbd>⌘</Kbd>}
                        {shortcut.ctrl && <Kbd>Ctrl</Kbd>}
                        {shortcut.alt && <Kbd>Alt</Kbd>}
                        {shortcut.shift && <Kbd>⇧</Kbd>}
                        <Kbd>{shortcut.key.toUpperCase()}</Kbd>
                      </div>
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span>
              <Kbd>↑</Kbd> <Kbd>↓</Kbd> Navigate
            </span>
            <span>
              <Kbd>⏎</Kbd> Select
            </span>
            <span>
              <Kbd>Esc</Kbd> Close
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Kbd>⌘</Kbd> <Kbd>K</Kbd> to toggle
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(palette, document.body);
}

/**
 * Keyboard Key Badge Component
 */
function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[1.5rem] h-6 px-1.5 font-mono text-xs font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded shadow-sm">
      {children}
    </kbd>
  );
}

/**
 * Keyboard Shortcut Hint Component
 * Shows shortcut hint inline in UI
 */
export function ShortcutHint({ shortcut }: { shortcut: Omit<KeyboardShortcut, 'action'> }) {
  return (
    <div className="flex items-center gap-1 text-xs text-gray-500">
      {shortcut.meta && <Kbd>⌘</Kbd>}
      {shortcut.ctrl && <Kbd>Ctrl</Kbd>}
      {shortcut.alt && <Kbd>Alt</Kbd>}
      {shortcut.shift && <Kbd>⇧</Kbd>}
      <Kbd>{shortcut.key.toUpperCase()}</Kbd>
    </div>
  );
}
