'use client';

import { formatDistanceToNow } from 'date-fns';
import {
  AlertCircle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
} from 'lucide-react';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  SyncHistoryRecord,
  SyncHistoryResponse,
  SyncSource,
} from '@/types/knowledge-sync.types';

interface SyncHistoryTableProps {
  history: SyncHistoryResponse;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onFilterChange: (filters: {
    source?: SyncSource;
    sync_type?: 'auto' | 'manual';
  }) => void;
}

const sourceLabels: Record<SyncSource, string> = {
  faqs: 'FAQs',
  packages: 'Packages',
  business_charter: 'Business Charter',
};

const getStatusBadge = (status: SyncHistoryRecord['status']) => {
  switch (status) {
    case 'success':
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle className="w-3 h-3 mr-1" />
          Success
        </Badge>
      );
    case 'partial':
      return (
        <Badge variant="secondary">
          <AlertCircle className="w-3 h-3 mr-1" />
          Partial
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="destructive">
          <AlertCircle className="w-3 h-3 mr-1" />
          Failed
        </Badge>
      );
  }
};

const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
};

export function SyncHistoryTable({
  history,
  isLoading = false,
  onPageChange,
  onFilterChange,
}: SyncHistoryTableProps) {
  const [selectedSource, setSelectedSource] = React.useState<string>('all');
  const [selectedType, setSelectedType] = React.useState<string>('all');

  const handleSourceChange = (value: string) => {
    setSelectedSource(value);
    onFilterChange({
      source: value === 'all' ? undefined : (value as SyncSource),
      sync_type:
        selectedType === 'all'
          ? undefined
          : (selectedType as 'auto' | 'manual'),
    });
  };

  const handleTypeChange = (value: string) => {
    setSelectedType(value);
    onFilterChange({
      source:
        selectedSource === 'all' ? undefined : (selectedSource as SyncSource),
      sync_type: value === 'all' ? undefined : (value as 'auto' | 'manual'),
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Sync History</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              View past synchronization operations and their results
            </p>
          </div>

          {/* Filters */}
          <div className="flex gap-2">
            <Select value={selectedSource} onValueChange={handleSourceChange}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="faqs">FAQs</SelectItem>
                <SelectItem value="packages">Packages</SelectItem>
                <SelectItem value="business_charter">
                  Business Charter
                </SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedType} onValueChange={handleTypeChange}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="auto">Auto Sync</SelectItem>
                <SelectItem value="manual">Manual Sync</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Changes</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <Clock className="w-6 h-6 animate-spin mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">
                      Loading history...
                    </p>
                  </TableCell>
                </TableRow>
              ) : history.records.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <AlertCircle className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      No sync history found
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                history.records.map(record => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium">
                          {formatDistanceToNow(new Date(record.completed_at), {
                            addSuffix: true,
                          })}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(record.completed_at).toLocaleString()}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {sourceLabels[record.source]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          record.sync_type === 'auto' ? 'secondary' : 'default'
                        }
                      >
                        {record.sync_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-col items-end">
                        <span className="text-sm font-medium">
                          {record.changes_applied}/{record.changes_detected}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          applied/detected
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(record.status)}</TableCell>
                    <TableCell>
                      <code className="text-xs">
                        {formatDuration(record.duration_ms)}
                      </code>
                    </TableCell>
                    <TableCell>
                      {record.error_message ? (
                        <div className="max-w-xs truncate text-xs text-destructive">
                          {record.error_message}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {history.total_pages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <p className="text-sm text-muted-foreground">
              Showing {(history.page - 1) * history.per_page + 1} to{' '}
              {Math.min(history.page * history.per_page, history.total)} of{' '}
              {history.total} records
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(history.page - 1)}
                disabled={history.page === 1 || isLoading}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>
              <div className="flex items-center gap-2">
                <span className="text-sm">
                  Page {history.page} of {history.total_pages}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(history.page + 1)}
                disabled={history.page === history.total_pages || isLoading}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
