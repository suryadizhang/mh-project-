'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Shield,
  FileText,
  Settings,
  Plus,
  Search,
  RefreshCw,
  ChevronRight,
  UserPlus,
  Key,
  Mail,
  Trash2,
  Edit,
  MoreHorizontal,
  Check,
  X,
  AlertTriangle,
  Database,
  Activity,
  Clock,
  UserCheck,
  UserX,
  Loader2,
  Eye,
  EyeOff,
} from 'lucide-react';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { toast } from 'sonner';
import { apiFetch } from '@/lib/api';

import { BaseLocationManager } from '@/components/BaseLocationManager';

// Types
interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  roles?: { id: string; name: string }[];
  status: string;
  lastLogin?: string;
  createdAt?: string;
  created_at?: string;
  last_login?: string;
  is_active?: boolean;
  is_verified?: boolean;
}

interface Role {
  id: string;
  name: string;
  description?: string;
  permission_count?: number;
  user_count?: number;
  permissions?: string[];
}

interface AuditLog {
  id: string;
  action: string;
  actor_email?: string;
  actor_name?: string;
  target_type?: string;
  target_id?: string;
  details?: Record<string, unknown>;
  created_at: string;
  ip_address?: string;
}

interface SystemStats {
  totalUsers: number;
  pendingUsers: number;
  activeUsers: number;
  suspendedUsers: number;
}

