'use client';

import {
  CheckCircle,
  Key,
  Lock,
  Plus,
  Shield,
  Trash2,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { logger } from '@/lib/logger';
import { tokenManager } from '@/services/api';

interface Permission {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  resource: string;
  action: string;
}

interface Role {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  is_system_role: boolean;
  is_active: boolean;
  permission_count: number;
  permissions: string[];
}

interface UserRole {
  user_id: string;
  user_email: string;
  user_name: string;
  roles: Role[];
  all_permissions: string[];
}

interface User {
  id: string;
  email: string;
  full_name: string;
  status: string;
}

export default function RoleManagementPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userRoles, setUserRoles] = useState<UserRole | null>(null);
  const [loading, setLoading] = useState(true);
  const [assigningRole, setAssigningRole] = useState(false);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  useEffect(() => {
    // Check if user is super admin from localStorage
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setIsSuperAdmin(user.is_super_admin || false);
      if (user.is_super_admin) {
        loadData();
      }
    }
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const token = tokenManager.getToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;

      // Load roles, permissions, and users in parallel
      const [rolesRes, permsRes, usersRes] = await Promise.all([
        fetch(`${apiUrl}/admin/roles`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/admin/roles/permissions/all`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/admin/users`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (rolesRes.ok && permsRes.ok && usersRes.ok) {
        const rolesData = await rolesRes.json();
        const permsData = await permsRes.json();
        const usersData = await usersRes.json();

        setRoles(rolesData);
        setPermissions(permsData);
        setUsers(
          (usersData.data || usersData).filter(
            (u: User) => u.status === 'ACTIVE'
          )
        );
      }
    } catch (error: any) {
      logger.error(error, { context: 'load_role_data' });
    } finally {
      setLoading(false);
    }
  };

  const loadUserRoles = async (userId: string) => {
    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/roles/users/${userId}/permissions`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUserRoles(data);
      }
    } catch (error: any) {
      logger.error(error, { context: 'load_user_roles', userId });
    }
  };

  const handleSelectUser = async (user: User) => {
    setSelectedUser(user);
    await loadUserRoles(user.id);
  };

  const handleAssignRole = async (roleId: string) => {
    if (!selectedUser) return;

    try {
      setAssigningRole(true);
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/roles/users/${selectedUser.id}/roles`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ role_id: roleId }),
        }
      );

      if (response.ok) {
        logger.info('Role assigned successfully', {
          userId: selectedUser.id,
          roleId,
        });
        await loadUserRoles(selectedUser.id);
      } else {
        throw new Error('Failed to assign role');
      }
    } catch (error: any) {
      logger.error(error, {
        context: 'assign_role',
        userId: selectedUser.id,
        roleId,
      });
    } finally {
      setAssigningRole(false);
    }
  };

  const handleRemoveRole = async (roleId: string) => {
    if (!selectedUser) return;

    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/roles/users/${selectedUser.id}/roles/${roleId}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        logger.info('Role removed successfully', {
          userId: selectedUser.id,
          roleId,
        });
        await loadUserRoles(selectedUser.id);
      } else {
        throw new Error('Failed to remove role');
      }
    } catch (error: any) {
      logger.error(error, {
        context: 'remove_role',
        userId: selectedUser.id,
        roleId,
      });
    }
  };

  // Group permissions by resource
  const groupedPermissions = permissions.reduce(
    (acc, perm) => {
      if (!acc[perm.resource]) {
        acc[perm.resource] = [];
      }
      acc[perm.resource].push(perm);
      return acc;
    },
    {} as Record<string, Permission[]>
  );

  if (!isSuperAdmin) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <Lock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Access Denied</h3>
              <p className="text-gray-600">
                Only super administrators can access role management.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="h-8 w-8 text-blue-600" />
            Role Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage user roles and permissions
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roles List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Roles ({roles.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {roles.map(role => (
              <div
                key={role.id}
                className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{role.display_name}</h3>
                      {role.is_system_role && (
                        <Badge variant="secondary" className="text-xs">
                          System
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {role.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      {role.permission_count} permissions
                    </p>
                  </div>
                </div>

                {/* Permission preview */}
                <div className="mt-3 flex flex-wrap gap-1">
                  {role.permissions.slice(0, 3).map((perm, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {perm.split(':')[0]}
                    </Badge>
                  ))}
                  {role.permissions.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{role.permissions.length - 3}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* User Selection & Role Assignment */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Role Assignment
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* User Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Select User
              </label>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={selectedUser?.id || ''}
                onChange={e => {
                  const user = users.find(u => u.id === e.target.value);
                  if (user) handleSelectUser(user);
                }}
              >
                <option value="">-- Select a user --</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.full_name || user.email} ({user.email})
                  </option>
                ))}
              </select>
            </div>

            {/* User Roles Display */}
            {selectedUser && userRoles && (
              <div className="space-y-4">
                {/* Current Roles */}
                <div>
                  <h3 className="font-semibold mb-2">Current Roles</h3>
                  {userRoles.roles.length === 0 ? (
                    <div className="text-sm text-gray-500 py-4 text-center border rounded-lg">
                      No roles assigned
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {userRoles.roles.map(role => (
                        <div
                          key={role.id}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div>
                            <p className="font-medium">{role.display_name}</p>
                            <p className="text-xs text-gray-500">
                              {role.permission_count} permissions
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveRole(role.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Assign New Role */}
                <div>
                  <h3 className="font-semibold mb-2">Assign Role</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {roles
                      .filter(
                        role => !userRoles.roles.find(ur => ur.id === role.id)
                      )
                      .map(role => (
                        <Button
                          key={role.id}
                          variant="outline"
                          onClick={() => handleAssignRole(role.id)}
                          disabled={assigningRole}
                          className="justify-start"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          {role.display_name}
                        </Button>
                      ))}
                  </div>
                </div>

                {/* Effective Permissions */}
                <div>
                  <h3 className="font-semibold mb-2">
                    Effective Permissions ({userRoles.all_permissions.length})
                  </h3>
                  <div className="border rounded-lg p-3 max-h-64 overflow-y-auto">
                    <div className="flex flex-wrap gap-1">
                      {userRoles.all_permissions.map((perm, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="text-xs"
                        >
                          {perm}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Permission Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Permission Matrix
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {Object.entries(groupedPermissions).map(([resource, perms]) => (
              <div key={resource}>
                <h3 className="font-semibold text-lg mb-3 capitalize">
                  {resource} Permissions
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {perms.map(perm => (
                    <div
                      key={perm.id}
                      className="p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <Badge variant="outline" className="text-xs">
                          {perm.action}
                        </Badge>
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      </div>
                      <p className="font-medium text-sm mt-2">
                        {perm.display_name}
                      </p>
                      {perm.description && (
                        <p className="text-xs text-gray-500 mt-1">
                          {perm.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
