'use client';

import {
  AlertCircle,
  Calendar,
  LucideIcon,
  Mail,
  MessageSquare,
  Package,
  Search,
  Star,
  TrendingUp,
  Users,
} from 'lucide-react';
import React from 'react';

export type EmptyStateVariant =
  | 'no-data'
  | 'no-results'
  | 'error'
  | 'bookings'
  | 'customers'
  | 'leads'
  | 'reviews'
  | 'newsletter'
  | 'messages'
  | 'analytics';

export interface EmptyStateAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  icon?: LucideIcon;
}

export interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  description?: string;
  icon?: LucideIcon;
  actions?: EmptyStateAction[];
  className?: string;
}

const variantConfig: Record<
  EmptyStateVariant,
  {
    icon: LucideIcon;
    title: string;
    description: string;
    iconColor: string;
    iconBg: string;
  }
> = {
  'no-data': {
    icon: Package,
    title: 'No data yet',
    description: 'Get started by adding your first item.',
    iconColor: 'text-gray-400',
    iconBg: 'bg-gray-100',
  },
  'no-results': {
    icon: Search,
    title: 'No results found',
    description: 'Try adjusting your search or filters to find what you need.',
    iconColor: 'text-blue-400',
    iconBg: 'bg-blue-100',
  },
  error: {
    icon: AlertCircle,
    title: 'Something went wrong',
    description: 'We encountered an error loading this data. Please try again.',
    iconColor: 'text-red-400',
    iconBg: 'bg-red-100',
  },
  bookings: {
    icon: Calendar,
    title: 'No bookings yet',
    description: 'When customers make bookings, they will appear here.',
    iconColor: 'text-purple-400',
    iconBg: 'bg-purple-100',
  },
  customers: {
    icon: Users,
    title: 'No customers yet',
    description:
      'Your customer list will appear here once you start getting bookings.',
    iconColor: 'text-blue-400',
    iconBg: 'bg-blue-100',
  },
  leads: {
    icon: TrendingUp,
    title: 'No leads yet',
    description: 'Leads from your website and campaigns will show up here.',
    iconColor: 'text-green-400',
    iconBg: 'bg-green-100',
  },
  reviews: {
    icon: Star,
    title: 'No reviews yet',
    description: 'Customer reviews and feedback will be displayed here.',
    iconColor: 'text-yellow-400',
    iconBg: 'bg-yellow-100',
  },
  newsletter: {
    icon: Mail,
    title: 'No subscribers yet',
    description:
      'Start building your email list to send newsletters and campaigns.',
    iconColor: 'text-indigo-400',
    iconBg: 'bg-indigo-100',
  },
  messages: {
    icon: MessageSquare,
    title: 'No messages',
    description: 'Your conversations and messages will appear here.',
    iconColor: 'text-cyan-400',
    iconBg: 'bg-cyan-100',
  },
  analytics: {
    icon: TrendingUp,
    title: 'No analytics data',
    description:
      'Analytics and insights will be available once you have activity.',
    iconColor: 'text-green-400',
    iconBg: 'bg-green-100',
  },
};

export function EmptyState({
  variant = 'no-data',
  title,
  description,
  icon,
  actions = [],
  className = '',
}: EmptyStateProps) {
  const config = variantConfig[variant];
  const Icon = icon || config.icon;
  const displayTitle = title || config.title;
  const displayDescription = description || config.description;

  return (
    <div
      className={`flex flex-col items-center justify-center py-12 px-4 text-center ${className}`}
    >
      <div className={`rounded-full ${config.iconBg} p-6 mb-4`}>
        <Icon className={`h-12 w-12 ${config.iconColor}`} />
      </div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {displayTitle}
      </h3>
      <p className="text-sm text-gray-500 max-w-md mb-6">
        {displayDescription}
      </p>

      {actions.length > 0 && (
        <div className="flex flex-wrap gap-3 justify-center">
          {actions.map((action, index) => {
            const ActionIcon = action.icon;
            const isPrimary = action.variant !== 'secondary';

            return (
              <button
                key={index}
                onClick={action.onClick}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  isPrimary
                    ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-500'
                }`}
              >
                {ActionIcon && <ActionIcon className="h-4 w-4" />}
                {action.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function EmptyStateCard(props: EmptyStateProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <EmptyState {...props} className="py-16" />
    </div>
  );
}

export function TableEmptyState(props: EmptyStateProps) {
  return (
    <tr>
      <td colSpan={100}>
        <EmptyState {...props} className="py-12" />
      </td>
    </tr>
  );
}
