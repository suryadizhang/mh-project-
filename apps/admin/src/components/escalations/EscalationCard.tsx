'use client';

import {
  AlertCircle,
  CheckCircle,
  Clock,
  Mail,
  MessageSquare,
  Phone,
  User,
  XCircle,
} from 'lucide-react';
import Link from 'next/link';

import { MessageReadReceipt } from './MessageReadReceipt';

interface Escalation {
  id: string;
  conversation_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  method: 'phone' | 'email' | 'preferred_method';
  status:
    | 'pending'
    | 'assigned'
    | 'in_progress'
    | 'waiting_customer'
    | 'resolved'
    | 'closed'
    | 'error';
  assigned_to_id?: string;
  assigned_to?: {
    id: string;
    full_name: string;
    email: string;
  };
  sms_sent: boolean;
  sms_status?: 'sending' | 'sent' | 'delivered' | 'read' | 'failed';
  last_sms_timestamp?: string;
  call_initiated: boolean;
  created_at: string;
  updated_at: string;
  escalated_at?: string;
}

interface EscalationCardProps {
  escalation: Escalation;
}

export function EscalationCard({ escalation }: EscalationCardProps) {
  // Priority badge styling
  const getPriorityStyle = (priority: Escalation['priority']) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  // Status badge styling
  const getStatusStyle = (status: Escalation['status']) => {
    switch (status) {
      case 'pending':
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          icon: Clock,
        };
      case 'assigned':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
          icon: User,
        };
      case 'in_progress':
        return {
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
          icon: MessageSquare,
        };
      case 'waiting_customer':
        return {
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          border: 'border-yellow-200',
          icon: Clock,
        };
      case 'resolved':
        return {
          bg: 'bg-green-100',
          text: 'text-green-800',
          border: 'border-green-200',
          icon: CheckCircle,
        };
      case 'closed':
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-600',
          border: 'border-gray-200',
          icon: XCircle,
        };
      case 'error':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          border: 'border-red-200',
          icon: AlertCircle,
        };
    }
  };

  // Format time ago
  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  // Get contact method icon
  const getMethodIcon = (method: Escalation['method']) => {
    switch (method) {
      case 'phone':
        return <Phone size={16} />;
      case 'email':
        return <Mail size={16} />;
      case 'preferred_method':
        return <MessageSquare size={16} />;
    }
  };

  const statusStyle = getStatusStyle(escalation.status);
  const StatusIcon = statusStyle.icon;

  return (
    <Link
      href={`/escalations/${escalation.id}`}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md hover:border-orange-300 transition-all"
    >
      <div className="flex items-start justify-between">
        {/* Left Side - Customer Info */}
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {escalation.customer_name}
            </h3>

            {/* Priority Badge */}
            <span
              className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityStyle(escalation.priority)}`}
            >
              {escalation.priority.toUpperCase()}
            </span>

            {/* Status Badge */}
            <span
              className={`flex items-center space-x-1 px-2 py-1 text-xs font-medium rounded-full border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}
            >
              <StatusIcon size={12} />
              <span>{escalation.status.replace('_', ' ')}</span>
            </span>

            {/* Method Icon */}
            <span
              className="text-gray-500"
              title={`Preferred: ${escalation.method}`}
            >
              {getMethodIcon(escalation.method)}
            </span>
          </div>

          <p className="text-gray-700 mb-3 line-clamp-2">
            {escalation.reason}
          </p>

          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Phone size={14} />
              <span>{escalation.customer_phone}</span>
            </div>
            {escalation.customer_email && (
              <div className="flex items-center space-x-1">
                <Mail size={14} />
                <span>{escalation.customer_email}</span>
              </div>
            )}
            {escalation.assigned_to && (
              <div className="flex items-center space-x-1">
                <User size={14} />
                <span>Assigned to: {escalation.assigned_to.full_name}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Time & Actions */}
        <div className="flex flex-col items-end space-y-2 ml-4">
          <span className="text-sm text-gray-500">
            {getTimeAgo(escalation.created_at)}
          </span>

          <div className="flex items-center space-x-2">
            {escalation.sms_sent && (
              <span className="flex items-center space-x-1 px-2 py-1 bg-green-50 text-green-700 rounded-full text-xs">
                <MessageSquare size={12} />
                {escalation.sms_status ? (
                  <MessageReadReceipt
                    status={escalation.sms_status}
                    timestamp={escalation.last_sms_timestamp}
                    size="sm"
                    showLabel={false}
                  />
                ) : (
                  <span>SMS Sent</span>
                )}
              </span>
            )}
            {escalation.call_initiated && (
              <span className="flex items-center space-x-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                <Phone size={12} />
                <span>Called</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
