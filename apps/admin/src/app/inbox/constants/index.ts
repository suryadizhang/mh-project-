/**
 * Inbox Constants Module
 * ======================
 * All constant data for the unified inbox system.
 *
 * SSoT: These are UI constants, not business values.
 * Business values (like pricing) come from usePricing() hook.
 */

import { Facebook, Instagram, MessageCircle, Mail } from 'lucide-react';
import type {
  ChannelType,
  ChannelConfig,
  ReplyTemplate,
  QuickReply,
} from '../types';

// ============================================================================
// Channel Configuration
// ============================================================================

export const CHANNELS = {
  ALL: 'all',
  FACEBOOK: 'facebook',
  INSTAGRAM: 'instagram',
  SMS: 'sms',
  EMAIL: 'email',
} as const;

export const CHANNEL_CONFIG: Record<
  Exclude<ChannelType, 'all'>,
  ChannelConfig
> = {
  facebook: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    icon: Facebook,
    label: 'Facebook',
    borderColor: 'border-blue-600',
  },
  instagram: {
    bg: 'bg-pink-50',
    text: 'text-pink-600',
    icon: Instagram,
    label: 'Instagram',
    borderColor: 'border-pink-600',
  },
  sms: {
    bg: 'bg-green-50',
    text: 'text-green-600',
    icon: MessageCircle,
    label: 'SMS',
    borderColor: 'border-green-600',
  },
  email: {
    bg: 'bg-purple-50',
    text: 'text-purple-600',
    icon: Mail,
    label: 'Email',
    borderColor: 'border-purple-600',
  },
};

// ============================================================================
// Email Signature
// ============================================================================

export const EMAIL_SIGNATURE = `

---
Best regards,
My Hibachi Chef Team

📧 cs@myhibachichef.com
📞 (916) 740-8768
🌐 www.myhibachichef.com`;

// ============================================================================
// Reply Templates (for emails)
// ============================================================================

export const REPLY_TEMPLATES: ReplyTemplate[] = [
  {
    id: 'thank_you',
    name: 'Thank You',
    text: `Hi {{customer_name}},

Thank you for reaching out to My Hibachi Chef! We truly appreciate your interest in our services.

{{response_content}}

If you have any other questions, please don't hesitate to ask. We're here to make your hibachi experience unforgettable!${EMAIL_SIGNATURE}`,
  },
  {
    id: 'booking_confirmed',
    name: 'Booking Confirmed',
    text: `Hi {{customer_name}},

Great news! Your hibachi party booking has been confirmed! 🎉

Here are your booking details:
- Date: {{event_date}}
- Time: {{event_time}}
- Location: {{event_location}}
- Guest Count: {{guest_count}}

Your chef will arrive approximately 30 minutes before your event time to set up.

Please make sure you have:
✅ A flat, stable surface for the grill
✅ Access to an electrical outlet
✅ Good ventilation (outdoor is preferred)

We'll send you a reminder 24 hours before your event.${EMAIL_SIGNATURE}`,
  },
  {
    id: 'apology',
    name: 'Apology',
    text: `Hi {{customer_name}},

I want to sincerely apologize for {{issue_description}}.

We take customer satisfaction very seriously, and we're truly sorry this happened. Here's what we're doing to make it right:

{{resolution}}

Your experience matters to us, and we hope to have the opportunity to serve you again.${EMAIL_SIGNATURE}`,
  },
  {
    id: 'refund_processed',
    name: 'Refund Processed',
    text: `Hi {{customer_name}},

We wanted to confirm that your refund of \${{refund_amount}} has been processed.

Transaction Details:
- Amount: \${{refund_amount}}
- Processing Date: {{processing_date}}
- Expected Return: 3-5 business days

Please note that the exact timing depends on your bank or credit card company.

If you don't see the refund after 5 business days, please contact us and we'll help investigate.${EMAIL_SIGNATURE}`,
  },
  {
    id: 'more_info',
    name: 'Need More Info',
    text: `Hi {{customer_name}},

Thank you for contacting us! To better assist you with {{inquiry_topic}}, we need a bit more information:

{{questions}}

Once we have these details, we'll be able to provide you with a complete answer.

Looking forward to hearing from you!${EMAIL_SIGNATURE}`,
  },
];