// ========== Dashboard Tab ==========
function DashboardTab() {
  const [stats, setStats] = useState<SystemStats>({
    totalUsers: 0,
    pendingUsers: 0,
    activeUsers: 0,
    suspendedUsers: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      // Fetch all users to calculate stats
      const response = await apiFetch('/api/admin/users');
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        const users = (data?.users || data || []) as AdminUser[];

        setStats({
          totalUsers: users.length,
          pendingUsers: users.filter(
            (u: AdminUser) => u.status === 'pending' || !u.is_verified
          ).length,
          activeUsers: users.filter(
            (u: AdminUser) => u.status === 'active' || u.is_active
          ).length,
          suspendedUsers: users.filter(
            (u: AdminUser) => u.status === 'suspended' || !u.is_active
          ).length,
        });
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      label: 'Total Admin Users',
      value: stats.totalUsers,
      icon: Users,
      color: 'text-blue-600',
    },
    {
      label: 'Pending Approval',
      value: stats.pendingUsers,
      icon: Clock,
      color: 'text-yellow-600',
    },
    {
      label: 'Active Users',
      value: stats.activeUsers,
      icon: UserCheck,
      color: 'text-green-600',
    },
    {
      label: 'Suspended Users',
      value: stats.suspendedUsers,
      icon: UserX,
      color: 'text-red-600',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map(stat => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  stat.value
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Base Location Manager */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Base Location Configuration
          </CardTitle>
          <CardDescription>
            Configure the primary service location for travel fee calculations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BaseLocationManager />
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <Button
            variant="outline"
            className="justify-start"
            onClick={() => (window.location.href = '#users')}
          >
            <UserPlus className="mr-2 h-4 w-4" />
            Add Admin User
          </Button>
          <Button
            variant="outline"
            className="justify-start"
            onClick={() => (window.location.href = '#audit')}
          >
            <FileText className="mr-2 h-4 w-4" />
            View Audit Logs
          </Button>
          <Button
            variant="outline"
            className="justify-start"
            onClick={loadStats}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh Stats
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// ========== Users Tab ==========
function UsersTab() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [editRolesDialogOpen, setEditRolesDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);

  // Form states
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [newUserRole, setNewUserRole] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/api/admin/users');
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        setUsers((data?.users || data || []) as AdminUser[]);
      }
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadRoles = async () => {
    try {
      const response = await apiFetch('/api/admin/roles');
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        setRoles((data?.roles || data || []) as Role[]);
      }
    } catch (error) {
      console.error('Failed to load roles:', error);
    }
  };

  const handleCreateUser = async () => {
    if (!newUserEmail || !newUserName) {
      toast.error('Email and name are required');
      return;
    }

    setSubmitting(true);
    try {
      const response = await apiFetch('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify({
          email: newUserEmail,
          name: newUserName,
          role: newUserRole || 'ADMIN',
          password: newUserPassword || undefined,
        }),
      });

      if (response.success) {
        toast.success('Admin user created successfully');
        setCreateDialogOpen(false);
        setNewUserEmail('');
        setNewUserName('');
        setNewUserRole('');
        setNewUserPassword('');
        loadUsers();
      } else {
        toast.error(
          response.error || response.message || 'Failed to create user'
        );
      }
    } catch (error) {
      console.error('Failed to create user:', error);
      toast.error('Failed to create user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleForceResetPassword = async () => {
    if (!selectedUser) return;

    setSubmitting(true);
    try {
      const response = await apiFetch(
        `/api/admin/users/${selectedUser.id}/force-reset-password`,
        {
          method: 'POST',
        }
      );

      if (response.success) {
        toast.success(`Password reset email sent to ${selectedUser.email}`);
        setResetPasswordDialogOpen(false);
        setSelectedUser(null);
      } else {
        toast.error(
          response.error || response.message || 'Failed to send reset email'
        );
      }
    } catch (error) {
      console.error('Failed to reset password:', error);
      toast.error('Failed to send reset email');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApproveUser = async (userId: string) => {
    try {
      const response = await apiFetch(`/api/admin/users/${userId}/approve`, {
        method: 'POST',
      });

      if (response.success) {
        toast.success('User approved successfully');
        loadUsers();
      } else {
        toast.error(
          response.error || response.message || 'Failed to approve user'
        );
      }
    } catch (error) {
      console.error('Failed to approve user:', error);
      toast.error('Failed to approve user');
    }
  };

  const handleRejectUser = async (userId: string) => {
    try {
      const response = await apiFetch(`/api/admin/users/${userId}/reject`, {
        method: 'POST',
      });

      if (response.success) {
        toast.success('User rejected');
        loadUsers();
      } else {
        toast.error(
          response.error || response.message || 'Failed to reject user'
        );
      }
    } catch (error) {
      console.error('Failed to reject user:', error);
      toast.error('Failed to reject user');
    }
  };

  const handleSuspendUser = async (userId: string) => {
    try {
      const response = await apiFetch(`/api/admin/users/${userId}/suspend`, {
        method: 'POST',
      });

      if (response.success) {
        toast.success('User suspended');
        loadUsers();
      } else {
        toast.error(
          response.error || response.message || 'Failed to suspend user'
        );
      }
    } catch (error) {
      console.error('Failed to suspend user:', error);
      toast.error('Failed to suspend user');
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    setSubmitting(true);
    try {
      const response = await apiFetch(`/api/admin/users/${selectedUser.id}`, {
        method: 'DELETE',
      });

      if (response.success) {
        toast.success('User deleted successfully');
        setDeleteDialogOpen(false);
        setSelectedUser(null);
        loadUsers();
      } else {
        toast.error(
          response.error || response.message || 'Failed to delete user'
        );
      }
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error('Failed to delete user');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (user: AdminUser) => {
    const status = user.status || (user.is_active ? 'active' : 'pending');
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'suspended':
        return <Badge className="bg-red-100 text-red-800">Suspended</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.name?.toLowerCase().includes(searchQuery.toLowerCase());

    if (filterStatus === 'all') return matchesSearch;

    const userStatus = user.status || (user.is_active ? 'active' : 'pending');
    return matchesSearch && userStatus === filterStatus;
  });

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-1 gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search users..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Users</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="suspended">Suspended</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadUsers}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Admin User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Admin User</DialogTitle>
                <DialogDescription>
                  Add a new administrator to the system. They will receive an
                  email invitation.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@example.com"
                    value={newUserEmail}
                    onChange={e => setNewUserEmail(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    placeholder="John Doe"
                    value={newUserName}
                    onChange={e => setNewUserName(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="role">Role</Label>
                  <Select value={newUserRole} onValueChange={setNewUserRole}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a role" />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.map(role => (
                        <SelectItem key={role.id} value={role.name}>
                          {role.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">Initial Password (optional)</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Leave blank to send invitation email"
                      value={newUserPassword}
                      onChange={e => setNewUserPassword(e.target.value)}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setCreateDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateUser} disabled={submitting}>
                  {submitting && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Create User
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Login</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map(user => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">
                          {user.name || 'No name'}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {user.email}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {user.role || user.roles?.[0]?.name || 'No role'}
                      </Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(user)}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {user.lastLogin || user.last_login
                        ? new Date(
                            user.lastLogin || user.last_login!
                          ).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {(user.status === 'pending' || !user.is_verified) && (
                            <>
                              <DropdownMenuItem
                                onClick={() => handleApproveUser(user.id)}
                              >
                                <Check className="mr-2 h-4 w-4 text-green-600" />
                                Approve
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleRejectUser(user.id)}
                              >
                                <X className="mr-2 h-4 w-4 text-red-600" />
                                Reject
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                            </>
                          )}
                          <DropdownMenuItem
                            onClick={() => {
                              setSelectedUser(user);
                              setEditRolesDialogOpen(true);
                            }}
                          >
                            <Shield className="mr-2 h-4 w-4" />
                            Edit Roles
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              setSelectedUser(user);
                              setResetPasswordDialogOpen(true);
                            }}
                          >
                            <Key className="mr-2 h-4 w-4" />
                            Force Reset Password
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {user.status !== 'suspended' &&
                            user.is_active !== false && (
                              <DropdownMenuItem
                                onClick={() => handleSuspendUser(user.id)}
                              >
                                <AlertTriangle className="mr-2 h-4 w-4 text-yellow-600" />
                                Suspend User
                              </DropdownMenuItem>
                            )}
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setSelectedUser(user);
                              setDeleteDialogOpen(true);
                            }}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete User
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Force Reset Password Dialog */}
      <AlertDialog
        open={resetPasswordDialogOpen}
        onOpenChange={setResetPasswordDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Force Password Reset</AlertDialogTitle>
            <AlertDialogDescription>
              This will send a password reset email to{' '}
              <strong>{selectedUser?.email}</strong>. The user will need to
              click the link in the email to set a new password.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedUser(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleForceResetPassword}
              disabled={submitting}
            >
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Mail className="mr-2 h-4 w-4" />
              Send Reset Email
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete User Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete{' '}
              <strong>{selectedUser?.name}</strong> ({selectedUser?.email})?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedUser(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteUser}
              disabled={submitting}
              className="bg-red-600 hover:bg-red-700"
            >
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Roles Dialog */}
      <EditRolesDialog
        open={editRolesDialogOpen}
        onOpenChange={setEditRolesDialogOpen}
        user={selectedUser}
        roles={roles}
        onSuccess={() => {
          loadUsers();
          setSelectedUser(null);
        }}
      />
    </div>
  );
}

// Edit Roles Dialog Component
function EditRolesDialog({
  open,
  onOpenChange,
  user,
  roles,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: AdminUser | null;
  roles: Role[];
  onSuccess: () => void;
}) {
  const [userRoles, setUserRoles] = useState<{ id: string; name: string }[]>(
    []
  );
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && user) {
      loadUserRoles();
    }
  }, [open, user]);

  const loadUserRoles = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const response = await apiFetch(
        `/api/admin/roles/users/${user.id}/permissions`
      );
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        setUserRoles((data?.roles || []) as Role[]);
      }
    } catch (error) {
      console.error('Failed to load user roles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRole = async (roleId: string) => {
    if (!user) return;
    setSubmitting(true);
    try {
      const response = await apiFetch(
        `/api/admin/roles/users/${user.id}/roles`,
        {
          method: 'POST',
          body: JSON.stringify({ role_id: roleId }),
        }
      );

      if (response.success) {
        toast.success('Role added successfully');
        loadUserRoles();
      } else {
        toast.error(response.error || response.message || 'Failed to add role');
      }
    } catch (error) {
      console.error('Failed to add role:', error);
      toast.error('Failed to add role');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveRole = async (roleId: string) => {
    if (!user) return;
    setSubmitting(true);
    try {
      const response = await apiFetch(
        `/api/admin/roles/users/${user.id}/roles/${roleId}`,
        {
          method: 'DELETE',
        }
      );

      if (response.success) {
        toast.success('Role removed successfully');
        loadUserRoles();
      } else {
        toast.error(
          response.error || response.message || 'Failed to remove role'
        );
      }
    } catch (error) {
      console.error('Failed to remove role:', error);
      toast.error('Failed to remove role');
    } finally {
      setSubmitting(false);
    }
  };

  const availableRoles = roles.filter(
    role => !userRoles.some(ur => ur.id === role.id)
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit User Roles</DialogTitle>
          <DialogDescription>
            Manage roles for {user?.name} ({user?.email})
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div>
            <Label className="mb-2 block">Current Roles</Label>
            {loading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : userRoles.length === 0 ? (
              <p className="text-sm text-muted-foreground">No roles assigned</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {userRoles.map(role => (
                  <Badge key={role.id} variant="secondary" className="gap-1">
                    {role.name}
                    <button
                      onClick={() => handleRemoveRole(role.id)}
                      disabled={submitting}
                      className="ml-1 hover:text-red-600"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
          {availableRoles.length > 0 && (
            <div>
              <Label className="mb-2 block">Add Role</Label>
              <Select onValueChange={handleAddRole} disabled={submitting}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a role to add" />
                </SelectTrigger>
                <SelectContent>
                  {availableRoles.map(role => (
                    <SelectItem key={role.id} value={role.id}>
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button
            onClick={() => {
              onOpenChange(false);
              onSuccess();
            }}
          >
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ========== Roles Tab ==========
function RolesTab() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  useEffect(() => {
    loadRoles();
    loadPermissions();
  }, []);

  const loadRoles = async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/api/admin/roles');
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        setRoles((data?.roles || data || []) as Role[]);
      }
    } catch (error) {
      console.error('Failed to load roles:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPermissions = async () => {
    try {
      const response = await apiFetch('/api/admin/roles/permissions/all');
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        setPermissions((data?.permissions || data || []) as string[]);
      }
    } catch (error) {
      console.error('Failed to load permissions:', error);
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Roles List */}
      <Card>
        <CardHeader>
          <CardTitle>System Roles</CardTitle>
          <CardDescription>Available roles in the system</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="space-y-2">
              {roles.map(role => (
                <button
                  key={role.id}
                  onClick={() => setSelectedRole(role)}
                  className={`w-full p-3 rounded-lg text-left transition-colors ${
                    selectedRole?.id === role.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <div className="font-medium">{role.name}</div>
                  {role.description && (
                    <div
                      className={`text-sm ${
                        selectedRole?.id === role.id
                          ? 'text-primary-foreground/70'
                          : 'text-muted-foreground'
                      }`}
                    >
                      {role.description}
                    </div>
                  )}
                  <div
                    className={`text-xs mt-1 ${
                      selectedRole?.id === role.id
                        ? 'text-primary-foreground/60'
                        : 'text-muted-foreground'
                    }`}
                  >
                    {role.permission_count || role.permissions?.length || 0}{' '}
                    permissions
                    {role.user_count !== undefined &&
                      ` • ${role.user_count} users`}
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Role Details */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedRole ? `${selectedRole.name} Permissions` : 'Role Details'}
          </CardTitle>
          <CardDescription>
            {selectedRole
              ? `Permissions assigned to the ${selectedRole.name} role`
              : 'Select a role to view its permissions'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {selectedRole ? (
            <div className="space-y-2">
              {(selectedRole.permissions || []).map(permission => (
                <Badge key={permission} variant="outline" className="mr-2 mb-2">
                  {permission}
                </Badge>
              ))}
              {(!selectedRole.permissions ||
                selectedRole.permissions.length === 0) && (
                <p className="text-sm text-muted-foreground">
                  No permissions configured
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Select a role from the list
            </p>
          )}
        </CardContent>
      </Card>

      {/* All Permissions Reference */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>All System Permissions</CardTitle>
          <CardDescription>
            Complete list of available permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {permissions.map(permission => (
              <Badge key={permission} variant="secondary">
                {permission}
              </Badge>
            ))}
            {permissions.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No permissions found
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ========== Audit Logs Tab ==========
function AuditLogsTab() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [actionFilter, setActionFilter] = useState('all');

  useEffect(() => {
    loadLogs();
  }, [page, actionFilter]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
      });
      if (actionFilter !== 'all') {
        params.append('action', actionFilter);
      }

      const response = await apiFetch(`/api/admin/audit-logs?${params}`);
      if (response.success) {
        const data = response.data as Record<string, unknown>;
        setLogs((data?.logs || data?.items || data || []) as AuditLog[]);
        setTotalPages(
          (data?.total_pages as number) ||
            Math.ceil(((data?.total as number) || 0) / 20) ||
            1
        );
      }
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionBadge = (action: string) => {
    const colors: Record<string, string> = {
      login: 'bg-blue-100 text-blue-800',
      logout: 'bg-gray-100 text-gray-800',
      create: 'bg-green-100 text-green-800',
      update: 'bg-yellow-100 text-yellow-800',
      delete: 'bg-red-100 text-red-800',
      approve: 'bg-green-100 text-green-800',
      reject: 'bg-red-100 text-red-800',
      suspend: 'bg-orange-100 text-orange-800',
    };
    return (
      <Badge
        className={colors[action.toLowerCase()] || 'bg-gray-100 text-gray-800'}
      >
        {action}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            <SelectItem value="login">Login</SelectItem>
            <SelectItem value="logout">Logout</SelectItem>
            <SelectItem value="create">Create</SelectItem>
            <SelectItem value="update">Update</SelectItem>
            <SelectItem value="delete">Delete</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={loadLogs}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>IP Address</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <FileText className="h-8 w-8" />
                      <p>No audit logs found</p>
                      <p className="text-sm">
                        Logs will appear here as actions are performed
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                logs.map(log => (
                  <TableRow key={log.id}>
                    <TableCell className="text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>{getActionBadge(log.action)}</TableCell>
                    <TableCell>
                      {log.actor_name || log.actor_email || 'System'}
                    </TableCell>
                    <TableCell>
                      {log.target_type && log.target_id
                        ? `${log.target_type}: ${log.target_id.substring(0, 8)}...`
                        : '-'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {log.ip_address || '-'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

// ========== System Tab ==========
function SystemTab() {
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    database: string;
    cache: string;
  } | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  const checkHealth = async () => {
    setLoadingHealth(true);
    try {
      const response = await apiFetch('/api/health');
      if (response.success) {
        const data = response.data as {
          status: string;
          database: string;
          cache: string;
        };
        setHealthStatus(data);
        toast.success('System health check completed');
      }
    } catch (error) {
      console.error('Health check failed:', error);
      toast.error('Health check failed');
    } finally {
      setLoadingHealth(false);
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Database Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Database Management
          </CardTitle>
          <CardDescription>
            Manage database operations and migrations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button variant="outline" className="w-full justify-start">
            <RefreshCw className="mr-2 h-4 w-4" />
            Run Pending Migrations
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <Database className="mr-2 h-4 w-4" />
            View Schema Info
          </Button>
        </CardContent>
      </Card>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Health
          </CardTitle>
          <CardDescription>Check system component status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={checkHealth}
            disabled={loadingHealth}
            className="w-full"
          >
            {loadingHealth && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Run Health Check
          </Button>
          {healthStatus && (
            <div className="space-y-2 pt-4 border-t">
              <div className="flex justify-between">
                <span>Overall Status</span>
                <Badge
                  className={
                    healthStatus.status === 'healthy'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }
                >
                  {healthStatus.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>Database</span>
                <Badge
                  className={
                    healthStatus.database === 'connected'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }
                >
                  {healthStatus.database}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>Cache</span>
                <Badge
                  className={
                    healthStatus.cache === 'connected'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }
                >
                  {healthStatus.cache}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            System Configuration
          </CardTitle>
          <CardDescription>View and manage system settings</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            System configuration settings will be available here in a future
            update. Currently, configurations are managed via environment
            variables.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

// ========== Main Page Component ==========
export default function SuperAdminPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Super Admin Console</h1>
          <p className="text-muted-foreground">
            System administration and configuration
          </p>
        </div>
      </div>

      {/* Chrome-style Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="dashboard" className="gap-2">
            <LayoutDashboard className="h-4 w-4" />
            <span className="hidden sm:inline">Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="users" className="gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Admin Users</span>
          </TabsTrigger>
          <TabsTrigger value="roles" className="gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">Roles</span>
          </TabsTrigger>
          <TabsTrigger value="audit" className="gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Audit Logs</span>
          </TabsTrigger>
          <TabsTrigger value="system" className="gap-2">
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">System</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <DashboardTab />
        </TabsContent>

        <TabsContent value="users">
          <UsersTab />
        </TabsContent>

        <TabsContent value="roles">
          <RolesTab />
        </TabsContent>

        <TabsContent value="audit">
          <AuditLogsTab />
        </TabsContent>

        <TabsContent value="system">
          <SystemTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
