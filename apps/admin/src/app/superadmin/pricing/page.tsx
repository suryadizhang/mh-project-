'use client';

import { DollarSign, Loader2, Plus } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ActionButtons } from '@/components/pricing/ActionButtons';
import { DeleteConfirmDialog } from '@/components/pricing/DeleteConfirmDialog';
import { MenuItemDialog, type MenuItemFormData } from '@/components/pricing/MenuItemDialog';
import { AddonItemDialog, type AddonItemFormData } from '@/components/pricing/AddonItemDialog';
import { TravelFeeStationDialog, type TravelFeeStationFormData } from '@/components/pricing/TravelFeeStationDialog';

interface MenuItem {
  id: string;
  name: string;
  description: string | null;
  price: number;
  category: 'base_pricing' | 'protein' | 'side';
  is_included: boolean;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

interface AddonItem {
  id: string;
  name: string;
  description: string | null;
  price: number;
  category: 'protein_upgrades' | 'enhancements' | 'equipment' | 'entertainment' | 'beverages';
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

interface TravelFeeStation {
  id: number;
  station_name: string;
  station_address: string;
  city: string;
  state: string;
  postal_code: string;
  latitude: number | null;
  longitude: number | null;
  free_miles: number;
  price_per_mile: number;
  max_service_distance: number | null;
  is_active: boolean;
  notes: string | null;
  display_order: number;
}

type SortField = 'name' | 'category' | 'price' | 'status';
type SortDirection = 'asc' | 'desc';

export default function PricingManagementPage() {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [addonItems, setAddonItems] = useState<AddonItem[]>([]);
  const [travelFeeStations, setTravelFeeStations] = useState<TravelFeeStation[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Sorting states
  const [menuSortField, setMenuSortField] = useState<SortField>('name');
  const [menuSortDirection, setMenuSortDirection] = useState<SortDirection>('asc');
  const [addonSortField, setAddonSortField] = useState<SortField>('name');
  const [addonSortDirection, setAddonSortDirection] = useState<SortDirection>('asc');
  const [stationSortField, setStationSortField] = useState<'name' | 'city' | 'price'>('name');
  const [stationSortDirection, setStationSortDirection] = useState<SortDirection>('asc');

  // Modal states
  const [menuItemDialog, setMenuItemDialog] = useState(false);
  const [addonItemDialog, setAddonItemDialog] = useState(false);
  const [travelFeeDialog, setTravelFeeDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [editingMenuItem, setEditingMenuItem] = useState<MenuItem | null>(null);
  const [editingAddonItem, setEditingAddonItem] = useState<AddonItem | null>(null);
  const [editingTravelFee, setEditingTravelFee] = useState<TravelFeeStation | null>(null);
  const [deletingId, setDeletingId] = useState<string | number | null>(null);
  const [deletingType, setDeletingType] = useState<'menu' | 'addon' | 'travel_fee'>('menu');

  // Form states
  const [menuItemForm, setMenuItemForm] = useState<MenuItemFormData>({
    name: '',
    description: null,
    price: 0,
    category: 'base_pricing',
    subcategory: null,
    tags: [],
    is_included: false,
    is_active: true,
    display_order: 0,
  });

  const [addonItemForm, setAddonItemForm] = useState<AddonItemFormData>({
    name: '',
    description: null,
    price: 0,
    category: 'protein_upgrades',
    is_active: true,
    display_order: 0,
  });

  const [travelFeeForm, setTravelFeeForm] = useState<TravelFeeStationFormData>({
    station_name: '',
    station_address: '',
    city: '',
    state: '',
    postal_code: '',
    latitude: null,
    longitude: null,
    free_miles: 30,
    price_per_mile: 2.00,
    max_service_distance: null,
    is_active: true,
    notes: null,
    display_order: 0,
  });

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch pricing data
  const fetchPricingData = useCallback(async () => {
    try {
      setLoading(true);
      console.log('🔍 Fetching pricing data from:', `${API_BASE_URL}/api/v1/pricing/current`);

      const response = await fetch(`${API_BASE_URL}/api/v1/pricing/current`);
      console.log('📡 Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Response error:', errorText);
        throw new Error(`Failed to fetch pricing data: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Pricing data received:', {
        menuItems: data.menu_items?.length || 0,
        addonItems: data.addon_items?.length || 0,
        travelFeeStations: data.travel_fee_stations?.length || 0,
      });

      setMenuItems(data.menu_items || []);
      setAddonItems(data.addon_items || []);
      setTravelFeeStations(data.travel_fee_stations || []);
    } catch (error) {
      console.error('❌ Error fetching pricing data:', error);
      // Show error to user
      alert(`Failed to load pricing data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    fetchPricingData();
  }, [fetchPricingData]);

  // Menu Item handlers
  const handleCreateMenuItem = () => {
    setEditingMenuItem(null);
    setMenuItemForm({
      name: '',
      description: null,
      price: 0,
      category: 'base_pricing',
      is_included: false,
      is_active: true,
      display_order: menuItems.length,
    });
    setMenuItemDialog(true);
  };

  const handleEditMenuItem = (item: MenuItem) => {
    setEditingMenuItem(item);
    setMenuItemForm({
      name: item.name,
      description: item.description,
      price: item.price,
      category: item.category,
      subcategory: (item as any).subcategory || null,
      tags: (item as any).tags || [],
      is_included: item.is_included,
      is_active: item.is_active,
      display_order: item.display_order,
    });
    setMenuItemDialog(true);
  };

  const handleSaveMenuItem = async () => {
    try {
      setSaving(true);
      const url = editingMenuItem
        ? `${API_BASE_URL}/api/v1/menu-items/${editingMenuItem.id}`
        : `${API_BASE_URL}/api/v1/menu-items`;
      const method = editingMenuItem ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(menuItemForm),
      });

      if (!response.ok) throw new Error('Failed to save menu item');

      await fetchPricingData();
      setMenuItemDialog(false);
    } catch (error) {
      console.error('Error saving menu item:', error);
    } finally {
      setSaving(false);
    }
  };

  // Addon Item handlers
  const handleCreateAddonItem = () => {
    setEditingAddonItem(null);
    setAddonItemForm({
      name: '',
      description: null,
      price: 0,
      category: 'protein_upgrades',
      is_active: true,
      display_order: addonItems.length,
    });
    setAddonItemDialog(true);
  };

  const handleEditAddonItem = (item: AddonItem) => {
    setEditingAddonItem(item);
    setAddonItemForm({
      name: item.name,
      description: item.description,
      price: item.price,
      category: item.category,
      is_active: item.is_active,
      display_order: item.display_order,
    });
    setAddonItemDialog(true);
  };

  const handleSaveAddonItem = async () => {
    try {
      setSaving(true);
      const url = editingAddonItem
        ? `${API_BASE_URL}/api/v1/addon-items/${editingAddonItem.id}`
        : `${API_BASE_URL}/api/v1/addon-items`;
      const method = editingAddonItem ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(addonItemForm),
      });

      if (!response.ok) throw new Error('Failed to save addon item');

      await fetchPricingData();
      setAddonItemDialog(false);
    } catch (error) {
      console.error('Error saving addon item:', error);
    } finally {
      setSaving(false);
    }
  };

  // Travel Fee Station handlers
  const handleCreateTravelFeeStation = () => {
    setEditingTravelFee(null);
    setTravelFeeForm({
      station_name: '',
      station_address: '',
      city: '',
      state: '',
      postal_code: '',
      latitude: null,
      longitude: null,
      free_miles: 30,
      price_per_mile: 2.00,
      max_service_distance: null,
      is_active: true,
      notes: null,
      display_order: travelFeeStations.length,
    });
    setTravelFeeDialog(true);
  };

  const handleEditTravelFeeStation = (station: TravelFeeStation) => {
    setEditingTravelFee(station);
    setTravelFeeForm({
      station_name: station.station_name,
      station_address: station.station_address,
      city: station.city,
      state: station.state,
      postal_code: station.postal_code,
      latitude: station.latitude,
      longitude: station.longitude,
      free_miles: station.free_miles,
      price_per_mile: station.price_per_mile,
      max_service_distance: station.max_service_distance,
      is_active: station.is_active,
      notes: station.notes,
      display_order: station.display_order,
    });
    setTravelFeeDialog(true);
  };

  const handleSaveTravelFeeStation = async () => {
    try {
      setSaving(true);
      // TODO: Replace with actual API endpoint once backend is ready
      console.log('Saving travel fee station:', travelFeeForm);
      alert('Travel fee station CRUD not yet implemented in backend. This is a UI preview.');
      setTravelFeeDialog(false);
    } catch (error) {
      console.error('Error saving travel fee station:', error);
    } finally {
      setSaving(false);
    }
  };

  // Delete handler
  const handleDelete = async () => {
    if (!deletingId) return;

    try {
      setSaving(true);
      let url: string;

      if (deletingType === 'menu') {
        url = `${API_BASE_URL}/api/v1/menu-items/${deletingId}`;
      } else if (deletingType === 'addon') {
        url = `${API_BASE_URL}/api/v1/addon-items/${deletingId}`;
      } else {
        // travel_fee
        console.log('Deleting travel fee station:', deletingId);
        alert('Travel fee station CRUD not yet implemented in backend. This is a UI preview.');
        setDeleteDialog(false);
        setDeletingId(null);
        setSaving(false);
        return;
      }

      const response = await fetch(url, { method: 'DELETE' });
      if (!response.ok) throw new Error('Failed to delete item');

      await fetchPricingData();
      setDeleteDialog(false);
      setDeletingId(null);
    } catch (error) {
      console.error('Error deleting item:', error);
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = (id: string | number, type: 'menu' | 'addon' | 'travel_fee') => {
    setDeletingId(id);
    setDeletingType(type);
    setDeleteDialog(true);
  };

  // Sorting helper functions
  const sortMenuItems = (items: MenuItem[]) => {
    return [...items].sort((a, b) => {
      let compareValue = 0;

      switch (menuSortField) {
        case 'name':
          compareValue = a.name.localeCompare(b.name);
          break;
        case 'category':
          compareValue = a.category.localeCompare(b.category);
          break;
        case 'price':
          compareValue = a.price - b.price;
          break;
        case 'status':
          compareValue = (a.is_active === b.is_active) ? 0 : a.is_active ? -1 : 1;
          break;
      }

      return menuSortDirection === 'asc' ? compareValue : -compareValue;
    });
  };

  const sortAddonItems = (items: AddonItem[]) => {
    return [...items].sort((a, b) => {
      let compareValue = 0;

      switch (addonSortField) {
        case 'name':
          compareValue = a.name.localeCompare(b.name);
          break;
        case 'category':
          compareValue = a.category.localeCompare(b.category);
          break;
        case 'price':
          compareValue = a.price - b.price;
          break;
        case 'status':
          compareValue = (a.is_active === b.is_active) ? 0 : a.is_active ? -1 : 1;
          break;
      }

      return addonSortDirection === 'asc' ? compareValue : -compareValue;
    });
  };

  const sortTravelFeeStations = (stations: TravelFeeStation[]) => {
    return [...stations].sort((a, b) => {
      let compareValue = 0;

      switch (stationSortField) {
        case 'name':
          compareValue = a.station_name.localeCompare(b.station_name);
          break;
        case 'city':
          compareValue = a.city.localeCompare(b.city);
          break;
        case 'price':
          compareValue = a.price_per_mile - b.price_per_mile;
          break;
      }

      return stationSortDirection === 'asc' ? compareValue : -compareValue;
    });
  };

  const toggleMenuSort = (field: SortField) => {
    if (menuSortField === field) {
      setMenuSortDirection(menuSortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setMenuSortField(field);
      setMenuSortDirection('asc');
    }
  };

  const toggleAddonSort = (field: SortField) => {
    if (addonSortField === field) {
      setAddonSortDirection(addonSortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setAddonSortField(field);
      setAddonSortDirection('asc');
    }
  };

  const toggleStationSort = (field: 'name' | 'city' | 'price') => {
    if (stationSortField === field) {
      setStationSortDirection(stationSortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setStationSortField(field);
      setStationSortDirection('asc');
    }
  };

  const getSortIcon = (field: string, currentField: string, currentDirection: SortDirection) => {
    if (field !== currentField) return '↕';
    return currentDirection === 'asc' ? '↑' : '↓';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <DollarSign className="w-8 h-8 text-green-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Pricing Management</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage menu items, addon items, and pricing structure
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="menu" className="w-full">
        <TabsList className="grid w-full max-w-2xl grid-cols-3">
          <TabsTrigger value="menu">
            Menu Items ({menuItems.length})
          </TabsTrigger>
          <TabsTrigger value="addons">
            Addon Items ({addonItems.length})
          </TabsTrigger>
          <TabsTrigger value="travel_fees">
            Travel Fee Stations ({travelFeeStations.length})
          </TabsTrigger>
        </TabsList>

        {/* Menu Items Tab */}
        <TabsContent value="menu" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Base pricing, proteins, and sides included in standard menu
            </p>
            <Button onClick={handleCreateMenuItem}>
              <Plus className="w-4 h-4 mr-2" />
              Add Menu Item
            </Button>
          </div>

          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleMenuSort('name')}
                  >
                    Name {getSortIcon('name', menuSortField, menuSortDirection)}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleMenuSort('category')}
                  >
                    Category {getSortIcon('category', menuSortField, menuSortDirection)}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleMenuSort('price')}
                  >
                    Price {getSortIcon('price', menuSortField, menuSortDirection)}
                  </TableHead>
                  <TableHead>Included</TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleMenuSort('status')}
                  >
                    Status {getSortIcon('status', menuSortField, menuSortDirection)}
                  </TableHead>
                  <TableHead>Order</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortMenuItems(menuItems).map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        {item.name}
                        {item.description && (
                          <p className="text-xs text-gray-500">{item.description}</p>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                          {item.category.replace('_', ' ')}
                        </span>
                      </TableCell>
                      <TableCell className="font-semibold">
                        ${item.price.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        {item.is_included ? (
                          <span className="text-green-600 text-sm">✓ Included</span>
                        ) : (
                          <span className="text-gray-400 text-sm">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.is_active ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </TableCell>
                      <TableCell>{item.display_order}</TableCell>
                      <TableCell className="text-right">
                        <ActionButtons
                          onEdit={() => handleEditMenuItem(item)}
                          onDelete={() => confirmDelete(item.id, 'menu')}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        {/* Addon Items Tab */}
        <TabsContent value="addons" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Premium proteins, enhancements, equipment, and beverages
            </p>
            <Button onClick={handleCreateAddonItem}>
              <Plus className="w-4 h-4 mr-2" />
              Add Addon Item
            </Button>
          </div>

          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleAddonSort('name')}
                  >
                    Name {getSortIcon('name', addonSortField, addonSortDirection)}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleAddonSort('category')}
                  >
                    Category {getSortIcon('category', addonSortField, addonSortDirection)}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleAddonSort('price')}
                  >
                    Price {getSortIcon('price', addonSortField, addonSortDirection)}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleAddonSort('status')}
                  >
                    Status {getSortIcon('status', addonSortField, addonSortDirection)}
                  </TableHead>
                  <TableHead>Order</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortAddonItems(addonItems).map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        {item.name}
                        {item.description && (
                          <p className="text-xs text-gray-500">{item.description}</p>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                          {item.category.replace('_', ' ')}
                        </span>
                      </TableCell>
                      <TableCell className="font-semibold">
                        ${item.price.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        {item.is_active ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </TableCell>
                      <TableCell>{item.display_order}</TableCell>
                      <TableCell className="text-right">
                        <ActionButtons
                          onEdit={() => handleEditAddonItem(item)}
                          onDelete={() => confirmDelete(item.id, 'addon')}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        {/* Travel Fee Stations Tab */}
        <TabsContent value="travel_fees" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Configure station locations and travel fee pricing rules
            </p>
            <Button onClick={handleCreateTravelFeeStation}>
              <Plus className="w-4 h-4 mr-2" />
              Add Station
            </Button>
          </div>

          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleStationSort('name')}
                  >
                    Station Name {getSortIcon('name', stationSortField, stationSortDirection)}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleStationSort('city')}
                  >
                    Location {getSortIcon('city', stationSortField, stationSortDirection)}
                  </TableHead>
                  <TableHead>Free Miles</TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50 select-none"
                    onClick={() => toggleStationSort('price')}
                  >
                    Per Mile {getSortIcon('price', stationSortField, stationSortDirection)}
                  </TableHead>
                  <TableHead>Max Distance</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Order</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortTravelFeeStations(travelFeeStations).map((station) => (
                    <TableRow key={station.id}>
                      <TableCell className="font-medium">
                        {station.station_name}
                        {station.notes && (
                          <p className="text-xs text-gray-500">{station.notes}</p>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{station.station_address}</div>
                          <div className="text-gray-500">
                            {station.city}, {station.state} {station.postal_code}
                          </div>
                          {station.latitude && station.longitude && (
                            <div className="text-xs text-gray-400 mt-1">
                              📍 {station.latitude.toFixed(6)}, {station.longitude.toFixed(6)}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold text-green-700">
                          {station.free_miles} mi
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold text-blue-700">
                          ${station.price_per_mile.toFixed(2)}/mi
                        </span>
                      </TableCell>
                      <TableCell>
                        {station.max_service_distance ? (
                          <span className="text-gray-700">
                            {station.max_service_distance} mi
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">Unlimited</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {station.is_active ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </TableCell>
                      <TableCell>{station.display_order}</TableCell>
                      <TableCell className="text-right">
                        <ActionButtons
                          onEdit={() => handleEditTravelFeeStation(station)}
                          onDelete={() => confirmDelete(station.id, 'travel_fee')}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                {travelFeeStations.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                      No travel fee stations configured. Run database migration to add Fremont station.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>

      {/* Menu Item Dialog - Enhanced UX */}
      <MenuItemDialog
        open={menuItemDialog}
        onOpenChange={setMenuItemDialog}
        onSave={handleSaveMenuItem}
        formData={menuItemForm}
        onFormChange={setMenuItemForm}
        isEditing={!!editingMenuItem}
        isSaving={saving}
      />

      {/* Addon Item Dialog - Enhanced UX */}
      <AddonItemDialog
        open={addonItemDialog}
        onOpenChange={setAddonItemDialog}
        onSave={handleSaveAddonItem}
        formData={addonItemForm}
        onFormChange={setAddonItemForm}
        isEditing={!!editingAddonItem}
        isSaving={saving}
      />

      {/* Travel Fee Station Dialog - Enhanced UX */}
      <TravelFeeStationDialog
        open={travelFeeDialog}
        onOpenChange={setTravelFeeDialog}
        onSave={handleSaveTravelFeeStation}
        formData={travelFeeForm}
        onFormChange={setTravelFeeForm}
        isEditing={!!editingTravelFee}
        isSaving={saving}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmDialog
        open={deleteDialog}
        onOpenChange={setDeleteDialog}
        onConfirm={handleDelete}
        itemType={deletingType === 'menu' ? 'menu item' : deletingType === 'addon' ? 'addon item' : 'travel fee station'}
        isDeleting={saving}
      />
    </div>
  );
}
