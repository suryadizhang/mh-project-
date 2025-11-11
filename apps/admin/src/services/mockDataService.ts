/**
 * Mock Data Service
 *
 * Centralized service for realistic mock data across admin dashboard.
 * This allows consistent data across all pages and easy transition to real API.
 *
 * FUTURE: Replace with real API calls when database is ready
 */

import { addDays, format, subDays } from 'date-fns';

// Configuration
const MOCK_DATA_ENABLED = true; // Set to false when real API is ready

// ============================================================================
// Types
// ============================================================================

export interface MockBooking {
  id: string;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  eventDate: string;
  eventTime: string;
  guestCount: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  createdAt: string;
  venueAddress: string;
  billingAddress: string;
  totalAmount: number;
  depositPaid: boolean;
  specialRequests?: string;
  stationId?: string;
}

export interface MockAnalytics {
  overview: {
    totalRevenue: number;
    totalBookings: number;
    totalCustomers: number;
    totalLeads: number;
    avgBookingValue: number;
    conversionRate: number;
    activeNLCampaigns: number;
    pendingReviews: number;
  };
  revenueByMonth: Array<{ month: string; revenue: number }>;
  bookingsByStatus: Array<{ status: string; count: number }>;
  leadsBySource: Array<{ source: string; count: number }>;
  topRevenueCustomers: Array<{
    name: string;
    email: string;
    totalSpent: number;
  }>;
}

export interface MockLead {
  id: string;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  source: 'website' | 'referral' | 'social' | 'direct';
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost';
  quality: 'hot' | 'warm' | 'cold';
  createdAt: string;
  lastContactedAt?: string;
  notes?: string;
  estimatedValue?: number;
}

export interface MockCustomer {
  id: string;
  name: string;
  email: string;
  phone: string;
  totalBookings: number;
  totalSpent: number;
  lastBookingDate: string;
  createdAt: string;
  loyaltyTier: 'bronze' | 'silver' | 'gold' | 'platinum';
}

// ============================================================================
// Mock Data Generators
// ============================================================================

const SAMPLE_NAMES = [
  'John Smith',
  'Sarah Johnson',
  'Mike Chen',
  'Lisa Rodriguez',
  'David Kim',
  'Emily Brown',
  'James Wilson',
  'Maria Garcia',
  'Robert Taylor',
  'Jennifer Martinez',
  'William Anderson',
  'Jessica Lee',
  'Michael Thomas',
  'Ashley Jackson',
  'Christopher White',
  'Amanda Harris',
];

const SAMPLE_ADDRESSES = [
  '123 Main St, Los Angeles, CA 90001',
  '456 Oak Ave, San Francisco, CA 94102',
  '789 Pine Blvd, San Diego, CA 92101',
  '321 Elm Dr, Sacramento, CA 95814',
  '654 Maple Way, Fresno, CA 93721',
  '987 Cedar Ln, Long Beach, CA 90802',
  '147 Birch Rd, Oakland, CA 94601',
  '258 Willow Ct, Bakersfield, CA 93301',
];

const EVENT_TIMES = ['12PM', '3PM', '6PM', '9PM'];

const LEAD_SOURCES = ['website', 'referral', 'social', 'direct'] as const;
const LEAD_STATUSES = [
  'new',
  'contacted',
  'qualified',
  'converted',
  'lost',
] as const;

/**
 * Generate realistic bookings with varied dates and statuses
 */
