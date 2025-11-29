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

export interface MenuItemFormData {
  name: string;
  description: string | null;
  price: number;
  category: 'base_pricing' | 'protein' | 'side';
  subcategory: string | null;
  tags: string[];
  is_included: boolean;
  is_active: boolean;
  display_order: number;
}

interface MenuItemDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: () => void;
  formData: MenuItemFormData;
  onFormChange: (data: MenuItemFormData) => void;
  isEditing: boolean;
  isSaving: boolean;
}

export function MenuItemDialog({
  open,
  onOpenChange,
  onSave,
  formData,
  onFormChange,
  isEditing,
  isSaving,
}: MenuItemDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            {isEditing ? 'Edit Menu Item' : 'Create Menu Item'}
          </DialogTitle>
          <DialogDescription>
            Configure menu item details, pricing, and availability
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
              <Label htmlFor="menu-name">Item Name *</Label>
              <Input
                id="menu-name"
                value={formData.name}
                onChange={(e) => onFormChange({ ...formData, name: e.target.value })}
                placeholder="e.g., Hibachi Chicken"
                className="bg-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="menu-description">Description</Label>
              <Input
                id="menu-description"
                value={formData.description || ''}
                onChange={(e) => onFormChange({ ...formData, description: e.target.value || null })}
                placeholder="Optional description"
                className="bg-white"
              />
            </div>
          </div>

          {/* Pricing & Category Section */}
          <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
            <h3 className="font-semibold text-sm text-green-900 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Pricing & Category
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="menu-price">Price ($) *</Label>
                <Input
                  id="menu-price"
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => onFormChange({ ...formData, price: parseFloat(e.target.value) || 0 })}
                  className="bg-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="menu-category">Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value: string) => onFormChange({ ...formData, category: value as 'base_pricing' | 'protein' | 'side' })}
                >
                  <SelectTrigger id="menu-category" className="bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="base_pricing">Base Pricing</SelectItem>
                    <SelectItem value="protein">Protein</SelectItem>
                    <SelectItem value="side">Side</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="menu-subcategory">Subcategory</Label>
              <Select
                value={formData.subcategory || ''}
                onValueChange={(value: string) => onFormChange({ ...formData, subcategory: value || null })}
              >
                <SelectTrigger id="menu-subcategory" className="bg-white">
                  <SelectValue placeholder="Select subcategory (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  <SelectItem value="poultry">🍗 Poultry (Chicken, Duck)</SelectItem>
                  <SelectItem value="fish">🐟 Fish (Salmon - Safe for shellfish allergies)</SelectItem>
                  <SelectItem value="shellfish">🦐 Shellfish (Shrimp, Scallops, Lobster - ⚠️ Allergen)</SelectItem>
                  <SelectItem value="beef">🥩 Beef</SelectItem>
                  <SelectItem value="vegetarian">🥗 Vegetarian</SelectItem>
                  <SelectItem value="tofu">🧀 Tofu</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                Primary classification for AI allergen awareness and filtering
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="menu-tags">Tags (Multi-select)</Label>
              <div className="bg-white p-3 rounded-md border space-y-2">
                <p className="text-xs text-gray-500 mb-2">Select all that apply:</p>

                {/* Allergen Tags */}
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-red-600">⚠️ Allergen Tags (FDA Top 9)</p>
                  <div className="grid grid-cols-2 gap-2">
                    {['contains_shellfish', 'contains_eggs', 'contains_fish'].map(tag => (
                      <label key={tag} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.tags?.includes(tag)}
                          onChange={(e) => {
                            const newTags = e.target.checked
                              ? [...(formData.tags || []), tag]
                              : (formData.tags || []).filter(t => t !== tag);
                            onFormChange({ ...formData, tags: newTags });
                          }}
                          className="rounded"
                        />
                        <span>{tag.replace('contains_', '').replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Dietary Tags */}
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-green-600">✅ Dietary Tags (Allergen-Friendly!)</p>
                  <div className="grid grid-cols-3 gap-2">
                    {['vegan', 'vegetarian', 'gluten_free', 'dairy_free', 'nut_free', 'sesame_free', 'can_be_gluten_free'].map(tag => (
                      <label key={tag} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.tags?.includes(tag)}
                          onChange={(e) => {
                            const newTags = e.target.checked
                              ? [...(formData.tags || []), tag]
                              : (formData.tags || []).filter(t => t !== tag);
                            onFormChange({ ...formData, tags: newTags });
                          }}
                          className="rounded"
                        />
                        <span>{tag.replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Religious/Cultural Tags */}
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-purple-600">🕌 Religious/Cultural (Certified!)</p>
                  <div className="grid grid-cols-2 gap-2">
                    {['halal', 'kosher_style'].map(tag => (
                      <label key={tag} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.tags?.includes(tag)}
                          onChange={(e) => {
                            const newTags = e.target.checked
                              ? [...(formData.tags || []), tag]
                              : (formData.tags || []).filter(t => t !== tag);
                            onFormChange({ ...formData, tags: newTags });
                          }}
                          className="rounded"
                        />
                        <span>{tag.replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Cooking Style Tags */}
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-blue-600">🔥 Cooking Style</p>
                  <div className="grid grid-cols-2 gap-2">
                    {['grilled', 'fried', 'steamed', 'raw'].map(tag => (
                      <label key={tag} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.tags?.includes(tag)}
                          onChange={(e) => {
                            const newTags = e.target.checked
                              ? [...(formData.tags || []), tag]
                              : (formData.tags || []).filter(t => t !== tag);
                            onFormChange({ ...formData, tags: newTags });
                          }}
                          className="rounded"
                        />
                        <span>{tag}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Special Tags */}
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-yellow-600">⭐ Special</p>
                  <div className="grid grid-cols-3 gap-2">
                    {['premium', 'customer_favorite', 'high_protein', 'customizable', 'kid_friendly', 'chef_special', 'seasonal'].map(tag => (
                      <label key={tag} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.tags?.includes(tag)}
                          onChange={(e) => {
                            const newTags = e.target.checked
                              ? [...(formData.tags || []), tag]
                              : (formData.tags || []).filter(t => t !== tag);
                            onFormChange({ ...formData, tags: newTags });
                          }}
                          className="rounded"
                        />
                        <span>{tag.replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                Tags help AI understand allergens, dietary restrictions, and item characteristics
              </p>
            </div>
          </div>

          {/* Settings Section */}
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Settings</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="menu-included"
                  checked={formData.is_included}
                  onCheckedChange={(checked) => onFormChange({ ...formData, is_included: checked })}
                />
                <Label htmlFor="menu-included" className="flex items-center gap-2">
                  Included in base
                  {formData.is_included ? (
                    <span className="text-xs text-green-600">(No extra charge)</span>
                  ) : (
                    <span className="text-xs text-gray-500">(Additional cost)</span>
                  )}
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="menu-active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => onFormChange({ ...formData, is_active: checked })}
                />
                <Label htmlFor="menu-active" className="flex items-center gap-2">
                  Active
                  {formData.is_active ? (
                    <span className="text-xs text-green-600">(Visible to customers)</span>
                  ) : (
                    <span className="text-xs text-gray-500">(Hidden from customers)</span>
                  )}
                </Label>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="menu-order">Display Order</Label>
              <Input
                id="menu-order"
                type="number"
                value={formData.display_order}
                onChange={(e) => onFormChange({ ...formData, display_order: parseInt(e.target.value) || 0 })}
                className="bg-white"
              />
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
            className="bg-green-600 hover:bg-green-700"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ? 'Update Menu Item' : 'Create Menu Item'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
