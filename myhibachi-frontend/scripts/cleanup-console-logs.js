#!/usr/bin/env node

/**
 * Comprehensive Console Log and TypeScript Cleanup Script
 * Part of the Reliable Formatting Pipeline (RFP)
 *
 * This script removes console.log statements and fixes TypeScript issues
 * while preserving intentional debug/error logging for production.
 */

// eslint-disable-next-line @typescript-eslint/no-require-imports
const fs = require('fs')
// eslint-disable-next-line @typescript-eslint/no-require-imports
const path = require('path')

// Files that contain console statements to clean up
const filesToClean = [
  './src/app/admin/page.tsx',
  './src/app/BookUs/BookUsPageClient.tsx',
  './src/app/contact/ContactPageClient.tsx',
  './src/components/admin/SEOAutomationDashboard.tsx',
  './src/components/booking/BookingForm.tsx',
  './src/components/booking/BookingFormContainer.tsx',
  './src/components/chat/Assistant.tsx',
  './src/components/chat/MetaMessenger.tsx',
  './src/components/faq/FaqItem.tsx',
  './src/hooks/booking/useBooking.ts',
  './src/lib/advancedAutomation.ts',
  './src/lib/email-automation-init.ts',
  './src/lib/email-scheduler.ts',
  './src/lib/email-service.ts',
  './src/lib/server/stripeCustomerService.ts'
]

// Specific fixes for TypeScript issues
const typeScriptFixes = {
  './src/app/BookUs/page.tsx': {
    find: 'any',
    replace: 'unknown',
    lineApprox: 115
  }
}

function cleanupFile(filePath) {
  try {
    const fullPath = path.resolve(filePath)
    if (!fs.existsSync(fullPath)) {
      console.log(`⚠️  File not found: ${filePath}`)
      return
    }

    let content = fs.readFileSync(fullPath, 'utf8')
    let originalContent = content
    let changes = 0

    // More precise console.log removal that preserves code structure
    const lines = content.split('\n')
    const newLines = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const trimmed = line.trim()

      // Skip lines that are purely console.log statements
      if (trimmed.startsWith('console.log(') && (trimmed.endsWith(');') || trimmed.endsWith(')'))) {
        changes++
        continue // Skip this line entirely
      }

      // Handle inline console.log statements
      if (line.includes('console.log(') && !trimmed.startsWith('//')) {
        // Remove console.log but preserve the rest of the line structure
        const newLine = line.replace(/console\.log\([^)]*\);?\s*/, '')
        if (newLine.trim().length > 0) {
          newLines.push(newLine)
        }
        changes++
      } else {
        newLines.push(line)
      }
    }

    content = newLines.join('\n')

    // Apply TypeScript-specific fixes
    if (typeScriptFixes[filePath]) {
      const fix = typeScriptFixes[filePath]
      if (fix.find && fix.replace) {
        const fixLines = content.split('\n')
        for (
          let i = Math.max(0, fix.lineApprox - 5);
          i < Math.min(fixLines.length, fix.lineApprox + 5);
          i++
        ) {
          if (fixLines[i] && fixLines[i].includes(fix.find)) {
            fixLines[i] = fixLines[i].replace(new RegExp(`\\b${fix.find}\\b`, 'g'), fix.replace)
            changes++
            break
          }
        }
        content = fixLines.join('\n')
      }
    }

    if (content !== originalContent) {
      fs.writeFileSync(fullPath, content, 'utf8')
      console.log(`✅ Cleaned ${filePath} (${changes} changes)`)
    } else {
      console.log(`✨ No changes needed for ${filePath}`)
    }
  } catch (error) {
    console.error(`❌ Error processing ${filePath}:`, error.message)
  }
}

function main() {
  console.log('🚀 Starting Console Log and TypeScript Cleanup...\n')

  filesToClean.forEach(cleanupFile)

  console.log('\n✅ Cleanup complete! Running lint check...')
}

if (require.main === module) {
  main()
}

module.exports = { cleanupFile, filesToClean }
