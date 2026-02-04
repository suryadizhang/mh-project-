/**
 * Comprehensive Mock Data for E2E Testing
 *
 * This file contains all mock data for testing:
 * - Customers
 * - Bookings
 * - Quotes
 * - Chefs
 * - Stations
 * - Slots/Scheduling
 * - Agreements
 * - Admin Users
 */

// =============================================================================
// Customer Mock Data
// =============================================================================

export function generateUniqueEmail(prefix = 'test'): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 6);
  return `${prefix}-${timestamp}-${random}@e2etest.myhibachi.com`;
}

export function generateUniquePhone(): string {
  const random = Math.floor(Math.random() * 9000000) + 1000000;
  return `555-${random.toString().substring(0, 3)}-${random.toString().substring(3, 7)}`;
}

export const mockCustomers = {
  basic: {
    first_name: 'John',
    last_name: 'Doe',
    email: generateUniqueEmail('john'),
    phone: '555-123-4567',
    address: '123 Main Street',
    city: 'Los Angeles',
    state: 'CA',
    zip_code: '90001',
  },
  premium: {
    first_name: 'Jane',
    last_name: 'Smith',
    email: generateUniqueEmail('jane'),
    phone: '555-987-6543',
    address: '456 Beverly Hills Drive',
    city: 'Beverly Hills',
    state: 'CA',
    zip_code: '90210',
  },
  corporate: {
    first_name: 'Corporate',
    last_name: 'Client',
    email: generateUniqueEmail('corp'),
    phone: '555-555-5555',
    address: '789 Business Park',
    city: 'Irvine',
    state: 'CA',
    zip_code: '92614',
    company_name: 'Acme Corporation',
  },
};

// =============================================================================
// Quote Mock Data (for Quote → Booking flow)
// =============================================================================

export function getTestDate(daysFromNow: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString().split('T')[0]; // YYYY-MM-DD
}

export function getTestTime(hour: number, minute: number = 0): string {
  return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
}

export const mockQuotes = {
  smallParty: {
    adult_count: 8,
    child_count: 2,
    event_date: getTestDate(30), // 30 days from now
    event_time: getTestTime(18, 0), // 6:00 PM
    venue_address: '123 Test Street, Los Angeles, CA 90001',
    venue_lat: 34.0522,
    venue_lng: -118.2437,
    upgrades: [],
    add_ons: [],
  },
  mediumParty: {
    adult_count: 15,
    child_count: 5,
    event_date: getTestDate(45), // 45 days from now
    event_time: getTestTime(17, 30), // 5:30 PM
    venue_address: '456 Party Ave, Beverly Hills, CA 90210',
    venue_lat: 34.0736,
    venue_lng: -118.4004,
    upgrades: ['salmon', 'scallops'],
    add_ons: ['yakisoba', 'gyoza'],
  },
  largeParty: {
    adult_count: 30,
    child_count: 10,
    event_date: getTestDate(60), // 60 days from now
    event_time: getTestTime(18, 30), // 6:30 PM
    venue_address: '789 Grand Blvd, Malibu, CA 90265',
    venue_lat: 34.0259,
    venue_lng: -118.7798,
    upgrades: ['filet', 'lobster'],
    add_ons: ['yakisoba', 'gyoza', 'edamame'],
  },
  corporateEvent: {
    adult_count: 50,
    child_count: 0,
    event_date: getTestDate(90), // 90 days from now
    event_time: getTestTime(12, 0), // 12:00 PM (lunch)
    venue_address: '1000 Corporate Center, Irvine, CA 92614',
    venue_lat: 33.6846,
    venue_lng: -117.8265,
    upgrades: ['filet', 'lobster', 'salmon'],
    add_ons: ['yakisoba', 'gyoza', 'edamame', 'shrimp_appetizer'],
    special_instructions: 'Corporate event - please set up by 11:30 AM',
  },
};

// =============================================================================
// Booking Mock Data
// =============================================================================

export type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export interface MockBooking {
  customer: typeof mockCustomers.basic;
  quote: typeof mockQuotes.smallParty;
  status: BookingStatus;
  special_requests?: string;
  dietary_restrictions?: string[];
}

