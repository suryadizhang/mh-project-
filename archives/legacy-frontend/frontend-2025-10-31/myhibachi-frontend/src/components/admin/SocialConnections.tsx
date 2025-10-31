import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Settings,
  Link,
  CheckCircle,
  AlertCircle,
  Unlink,
  RefreshCw,
  Key,
  Globe,
  MessageCircle,
} from 'lucide-react';

interface SocialAccount {
  id: string;
  platform: 'instagram' | 'facebook' | 'google' | 'yelp';
  account_name: string;
  account_id: string;
  is_active: boolean;
  connected_at: string;
  last_sync: string | null;
  sync_status: 'healthy' | 'error' | 'pending';
  error_message: string | null;
  credentials_valid: boolean;
  permissions: string[];
  settings: {
    auto_reply_enabled: boolean;
    dm_monitoring: boolean;
    review_monitoring: boolean;
    comment_monitoring: boolean;
    webhook_url?: string;
  };
}

interface ConnectionForm {
  platform: string;
  account_id: string;
  access_token: string;
  refresh_token?: string;
  page_id?: string;
  business_id?: string;
  webhook_secret?: string;
}

const PLATFORM_INFO = {
  instagram: {
    name: 'Instagram',
    color: 'bg-pink-100 text-pink-800',
    icon: MessageCircle,
    description: 'Connect Instagram Business account for DMs and comments',
  },
  facebook: {
    name: 'Facebook',
    color: 'bg-blue-100 text-blue-800',
    icon: MessageCircle,
    description: 'Connect Facebook Page for messages and comments',
  },
  google: {
    name: 'Google Business',
    color: 'bg-green-100 text-green-800',
    icon: Globe,
    description: 'Connect Google Business Profile for reviews and Q&A',
  },
  yelp: {
    name: 'Yelp',
    color: 'bg-red-100 text-red-800',
    icon: MessageCircle,
    description: 'Connect Yelp Business account for reviews',
  },
};

