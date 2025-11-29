/**
 * Menu Item Dialog with Multi-Tag Allergen System
 * Supports hierarchical categories + allergen tracking
 */

'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

// ============================================================================
// Type Definitions
// ============================================================================

export interface MenuItemFormData {
  id?: string;
  name: string;
  description: string;
  main_category: 'protein' | 'premium_protein' | 'appetizer' | 'addon' | 'sauce';
  tags: string[];
  base_price: number;
  is_included: boolean;
  is_active: boolean;
  display_order: number;
}

// ============================================================================
// Tag Configuration
// ============================================================================

const MAIN_CATEGORIES = [
  { value: 'protein', label: 'Protein (Base)', color: 'bg-blue-100 text-blue-800' },
  { value: 'premium_protein', label: 'Premium Protein (Upgrade)', color: 'bg-purple-100 text-purple-800' },
  { value: 'appetizer', label: 'Appetizer', color: 'bg-green-100 text-green-800' },
  { value: 'addon', label: 'Add-on', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'sauce', label: 'Sauce', color: 'bg-gray-100 text-gray-800' },
] as const;

const TAG_GROUPS = {
  protein_type: {
    label: 'Protein Type',
    color: 'bg-blue-50 border-blue-200',
    tags: [
      { value: 'poultry', label: 'Poultry (Chicken)' },
      { value: 'seafood', label: 'Seafood' },
      { value: 'beef', label: 'Beef' },
      { value: 'vegetarian', label: 'Vegetarian' },
    ],
  },
  seafood_subtype: {
    label: 'Seafood Sub-Type',
    color: 'bg-cyan-50 border-cyan-200',
    tags: [
      { value: 'fish', label: '🐟 Fish (Salmon)' },
      { value: 'shellfish', label: '🦞 Shellfish' },
      { value: 'crustaceans', label: '🦐 Crustaceans (Shrimp, Lobster)' },
      { value: 'mollusks', label: '🐚 Mollusks (Scallops)' },
    ],
  },
  preparation: {
    label: 'Preparation Method',
    color: 'bg-orange-50 border-orange-200',
    tags: [
      { value: 'grilled', label: 'Grilled' },
      { value: 'steamed', label: 'Steamed' },
      { value: 'pan_fried', label: 'Pan Fried' },
      { value: 'raw', label: 'Raw' },
    ],
  },
  dietary: {
    label: 'Dietary Attributes',
    color: 'bg-green-50 border-green-200',
    tags: [
      { value: 'gluten_free', label: '✓ Gluten-Free' },
      { value: 'dairy_free', label: '✓ Dairy-Free' },
    ],
  },
  allergens_major: {
    label: 'Major Allergens (FDA Top 9)',
    color: 'bg-red-50 border-red-200',
    tags: [
      { value: 'contains_shellfish', label: '⚠️ Contains Shellfish' },
      { value: 'contains_crustaceans', label: '⚠️ Contains Crustaceans' },
      { value: 'contains_mollusks', label: '⚠️ Contains Mollusks' },
      { value: 'contains_fish', label: '⚠️ Contains Fish' },
      { value: 'contains_gluten', label: '⚠️ Contains Gluten (Wheat)' },
      { value: 'contains_soy', label: '⚠️ Contains Soy' },
      { value: 'contains_eggs', label: '⚠️ Contains Eggs' },
      { value: 'contains_tree_nuts', label: '⚠️ Contains Tree Nuts' },
      { value: 'contains_peanuts', label: '⚠️ Contains Peanuts' },
      { value: 'contains_dairy', label: '⚠️ Contains Dairy' },
    ],
  },
  allergens_rare: {
    label: 'Rare/Emerging Allergens',
    color: 'bg-yellow-50 border-yellow-200',
    tags: [
      { value: 'contains_sesame', label: 'Contains Sesame' },
      { value: 'contains_sulfites', label: 'Contains Sulfites' },
      { value: 'contains_msg', label: 'Contains MSG' },
      { value: 'contains_nightshades', label: 'Contains Nightshades' },
      { value: 'contains_corn', label: 'Contains Corn' },
      { value: 'contains_mustard', label: 'Contains Mustard (EU)' },
      { value: 'contains_celery', label: 'Contains Celery (EU)' },
      { value: 'contains_lupin', label: 'Contains Lupin (EU)' },
    ],
  },
};

// ============================================================================
// Component
// ============================================================================

interface MenuItemDialogNewProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: MenuItemFormData) => void;
  initialData?: MenuItemFormData | null;
  mode: 'create' | 'edit';
}

