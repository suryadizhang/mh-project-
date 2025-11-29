import { DollarSign, Loader2, MapPin, Save } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

export interface TravelFeeStationFormData {
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

interface TravelFeeStationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: () => void;
  formData: TravelFeeStationFormData;
  onFormChange: (data: TravelFeeStationFormData) => void;
  isEditing: boolean;
  isSaving: boolean;
}

export function TravelFeeStationDialog({
  open,
  onOpenChange,
  onSave,
  formData,
  onFormChange,
  isEditing,
  isSaving,
}: TravelFeeStationDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-blue-600" />
            {isEditing ? 'Edit Travel Fee Station' : 'Create Travel Fee Station'}
          </DialogTitle>
          <DialogDescription>
            Configure station location, service area, and travel fee pricing rules
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Station Information Section */}
          <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-sm text-blue-900 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Station Information
            </h3>

            <div className="space-y-2">
              <Label htmlFor="station-name">Station Name *</Label>
              <Input
                id="station-name"
                value={formData.station_name}
                onChange={(e) => onFormChange({ ...formData, station_name: e.target.value })}
                placeholder="e.g., Fremont Station (Main)"
                className="bg-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="station-notes">Station Notes</Label>
              <Input
                id="station-notes"
                value={formData.notes || ''}
                onChange={(e) => onFormChange({ ...formData, notes: e.target.value || null })}
                placeholder="e.g., Main station covering Bay Area and Sacramento regions"
                className="bg-white"
              />
            </div>
          </div>

          {/* Location Details Section */}
          <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
            <h3 className="font-semibold text-sm text-green-900 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Location Details
            </h3>

            <div className="space-y-2">
              <Label htmlFor="station-address">Street Address *</Label>
              <Input
                id="station-address"
                value={formData.station_address}
                onChange={(e) => onFormChange({ ...formData, station_address: e.target.value })}
                placeholder="e.g., 47481 Towhee St"
                className="bg-white"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="station-city">City *</Label>
                <Input
                  id="station-city"
                  value={formData.city}
                  onChange={(e) => onFormChange({ ...formData, city: e.target.value })}
                  placeholder="e.g., Fremont"
                  className="bg-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="station-state">State *</Label>
                <Input
                  id="station-state"
                  value={formData.state}
                  onChange={(e) => onFormChange({ ...formData, state: e.target.value })}
                  placeholder="e.g., CA"
                  className="bg-white"
                  maxLength={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="station-postal">Postal Code *</Label>
                <Input
                  id="station-postal"
                  value={formData.postal_code}
                  onChange={(e) => onFormChange({ ...formData, postal_code: e.target.value })}
                  placeholder="e.g., 94539"
                  className="bg-white"
                />
              </div>
            </div>

            {/* Optional Geocoding */}
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-green-300">
              <div className="space-y-2">
                <Label htmlFor="station-lat" className="text-xs text-gray-600">
                  Latitude (Optional)
                </Label>
                <Input
                  id="station-lat"
                  type="number"
                  step="0.000001"
                  value={formData.latitude ?? ''}
                  onChange={(e) => onFormChange({ ...formData, latitude: e.target.value ? parseFloat(e.target.value) : null })}
                  placeholder="e.g., 37.548270"
                  className="bg-white text-xs"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="station-lng" className="text-xs text-gray-600">
                  Longitude (Optional)
                </Label>
                <Input
                  id="station-lng"
                  type="number"
                  step="0.000001"
                  value={formData.longitude ?? ''}
                  onChange={(e) => onFormChange({ ...formData, longitude: e.target.value ? parseFloat(e.target.value) : null })}
                  placeholder="e.g., -121.988571"
                  className="bg-white text-xs"
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 italic">
              💡 Tip: Leave lat/long empty to use address-based distance calculation
            </p>
          </div>

          {/* Pricing Rules Section */}
          <div className="space-y-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
            <h3 className="font-semibold text-sm text-amber-900 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Travel Fee Pricing Rules
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="free-miles" className="flex items-center gap-2">
                  Free Miles *
                  <span className="text-xs text-green-600 font-normal">(No charge within this range)</span>
                </Label>
                <Input
                  id="free-miles"
                  type="number"
                  step="0.01"
                  value={formData.free_miles}
                  onChange={(e) => onFormChange({ ...formData, free_miles: parseFloat(e.target.value) || 0 })}
                  placeholder="e.g., 30"
                  className="bg-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="price-per-mile" className="flex items-center gap-2">
                  Price Per Mile ($) *
                  <span className="text-xs text-blue-600 font-normal">(After free miles)</span>
                </Label>
                <Input
                  id="price-per-mile"
                  type="number"
                  step="0.01"
                  value={formData.price_per_mile}
                  onChange={(e) => onFormChange({ ...formData, price_per_mile: parseFloat(e.target.value) || 0 })}
                  placeholder="e.g., 2.00"
                  className="bg-white"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-distance" className="flex items-center gap-2">
                Max Service Distance (Optional)
                <span className="text-xs text-gray-500 font-normal">(Leave empty for unlimited)</span>
              </Label>
              <Input
                id="max-distance"
                type="number"
                step="0.01"
                value={formData.max_service_distance ?? ''}
                onChange={(e) => onFormChange({ ...formData, max_service_distance: e.target.value ? parseFloat(e.target.value) : null })}
                placeholder="e.g., 100 (or leave empty)"
                className="bg-white"
              />
            </div>

            {/* Pricing Example */}
            <div className="p-3 bg-white rounded border border-amber-300">
              <p className="text-xs font-semibold text-amber-900 mb-2">📊 Pricing Examples:</p>
              <ul className="text-xs text-gray-700 space-y-1">
                <li>• Customer 20 miles away: <span className="font-semibold text-green-600">$0.00</span> (within {formData.free_miles} free miles)</li>
                <li>• Customer 45 miles away: <span className="font-semibold text-blue-600">${((45 - formData.free_miles) * formData.price_per_mile).toFixed(2)}</span> ({(45 - formData.free_miles).toFixed(1)} × ${formData.price_per_mile.toFixed(2)})</li>
                <li>• Customer 100 miles away: <span className="font-semibold text-blue-600">${((100 - formData.free_miles) * formData.price_per_mile).toFixed(2)}</span> ({(100 - formData.free_miles).toFixed(1)} × ${formData.price_per_mile.toFixed(2)})</li>
              </ul>
            </div>
          </div>

          {/* Status & Settings Section */}
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Settings</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="station-active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => onFormChange({ ...formData, is_active: checked })}
                />
                <Label htmlFor="station-active" className="flex items-center gap-2">
                  Active
                  {formData.is_active ? (
                    <span className="text-xs text-green-600">(Visible to customers)</span>
                  ) : (
                    <span className="text-xs text-gray-500">(Hidden from customers)</span>
                  )}
                </Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="station-order">Display Order</Label>
                <Input
                  id="station-order"
                  type="number"
                  value={formData.display_order}
                  onChange={(e) => onFormChange({ ...formData, display_order: parseInt(e.target.value) || 0 })}
                  className="bg-white"
                />
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="border-t pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={onSave}
            disabled={isSaving || !formData.station_name || !formData.station_address || !formData.city || !formData.state || !formData.postal_code}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ? 'Update Station' : 'Create Station'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
