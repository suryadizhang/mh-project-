'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, UserCheck, UserX, Clock, Mail, Calendar, Shield, Search, Filter } from 'lucide-react';
import { logger } from '@/lib/logger';

interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  auth_provider: 'google' | 'email' | 'microsoft' | 'apple';
  google_id?: string;
  status: 'pending' | 'active' | 'suspended' | 'deactivated';
  is_super_admin: boolean;
  is_email_verified: boolean;
  created_at: string;
  last_login_at?: string;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'active' | 'suspended'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
  }, [filter]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const endpoint = filter === 'pending' 
        ? `${process.env.NEXT_PUBLIC_API_URL}/admin/users/pending`
        : `${process.env.NEXT_PUBLIC_API_URL}/admin/users?status=${filter !== 'all' ? filter : ''}`;
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.data || []);
      } else {
        throw new Error('Failed to fetch users');
      }
    } catch (err) {
      logger.error(err as Error, { context: 'fetch_users', filter });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId: string) => {
    setActionLoading(userId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users/${userId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchUsers(); // Refresh list
      } else {
        throw new Error('Failed to approve user');
      }
    } catch (err) {
      logger.error(err as Error, { context: 'approve_user', userId });
      alert('Failed to approve user. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (userId: string) => {
    if (!confirm('Are you sure you want to reject this user? This action cannot be undone.')) {
      return;
    }

    setActionLoading(userId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users/${userId}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchUsers(); // Refresh list
      } else {
        throw new Error('Failed to reject user');
      }
    } catch (err) {
      logger.error(err as Error, { context: 'reject_user', userId });
      alert('Failed to reject user. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleSuspend = async (userId: string) => {
    if (!confirm('Are you sure you want to suspend this user?')) {
      return;
    }

    setActionLoading(userId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users/${userId}/suspend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchUsers(); // Refresh list
      } else {
        throw new Error('Failed to suspend user');
      }
    } catch (err) {
      logger.error(err as Error, { context: 'suspend_user', userId });
      alert('Failed to suspend user. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const filteredUsers = users.filter(user => {
    if (searchQuery) {
      return user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
             user.full_name.toLowerCase().includes(searchQuery.toLowerCase());
    }
    return true;
  });

  const getStatusBadge = (status: User['status']) => {
    const variants: Record<User['status'], { variant: 'default' | 'secondary' | 'destructive' | 'outline', label: string }> = {
      pending: { variant: 'outline', label: 'Pending' },
      active: { variant: 'default', label: 'Active' },
      suspended: { variant: 'destructive', label: 'Suspended' },
      deactivated: { variant: 'secondary', label: 'Deactivated' },
    };
    
    const config = variants[status];
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getProviderIcon = (provider: User['auth_provider']) => {
    switch (provider) {
      case 'google':
        return '🔵';
      case 'microsoft':
        return '🟦';
      case 'apple':
        return '⚫';
      default:
        return '📧';
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">User Management</h1>
        <p className="text-gray-600">Manage user accounts and permissions</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{users.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {users.filter(u => u.status === 'pending').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {users.filter(u => u.status === 'active').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Super Admins</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {users.filter(u => u.is_super_admin).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by email or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Filter Buttons */}
            <div className="flex gap-2">
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                onClick={() => setFilter('all')}
                size="sm"
              >
                All
              </Button>
              <Button
                variant={filter === 'pending' ? 'default' : 'outline'}
                onClick={() => setFilter('pending')}
                size="sm"
              >
                Pending
              </Button>
              <Button
                variant={filter === 'active' ? 'default' : 'outline'}
                onClick={() => setFilter('active')}
                size="sm"
              >
                Active
              </Button>
              <Button
                variant={filter === 'suspended' ? 'default' : 'outline'}
                onClick={() => setFilter('suspended')}
                size="sm"
              >
                Suspended
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredUsers.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
              <p className="text-gray-600">
                {searchQuery ? 'Try adjusting your search query.' : 'No users match the selected filter.'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredUsers.map((user) => (
            <Card key={user.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Avatar */}
                    <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      {user.avatar_url ? (
                        <img src={user.avatar_url} alt={user.full_name} className="h-12 w-12 rounded-full" />
                      ) : (
                        <span className="text-blue-600 font-semibold text-lg">
                          {user.full_name.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>

                    {/* User Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="text-lg font-semibold text-gray-900">{user.full_name}</h3>
                        {user.is_super_admin && (
                          <Badge variant="default" className="bg-purple-600">
                            <Shield className="h-3 w-3 mr-1" />
                            Super Admin
                          </Badge>
                        )}
                        {getStatusBadge(user.status)}
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center">
                          <Mail className="h-4 w-4 mr-1" />
                          {user.email}
                        </div>
                        <div className="flex items-center">
                          <span className="mr-1">{getProviderIcon(user.auth_provider)}</span>
                          {user.auth_provider.charAt(0).toUpperCase() + user.auth_provider.slice(1)}
                        </div>
                        {user.is_email_verified && (
                          <Badge variant="outline" className="text-green-600 border-green-600">
                            ✓ Verified
                          </Badge>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500 mt-2">
                        <div className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          Joined {new Date(user.created_at).toLocaleDateString()}
                        </div>
                        {user.last_login_at && (
                          <div className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            Last login {new Date(user.last_login_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2 ml-4">
                    {user.status === 'pending' && (
                      <>
                        <Button
                          size="sm"
                          onClick={() => handleApprove(user.id)}
                          disabled={actionLoading === user.id}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {actionLoading === user.id ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          ) : (
                            <>
                              <UserCheck className="h-4 w-4 mr-1" />
                              Approve
                            </>
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleReject(user.id)}
                          disabled={actionLoading === user.id}
                        >
                          <UserX className="h-4 w-4 mr-1" />
                          Reject
                        </Button>
                      </>
                    )}
                    {user.status === 'active' && !user.is_super_admin && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSuspend(user.id)}
                        disabled={actionLoading === user.id}
                      >
                        Suspend
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
