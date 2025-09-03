// Fix remaining hardcoded fetch calls in frontend
const fs = require('fs')
const path = require('path')

const filesToFix = [
  'src/components/payment/AlternativePaymentOptions.tsx',
  'src/components/CustomerSavingsDisplay.tsx',
  'src/components/booking/BookingFormContainer.tsx',
  'src/components/admin/BaseLocationManager-simplified.tsx',
  'src/components/admin/PaymentManagement.tsx'
]

const fetchPatterns = [
  {
    // Regular fetch('/api/...')
    pattern: /await fetch\('\/api\/([^']+)',\s*{\s*method:\s*'([^']+)'[^}]*}\)/g,
    replacement: "await apiFetch('/api/$1', { method: '$2' })"
  },
  {
    // fetch without await
    pattern: /fetch\('\/api\/([^']+)',\s*{\s*method:\s*'([^']+)'[^}]*}\)/g,
    replacement: "apiFetch('/api/$1', { method: '$2' })"
  },
  {
    // Simple fetch calls without method
    pattern: /await fetch\('\/api\/([^']+)'\)/g,
    replacement: "await apiFetch('/api/$1')"
  }
]

function fixFetchCalls() {
  let totalFixed = 0

  filesToFix.forEach(filePath => {
    const fullPath = path.join(__dirname, filePath)

    if (!fs.existsSync(fullPath)) {
      console.log(`⚠️ File not found: ${filePath}`)
      return
    }

    let content = fs.readFileSync(fullPath, 'utf8')
    let fileFixed = 0

    // Check if apiFetch import exists
    if (!content.includes('import { apiFetch }')) {
      // Add import at the top after other imports
      const importMatch = content.match(/^((?:import.*\n)*)/m)
      if (importMatch) {
        content = content.replace(
          importMatch[1],
          importMatch[1] + "import { apiFetch } from '@/lib/api'\n"
        )
        console.log(`✅ Added apiFetch import to ${filePath}`)
      }
    }

    // Apply fetch pattern replacements
    fetchPatterns.forEach(({ pattern, replacement }) => {
      const matches = content.match(pattern)
      if (matches) {
        content = content.replace(pattern, replacement)
        fileFixed += matches.length
        console.log(`✅ Fixed ${matches.length} fetch calls in ${filePath}`)
      }
    })

    // Handle response processing changes
    if (content.includes('await response.json()')) {
      content = content.replace(
        /const\s+(\w+)\s*=\s*await\s+response\.json\(\)/g,
        'const $1 = response.success ? response.data : response'
      )
      fileFixed++
      console.log(`✅ Fixed response handling in ${filePath}`)
    }

    if (fileFixed > 0) {
      fs.writeFileSync(fullPath, content, 'utf8')
      totalFixed += fileFixed
      console.log(`📝 Updated ${filePath} (${fileFixed} fixes)`)
    } else {
      console.log(`⏭️ No changes needed in ${filePath}`)
    }
  })

  console.log(`\n🎉 Total fixes applied: ${totalFixed}`)
  return totalFixed
}

// Run the fixes
fixFetchCalls()