export const mockBookings: Record<string, MockBooking> = {
  pendingBooking: {
    customer: { ...mockCustomers.basic, email: generateUniqueEmail('pending') },
    quote: mockQuotes.smallParty,
    status: 'pending',
  },
  confirmedBooking: {
    customer: {
      ...mockCustomers.premium,
      email: generateUniqueEmail('confirmed'),
    },
    quote: mockQuotes.mediumParty,
    status: 'confirmed',
    special_requests: 'Please arrive 30 minutes early',
  },
  bookingWithDietaryRestrictions: {
    customer: { ...mockCustomers.basic, email: generateUniqueEmail('dietary') },
    quote: mockQuotes.smallParty,
    status: 'pending',
    dietary_restrictions: ['vegetarian', 'gluten-free'],
  },
  corporateBooking: {
    customer: {
      ...mockCustomers.corporate,
      email: generateUniqueEmail('corp'),
    },
    quote: mockQuotes.corporateEvent,
    status: 'confirmed',
    special_requests: 'Corporate event - need invoice for accounting',
  },
};

// =============================================================================
// Chef Mock Data
// =============================================================================

export const mockChefs = {
  chef1: {
    first_name: 'Taro',
    last_name: 'Yamamoto',
    email: 'taro@myhibachi.test',
    phone: '555-CHEF-001',
    station_id: 'station-la-central',
    skills: ['hibachi', 'sushi', 'teppanyaki'],
    rating: 4.9,
    experience_years: 10,
    max_guests: 30,
    travel_radius_miles: 50,
  },
  chef2: {
    first_name: 'Sakura',
    last_name: 'Tanaka',
    email: 'sakura@myhibachi.test',
    phone: '555-CHEF-002',
    station_id: 'station-la-central',
    skills: ['hibachi', 'vegetarian_specialist'],
    rating: 4.8,
    experience_years: 7,
    max_guests: 25,
    travel_radius_miles: 40,
  },
  chef3: {
    first_name: 'Kenji',
    last_name: 'Nakamura',
    email: 'kenji@myhibachi.test',
    phone: '555-CHEF-003',
    station_id: 'station-oc',
    skills: ['hibachi', 'large_events'],
    rating: 4.7,
    experience_years: 12,
    max_guests: 50,
    travel_radius_miles: 60,
  },
};

// =============================================================================
// Station Mock Data
// =============================================================================

export const mockStations = {
  laCentral: {
    id: 'station-la-central',
    name: 'Los Angeles Central',
    code: 'LA-CENTRAL',
    address: '100 Main Street, Los Angeles, CA 90001',
    lat: 34.0522,
    lng: -118.2437,
    service_radius_miles: 30,
    is_active: true,
  },
  orangeCounty: {
    id: 'station-oc',
    name: 'Orange County',
    code: 'OC-MAIN',
    address: '200 Beach Blvd, Huntington Beach, CA 92648',
    lat: 33.6603,
    lng: -117.9992,
    service_radius_miles: 25,
    is_active: true,
  },
  sanDiego: {
    id: 'station-sd',
    name: 'San Diego',
    code: 'SD-MAIN',
    address: '300 Harbor Drive, San Diego, CA 92101',
    lat: 32.7157,
    lng: -117.1611,
    service_radius_miles: 35,
    is_active: true,
  },
};

// =============================================================================
// Slot/Scheduling Mock Data
// =============================================================================

export const mockTimeSlots = {
  morning: [
    { time: '10:00', label: 'Late Morning', peak: false },
    { time: '11:00', label: 'Brunch', peak: false },
  ],
  afternoon: [
    { time: '12:00', label: 'Lunch', peak: true },
    { time: '13:00', label: 'Early Afternoon', peak: false },
    { time: '14:00', label: 'Afternoon', peak: false },
    { time: '15:00', label: 'Late Afternoon', peak: false },
  ],
  evening: [
    { time: '16:00', label: 'Early Evening', peak: false },
    { time: '17:00', label: 'Dinner Prep', peak: true },
    { time: '17:30', label: 'Dinner', peak: true },
    { time: '18:00', label: 'Prime Dinner', peak: true },
    { time: '18:30', label: 'Prime Dinner', peak: true },
    { time: '19:00', label: 'Dinner', peak: true },
    { time: '19:30', label: 'Late Dinner', peak: false },
    { time: '20:00', label: 'Late Dinner', peak: false },
  ],
};

