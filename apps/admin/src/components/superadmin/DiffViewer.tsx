'use client';

import { AlertCircle, ChevronDown, ChevronRight, Download } from 'lucide-react';
import React from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileChange,
  SourceDiff,
  SyncDiff,
  SyncSource,
} from '@/types/knowledge-sync.types';

interface DiffViewerProps {
  diff: SyncDiff;
  // onApplyChanges?: (source: SyncSource) => void; // TODO: Future enhancement
  // isLoading?: boolean; // TODO: Future enhancement
}

const sourceLabels: Record<SyncSource, string> = {
  faqs: 'FAQs',
  packages: 'Packages',
  business_charter: 'Business Charter',
};

const changeTypeColors: Record<FileChange['change_type'], string> = {
  added:
    'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400',
  modified:
    'bg-yellow-500/10 border-yellow-500/20 text-yellow-700 dark:text-yellow-400',
  deleted: 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400',
};

const changeTypeLabels: Record<FileChange['change_type'], string> = {
  added: 'Added',
  modified: 'Modified',
  deleted: 'Deleted',
};

function ChangeRow({ change }: { change: FileChange }) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div
      className={`border rounded-md p-3 ${changeTypeColors[change.change_type]}`}
    >
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 flex-1">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          <Badge variant="outline" className="font-mono text-xs">
            {changeTypeLabels[change.change_type]}
          </Badge>
          <code className="text-sm font-mono">{change.field}</code>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-3 space-y-2 pl-6">
          {/* Source Value (TypeScript file) */}
          {change.source_value !== null && (
            <div>
              <p className="text-xs font-semibold mb-1 text-muted-foreground">
                TypeScript File:
              </p>
              <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
                {typeof change.source_value === 'string'
                  ? change.source_value
                  : JSON.stringify(change.source_value, null, 2)}
              </pre>
            </div>
          )}

          {/* Database Value */}
          {change.db_value !== null && (
            <div>
              <p className="text-xs font-semibold mb-1 text-muted-foreground">
                Database:
              </p>
              <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
                {typeof change.db_value === 'string'
                  ? change.db_value
                  : JSON.stringify(change.db_value, null, 2)}
              </pre>
            </div>
          )}

          {change.source_value === null && change.change_type === 'deleted' && (
            <p className="text-xs italic text-muted-foreground">
              Field will be removed
            </p>
          )}

          {change.db_value === null && change.change_type === 'added' && (
            <p className="text-xs italic text-muted-foreground">
              Field will be added
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Source diff panel component
function SourceDiffPanel({ sourceDiff }: { sourceDiff: SourceDiff }) {
  const [expandAll, setExpandAll] = React.useState(false);

  if (!sourceDiff.has_changes) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No changes detected. Database is in sync with TypeScript files.
        </AlertDescription>
      </Alert>
    );
  }

  // Group changes by type
  const added = sourceDiff.changes.filter(c => c.change_type === 'added');
  const modified = sourceDiff.changes.filter(c => c.change_type === 'modified');
  const deleted = sourceDiff.changes.filter(c => c.change_type === 'deleted');

  return (
    <div className="space-y-4">
      {/* Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex gap-4">
              <div>
                <p className="text-2xl font-bold">{sourceDiff.changes_count}</p>
                <p className="text-xs text-muted-foreground">Total Changes</p>
              </div>
              {added.length > 0 && (
                <div>
                  <p className="text-2xl font-bold text-green-600">
                    {added.length}
                  </p>
                  <p className="text-xs text-muted-foreground">Added</p>
                </div>
              )}
              {modified.length > 0 && (
                <div>
                  <p className="text-2xl font-bold text-yellow-600">
                    {modified.length}
                  </p>
                  <p className="text-xs text-muted-foreground">Modified</p>
                </div>
              )}
              {deleted.length > 0 && (
                <div>
                  <p className="text-2xl font-bold text-red-600">
                    {deleted.length}
                  </p>
                  <p className="text-xs text-muted-foreground">Deleted</p>
                </div>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpandAll(!expandAll)}
            >
              {expandAll ? 'Collapse All' : 'Expand All'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Changes List */}
      <div className="space-y-2">
        {sourceDiff.changes.map((change, index) => (
          <ChangeRow key={`${change.field}-${index}`} change={change} />
        ))}
      </div>

      {/* Last Checked */}
      <p className="text-xs text-muted-foreground">
        Last checked: {new Date(sourceDiff.last_checked).toLocaleString()}
      </p>
    </div>
  );
}

// TODO: Future enhancement - Add onApplyChanges callback to apply selected changes
// TODO: Future enhancement - Add isLoading prop to show loading state during API calls
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function DiffViewer({ diff }: DiffViewerProps) {
  const handleDownloadDiff = () => {
    const diffText = JSON.stringify(diff, null, 2);
    const blob = new Blob([diffText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge-sync-diff-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Detected Changes</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Compare TypeScript source files with database content
            </p>
          </div>
          <Button onClick={handleDownloadDiff} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export Diff
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {diff.total_changes === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              All sources are in sync. No changes detected.
            </AlertDescription>
          </Alert>
        ) : (
          <Tabs defaultValue="faqs" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              {(['faqs', 'packages', 'business_charter'] as SyncSource[]).map(
                source => (
                  <TabsTrigger key={source} value={source} className="relative">
                    {sourceLabels[source]}
                    {diff[source].has_changes && (
                      <Badge variant="destructive" className="ml-2">
                        {diff[source].changes_count}
                      </Badge>
                    )}
                  </TabsTrigger>
                )
              )}
            </TabsList>
            {(['faqs', 'packages', 'business_charter'] as SyncSource[]).map(
              source => (
                <TabsContent key={source} value={source} className="mt-4">
                  <SourceDiffPanel sourceDiff={diff[source]} />
                </TabsContent>
              )
            )}
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
