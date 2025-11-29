import { DollarSign, Loader2, Save } from 'lucide-react';

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export interface AddonItemFormData {
  name: string;
  description: string | null;
  price: number;
  category: 'protein_upgrades' | 'enhancements' | 'equipment' | 'entertainment' | 'beverages';
  is_active: boolean;
  display_order: number;
}

interface AddonItemDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: () => void;
  formData: AddonItemFormData;
  onFormChange: (data: AddonItemFormData) => void;
  isEditing: boolean;
  isSaving: boolean;
}

export function AddonItemDialog({
  open,
  onOpenChange,
  onSave,
  formData,
  onFormChange,
  isEditing,
  isSaving,
}: AddonItemDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-purple-600" />
            {isEditing ? 'Edit Addon Item' : 'Create Addon Item'}
          </DialogTitle>
          <DialogDescription>
            Configure premium proteins, enhancements, equipment, and beverages
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Basic Information Section */}
          <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-sm text-blue-900 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Basic Information
            </h3>

            <div className="space-y-2">
              <Label htmlFor="addon-name">Item Name *</Label>
              <Input
                id="addon-name"
                value={formData.name}
                onChange={(e) => onFormChange({ ...formData, name: e.target.value })}
                placeholder="e.g., Premium Salmon"
                className="bg-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="addon-description">Description</Label>
              <Input
                id="addon-description"
                value={formData.description || ''}
                onChange={(e) => onFormChange({ ...formData, description: e.target.value || null })}
                placeholder="Optional description"
                className="bg-white"
              />
            </div>
          </div>

          {/* Pricing & Category Section */}
          <div className="space-y-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
            <h3 className="font-semibold text-sm text-purple-900 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Pricing & Category
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="addon-price">Price ($) *</Label>
                <Input
                  id="addon-price"
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => onFormChange({ ...formData, price: parseFloat(e.target.value) || 0 })}
                  className="bg-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="addon-category">Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value: string) => onFormChange({ ...formData, category: value as 'protein_upgrades' | 'enhancements' | 'equipment' | 'entertainment' | 'beverages' })}
                >
                  <SelectTrigger id="addon-category" className="bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="protein_upgrades">Protein Upgrades</SelectItem>
                    <SelectItem value="enhancements">Enhancements</SelectItem>
                    <SelectItem value="equipment">Equipment</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                    <SelectItem value="beverages">Beverages</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Settings Section */}
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Settings</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="addon-active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => onFormChange({ ...formData, is_active: checked })}
                />
                <Label htmlFor="addon-active" className="flex items-center gap-2">
                  Active
                  {formData.is_active ? (
                    <span className="text-xs text-green-600">(Visible to customers)</span>
                  ) : (
                    <span className="text-xs text-gray-500">(Hidden from customers)</span>
                  )}
                </Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="addon-order">Display Order</Label>
                <Input
                  id="addon-order"
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
            disabled={isSaving || !formData.name}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ? 'Update Addon Item' : 'Create Addon Item'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
