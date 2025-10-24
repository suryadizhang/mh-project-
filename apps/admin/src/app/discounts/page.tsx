'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { logger } from '@/lib/logger';

// Validation schemas
const discountSchema = z.object({
  name: z.string().min(1, 'Discount name is required'),
  type: z.enum(['percentage', 'fixed_amount']),
  value: z.number().min(0.01, 'Value must be greater than 0'),
  description: z.string().min(1, 'Description is required'),
  code: z.string().optional(),
  minOrderAmount: z.number().min(0).optional(),
  maxDiscount: z.number().min(0).optional(),
  validFrom: z.string().optional(),
  validTo: z.string().optional(),
  isActive: z.boolean(),
});

type DiscountFormData = z.infer<typeof discountSchema>;

interface Discount extends DiscountFormData {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export default function AdminDiscountsPage() {
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDiscount, setEditingDiscount] = useState<Discount | null>(null);
  const [loading, setLoading] = useState(false);

  const form = useForm<DiscountFormData>({
    resolver: zodResolver(discountSchema),
    defaultValues: {
      name: '',
      type: 'percentage',
      value: 0,
      description: '',
      code: '',
      minOrderAmount: 0,
      maxDiscount: 0,
      validFrom: '',
      validTo: '',
      isActive: true,
    },
  });

