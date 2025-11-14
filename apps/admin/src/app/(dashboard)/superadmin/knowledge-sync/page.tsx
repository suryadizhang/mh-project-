'use client';

import { RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import React from 'react';

import { DiffViewer } from '@/components/superadmin/DiffViewer';
import { SyncHistoryTable } from '@/components/superadmin/SyncHistoryTable';
import { SyncStatusCards } from '@/components/superadmin/SyncStatusCards';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/contexts/AuthContext';
import { knowledgeSyncService } from '@/services/knowledge-sync.service';
import {
  SyncDiff,
  SyncHistoryResponse,
  SyncSource,
  SyncStatusResponse,
} from '@/types/knowledge-sync.types';

export default function KnowledgeSyncDashboard() {
  const { success, error } = useToast();
  const { isSuperAdmin } = useAuth();
  const router = useRouter();

  // State
  const [syncStatus, setSyncStatus] = React.useState<SyncStatusResponse | null>(null);
  const [diff, setDiff] = React.useState<SyncDiff | null>(null);
  const [history, setHistory] = React.useState<SyncHistoryResponse | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = React.useState(true);
  const [isLoadingDiff, setIsLoadingDiff] = React.useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = React.useState(false);
  const [isSyncing, setIsSyncing] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState('status');
  const [historyPage, setHistoryPage] = React.useState(1);
  const [historyFilters, setHistoryFilters] = React.useState<{
    source?: SyncSource;
    sync_type?: 'auto' | 'manual';
  }>({});

  // Force sync confirmation dialog
  const [showForceDialog, setShowForceDialog] = React.useState(false);
  const [forceSyncSource, setForceSyncSource] = React.useState<SyncSource | undefined>(undefined);

  // Load sync status
  const loadSyncStatus = React.useCallback(async () => {
    try {
      setIsLoadingStatus(true);
      const status = await knowledgeSyncService.getSyncStatus();
      setSyncStatus(status);
    } catch (err) {
      console.error('Failed to load sync status:', err);
      error('Error', 'Failed to load sync status. Please try again.');
    } finally {
      setIsLoadingStatus(false);
    }
  }, [error]);

  // Role protection - redirect non-superadmins
  React.useEffect(() => {
    if (!isSuperAdmin()) {
      error('Access Denied', 'This page is only accessible to super administrators.');
      router.push('/dashboard');
    }
  }, [isSuperAdmin, router, error]);

  // Load diff
  const loadDiff = React.useCallback(async () => {
    try {
      setIsLoadingDiff(true);
      const diffData = await knowledgeSyncService.getDiff();
      setDiff(diffData);
    } catch (err) {
      console.error('Failed to load diff:', err);
      error('Error', 'Failed to load differences. Please try again.');
    } finally {
      setIsLoadingDiff(false);
    }
  }, [error]);

  // Load history
  const loadHistory = React.useCallback(async () => {
    try {
      setIsLoadingHistory(true);
      const historyData = await knowledgeSyncService.getSyncHistory({
        page: historyPage,
        per_page: 20,
        ...historyFilters,
      });
      setHistory(historyData);
    } catch (err) {
      console.error('Failed to load history:', err);
      error('Error', 'Failed to load sync history. Please try again.');
    } finally {
      setIsLoadingHistory(false);
    }
  }, [historyPage, historyFilters, error]);

  // Auto sync
  const handleAutoSync = React.useCallback(
    async (source?: SyncSource) => {
      try {
        setIsSyncing(true);
        const result = await knowledgeSyncService.triggerAutoSync({
          sources: source ? [source] : undefined,
        });

        if (result.success) {
          success('Sync completed', `Successfully synced ${source || 'all sources'}.`);
          // Reload data
          await loadSyncStatus();
          if (activeTab === 'diff') await loadDiff();
          if (activeTab === 'history') await loadHistory();
        } else {
          throw new Error(result.message);
        }
      } catch (err) {
        console.error('Auto sync failed:', err);
        error('Sync failed', err instanceof Error ? err.message : 'Failed to sync. Please try again.');
      } finally {
        setIsSyncing(false);
      }
    },
    [activeTab, loadSyncStatus, loadDiff, loadHistory, success, error]
  );

  // Force sync (with confirmation)
  const handleForceSync = React.useCallback((source?: SyncSource) => {
    setForceSyncSource(source);
    setShowForceDialog(true);
  }, []);

  const confirmForceSync = React.useCallback(async () => {
    try {
      setShowForceDialog(false);
      setIsSyncing(true);

      const result = await knowledgeSyncService.triggerForceSync({
        sources: forceSyncSource ? [forceSyncSource] : undefined,
      });

      if (result.success) {
        success('Force sync completed', `Successfully force synced ${forceSyncSource || 'all sources'}.`);
        // Reload data
        await loadSyncStatus();
        if (activeTab === 'diff') await loadDiff();
        if (activeTab === 'history') await loadHistory();
      } else {
        throw new Error(result.message);
      }
    } catch (err) {
      console.error('Force sync failed:', err);
      error('Force sync failed', err instanceof Error ? err.message : 'Failed to force sync. Please try again.');
    } finally {
      setIsSyncing(false);
      setForceSyncSource(undefined);
    }
  }, [forceSyncSource, activeTab, loadSyncStatus, loadDiff, loadHistory, success, error]);

  // Refresh current view
  const handleRefresh = React.useCallback(async () => {
    if (activeTab === 'status') {
      await loadSyncStatus();
    } else if (activeTab === 'diff') {
      await loadDiff();
    } else if (activeTab === 'history') {
      await loadHistory();
    }
  }, [activeTab, loadSyncStatus, loadDiff, loadHistory]);

  // Load data on mount and when tab changes
  React.useEffect(() => {
    loadSyncStatus();
  }, [loadSyncStatus]);

  React.useEffect(() => {
    if (activeTab === 'diff' && !diff) {
      loadDiff();
    } else if (activeTab === 'history' && !history) {
      loadHistory();
    }
  }, [activeTab, diff, history, loadDiff, loadHistory]);

  // Auto-refresh status every 30 seconds
  React.useEffect(() => {
    if (activeTab === 'status') {
      const interval = setInterval(() => {
        loadSyncStatus();
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [activeTab, loadSyncStatus]);

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Sync Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage synchronization between TypeScript files and database
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline" disabled={isSyncing}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Status Cards (always visible) */}
      {syncStatus && (
        <SyncStatusCards
          status={syncStatus}
          isLoading={isLoadingStatus || isSyncing}
          onAutoSync={handleAutoSync}
          onForceSync={handleForceSync}
          onRefresh={loadSyncStatus}
        />
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="diff">Differences</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="diff" className="mt-6">
          {diff && <DiffViewer diff={diff} isLoading={isLoadingDiff} />}
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          {history && (
            <SyncHistoryTable
              history={history}
              isLoading={isLoadingHistory}
              onPageChange={(page) => {
                setHistoryPage(page);
                loadHistory();
              }}
              onFilterChange={(filters) => {
                setHistoryFilters(filters);
                setHistoryPage(1);
                loadHistory();
              }}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Force Sync Confirmation Dialog */}
      <AlertDialog open={showForceDialog} onOpenChange={setShowForceDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Force Sync Confirmation</AlertDialogTitle>
            <AlertDialogDescription>
              Force sync will override any manual changes made directly to the database. This action
              cannot be undone. Are you sure you want to continue?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmForceSync} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Force Sync
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