function generateBookings(count: number = 50): MockBooking[] {
  const bookings: MockBooking[] = [];

  for (let i = 0; i < count; i++) {
    const createdDate = subDays(new Date(), Math.floor(Math.random() * 60));
    const eventDate = addDays(createdDate, Math.floor(Math.random() * 90));
    const name = SAMPLE_NAMES[Math.floor(Math.random() * SAMPLE_NAMES.length)];
    const address =
      SAMPLE_ADDRESSES[Math.floor(Math.random() * SAMPLE_ADDRESSES.length)];

    // Status distribution: 60% confirmed, 20% pending, 10% completed, 10% cancelled
    const rand = Math.random();
    let status: MockBooking['status'];
    if (rand < 0.6) status = 'confirmed';
    else if (rand < 0.8) status = 'pending';
    else if (rand < 0.9) status = 'completed';
    else status = 'cancelled';

    const guestCount = Math.floor(Math.random() * 50) + 10;
    const pricePerGuest = 75 + Math.floor(Math.random() * 50); // $75-$125 per guest
    const totalAmount = guestCount * pricePerGuest;

    bookings.push({
      id: `MH-${Date.now()}-${i.toString().padStart(6, '0')}`,
      customerName: name,
      customerEmail: name.toLowerCase().replace(' ', '.') + '@email.com',
      customerPhone: `(555) ${Math.floor(Math.random() * 900) + 100}-${Math.floor(Math.random() * 9000) + 1000}`,
      eventDate: format(eventDate, 'yyyy-MM-dd'),
      eventTime: EVENT_TIMES[Math.floor(Math.random() * EVENT_TIMES.length)],
      guestCount,
      status,
      createdAt: createdDate.toISOString(),
      venueAddress: address,
      billingAddress:
        Math.random() > 0.3
          ? address
          : SAMPLE_ADDRESSES[
              Math.floor(Math.random() * SAMPLE_ADDRESSES.length)
            ],
      totalAmount,
      depositPaid: status !== 'pending',
      specialRequests:
        Math.random() > 0.7 ? 'Outdoor setup preferred' : undefined,
      stationId: `station-${Math.floor(Math.random() * 3) + 1}`,
    });
  }

  // Sort by event date (newest first)
  return bookings.sort(
    (a, b) => new Date(b.eventDate).getTime() - new Date(a.eventDate).getTime()
  );
}

/**
 * Generate realistic leads
 */
