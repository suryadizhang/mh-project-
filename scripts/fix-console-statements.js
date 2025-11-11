#!/usr/bin/env node
/**
 * Batch Console Statement Replacer
 * 
 * This script systematically replaces console statements with logger calls
 * across all customer frontend files.
 */

const fs = require('fs');
const path = require('path');

// Files to process with their console statement patterns
const filesToFix = [
  // Booking components
  {
    file: 'apps/customer/src/app/BookUs/page.tsx',
    replacements: [
      {
        search: /console\.warn\('Could not fetch booked dates, continuing without blocking dates'\)/g,
        replace: "logger.warn('Could not fetch booked dates, continuing without blocking dates')"
      },
      {
        search: /console\.warn\('Error fetching booked dates:', error\)/g,
        replace: "logger.warn('Error fetching booked dates', { error })"
      },
      {
        search: /console\.warn\('Could not fetch availability, using default slots'\)/g,
        replace: "logger.warn('Could not fetch availability, using default slots')"
      },
      {
        search: /console\.warn\('Error fetching availability:', error\)/g,
        replace: "logger.warn('Error fetching availability', { error })"
      },
      {
        search: /console\.warn\('Could not verify slot availability:', error\)/g,
        replace: "logger.warn('Could not verify slot availability', { error })"
      },
      {
        search: /console\.error\('Form submission error:', error\)/g,
        replace: "logger.error('Form submission error', error as Error)"
      },
      {
        search: /console\.error\('Booking submission error:', error\)/g,
        replace: "logger.error('Booking submission error', error as Error)"
      }
    ]
  },
  
  // Checkout pages
  {
    file: 'apps/customer/src/app/checkout/page.tsx',
    replacements: [
      {
        search: /console\.error\('Error retrieving session:', err\)/g,
        replace: "logger.error('Error retrieving session', err as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/app/checkout/success/page.tsx',
    replacements: [
      {
        search: /console\.error\('Error fetching session data:', err\)/g,
        replace: "logger.error('Error fetching session data', err as Error)"
      },
      {
        search: /console\.error\('Error downloading receipt:', err\)/g,
        replace: "logger.error('Error downloading receipt', err as Error)"
      }
    ]
  },
  
  // Booking success
  {
    file: 'apps/customer/src/app/booking-success/page.tsx',
    replacements: [
      {
        search: /console\.error\('Error downloading invoice:', error\)/g,
        replace: "logger.error('Error downloading invoice', error as Error)"
      }
    ]
  },
  
  // Global error
  {
    file: 'apps/customer/src/app/global-error.tsx',
    replacements: [
      {
        search: /console\.error\(error\)/g,
        replace: "logger.error('Global error caught', error)"
      }
    ]
  },
  
  // Components
  {
    file: 'apps/customer/src/components/booking/BookingFormContainer.tsx',
    replacements: [
      {
        search: /console\.warn\('Could not fetch booked dates, continuing without blocking dates'\)/g,
        replace: "logger.warn('Could not fetch booked dates, continuing without blocking dates')"
      },
      {
        search: /console\.warn\('Error fetching booked dates:', error\)/g,
        replace: "logger.warn('Error fetching booked dates', { error })"
      },
      {
        search: /console\.warn\('Error fetching time slots:', error\)/g,
        replace: "logger.warn('Error fetching time slots', { error })"
      },
      {
        search: /console\.log\('Form submission started with data:', data\)/g,
        replace: "logger.debug('Form submission started') // DO NOT log data - contains PII"
      },
      {
        search: /console\.log\('Submitting booking request:', formData\)/g,
        replace: "logger.debug('Submitting booking request') // DO NOT log formData - contains PII"
      },
      {
        search: /console\.log\('Booking submitted successfully'\)/g,
        replace: "logger.info('Booking submitted successfully')"
      },
      {
        search: /console\.error\('Booking submission failed:', errorData\)/g,
        replace: "logger.error('Booking submission failed', undefined, { error: errorData })"
      },
      {
        search: /console\.error\('Error submitting booking:', error\)/g,
        replace: "logger.error('Error submitting booking', error as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/booking/BookingForm.tsx',
    replacements: [
      {
        search: /console\.log\('Booking created:', result\)/g,
        replace: "logger.info('Booking created')"
      },
      {
        search: /console\.error\('Error creating booking:', error\)/g,
        replace: "logger.error('Error creating booking', error as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/payment/PaymentForm.tsx',
    replacements: [
      {
        search: /console\.error\('Payment error:', error\)/g,
        replace: "logger.error('Payment error', error as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/payment/BookingLookup.tsx',
    replacements: [
      {
        search: /console\.error\('Search error:', error\)/g,
        replace: "logger.error('Search error', error as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/payment/AlternativePaymentOptions.tsx',
    replacements: [
      {
        search: /console\.error\('Failed to copy:', err\)/g,
        replace: "logger.error('Failed to copy', err as Error)"
      },
      {
        search: /console\.error\('Error generating QR code:', error\)/g,
        replace: "logger.error('Error generating QR code', error as Error)"
      },
      {
        search: /console\.error\('Error recording payment:', error\)/g,
        replace: "logger.error('Error recording payment', error as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/quote/QuoteCalculator.tsx',
    replacements: [
      {
        search: /console\.error\('Calculation error:', error\)/g,
        replace: "logger.error('Calculation error', error as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/CustomerSavingsDisplay.tsx',
    replacements: [
      {
        search: /console\.error\('Error opening customer portal:', err\)/g,
        replace: "logger.error('Error opening customer portal', err as Error)"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/faq/FaqItem.tsx',
    replacements: [
      {
        search: /console\.log\('FAQ Feedback:', \{ faq_id: faq\.id, helpful, category: faq\.category \}\)/g,
        replace: "logger.debug('FAQ Feedback', { faq_id: faq.id, helpful, category: faq.category })"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/chat/Assistant.tsx',
    replacements: [
      {
        search: /console\.log\('Legacy Assistant component rendered for page:', page\)/g,
        replace: "logger.debug('Legacy Assistant component rendered', { page })"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/chat/MetaMessenger.tsx',
    replacements: [
      {
        search: /console\.warn\(/g,
        replace: "logger.warn("
      },
      {
        search: /console\.log\('Facebook SDK loaded successfully with App ID:', appId\)/g,
        replace: "logger.debug('Facebook SDK loaded', { appId })"
      },
      {
        search: /console\.error\('Failed to load Facebook SDK'\)/g,
        replace: "logger.error('Failed to load Facebook SDK')"
      }
    ]
  },
  
  {
    file: 'apps/customer/src/components/analytics/GoogleAnalytics.tsx',
    replacements: [
      {
        search: /console\.warn\(/g,
        replace: "logger.warn("
      }
    ]
  },
  
  // Hooks
  {
    file: 'apps/customer/src/hooks/booking/useBooking.ts',
    replacements: [
      {
        search: /console\.log\('Booked dates response:', result\.data\)/g,
        replace: "logger.debug('Booked dates response')"
      },
      {
        search: /console\.error\('Error fetching booked dates:', error\)/g,
        replace: "logger.error('Error fetching booked dates', error as Error)"
      },
      {
        search: /console\.error\('Failed to fetch availability'\)/g,
        replace: "logger.error('Failed to fetch availability')"
      },
      {
        search: /console\.error\('Error fetching availability:', error\)/g,
        replace: "logger.error('Error fetching availability', error as Error)"
      },
      {
        search: /console\.error\('Error in form submission:', error\)/g,
        replace: "logger.error('Error in form submission', error as Error)"
      }
    ]
  }
];

console.log('🔧 Console Statement Batch Replacer\n');
console.log(`Found ${filesToFix.length} files to process\n`);

// Process each file
let totalReplacements = 0;
let filesModified = 0;

filesToFix.forEach(({ file, replacements }) => {
  const filePath = path.join(__dirname, '..', '..', file);
  
  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  SKIP: ${file} (file not found)`);
    return;
  }
  
  let content = fs.readFileSync(filePath, 'utf8');
  let fileModified = false;
  let fileReplacements = 0;
  
  // Check if logger is already imported
  const hasLoggerImport = content.includes("from '@/lib/logger'");
  
  replacements.forEach(({ search, replace }) => {
    const matches = content.match(search);
    if (matches) {
      content = content.replace(search, replace);
      fileReplacements += matches.length;
      fileModified = true;
    }
  });
  
  if (fileModified) {
    // Add logger import if not present
    if (!hasLoggerImport) {
      // Find the last import statement
      const importRegex = /^import .+ from .+;?$/gm;
      const imports = content.match(importRegex);
      if (imports && imports.length > 0) {
        const lastImport = imports[imports.length - 1];
        const lastImportIndex = content.lastIndexOf(lastImport);
        content = content.slice(0, lastImportIndex + lastImport.length) + 
                  "\nimport { logger } from '@/lib/logger';" +
                  content.slice(lastImportIndex + lastImport.length);
      }
    }
    
    fs.writeFileSync(filePath, content, 'utf8');
    filesModified++;
    totalReplacements += fileReplacements;
    console.log(`✅ ${file} (${fileReplacements} replacements)`);
  } else {
    console.log(`⏭️  ${file} (no changes needed)`);
  }
});

console.log(`\n📊 Summary:`);
console.log(`   Files modified: ${filesModified}`);
console.log(`   Total replacements: ${totalReplacements}`);
console.log(`\n✨ Done! Run 'npm run typecheck' to verify.\n`);
