// Simple in-memory data store for demonstration
// In production, replace this with a real database

export interface Booking {
  id: string;
  name: string;
  email: string;
  phone: string;
  event_date: string;
  event_time: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zipcode: string;
  venue_street: string;
  venue_city: string;
  venue_state: string;
  venue_zipcode: string;
  status: string;
  created_at: string;
}

// Global storage (in production, use a database)
const bookingsStore: Booking[] = [];

export function addBooking(booking: Booking): void {
  bookingsStore.push(booking);
}

export function getBookings(): Booking[] {
  return [...bookingsStore];
}

export function isTimeSlotAvailable(date: string, time: string): boolean {
  return !bookingsStore.some(
    booking =>
      booking.event_date === date &&
      booking.event_time === time &&
      booking.status !== 'cancelled'
  );
}

export function generateId(): string {
  return (
    Math.random().toString(36).substring(2, 15) +
    Math.random().toString(36).substring(2, 15)
  );
}

export function isDateAtLeastTwoDaysInAdvance(dateString: string): boolean {
  const eventDate = new Date(dateString);
  const today = new Date();
  const twoDaysFromNow = new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000);

  // Reset time to start of day for accurate comparison
  eventDate.setHours(0, 0, 0, 0);
  twoDaysFromNow.setHours(0, 0, 0, 0);

  return eventDate >= twoDaysFromNow;
}