export function SocialConnections() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showConnectionDialog, setShowConnectionDialog] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [connectionForm, setConnectionForm] = useState<ConnectionForm>({
    platform: '',
    account_id: '',
    access_token: '',
    refresh_token: '',
    page_id: '',
    business_id: '',
    webhook_secret: '',
  });
  const [testingConnection, setTestingConnection] = useState(false);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/social/accounts');
      const data = await response.json();

      if (data.success) {
        setAccounts(data.data.accounts);
      }
    } catch (error) {
      console.error('Error fetching accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectAccount = async () => {
    try {
      const response = await fetch('/api/admin/social/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(connectionForm),
      });

      const data = await response.json();

      if (data.success) {
        setShowConnectionDialog(false);
        setConnectionForm({
          platform: '',
          account_id: '',
          access_token: '',
          refresh_token: '',
          page_id: '',
          business_id: '',
          webhook_secret: '',
        });
        fetchAccounts();
      }
    } catch (error) {
      console.error('Error connecting account:', error);
    }
  };

  const disconnectAccount = async (accountId: string) => {
    try {
      const response = await fetch(
        `/api/admin/social/account/${accountId}/disconnect`,
        {
          method: 'POST',
        }
      );

      if (response.ok) {
        fetchAccounts();
      }
    } catch (error) {
      console.error('Error disconnecting account:', error);
    }
  };

  const testConnection = async (accountId: string) => {
    try {
      setTestingConnection(true);
      const response = await fetch(
        `/api/admin/social/account/${accountId}/test`,
        {
          method: 'POST',
        }
      );

      const data = await response.json();

      if (data.success) {
        // Refresh accounts to get updated sync status
        fetchAccounts();
      }
    } catch (error) {
      console.error('Error testing connection:', error);
    } finally {
      setTestingConnection(false);
    }
  };

  const syncAccount = async (accountId: string) => {
    try {
      const response = await fetch(
        `/api/admin/social/account/${accountId}/sync`,
        {
          method: 'POST',
        }
      );

      if (response.ok) {
        fetchAccounts();
      }
    } catch (error) {
      console.error('Error syncing account:', error);
    }
  };

  const updateAccountSettings = async (accountId: string, settings: any) => {
    try {
      const response = await fetch(
        `/api/admin/social/account/${accountId}/settings`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ settings }),
        }
      );

      if (response.ok) {
        fetchAccounts();
      }
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const getSyncStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'pending':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const getSyncStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      case 'pending':
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const AccountCard = ({ account }: { account: SocialAccount }) => {
    const platform = PLATFORM_INFO[account.platform];
    const Icon = platform.icon;

    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Icon className="h-8 w-8 text-gray-500" />
              <div>
                <h3 className="font-medium">{platform.name}</h3>
                <p className="text-sm text-gray-600">{account.account_name}</p>
                <Badge className={platform.color}>{account.account_id}</Badge>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <div
                className={`flex items-center space-x-1 ${getSyncStatusColor(
                  account.sync_status
                )}`}
              >
                {getSyncStatusIcon(account.sync_status)}
                <span className="text-sm capitalize">
                  {account.sync_status}
                </span>
              </div>
            </div>
          </div>

          {account.error_message && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{account.error_message}</p>
            </div>
          )}

          <div className="space-y-3 mb-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Auto Reply</span>
              <input
                type="checkbox"
                checked={account.settings.auto_reply_enabled}
                onChange={e =>
                  updateAccountSettings(account.id, {
                    ...account.settings,
                    auto_reply_enabled: e.target.checked,
                  })
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">DM Monitoring</span>
              <input
                type="checkbox"
                checked={account.settings.dm_monitoring}
                onChange={e =>
                  updateAccountSettings(account.id, {
                    ...account.settings,
                    dm_monitoring: e.target.checked,
                  })
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">Review Monitoring</span>
              <input
                type="checkbox"
                checked={account.settings.review_monitoring}
                onChange={e =>
                  updateAccountSettings(account.id, {
                    ...account.settings,
                    review_monitoring: e.target.checked,
                  })
                }
              />
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs text-gray-500 mb-4">
            <span>
              Connected: {new Date(account.connected_at).toLocaleDateString()}
            </span>
            {account.last_sync && (
              <span>
                • Last sync: {new Date(account.last_sync).toLocaleString()}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => testConnection(account.id)}
              disabled={testingConnection}
            >
              <CheckCircle className="h-4 w-4 mr-1" />
              Test
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => syncAccount(account.id)}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Sync
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => disconnectAccount(account.id)}
            >
              <Unlink className="h-4 w-4 mr-1" />
              Disconnect
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Social Media Connections</h1>
        <Button onClick={() => setShowConnectionDialog(true)}>
          <Link className="h-4 w-4 mr-1" />
          Add Connection
        </Button>
      </div>

      {/* Connected Accounts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-8">
            Loading connections...
          </div>
        ) : accounts.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <div className="text-gray-500 mb-4">
              No social media accounts connected
            </div>
            <Button onClick={() => setShowConnectionDialog(true)}>
              Connect Your First Account
            </Button>
          </div>
        ) : (
          accounts.map(account => (
            <AccountCard key={account.id} account={account} />
          ))
        )}
      </div>

      {/* Available Platforms */}
      <div>
        <h2 className="text-lg font-medium mb-4">Available Platforms</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(PLATFORM_INFO).map(([key, platform]) => {
            const isConnected = accounts.some(
              account => account.platform === key
            );
            const Icon = platform.icon;

            return (
              <Card
                key={key}
                className={`cursor-pointer transition-colors ${
                  isConnected ? 'bg-gray-50' : 'hover:bg-gray-50'
                }`}
                onClick={() =>
                  !isConnected &&
                  (setSelectedPlatform(key), setShowConnectionDialog(true))
                }
              >
                <CardContent className="p-4 text-center">
                  <Icon className="h-8 w-8 mx-auto mb-2 text-gray-500" />
                  <h3 className="font-medium mb-1">{platform.name}</h3>
                  <p className="text-xs text-gray-600 mb-3">
                    {platform.description}
                  </p>
                  {isConnected ? (
                    <Badge className={platform.color}>Connected</Badge>
                  ) : (
                    <Button variant="outline" size="sm">
                      Connect
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Connection Dialog */}
      <Dialog
        open={showConnectionDialog}
        onOpenChange={setShowConnectionDialog}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Connect Social Account</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Platform</label>
              <Select
                value={selectedPlatform || connectionForm.platform}
                onValueChange={value => {
                  setSelectedPlatform(value);
                  setConnectionForm({ ...connectionForm, platform: value });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PLATFORM_INFO).map(([key, platform]) => (
                    <SelectItem key={key} value={key}>
                      {platform.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Account ID
              </label>
              <Input
                placeholder="Enter account ID"
                value={connectionForm.account_id}
                onChange={e =>
                  setConnectionForm({
                    ...connectionForm,
                    account_id: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Access Token
              </label>
              <Textarea
                placeholder="Enter access token"
                value={connectionForm.access_token}
                onChange={e =>
                  setConnectionForm({
                    ...connectionForm,
                    access_token: e.target.value,
                  })
                }
                rows={3}
              />
            </div>

            {(selectedPlatform === 'facebook' ||
              selectedPlatform === 'instagram') && (
              <>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Page ID (Facebook/Instagram)
                  </label>
                  <Input
                    placeholder="Enter page ID"
                    value={connectionForm.page_id}
                    onChange={e =>
                      setConnectionForm({
                        ...connectionForm,
                        page_id: e.target.value,
                      })
                    }
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Webhook Secret
                  </label>
                  <Input
                    placeholder="Enter webhook secret"
                    value={connectionForm.webhook_secret}
                    onChange={e =>
                      setConnectionForm({
                        ...connectionForm,
                        webhook_secret: e.target.value,
                      })
                    }
                  />
                </div>
              </>
            )}

            {selectedPlatform === 'google' && (
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Business ID
                </label>
                <Input
                  placeholder="Enter Google Business ID"
                  value={connectionForm.business_id}
                  onChange={e =>
                    setConnectionForm({
                      ...connectionForm,
                      business_id: e.target.value,
                    })
                  }
                />
              </div>
            )}

            <div className="flex items-center justify-end space-x-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowConnectionDialog(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={connectAccount}
                disabled={
                  !connectionForm.platform ||
                  !connectionForm.account_id ||
                  !connectionForm.access_token
                }
              >
                Connect
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
