'use client';

import {
  Building,
  Edit,
  Eye,
  Mail,
  MapPin,
  Phone,
  Plus,
  Shield,
  Trash2,
  User,
  UserPlus,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/lib/logger';
import type { AuditLog, Station, StationUser } from '@/services/api';
import { stationService } from '@/services/api';

interface StationManagerProps {
  className?: string;
}

export const StationManager: React.FC<StationManagerProps> = ({
  className,
}) => {
  const { hasPermission, isSuperAdmin } = useAuth();
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const [stationUsers, setStationUsers] = useState<StationUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'audit'>(
    'overview'
  );

  // Check permissions
  const canManageStations = isSuperAdmin() || hasPermission('manage_stations');
  const canViewStations = canManageStations || hasPermission('view_stations');
  const canManageUsers =
    isSuperAdmin() || hasPermission('manage_station_users');

  useEffect(() => {
    if (canViewStations) {
      loadStations();
    }
  }, [canViewStations]);

  const loadStations = async () => {
    try {
      setLoading(true);
      const response = await stationService.getStations();
      if (response.data) {
        setStations(response.data);
        if (response.data.length > 0 && !selectedStation) {
          setSelectedStation(response.data[0]);
        }
      }
    } catch (err: any) {
      setError('Failed to load stations: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadStationUsers = async (stationId: number) => {
    try {
      const response = await stationService.getStationUsers(stationId, true);
      if (response.data) {
        setStationUsers(response.data);
      }
    } catch (err: any) {
      logger.error(err as Error, {
        context: 'load_station_users',
        station_id: stationId,
      });
    }
  };

  const loadAuditLogs = async (stationId: number) => {
    try {
      const response = await stationService.getStationAuditLogs(stationId, {
        limit: 50,
      });
      if (response.data) {
        setAuditLogs(response.data);
      }
    } catch (err: any) {
      logger.error(err as Error, {
        context: 'load_audit_logs',
        station_id: stationId,
      });
    }
  };

  useEffect(() => {
    if (selectedStation) {
      if (activeTab === 'users' && canManageUsers) {
        loadStationUsers(selectedStation.id);
      } else if (activeTab === 'audit' && canViewStations) {
        loadAuditLogs(selectedStation.id);
      }
    }
  }, [selectedStation, activeTab, canManageUsers, canViewStations]);

  if (!canViewStations) {
    return (
      <div className={`${className} flex items-center justify-center p-8`}>
        <div className="text-center">
          <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">
            You don&apos;t have permission to view stations.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`${className} flex items-center justify-center p-8`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} p-4`}>
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      </div>
    );
  }

  const renderStationOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Station Details
            </CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-600">Name</p>
                <p className="text-lg font-semibold">{selectedStation?.name}</p>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <MapPin className="h-4 w-4 mr-2" />
                {selectedStation?.location}
              </div>
              {selectedStation?.phone && (
                <div className="flex items-center text-sm text-gray-600">
                  <Phone className="h-4 w-4 mr-2" />
                  {selectedStation.phone}
                </div>
              )}
              {selectedStation?.email && (
                <div className="flex items-center text-sm text-gray-600">
                  <Mail className="h-4 w-4 mr-2" />
                  {selectedStation.email}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <div
              className={`h-3 w-3 rounded-full ${selectedStation?.is_active ? 'bg-green-500' : 'bg-red-500'}`}
            />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-600">Status</p>
                <p
                  className={`text-lg font-semibold ${selectedStation?.is_active ? 'text-green-600' : 'text-red-600'}`}
                >
                  {selectedStation?.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Created</p>
                <p className="text-sm">
                  {selectedStation?.created_at
                    ? new Date(selectedStation.created_at).toLocaleDateString()
                    : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {canManageStations && (
        <div className="flex space-x-3">
          <Button variant="outline" className="flex items-center">
            <Edit className="h-4 w-4 mr-2" />
            Edit Station
          </Button>
          <Button
            variant="outline"
            className="flex items-center text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Station
          </Button>
        </div>
      )}
    </div>
  );

  const renderStationUsers = () => (
    <div className="space-y-4">
      {canManageUsers && (
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium">Station Users</h3>
          <Button className="flex items-center">
            <UserPlus className="h-4 w-4 mr-2" />
            Add User
          </Button>
        </div>
      )}

      <div className="space-y-3">
        {stationUsers.map(user => (
          <Card key={user.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {user.user_email || `User ${user.user_id}`}
                    </p>
                    <p className="text-sm text-gray-600">{user.role}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      user.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                  {canManageUsers && (
                    <Button variant="outline" size="sm">
                      <Edit className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderAuditLogs = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Audit Trail</h3>

      <div className="space-y-3">
        {auditLogs.map(log => (
          <Card key={log.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="font-medium">{log.action}</p>
                  <p className="text-sm text-gray-600">
                    {JSON.stringify(log.details)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(log.timestamp).toLocaleString()}
                  </p>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>User: {log.user_id}</p>
                  <p>IP: {log.ip_address}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <div className={className}>
      <div className="flex h-full">
        {/* Station List */}
        <div className="w-1/3 border-r border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Stations</h2>
            {canManageStations && (
              <Button size="sm" className="flex items-center">
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            )}
          </div>

          <div className="space-y-2">
            {stations.map(station => (
              <Card
                key={station.id}
                className={`cursor-pointer transition-colors ${
                  selectedStation?.id === station.id
                    ? 'bg-blue-50 border-blue-200'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedStation(station)}
              >
                <CardContent className="p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{station.name}</p>
                      <p className="text-sm text-gray-600">
                        {station.location}
                      </p>
                    </div>
                    <div
                      className={`h-2 w-2 rounded-full ${station.is_active ? 'bg-green-500' : 'bg-red-500'}`}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Station Details */}
        <div className="flex-1 p-6">
          {selectedStation ? (
            <>
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">{selectedStation.name}</h1>
                <div className="flex space-x-2">
                  <Button
                    variant={activeTab === 'overview' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('overview')}
                    className="flex items-center"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Overview
                  </Button>
                  {canManageUsers && (
                    <Button
                      variant={activeTab === 'users' ? 'default' : 'outline'}
                      onClick={() => setActiveTab('users')}
                      className="flex items-center"
                    >
                      <Users className="h-4 w-4 mr-2" />
                      Users
                    </Button>
                  )}
                  <Button
                    variant={activeTab === 'audit' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('audit')}
                    className="flex items-center"
                  >
                    <Shield className="h-4 w-4 mr-2" />
                    Audit
                  </Button>
                </div>
              </div>

              {activeTab === 'overview' && renderStationOverview()}
              {activeTab === 'users' && renderStationUsers()}
              {activeTab === 'audit' && renderAuditLogs()}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Building className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  Select a station to view details
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StationManager;