// ============================================================================
// Quick Replies (for SMS and social channels)
// ============================================================================

export const QUICK_REPLIES: Record<string, QuickReply[]> = {
  general: [
    {
      id: 'greeting',
      label: '👋 Greeting',
      text: 'Hi! Thanks for reaching out to My Hibachi Chef. How can I help you today?',
    },
    {
      id: 'availability',
      label: '📅 Check Availability',
      text: "I'd be happy to check our availability for you! What date and time were you thinking?",
    },
    {
      id: 'pricing',
      label: '💰 Pricing Info',
      text: "Great question! Our pricing starts at $55 per adult and $30 per child (6-12). Kids 5 and under eat free! There's a $550 minimum for bookings. Would you like a quote for your event?",
    },
    {
      id: 'callback',
      label: '📞 Request Callback',
      text: "I'd be happy to have someone call you back. What's the best number to reach you, and what time works best?",
    },
    {
      id: 'thanks',
      label: '🙏 Thank You',
      text: "Thank you for choosing My Hibachi Chef! We're looking forward to making your event special. 🔥🍽️",
    },
  ],
  sms: [
    {
      id: 'sms_greeting',
      label: '👋 SMS Greeting',
      text: 'Hi! This is My Hibachi Chef. Thanks for texting! How can we help?',
    },
    {
      id: 'sms_booking',
      label: '📅 Book Now',
      text: 'Ready to book? Visit myhibachichef.com/book or reply with your preferred date!',
    },
    {
      id: 'sms_confirm',
      label: '✅ Confirm Receipt',
      text: "Got it! We'll follow up shortly. 👍",
    },
  ],
  facebook: [
    {
      id: 'fb_greeting',
      label: '👋 FB Greeting',
      text: 'Hi there! 👋 Thanks for reaching out on Facebook. How can My Hibachi Chef help make your next event amazing?',
    },
  ],
  instagram: [
    {
      id: 'ig_greeting',
      label: '👋 IG Greeting',
      text: 'Hey! 🔥 Thanks for DMing us! How can we help you with your hibachi party?',
    },
  ],
};

// ============================================================================
// Default Label Colors
// ============================================================================

export const LABEL_COLORS = [
  { name: 'Red', value: '#ef4444' },
  { name: 'Orange', value: '#f97316' },
  { name: 'Yellow', value: '#eab308' },
  { name: 'Green', value: '#22c55e' },
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Purple', value: '#a855f7' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Gray', value: '#6b7280' },
];

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

export const KEYBOARD_SHORTCUTS = {
  NEXT_THREAD: 'j',
  PREV_THREAD: 'k',
  REPLY: 'r',
  ARCHIVE: 'e',
  STAR: 's',
  MARK_UNREAD: 'u',
  SEARCH: '/',
  SELECT_ALL: 'ctrl+a',
  DELETE: 'Delete',
} as const;

// ============================================================================
// SMS Character Limits
// ============================================================================

export const SMS_CHAR_LIMIT = 160;
export const SMS_CONCAT_LIMIT = 1600; // 10 concatenated messages

// ============================================================================
// Auto-save Configuration
// ============================================================================

export const DRAFT_AUTOSAVE_DELAY_MS = 3000; // 3 seconds
export const DRAFT_STORAGE_PREFIX = 'inbox-draft-';

// ============================================================================
// API Endpoints
// ============================================================================

export const INBOX_API = {
  THREADS: '/api/v1/inbox/threads',
  SEND_MESSAGE: '/api/v1/inbox/messages',
  AI_REPLY: '/api/v1/inbox/ai-reply',
  ASSIGN: '/api/v1/inbox/assign',
  CONVERT_TO_LEAD: '/api/leads/social-threads',
  EMAIL_THREADS: '/api/admin/emails',
  LABELS: '/api/admin/labels',
} as const;
