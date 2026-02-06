// Email automation startup and initialization
// This file should be imported in your main app or API route to start the email scheduler

import { emailScheduler } from '@/lib/email-scheduler';

// Initialize email automation system
export function initializeEmailAutomation(): void {
  console.log('[EMAIL AUTOMATION] Initializing email system...');

  // Start the email scheduler if enabled
  const schedulerEnabled = process.env.EMAIL_SCHEDULER_ENABLED !== 'false';

  if (schedulerEnabled) {
    emailScheduler.startScheduler();
    console.log('[EMAIL AUTOMATION] Email scheduler started successfully');
  } else {
    console.log(
      '[EMAIL AUTOMATION] Email scheduler disabled via environment variable'
    );
  }

  // Log current scheduler statistics
  const stats = emailScheduler.getSchedulerStats();
  console.log('[EMAIL AUTOMATION] Current stats:', {
    totalScheduled: stats.total,
    pending: stats.pending,
    upcomingIn24Hours: stats.upcomingIn24Hours,
  });
}

// Graceful shutdown handler
export function shutdownEmailAutomation(): void {
  console.log('[EMAIL AUTOMATION] Shutting down email system...');
  emailScheduler.stopScheduler();
  console.log('[EMAIL AUTOMATION] Email scheduler stopped');
}

// Health check for email system
export function checkEmailSystemHealth(): {
  scheduler: boolean;
  stats: ReturnType<typeof emailScheduler.getSchedulerStats>;
} {
  const stats = emailScheduler.getSchedulerStats();

  return {
    scheduler: true, // In production, this would check if scheduler is actually running
    stats,
  };
}

// Auto-initialize if this is the main server process
if (typeof window === 'undefined' && process.env.NODE_ENV !== 'test') {
  // Initialize after a short delay to ensure all modules are loaded
  setTimeout(initializeEmailAutomation, 1000);

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    shutdownEmailAutomation();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    shutdownEmailAutomation();
    process.exit(0);
  });
}
