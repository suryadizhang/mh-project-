/**
 * Type definitions for data structures used across the customer app.
 * This file ensures TypeScript strict mode compliance by eliminating `any` types.
 */

// ============================================================================
// Home Page Types
// ============================================================================

export interface HomeFeature {
  icon: string;
  title: string;
  description: string;
}

export interface HomeService {
  icon: string;
  title: string;
  description: string;
}

export interface CTAButton {
  href: string;
  text: string;
  primary: boolean;
}

// ============================================================================
// Menu Page Types
// ============================================================================

export interface MenuHeroFeature {
  icon: string;
  title: string;
  subtitle: string;
}

export interface ProteinItem {
  name: string;
  description: string;
}

export interface ProteinCategory {
  name: string;
  items: ProteinItem[];
}

export interface PricingTier {
  id: string;
  name: string;
  price: string;
  description: string;
  minGuests: number;
  popular?: boolean;
  features: string[];
}

// ============================================================================
// Google Places API Types
// ============================================================================

export interface GoogleAddressComponent {
  long_name: string;
  short_name: string;
  types: string[];
}

// ============================================================================
// Booking API Types
// ============================================================================

export interface TimeSlot {
  time: string;
  available: number;
  maxCapacity: number;
  booked: number;
  isAvailable: boolean;
}