  // Load sample discount data
  useEffect(() => {
    const sampleDiscounts: Discount[] = [
      {
        id: '1',
        name: 'First Time Customer',
        type: 'percentage',
        value: 10,
        description: '10% off for new customers',
        minOrderAmount: 300,
        maxDiscount: 100,
        isActive: true,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      {
        id: '2',
        name: 'Large Party Discount',
        type: 'percentage',
        value: 15,
        description: '15% off for parties of 15+ guests',
        minOrderAmount: 550,
        isActive: true,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      {
        id: '3',
        name: 'Birthday Special',
        type: 'fixed_amount',
        value: 25,
        description: '$25 off birthday celebrations',
        isActive: true,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      {
        id: '4',
        name: 'Holiday Promo',
        type: 'percentage',
        value: 20,
        description: '20% off holiday events',
        code: 'HOLIDAY25',
        minOrderAmount: 400,
        maxDiscount: 150,
        validFrom: '2024-11-15',
        validTo: '2025-01-15',
        isActive: true,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
      {
        id: '5',
        name: 'Military Discount',
        type: 'percentage',
        value: 10,
        description: '10% military discount (valid ID required)',
        isActive: false,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      },
    ];
    setDiscounts(sampleDiscounts);
  }, []);

  const openModal = (discount?: Discount) => {
    if (discount) {
      setEditingDiscount(discount);
      form.reset({
        name: discount.name,
        type: discount.type,
        value: discount.value,
        description: discount.description,
        code: discount.code || '',
        minOrderAmount: discount.minOrderAmount || 0,
        maxDiscount: discount.maxDiscount || 0,
        validFrom: discount.validFrom || '',
        validTo: discount.validTo || '',
        isActive: discount.isActive,
      });
    } else {
      setEditingDiscount(null);
      form.reset({
        name: '',
        type: 'percentage',
        value: 0,
        description: '',
        code: '',
        minOrderAmount: 0,
        maxDiscount: 0,
        validFrom: '',
        validTo: '',
        isActive: true,
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingDiscount(null);
    form.reset();
  };

  const onSubmit = async (data: DiscountFormData) => {
    setLoading(true);
    try {
      if (editingDiscount) {
        // Update existing discount
        const updatedDiscount: Discount = {
          ...editingDiscount,
          ...data,
          updatedAt: new Date().toISOString(),
        };
        setDiscounts(prev =>
          prev.map(d => (d.id === editingDiscount.id ? updatedDiscount : d))
        );
      } else {
        // Create new discount
        const newDiscount: Discount = {
          ...data,
          id: Date.now().toString(),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setDiscounts(prev => [newDiscount, ...prev]);
      }
      closeModal();
    } catch (error) {
      logger.error(error as Error, { context: 'save_discount', discount_id: editingDiscount?.id });
    } finally {
      setLoading(false);
    }
  };

  const deleteDiscount = (id: string) => {
    if (window.confirm('Are you sure you want to delete this discount?')) {
      setDiscounts(prev => prev.filter(d => d.id !== id));
    }
  };

  const toggleActive = (id: string) => {
    setDiscounts(prev =>
      prev.map(d =>
        d.id === id
          ? { ...d, isActive: !d.isActive, updatedAt: new Date().toISOString() }
          : d
      )
    );
  };

  const formatDiscountValue = (discount: Discount) => {
    if (discount.type === 'percentage') {
      return `${discount.value}%${
        discount.maxDiscount ? ` (max $${discount.maxDiscount})` : ''
      }`;
    } else {
      return `$${discount.value}`;
    }
  };

  return (
    <div className="admin-discounts-page">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Discount Management
              </h1>
              <p className="text-gray-600 mt-2">
                Manage discounts and promotional offers for MyHibachi bookings
              </p>
            </div>
            <button
              onClick={() => openModal()}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              ➕ Add New Discount
            </button>
          </div>
        </div>

        {/* Active Discounts */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Active Discounts ({discounts.filter(d => d.isActive).length})
          </h2>
          <div className="grid gap-4">
            {discounts
              .filter(d => d.isActive)
              .map(discount => (
                <div
                  key={discount.id}
                  className="border border-green-200 bg-green-50 rounded-lg p-4"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {discount.name}
                        </h3>
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                          {formatDiscountValue(discount)}
                        </span>
                        {discount.code && (
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                            Code: {discount.code}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 text-sm mb-2">
                        {discount.description}
                      </p>
                      <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                        {discount.minOrderAmount && (
                          <span>Min Order: ${discount.minOrderAmount}</span>
                        )}
                        {discount.validFrom && discount.validTo && (
                          <span>
                            Valid: {discount.validFrom} to {discount.validTo}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => toggleActive(discount.id)}
                        className="bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-3 py-1 rounded text-sm transition-colors"
                      >
                        Deactivate
                      </button>
                      <button
                        onClick={() => openModal(discount)}
                        className="bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded text-sm transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => deleteDiscount(discount.id)}
                        className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Inactive Discounts */}
        {discounts.filter(d => !d.isActive).length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Inactive Discounts ({discounts.filter(d => !d.isActive).length})
            </h2>
            <div className="grid gap-4">
              {discounts
                .filter(d => !d.isActive)
                .map(discount => (
                  <div
                    key={discount.id}
                    className="border border-gray-200 bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 opacity-75">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-gray-900">
                            {discount.name}
                          </h3>
                          <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs font-medium">
                            {formatDiscountValue(discount)}
                          </span>
                          {discount.code && (
                            <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs font-medium">
                              Code: {discount.code}
                            </span>
                          )}
                        </div>
                        <p className="text-gray-600 text-sm mb-2">
                          {discount.description}
                        </p>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => toggleActive(discount.id)}
                          className="bg-green-100 hover:bg-green-200 text-green-800 px-3 py-1 rounded text-sm transition-colors"
                        >
                          Activate
                        </button>
                        <button
                          onClick={() => openModal(discount)}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded text-sm transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deleteDiscount(discount.id)}
                          className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">
                  {editingDiscount ? 'Edit Discount' : 'Add New Discount'}
                </h2>
              </div>

              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="p-6 space-y-6"
              >
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discount Name *
                    </label>
                    <input
                      {...form.register('name')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      placeholder="e.g., First Time Customer"
                    />
                    {form.formState.errors.name && (
                      <p className="text-red-600 text-sm mt-1">
                        {form.formState.errors.name.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discount Type *
                    </label>
                    <select
                      {...form.register('type')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      <option value="percentage">Percentage</option>
                      <option value="fixed_amount">Fixed Amount</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discount Value *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...form.register('value', { valueAsNumber: true })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      placeholder={
                        form.watch('type') === 'percentage' ? '10' : '25'
                      }
                    />
                    <p className="text-gray-500 text-sm mt-1">
                      {form.watch('type') === 'percentage'
                        ? 'Enter percentage (e.g., 10 for 10%)'
                        : 'Enter dollar amount (e.g., 25 for $25)'}
                    </p>
                    {form.formState.errors.value && (
                      <p className="text-red-600 text-sm mt-1">
                        {form.formState.errors.value.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Promo Code
                    </label>
                    <input
                      {...form.register('code')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      placeholder="e.g., HOLIDAY25"
                    />
                    <p className="text-gray-500 text-sm mt-1">
                      Optional promotional code
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <textarea
                    {...form.register('description')}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    placeholder="Describe the discount and any conditions"
                  />
                  {form.formState.errors.description && (
                    <p className="text-red-600 text-sm mt-1">
                      {form.formState.errors.description.message}
                    </p>
                  )}
                </div>

                {/* Additional Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Order Amount
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...form.register('minOrderAmount', {
                        valueAsNumber: true,
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      placeholder="0"
                    />
                  </div>

                  {form.watch('type') === 'percentage' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Maximum Discount Amount
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        {...form.register('maxDiscount', {
                          valueAsNumber: true,
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                        placeholder="0"
                      />
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Valid From
                    </label>
                    <input
                      type="date"
                      {...form.register('validFrom')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Valid To
                    </label>
                    <input
                      type="date"
                      {...form.register('validTo')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="isActive"
                    {...form.register('isActive')}
                    className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="isActive"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Active (discount can be used immediately)
                  </label>
                </div>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors disabled:opacity-50"
                  >
                    {loading
                      ? 'Saving...'
                      : editingDiscount
                        ? 'Update Discount'
                        : 'Create Discount'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
