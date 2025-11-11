import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../../helpers/auth-helpers';

/**
 * Admin Dashboard Tests
 * 
 * Tests admin functionality for managing bookings
 * 
 * Tags: @admin @critical
 * Services needed: Frontend, Backend, Database
 */
test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });
  
  test('loads dashboard successfully @admin @smoke', async ({ page }) => {
    // Should already be on dashboard from login
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
  });
  
  test('displays booking statistics @admin', async ({ page }) => {
    // Verify stats cards
    await expect(page.locator('[data-testid="total-bookings"]')).toBeVisible();
    await expect(page.locator('[data-testid="pending-bookings"]')).toBeVisible();
    await expect(page.locator('[data-testid="completed-bookings"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue"]')).toBeVisible();
  });
  
  test('can view all bookings @admin @critical', async ({ page }) => {
    await page.click('text=Bookings');
    await expect(page).toHaveURL(/.*bookings/);
    
    // Verify bookings table
    await expect(page.locator('table')).toBeVisible();
    
    // Verify table headers
    await expect(page.locator('th:has-text("Booking ID")')).toBeVisible();
    await expect(page.locator('th:has-text("Customer")')).toBeVisible();
    await expect(page.locator('th:has-text("Event Date")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
  });
  
  test('can search bookings @admin', async ({ page }) => {
    await page.click('text=Bookings');
    
    // Search by booking ID
    await page.fill('[placeholder*="Search"]', 'MH-2025');
    
    // Wait for filtered results
    await page.waitForTimeout(1000);
    
    // Verify search results
    const rows = await page.locator('tbody tr').count();
    expect(rows).toBeGreaterThan(0);
  });
  
  test('can filter bookings by status @admin', async ({ page }) => {
    await page.click('text=Bookings');
    
    // Filter by pending
    await page.click('[data-testid="status-filter"]');
    await page.click('text=Pending');
    
    // Wait for filtered results
    await page.waitForTimeout(1000);
    
    // Verify all visible bookings are pending
    const statuses = await page.locator('[data-testid="booking-status"]').allTextContents();
    statuses.forEach(status => {
      expect(status.toLowerCase()).toContain('pending');
    });
  });
  
  test('can view booking details @admin @critical', async ({ page }) => {
    await page.click('text=Bookings');
    
    // Click first booking
    await page.locator('tbody tr').first().click();
    
    // Verify details modal/page
    await expect(page.locator('[data-testid="booking-details-modal"]')).toBeVisible();
    
    // Verify all details shown
    await expect(page.locator('text=Customer Information')).toBeVisible();
    await expect(page.locator('text=Event Details')).toBeVisible();
    await expect(page.locator('text=Payment Information')).toBeVisible();
  });
  
  test('can update booking status @admin @critical', async ({ page }) => {
    await page.click('text=Bookings');
    
    // Click first booking
    await page.locator('tbody tr').first().click();
    
    // Change status
    await page.click('[data-testid="status-dropdown"]');
    await page.click('text=Confirmed');
    
    // Save changes
    await page.click('button:has-text("Save")');
    
    // Verify success message
    await expect(page.locator('text=Status updated successfully')).toBeVisible();
  });
  
  test('can cancel booking @admin', async ({ page }) => {
    await page.click('text=Bookings');
    
    // Click first booking
    await page.locator('tbody tr').first().click();
    
    // Cancel booking
    await page.click('button:has-text("Cancel Booking")');
    
    // Confirm cancellation
    await page.click('button:has-text("Confirm")');
    
    // Verify success
    await expect(page.locator('text=Booking cancelled')).toBeVisible();
  });
  
  test('can add notes to booking @admin', async ({ page }) => {
    await page.click('text=Bookings');
    
    // Click first booking
    await page.locator('tbody tr').first().click();
    
    // Add note
    await page.fill('[name="note"]', 'Customer requested extra soy sauce');
    await page.click('button:has-text("Add Note")');
    
    // Verify note added
    await expect(page.locator('text=Customer requested extra soy sauce')).toBeVisible();
  });
});

test.describe('Admin Real-time Features', () => {
  test('receives real-time booking notifications @admin @realtime', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Wait for WebSocket connection
    await page.waitForTimeout(2000);
    
    // Simulate new booking (you might need to trigger this via API or another session)
    // This is a placeholder - adjust based on your implementation
    
    // Verify notification appears
    await expect(page.locator('[data-testid="notification"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=New booking received')).toBeVisible();
  });
  
  test('shows online status @admin @realtime', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Verify online indicator
    await expect(page.locator('[data-testid="online-status"]')).toBeVisible();
    await expect(page.locator('text=Online')).toBeVisible();
  });
});

test.describe('Admin Analytics', () => {
  test('displays revenue chart @admin', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Verify chart loads
    await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
  });
  
  test('shows booking trends @admin', async ({ page }) => {
    await loginAsAdmin(page);
    await page.click('text=Analytics');
    
    // Verify trends
    await expect(page.locator('[data-testid="booking-trends"]')).toBeVisible();
  });
});