export const mockAvailabilityRequest = {
  event_date: getTestDate(30),
  event_time: '18:00',
  guest_count: 20,
  venue_lat: 34.0522,
  venue_lng: -118.2437,
  preferred_chef_id: null,
};

// =============================================================================
// Agreement Mock Data
// =============================================================================

export const mockAgreements = {
  liabilityWaiver: {
    agreement_type: 'liability_waiver',
    version: '1.0',
    title: 'Liability Waiver and Release Agreement',
    requires_signature: true,
  },
  allergenDisclosure: {
    agreement_type: 'allergen_disclosure',
    version: '1.0',
    title: 'Allergen Acknowledgment and Disclosure',
    requires_signature: true,
  },
};

export const mockSignatureBase64 =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

// =============================================================================
// Admin/User Mock Data
// =============================================================================

export type UserRole =
  | 'super_admin'
  | 'admin'
  | 'station_manager'
  | 'customer_support'
  | 'chef';

export interface MockAdminUser {
  email: string;
  password: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  station_ids?: string[];
}

// Note: These are TEST accounts only - real credentials come from env vars
export const mockAdminUsers: Record<string, Omit<MockAdminUser, 'password'>> = {
  superAdmin: {
    email: process.env.TEST_ADMIN_EMAIL || '',
    first_name: 'Super',
    last_name: 'Admin',
    role: 'super_admin',
  },
  stationManager: {
    email: generateUniqueEmail('manager'),
    first_name: 'Station',
    last_name: 'Manager',
    role: 'station_manager',
    station_ids: ['station-la-central'],
  },
  customerSupport: {
    email: generateUniqueEmail('support'),
    first_name: 'Support',
    last_name: 'Agent',
    role: 'customer_support',
  },
  chefAccount: {
    email: generateUniqueEmail('chef'),
    first_name: 'Test',
    last_name: 'Chef',
    role: 'chef',
    station_ids: ['station-la-central'],
  },
};

// =============================================================================
// Pricing Mock Data (for validation)
// =============================================================================

export const mockPricing = {
  // These should match the dynamic variables in the database
  adult_price: 5500, // $55.00 in cents
  child_price: 3000, // $30.00 in cents
  child_free_under_age: 5,
  party_minimum: 55000, // $550.00 in cents
  deposit_amount: 10000, // $100.00 in cents
  free_miles: 30,
  per_mile_rate: 200, // $2.00 in cents
  upgrades: {
    salmon: 500, // $5.00
    scallops: 500, // $5.00
    filet: 500, // $5.00
    lobster: 1500, // $15.00
  },
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Generate a booking ID in the format MH-YYYYMMDD-XXXX
 */
export function generateBookingId(): string {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
  const random = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `MH-${dateStr}-${random}`;
}

/**
 * Calculate expected quote total
 */
export function calculateQuoteTotal(quote: typeof mockQuotes.smallParty): {
  subtotal: number;
  travel_fee: number;
  tax: number;
  total: number;
  deposit: number;
} {
  // Base pricing
  const adultTotal = quote.adult_count * mockPricing.adult_price;
  const childTotal = quote.child_count * mockPricing.child_price;
  let subtotal = adultTotal + childTotal;

  // Ensure minimum
  subtotal = Math.max(subtotal, mockPricing.party_minimum);

  // Add upgrades (per person)
  const totalGuests = quote.adult_count + quote.child_count;
  if (quote.upgrades && quote.upgrades.length > 0) {
    for (const upgrade of quote.upgrades) {
      const upgradePrice =
        mockPricing.upgrades[upgrade as keyof typeof mockPricing.upgrades];
      if (upgradePrice) {
        subtotal += upgradePrice * totalGuests;
      }
    }
  }

  // Travel fee (simplified - assume 10 miles for testing)
  const travel_fee = 0; // Within free miles

  // Tax (8.25% for CA)
  const tax = Math.round(subtotal * 0.0825);

  const total = subtotal + travel_fee + tax;
  const deposit = mockPricing.deposit_amount;

  return { subtotal, travel_fee, tax, total, deposit };
}

/**
 * Wait helper
 */
export function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Generate random alphanumeric string
 */
export function randomString(length: number): string {
  return Math.random()
    .toString(36)
    .substring(2, 2 + length);
}
