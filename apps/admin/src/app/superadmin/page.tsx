import { AlertTriangle, Database, Settings, Shield, Users, Key } from 'lucide-react';
import Link from 'next/link';

import { BaseLocationManager } from '@/components/BaseLocationManager';
import { Button } from '@/components/ui/button';

export default function SuperAdminPage() {
  const systemStats = [
    { label: 'Database Size', value: '2.4 GB', status: 'normal' },
    { label: 'Server Uptime', value: '99.9%', status: 'excellent' },
    { label: 'Active Sessions', value: '42', status: 'normal' },
    { label: 'Error Rate', value: '0.1%', status: 'good' },
  ];

  const adminUsers = [
    {
      id: 1,
      name: 'Admin User',
      email: 'admin@myhibachi.com',
      role: 'Super Admin',
      lastActive: '2025-01-30',
    },
    {
      id: 2,
      name: 'Manager User',
      email: 'manager@myhibachi.com',
      role: 'Manager',
      lastActive: '2025-01-30',
    },
    {
      id: 3,
      name: 'Staff User',
      email: 'staff@myhibachi.com',
      role: 'Staff',
      lastActive: '2025-01-29',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Shield className="w-8 h-8 text-red-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Super Admin</h1>
          <p className="text-gray-600">
            Advanced system administration and settings
          </p>
        </div>
      </div>

      {/* Warning Banner */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-600 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Warning</h3>
            <p className="text-sm text-red-700">
              This section contains sensitive system controls. Changes here can
              affect the entire application.
            </p>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {systemStats.map((stat, index) => (
          <div
            key={index}
            className="bg-white p-6 rounded-lg shadow border border-gray-200"
          >
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-600">{stat.label}</p>
              <div
                className={`mt-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  stat.status === 'excellent'
                    ? 'bg-green-100 text-green-800'
                    : stat.status === 'good'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                }`}
              >
                {stat.status}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Admin Users */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Admin Users</h2>
          <div className="flex gap-2">
            <Link href="/superadmin/users">
              <Button variant="outline">
                <Users className="w-4 h-4 mr-2" />
                User Management
              </Button>
            </Link>
            <Link href="/superadmin/roles">
              <Button variant="outline">
                <Key className="w-4 h-4 mr-2" />
                Role Management
              </Button>
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Active
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {adminUsers.map(user => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {user.name}
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.role === 'Super Admin'
                          ? 'bg-red-100 text-red-800'
                          : user.role === 'Manager'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.lastActive}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button className="text-blue-600 hover:text-blue-900">
                        Edit
                      </button>
                      <button className="text-red-600 hover:text-red-900">
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Base Location Management */}
      <BaseLocationManager />

      {/* System Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Database className="w-5 h-5 mr-2" />
              Database Management
            </h3>
          </div>
          <div className="p-6 space-y-3">
            <Button variant="outline" className="w-full justify-start">
              Backup Database
            </Button>
            <Button variant="outline" className="w-full justify-start">
              Restore Database
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start text-red-600 border-red-300 hover:bg-red-50"
            >
              Clear All Data
            </Button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              System Settings
            </h3>
          </div>
          <div className="p-6 space-y-3">
            <Button variant="outline" className="w-full justify-start">
              Application Settings
            </Button>
            <Button variant="outline" className="w-full justify-start">
              Email Configuration
            </Button>
            <Button variant="outline" className="w-full justify-start">
              Security Settings
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
