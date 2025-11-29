/**
 * LabelPicker Component
 * Dropdown to select/create labels for emails
 */

import { Check, Plus, Tag } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/Toast';
import { labelService } from '@/services/email-api';
import type { Label, LabelCreate } from '@/types/email';

import { LabelBadge } from './LabelBadge';

interface LabelPickerProps {
  selectedLabels: string[]; // Label slugs
  onToggleLabel: (labelSlug: string) => void;
  onClose: () => void;
  isOpen: boolean;
}

export function LabelPicker({
  selectedLabels,
  onToggleLabel,
  onClose,
  isOpen,
}: LabelPickerProps) {
  const [labels, setLabels] = useState<Label[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const toast = useToast();

  // Load labels with useCallback to fix dependency
  const loadLabels = useCallback(async () => {
    setLoading(true);
    const data = await labelService.getLabels();
    setLabels(data);
    setLoading(false);
  }, []);

  // Load labels
  useEffect(() => {
    if (isOpen) {
      loadLabels();
    }
  }, [isOpen, loadLabels]);

  const handleCreateLabel = async (newLabel: LabelCreate) => {
    const created = await labelService.createLabel(newLabel);
    setLabels([...labels, created]);
    setShowCreateModal(false);
    toast.success('Label created successfully');
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title="Manage Labels" size="md">
        <div className="space-y-4">
          {/* Create New Label Button */}
          <Button
            onClick={() => setShowCreateModal(true)}
            variant="outline"
            className="w-full justify-start gap-2"
          >
            <Plus className="w-4 h-4" />
            Create New Label
          </Button>

          {/* Label List */}
          {loading ? (
            <div className="text-center py-8 text-gray-500">
              Loading labels...
            </div>
          ) : labels.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Tag className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p>No labels yet</p>
              <p className="text-sm">Create your first label to get started</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {labels.map(label => {
                const isSelected = selectedLabels.includes(label.slug);
                return (
                  <button
                    key={label.slug}
                    type="button"
                    onClick={() => onToggleLabel(label.slug)}
                    className={`
                      w-full flex items-center justify-between p-3 rounded-lg
                      border-2 transition-all hover:bg-gray-50
                      ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: label.color }}
                      />
                      <span className="font-medium">{label.name}</span>
                      {label.icon && (
                        <span className="text-gray-500">{label.icon}</span>
                      )}
                      {label.is_system && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                          System
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">
                        {label.email_count || 0}
                      </span>
                      {isSelected && (
                        <Check className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </Modal>

      {/* Create Label Modal */}
      {showCreateModal && (
        <CreateLabelModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateLabel}
        />
      )}
    </>
  );
}

/**
 * CreateLabelModal Component
 * Modal for creating a new label
 */

interface CreateLabelModalProps {
  onClose: () => void;
  onCreate: (label: LabelCreate) => void;
}

function CreateLabelModal({ onClose, onCreate }: CreateLabelModalProps) {
  const [name, setName] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [icon, setIcon] = useState('');

  const predefinedColors = [
    '#3B82F6', // Blue
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#F97316', // Orange
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    onCreate({
      name: name.trim(),
      color,
      icon: icon.trim() || undefined,
    });
  };

  return (
    <Modal isOpen onClose={onClose} title="Create New Label" size="sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Label Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Label Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g., VIP Customer, Urgent"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
            maxLength={50}
          />
        </div>

        {/* Color Picker */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Color
          </label>
          <div className="flex gap-2 flex-wrap">
            {predefinedColors.map(c => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                className={`
                  w-8 h-8 rounded-full border-2 transition-all
                  ${color === c ? 'border-gray-800 scale-110' : 'border-gray-300'}
                `}
                style={{ backgroundColor: c }}
                aria-label={`Select color ${c}`}
              />
            ))}
          </div>
          <input
            type="color"
            value={color}
            onChange={e => setColor(e.target.value)}
            className="mt-2 w-full h-10 rounded cursor-pointer"
          />
        </div>

        {/* Icon (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Icon (Optional Emoji)
          </label>
          <input
            type="text"
            value={icon}
            onChange={e => setIcon(e.target.value)}
            placeholder="e.g., ⭐ 🔥 💎"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            maxLength={2}
          />
        </div>

        {/* Preview */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preview
          </label>
          <LabelBadge
            label={{
              id: '0',
              name: name || 'Label Name',
              slug: '',
              color,
              icon: icon || undefined,
              is_system: false,
              is_archived: false,
              email_count: 0,
              sort_order: 0,
              created_at: '',
              updated_at: '',
            }}
            size="md"
          />
        </div>

        {/* Actions */}
        <div className="flex gap-2 justify-end pt-4">
          <Button type="button" onClick={onClose} variant="outline">
            Cancel
          </Button>
          <Button type="submit" disabled={!name.trim()}>
            Create Label
          </Button>
        </div>
      </form>
    </Modal>
  );
}
