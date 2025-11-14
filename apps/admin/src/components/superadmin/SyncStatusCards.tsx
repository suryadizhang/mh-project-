'use client';

import { formatDistanceToNow } from 'date-fns';
import { AlertCircle, CheckCircle, Clock, RefreshCw, Zap } from 'lucide-react';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  SourceStatus,
  SyncSource,
  SyncStatusResponse,
} from '@/types/knowledge-sync.types';

interface SyncStatusCardsProps {
  status: SyncStatusResponse;
  isLoading?: boolean;
  onAutoSync: (source?: SyncSource) => Promise<void> | void;
  onForceSync: (source?: SyncSource) => Promise<void> | void;
  onRefresh: () => void;
}

const sourceLabels: Record<SyncSource, string> = {
  faqs: 'FAQs',
  packages: 'Packages',
  business_charter: 'Business Charter',
};

const sourceDescriptions: Record<SyncSource, string> = {
  faqs: 'Customer frequently asked questions',
  packages: 'Hibachi party packages and pricing',
  business_charter: 'Company policies and information',
};

const getStatusBadge = (status: SourceStatus['status']) => {
  switch (status) {
    case 'in_sync':
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle className="w-3 h-3 mr-1" />
          In Sync
        </Badge>
      );
    case 'out_of_sync':
      return (
        <Badge variant="destructive">
          <AlertCircle className="w-3 h-3 mr-1" />
          Out of Sync
        </Badge>
      );
    case 'syncing':
      return (
        <Badge variant="secondary">
          <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
          Syncing...
        </Badge>
      );
    case 'error':
      return (
        <Badge variant="destructive">
          <AlertCircle className="w-3 h-3 mr-1" />
          Error
        </Badge>
      );
    case 'never_synced':
      return (
        <Badge variant="outline">
          <Clock className="w-3 h-3 mr-1" />
          Never Synced
        </Badge>
      );
  }
};

const getLastSyncText = (lastSyncAt: string | null) => {
  if (!lastSyncAt) return 'Never synced';
  try {
    return `${formatDistanceToNow(new Date(lastSyncAt), { addSuffix: true })}`;
  } catch {
    return 'Invalid date';
  }
};

export function SyncStatusCards({
  status,
  isLoading = false,
  onAutoSync,
  onForceSync,
  onRefresh,
}: SyncStatusCardsProps) {
  const [syncingSource, setSyncingSource] = React.useState<SyncSource | null>(
    null
  );

  const handleAutoSync = async (source: SyncSource) => {
    setSyncingSource(source);
    try {
      await onAutoSync(source);
    } finally {
      setSyncingSource(null);
    }
  };

  const handleForceSync = async (source: SyncSource) => {
    setSyncingSource(source);
    try {
      await onForceSync(source);
    } finally {
      setSyncingSource(null);
    }
  };

  const sources: SyncSource[] = ['faqs', 'packages', 'business_charter'];

  return (
    <div className="space-y-4">
      {/* Header with Refresh Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Sync Status</h2>
          <p className="text-muted-foreground">
            Monitor and manage knowledge base synchronization
          </p>
        </div>
        <Button
          onClick={onRefresh}
          disabled={isLoading}
          variant="outline"
          size="sm"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`}
          />
          Refresh
        </Button>
      </div>

      {/* Status Cards Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        {sources.map(source => {
          const sourceStatus = status[source];
          const isSyncing = syncingSource === source;

          return (
            <Card key={source} className="relative">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{sourceLabels[source]}</CardTitle>
                  {getStatusBadge(sourceStatus.status)}
                </div>
                <CardDescription>{sourceDescriptions[source]}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Sync Information */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Sync:</span>
                    <span className="font-medium">
                      {getLastSyncText(sourceStatus.last_sync_at)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Sync Type:</span>
                    <span className="font-medium">
                      {sourceStatus.last_sync_type || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">
                      Changes Detected:
                    </span>
                    <Badge
                      variant={
                        sourceStatus.changes_detected > 0
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {sourceStatus.changes_detected}
                    </Badge>
                  </div>
                  {sourceStatus.changes_applied > 0 && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        Changes Applied:
                      </span>
                      <Badge variant="default">
                        {sourceStatus.changes_applied}
                      </Badge>
                    </div>
                  )}
                </div>

                {/* Error Message */}
                {sourceStatus.error_message && (
                  <div className="p-2 bg-destructive/10 rounded-md">
                    <p className="text-xs text-destructive">
                      {sourceStatus.error_message}
                    </p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleAutoSync(source)}
                    disabled={isSyncing || sourceStatus.status === 'syncing'}
                    variant="default"
                    size="sm"
                    className="flex-1"
                  >
                    <Zap className="w-3 h-3 mr-1" />
                    Auto Sync
                  </Button>
                  <Button
                    onClick={() => handleForceSync(source)}
                    disabled={isSyncing || sourceStatus.status === 'syncing'}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Force
                  </Button>
                </div>
              </CardContent>

              {/* Loading Overlay */}
              {isSyncing && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center rounded-lg">
                  <RefreshCw className="w-8 h-8 animate-spin text-primary" />
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
