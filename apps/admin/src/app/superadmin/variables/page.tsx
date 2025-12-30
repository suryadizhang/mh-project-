'use client';

import { AlertTriangle, CheckCircle, Clock, Database, Loader2, RefreshCw, Save, Sliders, X, XCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useConfigVariables } from '@/hooks/useApi';
import { configService, ConfigVariable, ApprovalRequest } from '@/services/api';

/**
 * UI Variable interface - maps from backend ConfigVariable
 */
interface Variable {
  key: string;
  value: string | number | boolean;
  type: 'string' | 'number' | 'boolean';
  category:
  | 'pricing'
  | 'business'
  | 'feature'
  | 'environment'
  | 'ai'
  | 'monitoring';
  description: string;
  source: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  lastModified?: string;
  // Backend fields for updates
  backendCategory?: string;
}

/**
 * Map backend category to frontend category
 */
function mapCategoryToFrontend(
  backendCategory: string
): Variable['category'] {
  const categoryMap: Record<string, Variable['category']> = {
    pricing: 'pricing',
    deposit: 'pricing', // deposit maps to pricing for display
    travel: 'pricing', // travel maps to pricing for display
    booking: 'business',
    feature: 'feature',
    ai: 'ai',
    environment: 'environment',
    monitoring: 'monitoring',
  };
  return categoryMap[backendCategory] || 'business';
}

/**
 * Determine priority based on category
 */
function determinePriority(category: string): Variable['priority'] {
  const priorityMap: Record<string, Variable['priority']> = {
    pricing: 'critical',
    deposit: 'critical',
    travel: 'high',
    booking: 'high',
    feature: 'medium',
    ai: 'high',
    environment: 'critical',
    monitoring: 'medium',
  };
  return priorityMap[category] || 'medium';
}

/**
 * Determine value type from the actual value
 */
function determineType(value: unknown): Variable['type'] {
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  return 'string';
}

/**
 * Map backend ConfigVariable to frontend Variable
 */
function mapToVariable(cv: ConfigVariable): Variable {
  return {
    key: cv.key,
    value: cv.value as string | number | boolean,
    type: determineType(cv.value),
    category: mapCategoryToFrontend(cv.category),
    description: cv.description || `${cv.category} configuration`,
    source: 'SSoT Database',
    priority: determinePriority(cv.category),
    lastModified: cv.updated_at
      ? new Date(cv.updated_at).toISOString().split('T')[0]
      : undefined,
    backendCategory: cv.category, // Keep original for API calls
  };
}

