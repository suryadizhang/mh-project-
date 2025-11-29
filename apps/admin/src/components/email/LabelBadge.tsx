/**
 * LabelBadge Component
 * Displays a colored label badge for emails
 */

import { Tag, X } from 'lucide-react';

import type { Label } from '@/types/email';

interface LabelBadgeProps {
  label: Label;
  onRemove?: () => void;
  size?: 'sm' | 'md';
  className?: string;
}

export function LabelBadge({
  label,
  onRemove,
  size = 'sm',
  className = '',
}: LabelBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        ${sizeClasses[size]}
        ${className}
      `}
      style={{
        backgroundColor: `${label.color}20`,
        color: label.color,
        borderColor: label.color,
        borderWidth: '1px',
      }}
    >
      {label.icon && <span className="text-xs">{label.icon}</span>}
      <span>{label.name}</span>
      {onRemove && (
        <button
          type="button"
          onClick={e => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-1 hover:opacity-70 transition-opacity"
          aria-label={`Remove ${label.name} label`}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </span>
  );
}

/**
 * LabelList Component
 * Displays multiple label badges
 */

interface LabelListProps {
  labels: Label[];
  onRemove?: (labelSlug: string) => void;
  maxVisible?: number;
  size?: 'sm' | 'md';
  className?: string;
}

export function LabelList({
  labels,
  onRemove,
  maxVisible = 3,
  size = 'sm',
  className = '',
}: LabelListProps) {
  const visibleLabels = labels.slice(0, maxVisible);
  const remainingCount = labels.length - maxVisible;

  if (labels.length === 0) return null;

  return (
    <div className={`flex items-center gap-1 flex-wrap ${className}`}>
      {visibleLabels.map(label => (
        <LabelBadge
          key={label.slug}
          label={label}
          size={size}
          onRemove={onRemove ? () => onRemove(label.slug) : undefined}
        />
      ))}
      {remainingCount > 0 && (
        <span
          className={`
            inline-flex items-center gap-1 rounded-full font-medium
            text-gray-600 bg-gray-100 border border-gray-300
            ${size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1'}
          `}
        >
          <Tag className="w-3 h-3" />+{remainingCount}
        </span>
      )}
    </div>
  );
}
