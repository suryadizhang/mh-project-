/**
 * Customer Preferences Types
 * ==========================
 *
 * Types for the unified customer preferences capture system:
 * - Chef request tracking (for 10% bonus)
 * - Allergen disclosure
 *
 * These match the backend schemas in:
 * apps/backend/src/schemas/customer_preferences.py
 *
 * Database Tables:
 * - core.bookings (6 new columns from migration 022)
 * - core.common_allergens (9 standard allergens)
 *
 * API Endpoints:
 * - GET /api/v1/allergens
 * - GET /api/v1/bookings/{id}/preferences
 * - PUT /api/v1/bookings/{id}/preferences
 * - GET /api/v1/bookings/{id}/prep-allergens
 * - GET /api/v1/bookings/{id}/chef-bonus
 */

/**
 * Common allergen from the reference table
 * Uses 'code' as primary identifier (matches DB column)
 */
export interface CommonAllergen {
  code: string;
  display_name: string;
  icon: string;
}

/**
 * Chef request source options
 * Tracks HOW the customer requested a specific chef
 */
export type ChefRequestSource =
  | 'booking_form' // Customer selected on website booking form
  | 'sms' // Customer requested via SMS
  | 'phone_call' // Customer mentioned during phone call
  | 'email' // Customer requested via email
  | 'social_dm' // Customer requested via social media DM
  | 'ai_chat' // Customer mentioned to AI assistant
  | 'repeat_customer' // Auto-detected from previous bookings
  | 'admin_manual'; // Admin manually marked as requested

/**
 * Chef request info for a booking
 */
export interface ChefRequestInfo {
  chef_was_requested: boolean;
  requested_chef_id: string | null;
  requested_chef_name: string | null;
  chef_request_source: ChefRequestSource | null;
}

/**
 * Allergen info for a booking
 */
export interface AllergenInfo {
  allergen_disclosure: string | null;
  common_allergens: string[]; // Array of allergen codes
  allergen_confirmed: boolean;
}

/**
 * Full customer preferences response (combines chef request + allergens)
 */
export interface CustomerPreferences {
  booking_id: string;
  chef_request: ChefRequestInfo;
  allergens: AllergenInfo;
}

/**
 * Update request for customer preferences
 * All fields are optional - only send what you want to update
 */
export interface CustomerPreferencesUpdate {
  // Chef request fields
  chef_was_requested?: boolean;
  requested_chef_id?: string | null;
  chef_request_source?: ChefRequestSource;

  // Allergen fields
  allergen_disclosure?: string;
  common_allergens?: string[]; // Array of allergen codes
  allergen_confirmed?: boolean;
}

/**
 * Chef prep view of allergens
 * Simplified view for chef mobile app / prep checklist
 */
export interface ChefPrepAllergens {
  booking_id: string;
  has_allergens: boolean;
  common_allergens: CommonAllergen[]; // Full allergen objects with display info
  additional_disclosure: string | null;
  confirmed: boolean;
  cooking_actions: CookingAction[];
}

/**
 * Cooking action for allergen accommodation
 */
export interface CookingAction {
  allergen_code: string;
  allergen_name: string;
  action: string; // e.g., "Cook shrimp LAST on separate section of grill"
}

/**
 * Chef bonus calculation result
 */
export interface ChefBonusInfo {
  booking_id: string;
  chef_was_requested: boolean;
  requested_chef_id: string | null;
  assigned_chef_id: string | null;
  bonus_applies: boolean; // True if requested == assigned
  bonus_pct: number; // e.g., 10
  base_earnings_cents: number;
  bonus_cents: number;
  message: string;
}

/**
 * Request source display info
 */
export const CHEF_REQUEST_SOURCE_LABELS: Record<ChefRequestSource, string> = {
  booking_form: 'Booking Form',
  sms: 'SMS',
  phone_call: 'Phone Call',
  email: 'Email',
  social_dm: 'Social Media DM',
  ai_chat: 'AI Chat',
  repeat_customer: 'Repeat Customer',
  admin_manual: 'Admin Manual',
};

/**
 * Request source icons (for UI)
 */
export const CHEF_REQUEST_SOURCE_ICONS: Record<ChefRequestSource, string> = {
  booking_form: '🌐',
  sms: '💬',
  phone_call: '📞',
  email: '📧',
  social_dm: '📱',
  ai_chat: '🤖',
  repeat_customer: '🔄',
  admin_manual: '✏️',
};
