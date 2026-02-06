import { type BookingEmailData } from '@/lib/email-service';

// Email automation scheduler for MyHibachi booking system
// This service handles scheduled emails: review requests and upsells

interface ScheduledEmail {
  id: string;
  bookingId: string;
  emailType: 'review_request' | 'upsell';
  scheduledFor: string; // ISO date string
  customerEmail: string;
  bookingData: BookingEmailData;
  status: 'pending' | 'sent' | 'failed' | 'cancelled';
  createdAt: string;
}

// In-memory scheduler storage (replace with database in production)
const scheduledEmails: ScheduledEmail[] = [];
let emailSchedulerRunning = false;

class EmailScheduler {
  // Schedule review request email (24 hours after event)
  scheduleReviewRequest(
    bookingId: string,
    eventDate: string,
    eventTime: string,
    customerEmail: string,
    bookingData: BookingEmailData,
  ): void {
    // Calculate when to send review email (24 hours after event end)
    const eventEndTime = this.calculateEventEndTime(eventDate, eventTime);
    const reviewTime = new Date(eventEndTime.getTime() + 24 * 60 * 60 * 1000); // 24 hours later

    const scheduledEmail: ScheduledEmail = {
      id: `review-${bookingId}-${Date.now()}`,
      bookingId,
      emailType: 'review_request',
      scheduledFor: reviewTime.toISOString(),
      customerEmail,
      bookingData,
      status: 'pending',
      createdAt: new Date().toISOString(),
    };

    scheduledEmails.push(scheduledEmail);
    console.log(
      `[EMAIL SCHEDULER] Review request scheduled for ${reviewTime.toISOString()} for booking ${bookingId}`,
    );
  }

  // Schedule upsell email (1 month after booking, only if no recent bookings)
  scheduleUpsellEmail(
    bookingId: string,
    customerEmail: string,
    bookingData: BookingEmailData,
  ): void {
    // Calculate when to send upsell email (30 days from now)
    const upsellTime = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days later

    const scheduledEmail: ScheduledEmail = {
      id: `upsell-${bookingId}-${Date.now()}`,
      bookingId,
      emailType: 'upsell',
      scheduledFor: upsellTime.toISOString(),
      customerEmail,
      bookingData,
      status: 'pending',
      createdAt: new Date().toISOString(),
    };

    scheduledEmails.push(scheduledEmail);
    console.log(
      `[EMAIL SCHEDULER] Upsell email scheduled for ${upsellTime.toISOString()} for booking ${bookingId}`,
    );
  }

  // Helper: Calculate event end time
  private calculateEventEndTime(eventDate: string, eventTime: string): Date {
    const timeMap: { [key: string]: number } = {
      '12PM': 14, // 2 PM end time (2-hour experience)
      '3PM': 17, // 5 PM end time
      '6PM': 20, // 8 PM end time
      '9PM': 23, // 11 PM end time
    };

    const endHour = timeMap[eventTime] || 14;
    const eventEndTime = new Date(`${eventDate}T${endHour.toString().padStart(2, '0')}:00:00`);

    return eventEndTime;
  }

