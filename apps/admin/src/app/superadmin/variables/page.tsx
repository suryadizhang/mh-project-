'use client';

import { AlertTriangle, Loader2, Save, Sliders } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

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
}

export default function VariablesManagementPage() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [pendingChanges, setPendingChanges] = useState<
    Record<string, string | number | boolean>
  >({});
  // TODO: Implement sync status tracking
  // const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');
  // const [lastSync, setLastSync] = useState<string>('');
  // const [dataSource, setDataSource] = useState<'local' | 'gsm' | 'hybrid'>('hybrid');

  // Sample data - in real implementation, fetch from API
  useEffect(() => {
    const sampleVariables: Variable[] = [
      // Pricing Variables (Critical)
      {
        key: 'BASE_PRICE_PER_PERSON',
        value: 75,
        type: 'number',
        category: 'pricing',
        description: 'Base hibachi price per person before add-ons',
        source: 'ai_booking_config_v2.py',
        priority: 'critical',
        lastModified: '2025-01-30',
      },
      {
        key: 'DEPOSIT_AMOUNT',
        value: 100,
        type: 'number',
        category: 'pricing',
        description: 'Fixed deposit amount for all bookings',
        source: 'faq.json, policies.json',
        priority: 'critical',
        lastModified: '2025-01-30',
      },
      {
        key: 'TRAVEL_FEE_BASE_RATE',
        value: 1.25,
        type: 'number',
        category: 'pricing',
        description: 'Base travel fee per mile',
        source: 'ai_booking_config_v2.py',
        priority: 'critical',
        lastModified: '2025-01-28',
      },

      // Business Rules (High Priority)
      {
        key: 'MINIMUM_GUESTS',
        value: 8,
        type: 'number',
        category: 'business',
        description: 'Minimum number of guests required for booking',
        source: 'ai_booking_config_v2.py',
        priority: 'high',
        lastModified: '2025-01-25',
      },
      {
        key: 'MAXIMUM_GUESTS',
        value: 20,
        type: 'number',
        category: 'business',
        description: 'Maximum guests per chef',
        source: 'ai_booking_config_v2.py',
        priority: 'high',
        lastModified: '2025-01-25',
      },
      {
        key: 'ADVANCE_BOOKING_HOURS',
        value: 48,
        type: 'number',
        category: 'business',
        description: 'Minimum advance notice required for booking',
        source: 'policies.json',
        priority: 'high',
        lastModified: '2025-01-20',
      },

      // Feature Flags (Medium Priority)
      {
        key: 'FEATURE_AI_BOOKING_V3',
        value: true,
        type: 'boolean',
        category: 'feature',
        description: 'Enable AI Booking System V3',
        source: 'env.ts',
        priority: 'medium',
        lastModified: '2025-01-30',
      },
      {
        key: 'FEATURE_TRAVEL_FEE_V2',
        value: false,
        type: 'boolean',
        category: 'feature',
        description: 'Enable Travel Fee Calculation V2',
        source: 'env.ts',
        priority: 'medium',
        lastModified: '2025-01-28',
      },

      // AI System Variables
      {
        key: 'AI_MODEL_VERSION',
        value: 'gpt-4o',
        type: 'string',
        category: 'ai',
        description: 'OpenAI model version for customer support',
        source: 'ai_booking_config_v2.py',
        priority: 'high',
        lastModified: '2025-01-30',
      },
      {
        key: 'AI_MAX_TOKENS',
        value: 1500,
        type: 'number',
        category: 'ai',
        description: 'Maximum tokens for AI responses',
        source: 'ai_booking_config_v2.py',
        priority: 'medium',
        lastModified: '2025-01-25',
      },

      // Environment Variables
      {
        key: 'DATABASE_URL',
        value: '***PROTECTED***',
        type: 'string',
        category: 'environment',
        description: 'Database connection string',
        source: '.env',
        priority: 'critical',
        lastModified: '2025-01-15',
      },

      // Monitoring Variables
      {
        key: 'ERROR_RATE_THRESHOLD',
        value: 0.05,
        type: 'number',
        category: 'monitoring',
        description: 'Alert threshold for error rate (5%)',
        source: 'monitoring_config.py',
        priority: 'medium',
        lastModified: '2025-01-20',
      },
    ];

    setVariables(sampleVariables);
    setLoading(false);
  }, []);

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
  };

  const handleSave = async () => {
    setSaving(true);
    // In real implementation, send API request to update variables
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Update local state
      setVariables(prev =>
        prev.map(variable =>
          pendingChanges[variable.key] !== undefined
            ? {
                ...variable,
                value: pendingChanges[variable.key],
                lastModified: new Date().toISOString().split('T')[0],
              }
            : variable
        )
      );

      setPendingChanges({});
      alert('Variables updated successfully!');
    } catch {
      alert('Error updating variables');
    } finally {
      setSaving(false);
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

      {/* Warning Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-amber-600 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-amber-800">Important</h3>
            <p className="text-sm text-amber-700">
              Changes to these variables affect the entire system. Critical
              variables (pricing, business rules) require careful consideration
              as they impact customer bookings and calculations.
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
                            <div className="text-sm font-medium text-gray-900 flex items-center">
                              {getCategoryIcon(variable.category)}
                              <span className="ml-2">{variable.key}</span>
                              {pendingChanges[variable.key] !== undefined && (
                                <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                                  Modified
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