export function MenuItemDialogNew({
  isOpen,
  onClose,
  onSave,
  initialData,
  mode,
}: MenuItemDialogNewProps) {
  const [formData, setFormData] = useState<MenuItemFormData>({
    name: '',
    description: '',
    main_category: 'protein',
    tags: [],
    base_price: 0,
    is_included: false,
    is_active: true,
    display_order: 0,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when dialog opens/closes or initialData changes
  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData(initialData);
      } else {
        setFormData({
          name: '',
          description: '',
          main_category: 'protein',
          tags: [],
          base_price: 0,
          is_included: false,
          is_active: true,
          display_order: 0,
        });
      }
      setErrors({});
    }
  }, [isOpen, initialData]);

  // ============================================================================
  // Tag Management
  // ============================================================================

  const toggleTag = (tag: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter((t) => t !== tag)
        : [...prev.tags, tag],
    }));
  };

  const removeTag = (tag: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tag),
    }));
  };

  const isTagSelected = (tag: string) => formData.tags.includes(tag);

  // ============================================================================
  // Validation
  // ============================================================================

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (formData.base_price < 0) {
      newErrors.base_price = 'Price must be non-negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // ============================================================================
  // Handlers
  // ============================================================================

  const handleSave = () => {
    if (!validateForm()) return;

    // Show alert for now (backend not connected)
    alert(
      `[PREVIEW MODE]\n\nBackend not connected yet. Would save:\n\n${JSON.stringify(
        formData,
        null,
        2
      )}`
    );

    onSave(formData);
  };

  const handleCancel = () => {
    setFormData({
      name: '',
      description: '',
      main_category: 'protein',
      tags: [],
      base_price: 0,
      is_included: false,
      is_active: true,
      display_order: 0,
    });
    setErrors({});
    onClose();
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Add New Menu Item' : 'Edit Menu Item'}
          </DialogTitle>
          <DialogDescription>
            Configure menu item with category, tags, allergens, and pricing.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">
                Item Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="e.g., Hibachi Shrimp"
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="base_price">
                Base Price (USD) <span className="text-red-500">*</span>
              </Label>
              <Input
                id="base_price"
                type="number"
                step="0.01"
                min="0"
                value={formData.base_price}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    base_price: parseFloat(e.target.value) || 0,
                  })
                }
                placeholder="21.99"
              />
              {errors.base_price && (
                <p className="text-sm text-red-500">{errors.base_price}</p>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">
              Description <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Detailed description of the menu item..."
              rows={3}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description}</p>
            )}
          </div>

          {/* Main Category */}
          <div className="space-y-2">
            <Label htmlFor="main_category">
              Main Category <span className="text-red-500">*</span>
            </Label>
            <Select
              value={formData.main_category}
              onValueChange={(value) =>
                setFormData({ ...formData, main_category: value as MenuItemFormData['main_category'] })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MAIN_CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    <span className={`px-2 py-1 rounded ${cat.color}`}>
                      {cat.label}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Selected Tags Display */}
          {formData.tags.length > 0 && (
            <div className="space-y-2">
              <Label>Selected Tags ({formData.tags.length})</Label>
              <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg border">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-200 hover:bg-red-100 cursor-pointer"
                    onClick={() => removeTag(tag)}
                  >
                    {tag}
                    <X className="w-3 h-3 ml-1" />
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tag Groups */}
          <div className="space-y-4">
            <Label className="text-lg font-semibold">
              Tags (Multi-Select)
            </Label>

            {Object.entries(TAG_GROUPS).map(([groupKey, group]) => (
              <div
                key={groupKey}
                className={`p-4 rounded-lg border-2 ${group.color}`}
              >
                <h4 className="font-semibold mb-3">{group.label}</h4>
                <div className="grid grid-cols-2 gap-2">
                  {group.tags.map((tag) => (
                    <div key={tag.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`tag-${tag.value}`}
                        checked={isTagSelected(tag.value)}
                        onChange={() => toggleTag(tag.value)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <Label
                        htmlFor={`tag-${tag.value}`}
                        className="text-sm cursor-pointer"
                      >
                        {tag.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Options */}
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_included"
                checked={formData.is_included}
                onChange={(e) =>
                  setFormData({ ...formData, is_included: e.target.checked })
                }
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <Label htmlFor="is_included" className="cursor-pointer">
                Included in Base Price
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <Label htmlFor="is_active" className="cursor-pointer">
                Active
              </Label>
            </div>

            <div className="space-y-2">
              <Label htmlFor="display_order">Display Order</Label>
              <Input
                id="display_order"
                type="number"
                min="0"
                value={formData.display_order}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    display_order: parseInt(e.target.value) || 0,
                  })
                }
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            {mode === 'create' ? 'Create Item' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