function generateLeads(count: number = 30): MockLead[] {
  const leads: MockLead[] = [];

  for (let i = 0; i < count; i++) {
    const createdDate = subDays(new Date(), Math.floor(Math.random() * 30));
    const name = SAMPLE_NAMES[Math.floor(Math.random() * SAMPLE_NAMES.length)];

    // Quality based on days old
    const daysOld = Math.floor(
      (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    let quality: MockLead['quality'];
    if (daysOld < 3) quality = 'hot';
    else if (daysOld < 10) quality = 'warm';
    else quality = 'cold';

    const source =
      LEAD_SOURCES[Math.floor(Math.random() * LEAD_SOURCES.length)];
    const status =
      LEAD_STATUSES[Math.floor(Math.random() * LEAD_STATUSES.length)];

    leads.push({
      id: `LEAD-${Date.now()}-${i.toString().padStart(4, '0')}`,
      customerName: name,
      customerEmail: name.toLowerCase().replace(' ', '.') + '@email.com',
      customerPhone: `(555) ${Math.floor(Math.random() * 900) + 100}-${Math.floor(Math.random() * 9000) + 1000}`,
      source,
      status,
      quality,
      createdAt: createdDate.toISOString(),
      lastContactedAt:
        status !== 'new'
          ? subDays(new Date(), Math.floor(Math.random() * 5)).toISOString()
          : undefined,
      estimatedValue: Math.floor(Math.random() * 3000) + 1000,
      notes: status !== 'new' ? 'Followed up via email' : undefined,
    });
  }

  return leads.sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
}

/**
 * Generate realistic customers
 */
function generateCustomers(bookings: MockBooking[]): MockCustomer[] {
  const customerMap = new Map<string, MockCustomer>();

  bookings.forEach(booking => {
    const existing = customerMap.get(booking.customerEmail);

    if (existing) {
      existing.totalBookings += 1;
      existing.totalSpent += booking.totalAmount;
      if (new Date(booking.eventDate) > new Date(existing.lastBookingDate)) {
        existing.lastBookingDate = booking.eventDate;
      }
    } else {
      customerMap.set(booking.customerEmail, {
        id: `CUST-${Date.now()}-${customerMap.size}`,
        name: booking.customerName,
        email: booking.customerEmail,
        phone: booking.customerPhone,
        totalBookings: 1,
        totalSpent: booking.totalAmount,
        lastBookingDate: booking.eventDate,
        createdAt: booking.createdAt,
        loyaltyTier: 'bronze',
      });
    }
  });

  // Calculate loyalty tiers based on spending
  const customers = Array.from(customerMap.values());
  customers.forEach(customer => {
    if (customer.totalSpent >= 10000) customer.loyaltyTier = 'platinum';
    else if (customer.totalSpent >= 5000) customer.loyaltyTier = 'gold';
    else if (customer.totalSpent >= 2000) customer.loyaltyTier = 'silver';
    else customer.loyaltyTier = 'bronze';
  });

  return customers.sort((a, b) => b.totalSpent - a.totalSpent);
}

/**
 * Generate analytics from bookings and leads
 */
function generateAnalytics(
  bookings: MockBooking[],
  leads: MockLead[]
): MockAnalytics {
  const last30Days = subDays(new Date(), 30);
  const recentBookings = bookings.filter(
    b => new Date(b.createdAt) >= last30Days
  );

  const totalRevenue = recentBookings
    .filter(b => b.status === 'completed' || b.status === 'confirmed')
    .reduce((sum, b) => sum + b.totalAmount, 0);

  const totalBookings = recentBookings.length;
  const avgBookingValue = totalBookings > 0 ? totalRevenue / totalBookings : 0;

  const uniqueCustomers = new Set(recentBookings.map(b => b.customerEmail))
    .size;
  const convertedLeads = leads.filter(l => l.status === 'converted').length;
  const conversionRate =
    leads.length > 0 ? (convertedLeads / leads.length) * 100 : 0;

  // Revenue by month (last 6 months)
  const revenueByMonth: Array<{ month: string; revenue: number }> = [];
  for (let i = 5; i >= 0; i--) {
    const monthDate = subDays(new Date(), i * 30);
    const monthStart = new Date(
      monthDate.getFullYear(),
      monthDate.getMonth(),
      1
    );
    const monthEnd = new Date(
      monthDate.getFullYear(),
      monthDate.getMonth() + 1,
      0
    );

    const monthRevenue = bookings
      .filter(b => {
        const bookingDate = new Date(b.createdAt);
        return (
          bookingDate >= monthStart &&
          bookingDate <= monthEnd &&
          (b.status === 'completed' || b.status === 'confirmed')
        );
      })
      .reduce((sum, b) => sum + b.totalAmount, 0);

    revenueByMonth.push({
      month: format(monthDate, 'MMM yyyy'),
      revenue: monthRevenue,
    });
  }

  // Bookings by status
  const bookingsByStatus = [
    {
      status: 'Confirmed',
      count: bookings.filter(b => b.status === 'confirmed').length,
    },
    {
      status: 'Pending',
      count: bookings.filter(b => b.status === 'pending').length,
    },
    {
      status: 'Completed',
      count: bookings.filter(b => b.status === 'completed').length,
    },
    {
      status: 'Cancelled',
      count: bookings.filter(b => b.status === 'cancelled').length,
    },
  ];

  // Leads by source
  const leadsBySource = LEAD_SOURCES.map(source => ({
    source: source.charAt(0).toUpperCase() + source.slice(1),
    count: leads.filter(l => l.source === source).length,
  }));

  // Top revenue customers
  const customers = generateCustomers(bookings);
  const topRevenueCustomers = customers.slice(0, 5).map(c => ({
    name: c.name,
    email: c.email,
    totalSpent: c.totalSpent,
  }));

  return {
    overview: {
      totalRevenue,
      totalBookings,
      totalCustomers: uniqueCustomers,
      totalLeads: leads.length,
      avgBookingValue,
      conversionRate,
      activeNLCampaigns: 3, // Mock newsletter campaigns
      pendingReviews: Math.floor(Math.random() * 10) + 5,
    },
    revenueByMonth,
    bookingsByStatus,
    leadsBySource,
    topRevenueCustomers,
  };
}

// ============================================================================
// Service Class
// ============================================================================

class MockDataService {
  private static instance: MockDataService;
  private bookings: MockBooking[];
  private leads: MockLead[];
  private customers: MockCustomer[];
  private analytics: MockAnalytics;

  private constructor() {
    // Generate all mock data on initialization
    this.bookings = generateBookings(50);
    this.leads = generateLeads(30);
    this.customers = generateCustomers(this.bookings);
    this.analytics = generateAnalytics(this.bookings, this.leads);
  }

  static getInstance(): MockDataService {
    if (!MockDataService.instance) {
      MockDataService.instance = new MockDataService();
    }
    return MockDataService.instance;
  }

  /**
   * Get all bookings (with optional filters)
   */
  async getBookings(filters?: {
    status?: string;
    dateFrom?: string;
    dateTo?: string;
    stationId?: string;
  }): Promise<MockBooking[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    let filtered = [...this.bookings];

    if (filters?.status && filters.status !== 'all') {
      filtered = filtered.filter(b => b.status === filters.status);
    }

    if (filters?.dateFrom) {
      filtered = filtered.filter(b => b.eventDate >= filters.dateFrom!);
    }

    if (filters?.dateTo) {
      filtered = filtered.filter(b => b.eventDate <= filters.dateTo!);
    }

    if (filters?.stationId) {
      filtered = filtered.filter(b => b.stationId === filters.stationId);
    }

    return filtered;
  }

  /**
   * Get single booking by ID
   */
  async getBooking(id: string): Promise<MockBooking | null> {
    await new Promise(resolve => setTimeout(resolve, 200));
    return this.bookings.find(b => b.id === id) || null;
  }

  /**
   * Update booking status
   */
  async updateBookingStatus(
    id: string,
    status: MockBooking['status']
  ): Promise<MockBooking | null> {
    await new Promise(resolve => setTimeout(resolve, 300));
    const booking = this.bookings.find(b => b.id === id);
    if (booking) {
      booking.status = status;
      // Regenerate analytics after update
      this.analytics = generateAnalytics(this.bookings, this.leads);
      return booking;
    }
    return null;
  }

  /**
   * Get dashboard analytics
   */
  async getAnalytics(): Promise<MockAnalytics> {
    await new Promise(resolve => setTimeout(resolve, 400));
    return this.analytics;
  }

  /**
   * Get all leads
   */
  async getLeads(filters?: {
    status?: string;
    quality?: string;
  }): Promise<MockLead[]> {
    await new Promise(resolve => setTimeout(resolve, 300));

    let filtered = [...this.leads];

    if (filters?.status) {
      filtered = filtered.filter(l => l.status === filters.status);
    }

    if (filters?.quality) {
      filtered = filtered.filter(l => l.quality === filters.quality);
    }

    return filtered;
  }

  /**
   * Get all customers
   */
  async getCustomers(): Promise<MockCustomer[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return this.customers;
  }

  /**
   * Get booking stats for dashboard
   */
  async getBookingStats(): Promise<{
    total: number;
    confirmed: number;
    pending: number;
    cancelled: number;
    completed: number;
    revenue: number;
  }> {
    await new Promise(resolve => setTimeout(resolve, 200));

    return {
      total: this.bookings.length,
      confirmed: this.bookings.filter(b => b.status === 'confirmed').length,
      pending: this.bookings.filter(b => b.status === 'pending').length,
      cancelled: this.bookings.filter(b => b.status === 'cancelled').length,
      completed: this.bookings.filter(b => b.status === 'completed').length,
      revenue: this.bookings
        .filter(b => b.status === 'completed' || b.status === 'confirmed')
        .reduce((sum, b) => sum + b.totalAmount, 0),
    };
  }
}

// ============================================================================
// Export
// ============================================================================

export const mockDataService = MockDataService.getInstance();

// Helper to check if mock data is enabled
export const isMockDataEnabled = () => MOCK_DATA_ENABLED;

// Helper for transition to real API
export const shouldUseMockData = () => {
  // Check if real API is available
  const hasRealDatabase = process.env.NEXT_PUBLIC_USE_REAL_API === 'true';
  return MOCK_DATA_ENABLED && !hasRealDatabase;
};
