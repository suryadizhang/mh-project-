/**
 * Empty State Component
 * Displays when no data is available
 */

import { LucideIcon } from 'lucide-react';
import { Button } from './button';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
}: EmptyStateProps) {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-12">
      <div className="text-center max-w-md mx-auto">
        {Icon && <Icon className="w-12 h-12 text-gray-400 mx-auto mb-4" />}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        {description && (
          <p className="text-gray-600 mb-6">{description}</p>
        )}
        {(actionLabel || secondaryActionLabel) && (
          <div className="flex gap-3 justify-center">
            {actionLabel && onAction && (
              <Button onClick={onAction}>{actionLabel}</Button>
            )}
            {secondaryActionLabel && onSecondaryAction && (
              <Button variant="outline" onClick={onSecondaryAction}>
                {secondaryActionLabel}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
