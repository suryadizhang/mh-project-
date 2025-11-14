'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import React, { useCallback, useEffect, useState } from 'react';

import { DiffViewer } from '@/components/superadmin/DiffViewer';
import { SyncHistoryTable } from '@/components/superadmin/SyncHistoryTable';
import { SyncStatusCards } from '@/components/superadmin/SyncStatusCards';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
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

/**
 * Knowledge Sync Dashboard - Superadmin Only
 * Manages synchronization between TypeScript files and PostgreSQL database
 * for FAQs, Packages, and Business Charter
 */
export default function KnowledgeSyncDashboard() {
  const router = useRouter();
  const { success, error: showError } = useToast();
  const { isSuperAdmin, loading: authLoading } = useAuth();

  // State
  const [status, setStatus] = useState<SyncStatusResponse | null>(null);
  const [diff, setDiff] = useState<SyncDiff | null>(null);
  const [history, setHistory] = useState<SyncHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncingSource, setSyncingSource] = useState<SyncSource | null>(null);
  const [activeTab, setActiveTab] = useState('status');
  const [historyPage, setHistoryPage] = useState(1);
  const [historyFilters, setHistoryFilters] = useState<{
    source?: SyncSource;
    sync_type?: 'auto' | 'manual';
  }>({});

  // Access Control - Redirect non-superadmins
  useEffect(() => {
    if (!authLoading && !isSuperAdmin()) {
      showError(
        'Access Denied',
        'You must be a superadmin to access this page.'
      );
      router.push('/dashboard');
    }
  }, [authLoading, isSuperAdmin, router, showError]);

  /**
   * Fetch sync status from API
   */
  const fetchStatus = useCallback(async () => {
    try {
      const statusData = await knowledgeSyncService.getSyncStatus();
      setStatus(statusData);
    } catch (error) {
      console.error('Failed to fetch sync status:', error);
      showError(
        'Error',
        error instanceof Error ? error.message : 'Failed to fetch sync status'
      );
    }
  }, [showError]);

  /**
   * Fetch differences between TypeScript and database
   */
  const fetchDiff = useCallback(
    async (sources?: SyncSource[]) => {
      try {
        const diffData = await knowledgeSyncService.getDiff(sources);
        setDiff(diffData);
      } catch (error) {
        console.error('Failed to fetch diff:', error);
        showError(
          'Error',
          error instanceof Error ? error.message : 'Failed to fetch differences'
        );
      }
    },
    [showError]
  );

  /**
   * Fetch sync history with pagination and filters
   */
  const fetchHistory = useCallback(async () => {
    try {
      const historyData = await knowledgeSyncService.getSyncHistory({
        page: historyPage,
        per_page: 20,
        ...historyFilters,
      });
      setHistory(historyData);
    } catch (error) {
      console.error('Failed to fetch sync history:', error);
      showError(
        'Error',
        error instanceof Error ? error.message : 'Failed to fetch sync history'
      );
    }
  }, [historyPage, historyFilters, showError]);

  /**
   * Initial data load
   */
  useEffect(() => {
    const loadData = async () => {
      if (authLoading || !isSuperAdmin()) return;

      setLoading(true);
      await Promise.all([fetchStatus(), fetchDiff(), fetchHistory()]);
      setLoading(false);
    };

    loadData();
  }, [authLoading, isSuperAdmin, fetchStatus, fetchDiff, fetchHistory]);

  /**
   * Real-time status polling (every 30 seconds)
   */
  useEffect(() => {
    if (!isSuperAdmin()) return;

    const interval = setInterval(() => {
      fetchStatus();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [isSuperAdmin, fetchStatus]);

  /**
   * Refetch history when page or filters change
   */
  useEffect(() => {
    if (!loading && isSuperAdmin()) {
      fetchHistory();
    }
  }, [historyPage, historyFilters, loading, isSuperAdmin, fetchHistory]);

  /**
   * Handle auto sync (only syncs if changes detected)
   */
  const handleAutoSync = async (source?: SyncSource) => {
    if (syncingSource) return; // Prevent multiple syncs

    setSyncingSource(source || 'faqs'); // Default to faqs if all sources
    try {
      const result = await knowledgeSyncService.triggerAutoSync(
        source ? { sources: [source] } : undefined
      );

      // Show results
      const successCount = result.results.filter(r => r.success).length;
      const totalCount = result.results.length;

      if (successCount === totalCount) {
        success(
          'Sync Successful',
          `${successCount} source(s) synchronized successfully`
        );
      } else {
        showError(
          'Sync Completed with Errors',
          `${successCount}/${totalCount} sources synchronized successfully`
        );
      }

      // Refresh data
      await Promise.all([fetchStatus(), fetchDiff(), fetchHistory()]);
    } catch (error) {
      console.error('Auto sync failed:', error);
      showError(
        'Sync Failed',
        error instanceof Error ? error.message : 'Failed to trigger auto sync'
      );
    } finally {
      setSyncingSource(null);
    }
  };

  /**
   * Handle force sync (overrides all changes - requires confirmation)
   */
  const handleForceSync = async (source?: SyncSource) => {
    if (syncingSource) return; // Prevent multiple syncs

    // Confirmation modal
    const confirmed = window.confirm(
      '⚠️ FORCE SYNC WARNING\n\n' +
        'This will OVERRIDE all manual changes in the database with TypeScript file contents.\n\n' +
        'Are you absolutely sure you want to proceed?'
    );

    if (!confirmed) return;

    setSyncingSource(source || 'faqs'); // Default to faqs if all sources
    try {
      const result = await knowledgeSyncService.triggerForceSync(
        source ? { sources: [source] } : undefined
      );

      // Show results
      const successCount = result.results.filter(r => r.success).length;
      const totalCount = result.results.length;

      if (successCount === totalCount) {
        success(
          'Force Sync Successful',
          `${successCount} source(s) force synchronized successfully`
        );
      } else {
        showError(
          'Force Sync Completed with Errors',
          `${successCount}/${totalCount} sources force synchronized successfully`
        );
      }

      // Refresh data
      await Promise.all([fetchStatus(), fetchDiff(), fetchHistory()]);
    } catch (error) {
      console.error('Force sync failed:', error);
      showError(
        'Force Sync Failed',
        error instanceof Error ? error.message : 'Failed to trigger force sync'
      );
    } finally {
      setSyncingSource(null);
    }
  };

  /**
   * Refresh all data
   */
  const handleRefresh = async () => {
    setLoading(true);
    await Promise.all([fetchStatus(), fetchDiff(), fetchHistory()]);
    setLoading(false);

    success('Refreshed', 'All data has been refreshed');
  };

  /**
   * Handle history page change
   */
  const handleHistoryPageChange = (page: number) => {
    setHistoryPage(page);
  };

  /**
   * Handle history filter change
   */
  const handleHistoryFilterChange = (filters: {
    source?: SyncSource;
    sync_type?: 'auto' | 'manual';
  }) => {
    setHistoryFilters(filters);
    setHistoryPage(1); // Reset to first page
  };

  // Show loading state
  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">
            Loading Knowledge Sync Dashboard...
          </p>
        </div>
      </div>
    );
  }

  // Access denied (shouldn't reach here due to redirect)
  if (!isSuperAdmin()) {
    return null;
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Knowledge Sync Dashboard
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage synchronization between TypeScript files and PostgreSQL
              database
            </p>
          </div>
          <Button onClick={handleRefresh} variant="outline" disabled={loading}>
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
        </div>

        {/* Help Alert */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>How it works</AlertTitle>
          <AlertDescription>
            This dashboard monitors changes between TypeScript knowledge files
            and the database. Use <strong>Auto Sync</strong> to safely sync only
            detected changes, or <strong>Force Sync</strong> to override all
            database content with TypeScript files.
          </AlertDescription>
        </Alert>
      </div>

      {/* Status Cards */}
      {status && (
        <div className="mb-8">
          <SyncStatusCards
            status={status}
            isLoading={!!syncingSource}
            onAutoSync={handleAutoSync}
            onForceSync={handleForceSync}
            onRefresh={fetchStatus}
          />
        </div>
      )}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="status">Differences</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Differences Tab */}
        <TabsContent value="status" className="space-y-4">
          {diff ? (
            <DiffViewer
              diff={diff}
              onApplyChanges={handleAutoSync}
              isLoading={!!syncingSource}
            />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <p>Loading differences...</p>
            </div>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {history ? (
            <SyncHistoryTable
              history={history}
              isLoading={loading}
              onPageChange={handleHistoryPageChange}
              onFilterChange={handleHistoryFilterChange}
            />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <p>Loading history...</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
