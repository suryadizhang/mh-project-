'use client';

import { CHANNELS, CHANNEL_CONFIG } from '../constants';
import type { ChannelType } from '../types';

interface ChannelTabsProps {
  activeChannel: ChannelType | 'all';
  onChannelChange: (channel: ChannelType | 'all') => void;
  counts: Record<ChannelType | 'all', number>;
}

/**
 * ChannelTabs - Channel filter tabs for unified inbox
 *
 * Displays tabs for All, Facebook, Instagram, SMS, Email
 * with badge counts showing unread messages per channel.
 */
export function ChannelTabs({
  activeChannel,
  onChannelChange,
  counts,
}: ChannelTabsProps) {
  const tabs: Array<{ key: ChannelType | 'all'; label: string }> = [
    { key: 'all', label: 'All Channels' },
    { key: CHANNELS.FACEBOOK, label: 'Facebook' },
    { key: CHANNELS.INSTAGRAM, label: 'Instagram' },
    { key: CHANNELS.SMS, label: 'SMS' },
    { key: CHANNELS.EMAIL, label: 'Email' },
  ];

  return (
    <div className="flex items-center gap-1 border-b border-gray-200 bg-white px-4">
      {tabs.map(tab => {
        const isActive = activeChannel === tab.key;
        const count = counts[tab.key] || 0;
        const config = tab.key === 'all' ? null : CHANNEL_CONFIG[tab.key];
        const Icon = config?.icon;

        return (
          <button
            key={tab.key}
            onClick={() => onChannelChange(tab.key)}
            className={`
              relative flex items-center gap-2 px-4 py-3 text-sm font-medium
              transition-colors duration-150 ease-in-out
              border-b-2 -mb-[1px]
              ${
                isActive
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
            aria-current={isActive ? 'page' : undefined}
          >
            {/* Channel icon */}
            {Icon && (
              <Icon
                className={`h-4 w-4 ${
                  isActive ? 'text-indigo-600' : 'text-gray-400'
                }`}
              />
            )}

            {/* Channel label */}
            <span>{tab.label}</span>

            {/* Unread count badge */}
            {count > 0 && (
              <span
                className={`
                  inline-flex items-center justify-center min-w-[20px] h-5 px-1.5
                  text-xs font-semibold rounded-full
                  ${
                    isActive
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-gray-100 text-gray-600'
                  }
                `}
              >
                {count > 99 ? '99+' : count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default ChannelTabs;
