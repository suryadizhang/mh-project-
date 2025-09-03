#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Files with hardcoded fetch calls that need updating
const filesToUpdate = [
  'myhibachi-frontend/src/components/admin/PaymentManagement.tsx',
  'myhibachi-frontend/src/app/checkout/page.tsx',
  'myhibachi-frontend/src/app/checkout/success/page.tsx',
  'myhibachi-frontend/src/lib/baseLocationUtils.ts',
  'myhibachi-frontend/src/hooks/booking/useBooking.ts',
  'myhibachi-frontend/src/components/payment/AlternativePaymentOptions.tsx',
  'myhibachi-frontend/src/components/CustomerSavingsDisplay.tsx',
  'myhibachi-frontend/src/components/booking/BookingFormContainer.tsx',
  'myhibachi-frontend/src/components/admin/BaseLocationManager.tsx',
  'myhibachi-frontend/src/components/admin/BaseLocationManager-simplified.tsx',
  'myhibachi-frontend/src/app/payment/page.tsx',
  'myhibachi-frontend/src/app/BookUs/page.tsx',
  'myhibachi-frontend/src/app/BookUs/BookUsPageClient.tsx'
];

function updateFileToUseApiClient(filePath) {
  try {
    const fullPath = path.resolve(filePath);
    if (!fs.existsSync(fullPath)) {
      console.log(`⚠️  File not found: ${filePath}`);
      return false;
    }

    let content = fs.readFileSync(fullPath, 'utf8');
    let hasChanges = false;

    // Check if apiFetch is already imported
    const hasApiImport = content.includes("import { apiFetch }") || 
                        content.includes("import {apiFetch}") ||
                        content.includes("from '@/lib/api'");

    // Add import if not present
    if (!hasApiImport) {
      // Find the import section
      const importRegex = /^(import .* from .*\n)/m;
      const lastImportMatch = content.match(/^import .* from .*$/gm);
      
      if (lastImportMatch) {
        const lastImport = lastImportMatch[lastImportMatch.length - 1];
        const importIndex = content.lastIndexOf(lastImport) + lastImport.length;
        
        content = content.slice(0, importIndex) + 
                  "\nimport { apiFetch } from '@/lib/api'" + 
                  content.slice(importIndex);
        hasChanges = true;
        console.log(`  ✅ Added apiFetch import to ${filePath}`);
      }
    }

    // Replace fetch patterns with apiFetch
    const fetchPatterns = [
      // Pattern: const response = await fetch('/api/...', ...)
      {
        pattern: /const response = await fetch\('\/api\/([^']+)',\s*\{([^}]*)\}\)/g,
        replacement: (match, apiPath, options) => {
          // Parse options to extract method, headers, body
          const methodMatch = options.match(/method:\s*['"]([^'"]+)['"]/);
          const bodyMatch = options.match(/body:\s*([^,}]+)/);
          
          let newOptions = [];
          if (methodMatch) newOptions.push(`method: '${methodMatch[1]}'`);
          if (bodyMatch) newOptions.push(`body: ${bodyMatch[1]}`);
          
          const optionsStr = newOptions.length > 0 ? `{ ${newOptions.join(', ')} }` : '{}';
          return `const result = await apiFetch('/api/${apiPath}', ${optionsStr})`;
        }
      },
      // Pattern: await fetch('/api/...', ...)
      {
        pattern: /await fetch\('\/api\/([^']+)',\s*\{([^}]*)\}\)/g,
        replacement: (match, apiPath, options) => {
          const methodMatch = options.match(/method:\s*['"]([^'"]+)['"]/);
          const bodyMatch = options.match(/body:\s*([^,}]+)/);
          
          let newOptions = [];
          if (methodMatch) newOptions.push(`method: '${methodMatch[1]}'`);
          if (bodyMatch) newOptions.push(`body: ${bodyMatch[1]}`);
          
          const optionsStr = newOptions.length > 0 ? `{ ${newOptions.join(', ')} }` : '{}';
          return `await apiFetch('/api/${apiPath}', ${optionsStr})`;
        }
      },
      // Pattern: fetch('/api/...') (simple GET)
      {
        pattern: /const response = await fetch\('\/api\/([^']+)'\)/g,
        replacement: (match, apiPath) => `const result = await apiFetch('/api/${apiPath}')`
      },
      {
        pattern: /await fetch\('\/api\/([^']+)'\)/g,
        replacement: (match, apiPath) => `await apiFetch('/api/${apiPath}')`
      }
    ];

    fetchPatterns.forEach(({ pattern, replacement }) => {
      const newContent = content.replace(pattern, replacement);
      if (newContent !== content) {
        content = newContent;
        hasChanges = true;
      }
    });

    // Remove response.ok checks and response.json() calls since apiFetch handles these
    const cleanupPatterns = [
      /if \(!response\.ok\) \{\s*throw new Error\([^}]+\}\s*/g,
      /const result = await response\.json\(\)/g,
      /const data = await response\.json\(\)/g
    ];

    cleanupPatterns.forEach(pattern => {
      const newContent = content.replace(pattern, '');
      if (newContent !== content) {
        content = newContent;
        hasChanges = true;
      }
    });

    if (hasChanges) {
      fs.writeFileSync(fullPath, content);
      console.log(`✅ Updated ${filePath} to use apiFetch`);
      return true;
    } else {
      console.log(`📝 No changes needed for ${filePath}`);
      return false;
    }

  } catch (error) {
    console.error(`❌ Failed to update ${filePath}:`, error.message);
    return false;
  }
}

function main() {
  console.log('🔄 Updating frontend files to use unified API client...\n');
  
  let totalUpdated = 0;
  
  for (const file of filesToUpdate) {
    if (updateFileToUseApiClient(file)) {
      totalUpdated++;
    }
  }
  
  console.log(`\n✅ API Client Migration Complete!`);
  console.log(`📊 Updated ${totalUpdated} files to use apiFetch`);
  console.log(`🔗 All API calls now go through unified backend client`);
  
  return totalUpdated;
}

if (require.main === module) {
  main();
}

module.exports = { updateFileToUseApiClient };