export default function VariablesManagementPage() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [pendingChanges, setPendingChanges] = useState<
    Record<string, string | number | boolean>
  >({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequest[]>([]);
  const [approvalsLoading, setApprovalsLoading] = useState(false);

  // Fetch variables from SSoT API
  const {
    data: configVars,
    loading,
    error,
    refetch,
  } = useConfigVariables();

  // Transform API data to UI format when it changes
  useEffect(() => {
    if (configVars && Array.isArray(configVars)) {
      const mappedVariables = configVars.map(mapToVariable);
      setVariables(mappedVariables);
    }
  }, [configVars]);

  // Fetch pending approvals for two-person approval workflow
  const fetchPendingApprovals = useCallback(async () => {
    setApprovalsLoading(true);
    try {
      const response = await configService.getPendingApprovals();
      if (response.success && response.data) {
        // API returns { data: ApprovalRequest[], total: number }
        setPendingApprovals(response.data.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch pending approvals:', err);
    } finally {
      setApprovalsLoading(false);
    }
  }, []);

  // Load pending approvals on mount and after saves
  useEffect(() => {
    fetchPendingApprovals();
  }, [fetchPendingApprovals]);

  const filteredVariables = variables.filter(variable => {
    const matchesSearch =
      variable.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
      variable.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory =
      selectedCategory === 'all' || variable.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleValueChange = (key: string, value: string | number | boolean) => {
    setPendingChanges(prev => ({
      ...prev,
      [key]: value,
    }));
    // Clear any previous save status when changes are made
    setSaveSuccess(false);
    setSaveError(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      // Separate changes by priority - critical/high need approval, medium/low can be direct
      const directUpdates: Array<{ variable: Variable; key: string; newValue: string | number | boolean }> = [];
      const approvalRequests: Array<{ variable: Variable; key: string; newValue: string | number | boolean }> = [];

      Object.entries(pendingChanges).forEach(([key, newValue]) => {
        const variable = variables.find((v) => v.key === key);
        if (!variable) return;

        const priority = determinePriority(variable.backendCategory || variable.category);
        if (priority === 'critical' || priority === 'high') {
          approvalRequests.push({ variable, key, newValue });
        } else {
          directUpdates.push({ variable, key, newValue });
        }
      });

      const results: Array<{ success: boolean; key: string; error?: string; needsApproval?: boolean }> = [];

      // Process direct updates (medium/low priority)
      if (directUpdates.length > 0) {
        const updatePromises = directUpdates.map(async ({ variable, key, newValue }) => {
          const backendCategory = variable.backendCategory || variable.category;
          const response = await configService.updateVariable(backendCategory, key, { value: newValue });
          return { success: response.success, key, error: response.error };
        });
        const directResults = await Promise.all(updatePromises);
        results.push(...directResults);
      }

      // Process approval requests (critical/high priority)
      if (approvalRequests.length > 0) {
        const approvalPromises = approvalRequests.map(async ({ variable, key, newValue }) => {
          const backendCategory = variable.backendCategory || variable.category;
          const response = await configService.requestApproval({
            category: backendCategory,
            key,
            proposed_value: newValue,
            reason: `Change requested via admin panel: ${variable.key} from ${variable.value} to ${newValue}`,
          });
          return {
            success: response.success,
            key,
            error: response.error,
            needsApproval: true,
          };
        });
        const approvalResults = await Promise.all(approvalPromises);
        results.push(...approvalResults);
      }

      // Check for failures
      const failures = results.filter((r) => !r.success);
      const approvalsPending = results.filter((r) => r.success && r.needsApproval);

      if (failures.length > 0) {
        setSaveError(
          `Failed to update ${failures.length} variable(s): ${failures.map((f) => f.key).join(', ')}`
        );
      } else if (approvalsPending.length > 0 && directUpdates.length === 0) {
        // All changes need approval
        setSaveSuccess(true);
        setSaveError(`${approvalsPending.length} change(s) submitted for approval. A second administrator must approve before changes take effect.`);
        setPendingChanges({});
        await fetchPendingApprovals();
      } else if (approvalsPending.length > 0) {
        // Mixed: some direct, some need approval
        setSaveSuccess(true);
        setSaveError(`${directUpdates.length} change(s) saved. ${approvalsPending.length} critical/high priority change(s) submitted for approval.`);
        setPendingChanges({});
        await refetch();
        await fetchPendingApprovals();
      } else {
        setSaveSuccess(true);
        setPendingChanges({});
        await refetch();
      }
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : 'Failed to save changes'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleRefresh = useCallback(async () => {
    await refetch();
    setPendingChanges({});
    setSaveSuccess(false);
    setSaveError(null);
  }, [refetch]);

  const handleInvalidateCache = async () => {
    try {
      const result = await configService.invalidateCache();
      if (result.success) {
        await handleRefresh();
        alert('Cache invalidated successfully!');
      } else {
        alert(`Failed to invalidate cache: ${result.error}`);
      }
    } catch (err) {
      alert('Failed to invalidate cache');
    }
  };

  const handleApprove = async (approvalId: string) => {
    try {
      const response = await configService.approveRequest(approvalId, 'Approved via admin panel');
      if (response.success) {
        await fetchPendingApprovals();
        await refetch();
        alert('Approval granted! Variable has been updated.');
      } else {
        alert(`Failed to approve: ${response.error}`);
      }
    } catch (err) {
      alert('Failed to approve request');
    }
  };

  const handleReject = async (approvalId: string) => {
    const reason = window.prompt('Please provide a reason for rejection:');
    if (reason === null) return; // User cancelled

    try {
      const response = await configService.rejectRequest(approvalId, reason || 'Rejected via admin panel');
      if (response.success) {
        await fetchPendingApprovals();
        alert('Request rejected.');
      } else {
        alert(`Failed to reject: ${response.error}`);
      }
    } catch (err) {
      alert('Failed to reject request');
    }
  };

  const hasChanges = Object.keys(pendingChanges).length > 0;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'pricing':
        return '💰';
      case 'business':
        return '📋';
      case 'feature':
        return '🚀';
      case 'environment':
        return '⚙️';
      case 'ai':
        return '🤖';
      case 'monitoring':
        return '📊';
      default:
        return '📝';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-blue-600 bg-blue-100';
      case 'low':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Sliders className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Variables Management
            </h1>
            <p className="text-gray-600">
              Manage system-wide variables and configuration settings
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Refresh Button */}
          <Button
            onClick={handleRefresh}
            disabled={loading}
            variant="outline"
            className="border-gray-300"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {/* Cache Invalidate Button */}
          <Button
            onClick={handleInvalidateCache}
            variant="outline"
            className="border-orange-300 text-orange-600 hover:bg-orange-50"
          >
            <Database className="w-4 h-4 mr-2" />
            Invalidate Cache
          </Button>

          {/* Save Button - Only shown when there are changes */}
          {hasChanges && (
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-green-600 hover:bg-green-700"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes ({Object.keys(pendingChanges).length})
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Success Message */}
      {saveSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-green-800">Changes Saved Successfully</h3>
              <p className="text-sm text-green-700">
                All configuration changes have been applied and cache has been refreshed.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {saveError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <XCircle className="w-5 h-5 text-red-600 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Failed to Save Changes</h3>
                <p className="text-sm text-red-700">{saveError}</p>
              </div>
            </div>
            <button
              onClick={() => setSaveError(null)}
              className="text-red-600 hover:text-red-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Pending Approvals Section */}
      {pendingApprovals.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <Clock className="w-5 h-5 text-purple-600 mr-3" />
              <h3 className="text-sm font-medium text-purple-800">
                Pending Approvals ({pendingApprovals.length})
              </h3>
            </div>
            {approvalsLoading && (
              <span className="text-xs text-purple-600">Loading...</span>
            )}
          </div>
          <div className="space-y-3">
            {pendingApprovals.map((approval) => (
              <div
                key={approval.id}
                className="bg-white border border-purple-100 rounded-md p-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-purple-700 bg-purple-100 px-2 py-0.5 rounded">
                        {approval.category}
                      </span>
                      <span className="font-medium text-gray-900">
                        {approval.key}
                      </span>
                    </div>
                    <div className="mt-1 text-sm text-gray-600">
                      <span className="text-red-600 line-through">
                        {JSON.stringify(approval.current_value)}
                      </span>
                      <span className="mx-2">→</span>
                      <span className="text-green-600 font-medium">
                        {JSON.stringify(approval.proposed_value)}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      Requested by {approval.requester_name || approval.requester_id} •{' '}
                      {new Date(approval.created_at).toLocaleString()}
                      {approval.reason && (
                        <span className="ml-2 italic">"{approval.reason}"</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleApprove(approval.id)}
                      className="px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleReject(approval.id)}
                      className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warning Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-amber-600 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-amber-800">Important</h3>
            <p className="text-sm text-amber-700">
              Changes to these variables affect the entire system. Critical and
              high priority variables require two-person approval before taking
              effect. Medium and low priority changes are applied immediately.
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <Input
          placeholder="Search variables..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="flex-1"
        />
        <select
          value={selectedCategory}
          onChange={e => setSelectedCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Categories</option>
          <option value="pricing">💰 Pricing</option>
          <option value="business">📋 Business Rules</option>
          <option value="feature">🚀 Feature Flags</option>
          <option value="environment">⚙️ Environment</option>
          <option value="ai">🤖 AI System</option>
          <option value="monitoring">📊 Monitoring</option>
        </select>
      </div>

      {/* Variables List */}
      <Tabs
        value={selectedCategory}
        onValueChange={setSelectedCategory}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="all">All ({variables.length})</TabsTrigger>
          <TabsTrigger value="pricing">
            💰 Pricing ({variables.filter(v => v.category === 'pricing').length}
            )
          </TabsTrigger>
          <TabsTrigger value="business">
            📋 Business (
            {variables.filter(v => v.category === 'business').length})
          </TabsTrigger>
          <TabsTrigger value="feature">
            🚀 Features (
            {variables.filter(v => v.category === 'feature').length})
          </TabsTrigger>
          <TabsTrigger value="environment">
            ⚙️ Environment (
            {variables.filter(v => v.category === 'environment').length})
          </TabsTrigger>
          <TabsTrigger value="ai">
            🤖 AI ({variables.filter(v => v.category === 'ai').length})
          </TabsTrigger>
          <TabsTrigger value="monitoring">
            📊 Monitor (
            {variables.filter(v => v.category === 'monitoring').length})
          </TabsTrigger>
        </TabsList>

        <div className="mt-6">
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Variable
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Modified
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredVariables.map((variable, index) => {
                    const currentValue =
                      pendingChanges[variable.key] !== undefined
                        ? pendingChanges[variable.key]
                        : variable.value;

                    return (
                      <tr
                        key={variable.key}
                        className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                      >
                        <td className="px-6 py-4">
                          <div>
                            <div className="text-sm font-medium text-gray-900 flex items-center flex-wrap gap-1">
                              {getCategoryIcon(variable.category)}
                              <span className="ml-2">{variable.key}</span>
                              {pendingChanges[variable.key] !== undefined && (
                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                                  Modified
                                </span>
                              )}
                              {pendingApprovals.some(
                                a => a.key === variable.key && a.category === variable.category
                              ) && (
                                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    Pending Approval
                                  </span>
                                )}
                            </div>
                            <div className="text-sm text-gray-500 mt-1">
                              {variable.description}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              Source: {variable.source}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="w-48">
                            {variable.type === 'boolean' ? (
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  checked={currentValue as boolean}
                                  onChange={e =>
                                    handleValueChange(
                                      variable.key,
                                      e.target.checked
                                    )
                                  }
                                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                />
                                <span className="text-sm">
                                  {currentValue ? 'Enabled' : 'Disabled'}
                                </span>
                              </div>
                            ) : variable.key.includes('PASSWORD') ||
                              variable.key.includes('SECRET') ||
                              variable.key.includes('DATABASE_URL') ? (
                              <Input
                                type="password"
                                value={currentValue as string}
                                onChange={e =>
                                  handleValueChange(
                                    variable.key,
                                    e.target.value
                                  )
                                }
                                className="text-sm"
                              />
                            ) : variable.type === 'number' ? (
                              <Input
                                type="number"
                                value={currentValue as number}
                                onChange={e =>
                                  handleValueChange(
                                    variable.key,
                                    parseFloat(e.target.value) || 0
                                  )
                                }
                                className="text-sm"
                              />
                            ) : (
                              <Input
                                type="text"
                                value={currentValue as string}
                                onChange={e =>
                                  handleValueChange(
                                    variable.key,
                                    e.target.value
                                  )
                                }
                                className="text-sm"
                              />
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-sm capitalize">
                            {variable.category}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(variable.priority)}`}
                          >
                            {variable.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {variable.lastModified}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Tabs>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {variables.length}
            </p>
            <p className="text-sm text-gray-600">Total Variables</p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">
              {variables.filter(v => v.priority === 'critical').length}
            </p>
            <p className="text-sm text-gray-600">Critical</p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">
              {variables.filter(v => v.priority === 'high').length}
            </p>
            <p className="text-sm text-gray-600">High Priority</p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-600">
              {Object.keys(pendingChanges).length}
            </p>
            <p className="text-sm text-gray-600">Pending Changes</p>
          </div>
        </div>
      </div>
    </div>
  );
}