  // Check if customer has recent bookings (for upsell eligibility)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  private hasRecentBookings(_customerEmail: string, _sinceDate: Date): boolean {
    // This would check your booking database in production
    // For now, we'll assume no recent bookings to demonstrate functionality
    return false;
  }

  // Process pending scheduled emails
  async processPendingEmails(): Promise<void> {
    const now = new Date();
    const pendingEmails = scheduledEmails.filter(
      (email) => email.status === 'pending' && new Date(email.scheduledFor) <= now,
    );

    if (pendingEmails.length === 0) {
      return;
    }

    console.log(`[EMAIL SCHEDULER] Processing ${pendingEmails.length} pending emails`);

    for (const scheduledEmail of pendingEmails) {
      try {
        let success = false;

        if (scheduledEmail.emailType === 'review_request') {
          // Import email service dynamically to avoid circular dependencies
          const { emailService } = await import('./email-service');
          success = await emailService.sendReviewRequest(scheduledEmail.bookingData);
        } else if (scheduledEmail.emailType === 'upsell') {
          // Check if customer has made recent bookings before sending upsell
          const hasRecent = this.hasRecentBookings(
            scheduledEmail.customerEmail,
            new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
          );

          if (hasRecent) {
            scheduledEmail.status = 'cancelled';
            console.log(
              `[EMAIL SCHEDULER] Upsell cancelled for ${scheduledEmail.bookingId} - customer has recent bookings`,
            );
            continue;
          }

          const { emailService } = await import('./email-service');
          success = await emailService.sendUpsellEmail(scheduledEmail.bookingData);
        }

        // Update status based on send result
        scheduledEmail.status = success ? 'sent' : 'failed';

        console.log(
          `[EMAIL SCHEDULER] ${scheduledEmail.emailType} email ${
            success ? 'sent' : 'failed'
          } for booking ${scheduledEmail.bookingId}`,
        );
      } catch (error) {
        scheduledEmail.status = 'failed';
        console.error(
          `[EMAIL SCHEDULER ERROR] Failed to process ${scheduledEmail.emailType} for booking ${scheduledEmail.bookingId}:`,
          error,
        );
      }
    }
  }

  // Start the email scheduler (runs every 5 minutes)
  startScheduler(): void {
    if (emailSchedulerRunning) {
      console.log('[EMAIL SCHEDULER] Already running');
      return;
    }

    emailSchedulerRunning = true;
    console.log('[EMAIL SCHEDULER] Started - checking every 5 minutes');

    // Run immediately
    this.processPendingEmails();

    // Then run every 5 minutes
    setInterval(
      async () => {
        if (emailSchedulerRunning) {
          await this.processPendingEmails();
        }
      },
      5 * 60 * 1000,
    ); // 5 minutes
  }

  // Stop the email scheduler
  stopScheduler(): void {
    emailSchedulerRunning = false;
    console.log('[EMAIL SCHEDULER] Stopped');
  }

  // Get all scheduled emails with filtering
  getScheduledEmails(status?: 'pending' | 'sent' | 'failed' | 'cancelled'): ScheduledEmail[] {
    if (status) {
      return scheduledEmails.filter((email) => email.status === status);
    }
    return [...scheduledEmails];
  }

  // Cancel a scheduled email
  cancelScheduledEmail(emailId: string): boolean {
    const email = scheduledEmails.find((e) => e.id === emailId);
    if (email && email.status === 'pending') {
      email.status = 'cancelled';
      console.log(`[EMAIL SCHEDULER] Cancelled scheduled email ${emailId}`);
      return true;
    }
    return false;
  }

  // Admin: Manually trigger a scheduled email
  async triggerScheduledEmail(emailId: string): Promise<boolean> {
    const email = scheduledEmails.find((e) => e.id === emailId && e.status === 'pending');
    if (!email) {
      return false;
    }

    console.log(`[EMAIL SCHEDULER] Manually triggering email ${emailId}`);

    try {
      let success = false;
      const { emailService } = await import('./email-service');

      if (email.emailType === 'review_request') {
        success = await emailService.sendReviewRequest(email.bookingData);
      } else if (email.emailType === 'upsell') {
        success = await emailService.sendUpsellEmail(email.bookingData);
      }

      email.status = success ? 'sent' : 'failed';
      return success;
    } catch (error) {
      email.status = 'failed';
      console.error(`[EMAIL SCHEDULER ERROR] Manual trigger failed for ${emailId}:`, error);
      return false;
    }
  }

  // Get scheduler statistics
  getSchedulerStats(): {
    total: number;
    pending: number;
    sent: number;
    failed: number;
    cancelled: number;
    upcomingIn24Hours: number;
  } {
    const stats = {
      total: scheduledEmails.length,
      pending: 0,
      sent: 0,
      failed: 0,
      cancelled: 0,
      upcomingIn24Hours: 0,
    };

    const next24Hours = new Date(Date.now() + 24 * 60 * 60 * 1000);

    scheduledEmails.forEach((email) => {
      stats[email.status]++;

      if (email.status === 'pending' && new Date(email.scheduledFor) <= next24Hours) {
        stats.upcomingIn24Hours++;
      }
    });

    return stats;
  }
}

// Export singleton instance
export const emailScheduler = new EmailScheduler();
export type { ScheduledEmail };
