'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Ban,
  AlertTriangle,
  RefreshCw,
  Activity,
  Server,
  Globe,
  Lock,
  Unlock,
  Clock,
  Users,
  Flame,
  Download,
  ChevronDown,
  ChevronUp,
  Eye,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { tokenManager } from '@/services/api';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { logger } from '@/lib/logger';

// ============================================
// Type Definitions
// ============================================

interface SecurityStatus {
  fail2ban_running: boolean;
  firewalld_running: boolean;
  total_banned_ips: number;
  active_jails: number;
  last_check: string;
  uptime: string;
}

interface JailStatus {
  name: string;
  currently_banned: number;
  total_banned: number;
  currently_failed: number;
  total_failed: number;
  file_list: string[];
  filter: string;
  findtime: number;
  bantime: number;
  maxretry: number;
}

interface BannedIP {
  ip: string;
  jail: string;
  ban_time: string;
  unban_time: string;
  country?: string;
  abuse_score?: number;
  reason?: string;
}

interface FirewallRule {
  zone: string;
  rule: string;
  type: 'rich_rule' | 'service' | 'port';
  source?: string;
  action?: string;
}

interface AttackLogEntry {
  timestamp: string;
  jail: string;
  ip: string;
  action: 'ban' | 'unban' | 'fail';
  message: string;
}

interface SecurityStats {
  total_bans_24h: number;
  total_bans_7d: number;
  total_bans_30d: number;
  unique_attackers_24h: number;
  unique_attackers_7d: number;
  top_jails: { jail: string; count: number }[];
  attack_trend: { date: string; count: number }[];
}

interface KnownAttacker {
  ip: string;
  times_banned: number;
  first_seen: string;
  last_seen: string;
  jails_triggered: string[];
  country?: string;
  abuse_score?: number;
}

// ============================================
// Helper Components
// ============================================

function StatsCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  variant = 'default',
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  trend?: 'up' | 'down' | 'neutral';
  variant?: 'default' | 'success' | 'warning' | 'danger';
}) {
  const variantStyles = {
    default: 'bg-white border-gray-200',
    success: 'bg-green-50 border-green-200',
    warning: 'bg-yellow-50 border-yellow-200',
    danger: 'bg-red-50 border-red-200',
  };

  const iconStyles = {
    default: 'text-gray-600',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
  };

  return (
    <Card className={`${variantStyles[variant]} border-2`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            {description && (
              <p className="text-sm text-gray-500 mt-1">{description}</p>
            )}
          </div>
          <Icon className={`h-12 w-12 ${iconStyles[variant]}`} />
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex justify-center items-center py-12">
      <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
    </div>
  );
}

function ServiceStatusBadge({ running }: { running: boolean }) {
  return running ? (
    <Badge className="bg-green-100 text-green-800 border-green-300">
      <ShieldCheck className="h-3 w-3 mr-1" />
      Running
    </Badge>
  ) : (
    <Badge className="bg-red-100 text-red-800 border-red-300">
      <ShieldAlert className="h-3 w-3 mr-1" />
      Stopped
    </Badge>
  );
}

// ============================================
// Main Component
// ============================================

export default function VPSSecurityPage() {
  // State
  const [status, setStatus] = useState<SecurityStatus | null>(null);
  const [jails, setJails] = useState<JailStatus[]>([]);
  const [bannedIPs, setBannedIPs] = useState<BannedIP[]>([]);
  const [firewallRules, setFirewallRules] = useState<FirewallRule[]>([]);
  const [attackLog, setAttackLog] = useState<AttackLogEntry[]>([]);
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [knownAttackers, setKnownAttackers] = useState<KnownAttacker[]>([]);

  // UI State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'jails' | 'banned' | 'firewall' | 'logs' | 'attackers'
  >('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [expandedJail, setExpandedJail] = useState<string | null>(null);

  // Unban state
  const [unbanning, setUnbanning] = useState<string | null>(null);
  const [unbanError, setUnbanError] = useState<string | null>(null);

  // ============================================
  // API Calls
  // ============================================

  const fetchSecurityData = useCallback(async () => {
    try {
      const token = tokenManager.getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const baseUrl = process.env.NEXT_PUBLIC_API_URL;

      // Fetch all data in parallel
      const [
        statusRes,
        jailsRes,
        bannedRes,
        firewallRes,
        logsRes,
        statsRes,
        attackersRes,
      ] = await Promise.all([
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_STATUS}`, {
          headers,
        }),
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_JAILS}`, {
          headers,
        }),
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_BANNED_IPS}`, {
          headers,
        }),
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_FIREWALL_RULES}`, {
          headers,
        }),
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_ATTACK_LOG}`, {
          headers,
        }),
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_STATS}`, {
          headers,
        }),
        fetch(`${baseUrl}${API_ENDPOINTS.ADMIN.VPS_SECURITY_KNOWN_ATTACKERS}`, {
          headers,
        }),
      ]);

      // Parse responses
      if (statusRes.ok) {
        const data = await statusRes.json();
        setStatus(data.data);
      }
      if (jailsRes.ok) {
        const data = await jailsRes.json();
        setJails(data.data || []);
      }
      if (bannedRes.ok) {
        const data = await bannedRes.json();
        setBannedIPs(data.data || []);
      }
      if (firewallRes.ok) {
        const data = await firewallRes.json();
        setFirewallRules(data.data || []);
      }
      if (logsRes.ok) {
        const data = await logsRes.json();
        setAttackLog(data.data || []);
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data.data);
      }
      if (attackersRes.ok) {
        const data = await attackersRes.json();
        setKnownAttackers(data.data || []);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      logger.error(err as Error, { context: 'fetch_security_data' });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const handleUnban = async (ip: string, jail: string) => {
    if (
      !confirm(
        `Are you sure you want to unban ${ip} from ${jail}? This may allow the attacker to resume malicious activity.`
      )
    ) {
      return;
    }

    setUnbanning(ip);
    setUnbanError(null);

    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.ADMIN.VPS_SECURITY_UNBAN}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ ip, jail }),
        }
      );

      if (response.ok) {
        // Refresh data
        await fetchSecurityData();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to unban IP');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setUnbanError(errorMessage);
      logger.error(err as Error, { context: 'unban_ip' });
    } finally {
      setUnbanning(null);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSecurityData();
  };

  const exportReport = async () => {
    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.ADMIN.VPS_SECURITY_REPORT}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: 'application/json',
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vps-security-report-${
          new Date().toISOString().split('T')[0]
        }.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      logger.error(err as Error, { context: 'export_security_report' });
    }
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    fetchSecurityData();

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      fetchSecurityData();
    }, 60000);

    return () => clearInterval(interval);
  }, [fetchSecurityData]);

  // ============================================
  // Render
  // ============================================

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Shield className="h-6 w-6" />
          VPS Security Dashboard
        </h1>
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Shield className="h-6 w-6" />
          VPS Security Dashboard
        </h1>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              <span>Error: {error}</span>
            </div>
            <Button onClick={handleRefresh} className="mt-4" variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="h-6 w-6" />
          VPS Security Dashboard
        </h1>
        <div className="flex gap-2">
          <Button onClick={exportReport} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <Button onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw
              className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      {/* Service Status Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Server className="h-5 w-5 text-gray-500" />
                <span className="font-medium">Fail2ban:</span>
                <ServiceStatusBadge
                  running={status?.fail2ban_running ?? false}
                />
              </div>
              <div className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-gray-500" />
                <span className="font-medium">Firewalld:</span>
                <ServiceStatusBadge
                  running={status?.firewalld_running ?? false}
                />
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Uptime: {status?.uptime || 'N/A'}</span>
              <span>
                Last check:{' '}
                {status?.last_check
                  ? new Date(status.last_check).toLocaleTimeString()
                  : 'N/A'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatsCard
          title="Total Banned IPs"
          value={status?.total_banned_ips ?? 0}
          icon={Ban}
          description="Currently blocked"
          variant={(status?.total_banned_ips ?? 0) > 10 ? 'warning' : 'default'}
        />
        <StatsCard
          title="Active Jails"
          value={status?.active_jails ?? 0}
          icon={Lock}
          description="Monitoring services"
          variant="success"
        />
        <StatsCard
          title="Bans (24h)"
          value={stats?.total_bans_24h ?? 0}
          icon={AlertTriangle}
          description={`${stats?.unique_attackers_24h ?? 0} unique attackers`}
          variant={(stats?.total_bans_24h ?? 0) > 20 ? 'danger' : 'default'}
        />
        <StatsCard
          title="Bans (7 days)"
          value={stats?.total_bans_7d ?? 0}
          icon={Activity}
          description={`${stats?.unique_attackers_7d ?? 0} unique attackers`}
          variant="default"
        />
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-4">
          {[
            { id: 'overview', label: 'Overview', icon: Eye },
            { id: 'jails', label: 'Jails', icon: Lock },
            { id: 'banned', label: 'Banned IPs', icon: Ban },
            { id: 'firewall', label: 'Firewall Rules', icon: Flame },
            { id: 'logs', label: 'Attack Log', icon: Activity },
            { id: 'attackers', label: 'Known Attackers', icon: Users },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() =>
                setActiveTab(
                  tab.id as
                    | 'overview'
                    | 'jails'
                    | 'banned'
                    | 'firewall'
                    | 'logs'
                    | 'attackers'
                )
              }
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Jails */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5" />
                Top Active Jails
              </CardTitle>
              <CardDescription>Jails with most blocked attacks</CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.top_jails && stats.top_jails.length > 0 ? (
                <div className="space-y-3">
                  {stats.top_jails.slice(0, 5).map((jail, idx) => (
                    <div
                      key={jail.jail}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-gray-400">#{idx + 1}</span>
                        <span className="font-medium">{jail.jail}</span>
                      </div>
                      <Badge variant="secondary">{jail.count} bans</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No jail activity recorded</p>
              )}
            </CardContent>
          </Card>

          {/* Recent Bans */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ban className="h-5 w-5" />
                Recent Bans
              </CardTitle>
              <CardDescription>Latest blocked IP addresses</CardDescription>
            </CardHeader>
            <CardContent>
              {bannedIPs.length > 0 ? (
                <div className="space-y-3">
                  {bannedIPs.slice(0, 5).map(ip => (
                    <div
                      key={`${ip.ip}-${ip.jail}`}
                      className="flex items-center justify-between"
                    >
                      <div>
                        <span className="font-mono font-medium">{ip.ip}</span>
                        <span className="text-gray-400 text-sm ml-2">
                          ({ip.jail})
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {ip.ban_time
                          ? new Date(ip.ban_time).toLocaleString()
                          : 'Unknown'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-green-500" />
                  No currently banned IPs
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'jails' && (
        <div className="space-y-4">
          {jails.length > 0 ? (
            jails.map(jail => (
              <Card key={jail.name}>
                <CardHeader
                  className="cursor-pointer"
                  onClick={() =>
                    setExpandedJail(
                      expandedJail === jail.name ? null : jail.name
                    )
                  }
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Lock className="h-5 w-5" />
                      {jail.name}
                      {jail.currently_banned > 0 && (
                        <Badge className="ml-2 bg-red-100 text-red-800">
                          {jail.currently_banned} banned
                        </Badge>
                      )}
                    </CardTitle>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-500">
                        Total: {jail.total_banned} bans
                      </span>
                      {expandedJail === jail.name ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </div>
                  </div>
                </CardHeader>
                {expandedJail === jail.name && (
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">
                          Currently Failed
                        </p>
                        <p className="text-lg font-bold">
                          {jail.currently_failed}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Total Failed</p>
                        <p className="text-lg font-bold">{jail.total_failed}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Ban Time</p>
                        <p className="text-lg font-bold">
                          {jail.bantime > 0
                            ? `${Math.round(jail.bantime / 3600)}h`
                            : 'Permanent'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Max Retry</p>
                        <p className="text-lg font-bold">{jail.maxretry}</p>
                      </div>
                    </div>
                    {jail.file_list && jail.file_list.length > 0 && (
                      <div className="mt-4">
                        <p className="text-sm text-gray-500 mb-2">
                          Monitored Files:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {jail.file_list.map(file => (
                            <Badge
                              key={file}
                              variant="outline"
                              className="font-mono text-xs"
                            >
                              {file}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="p-6">
                <p className="text-gray-500">No jails configured</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'banned' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ban className="h-5 w-5" />
              Currently Banned IPs
            </CardTitle>
            <CardDescription>
              {bannedIPs.length} IP{bannedIPs.length !== 1 ? 's' : ''} currently
              blocked
            </CardDescription>
          </CardHeader>
          <CardContent>
            {unbanError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {unbanError}
              </div>
            )}
            {bannedIPs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">IP Address</th>
                      <th className="text-left py-2 px-4">Jail</th>
                      <th className="text-left py-2 px-4">Banned At</th>
                      <th className="text-left py-2 px-4">Unban At</th>
                      <th className="text-left py-2 px-4">Country</th>
                      <th className="text-left py-2 px-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bannedIPs.map(ip => (
                      <tr key={`${ip.ip}-${ip.jail}`} className="border-b">
                        <td className="py-2 px-4 font-mono">{ip.ip}</td>
                        <td className="py-2 px-4">
                          <Badge variant="outline">{ip.jail}</Badge>
                        </td>
                        <td className="py-2 px-4 text-sm text-gray-500">
                          {ip.ban_time
                            ? new Date(ip.ban_time).toLocaleString()
                            : 'Unknown'}
                        </td>
                        <td className="py-2 px-4 text-sm text-gray-500">
                          {ip.unban_time
                            ? new Date(ip.unban_time).toLocaleString()
                            : 'Never'}
                        </td>
                        <td className="py-2 px-4">
                          {ip.country || (
                            <span className="text-gray-400">Unknown</span>
                          )}
                        </td>
                        <td className="py-2 px-4">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleUnban(ip.ip, ip.jail)}
                            disabled={unbanning === ip.ip}
                          >
                            {unbanning === ip.ip ? (
                              <RefreshCw className="h-4 w-4 animate-spin" />
                            ) : (
                              <Unlock className="h-4 w-4 mr-1" />
                            )}
                            Unban
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <ShieldCheck className="h-12 w-12 mx-auto text-green-500 mb-3" />
                <p className="text-gray-500">No currently banned IPs</p>
                <p className="text-sm text-gray-400">
                  All threats have been handled
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'firewall' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5" />
              Firewall Rules
            </CardTitle>
            <CardDescription>
              Active firewalld rules and blocked sources
            </CardDescription>
          </CardHeader>
          <CardContent>
            {firewallRules.length > 0 ? (
              <div className="space-y-2">
                {firewallRules.map((rule, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded border"
                  >
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          rule.type === 'rich_rule'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {rule.type}
                      </Badge>
                      <span className="font-mono text-sm">{rule.rule}</span>
                    </div>
                    <span className="text-sm text-gray-500">{rule.zone}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No firewall rules found</p>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'logs' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Attack Log
            </CardTitle>
            <CardDescription>Recent security events</CardDescription>
          </CardHeader>
          <CardContent>
            {attackLog.length > 0 ? (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {attackLog.map((entry, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-4 p-3 rounded border ${
                      entry.action === 'ban'
                        ? 'bg-red-50 border-red-200'
                        : entry.action === 'unban'
                          ? 'bg-green-50 border-green-200'
                          : 'bg-yellow-50 border-yellow-200'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {entry.action === 'ban' ? (
                        <Ban className="h-4 w-4 text-red-500" />
                      ) : entry.action === 'unban' ? (
                        <Unlock className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      )}
                      <Badge
                        variant={
                          entry.action === 'ban'
                            ? 'destructive'
                            : entry.action === 'unban'
                              ? 'default'
                              : 'secondary'
                        }
                      >
                        {entry.action.toUpperCase()}
                      </Badge>
                    </div>
                    <span className="font-mono text-sm">{entry.ip}</span>
                    <Badge variant="outline">{entry.jail}</Badge>
                    <span className="text-sm text-gray-500 flex-1 truncate">
                      {entry.message}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No attack log entries</p>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'attackers' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Known Attackers
            </CardTitle>
            <CardDescription>
              IP addresses with repeated malicious activity
            </CardDescription>
          </CardHeader>
          <CardContent>
            {knownAttackers.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">IP Address</th>
                      <th className="text-left py-2 px-4">Times Banned</th>
                      <th className="text-left py-2 px-4">First Seen</th>
                      <th className="text-left py-2 px-4">Last Seen</th>
                      <th className="text-left py-2 px-4">Jails Triggered</th>
                      <th className="text-left py-2 px-4">Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {knownAttackers.map(attacker => (
                      <tr key={attacker.ip} className="border-b">
                        <td className="py-2 px-4 font-mono">{attacker.ip}</td>
                        <td className="py-2 px-4">
                          <Badge
                            className={
                              attacker.times_banned >= 5
                                ? 'bg-red-100 text-red-800'
                                : attacker.times_banned >= 3
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-gray-100 text-gray-800'
                            }
                          >
                            {attacker.times_banned}x
                          </Badge>
                        </td>
                        <td className="py-2 px-4 text-sm text-gray-500">
                          {new Date(attacker.first_seen).toLocaleDateString()}
                        </td>
                        <td className="py-2 px-4 text-sm text-gray-500">
                          {new Date(attacker.last_seen).toLocaleDateString()}
                        </td>
                        <td className="py-2 px-4">
                          <div className="flex flex-wrap gap-1">
                            {attacker.jails_triggered.map(jail => (
                              <Badge
                                key={jail}
                                variant="outline"
                                className="text-xs"
                              >
                                {jail}
                              </Badge>
                            ))}
                          </div>
                        </td>
                        <td className="py-2 px-4">
                          {attacker.country || (
                            <span className="text-gray-400">Unknown</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">No known attackers recorded</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
