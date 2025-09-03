// Comprehensive diagnostic script to identify all issues
// This script will check for missing files, imports, and functionality

const fs = require('fs')
const path = require('path')

console.log('\n🔍 COMPREHENSIVE SYSTEM DIAGNOSTIC')
console.log('==================================\n')

const checkFileExists = filePath => {
  const fullPath = path.resolve(filePath)
  const exists = fs.existsSync(fullPath)
  console.log(`   ${exists ? '✅' : '❌'} ${filePath}`)
  return exists
}

const checkFileContent = (filePath, searchTerm) => {
  try {
    const content = fs.readFileSync(filePath, 'utf8')
    const found = content.includes(searchTerm)
    console.log(`   ${found ? '✅' : '❌'} Contains "${searchTerm}"`)
    return found
  } catch (error) {
    console.log(`   ❌ Error reading file: ${error.message}`)
    return false
  }
}

// 1. Check core files exist
console.log('1. CORE FILES CHECK:')
console.log('===================')
const coreFiles = [
  'src/components/chat/Assistant.tsx',
  'src/app/api/assistant/route.ts',
  'src/app/contact/page.tsx',
  'src/lib/contactData.ts',
  'src/data/contact.json',
  'src/lib/vectorSearch.ts',
  'src/components/chat/MetaMessenger.tsx',
  'src/components/consent/ConsentBar.tsx'
]

let missingFiles = []
coreFiles.forEach(file => {
  if (!checkFileExists(file)) {
    missingFiles.push(file)
  }
})

// 2. Check package.json dependencies
console.log('\n2. PACKAGE.JSON CHECK:')
console.log('=====================')
checkFileExists('package.json')
if (fs.existsSync('package.json')) {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const requiredDeps = ['next', 'react', 'react-dom', 'lucide-react']

  requiredDeps.forEach(dep => {
    const exists = packageJson.dependencies?.[dep] || packageJson.devDependencies?.[dep]
    console.log(`   ${exists ? '✅' : '❌'} ${dep}: ${exists || 'missing'}`)
  })
}

// 3. Check imports in key files
console.log('\n3. IMPORT CHECKS:')
console.log('================')

// Check Assistant.tsx imports
console.log('\n   Assistant.tsx:')
if (fs.existsSync('src/components/chat/Assistant.tsx')) {
  checkFileContent('src/components/chat/Assistant.tsx', "from '@/lib/contactData'")
  checkFileContent('src/components/chat/Assistant.tsx', 'InlineMessengerButton')
  checkFileContent('src/components/chat/Assistant.tsx', 'InlineInstagramButton')
}

// Check contact page
console.log('\n   Contact Page:')
if (fs.existsSync('src/app/contact/page.tsx')) {
  checkFileContent('src/app/contact/page.tsx', 'function InlineMessengerButton')
  checkFileContent('src/app/contact/page.tsx', 'function InlineInstagramButton')
  checkFileContent('src/app/contact/page.tsx', '<InlineMessengerButton />')
  checkFileContent('src/app/contact/page.tsx', '<InlineInstagramButton />')
}

// Check API route
console.log('\n   API Route:')
if (fs.existsSync('src/app/api/assistant/route.ts')) {
  checkFileContent('src/app/api/assistant/route.ts', 'contact a person')
  checkFileContent('src/app/api/assistant/route.ts', 'cosineSearch')
}

// 4. Check configuration files
console.log('\n4. CONFIGURATION CHECK:')
console.log('======================')
if (fs.existsSync('src/data/contact.json')) {
  const contact = JSON.parse(fs.readFileSync('src/data/contact.json', 'utf8'))
  console.log(`   ✅ Facebook Page ID: ${contact.facebookPageId}`)
  console.log(`   ✅ Instagram Username: ${contact.instagramUsername}`)
  console.log(`   ✅ Phone: ${contact.phone}`)
  console.log(`   ✅ Email: ${contact.email}`)
}

// 5. Check for TypeScript errors
console.log('\n5. TYPESCRIPT COMPILATION CHECK:')
console.log('================================')
console.log('   Run: npx tsc --noEmit to check for TypeScript errors')

// 6. Check for Next.js specific issues
console.log('\n6. NEXT.JS SPECIFIC CHECKS:')
console.log('===========================')
checkFileExists('next.config.ts')
checkFileExists('tsconfig.json')
checkFileExists('.env.local')

// 7. Check for React 19 compatibility
console.log('\n7. REACT 19 COMPATIBILITY:')
console.log('==========================')
if (fs.existsSync('package.json')) {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const reactVersion = packageJson.dependencies?.react || 'not found'
  const nextVersion = packageJson.dependencies?.next || 'not found'
  console.log(`   React version: ${reactVersion}`)
  console.log(`   Next.js version: ${nextVersion}`)

  // Check for known compatibility issues
  if (reactVersion.includes('19')) {
    console.log('   ⚠️  React 19 detected - may have compatibility issues')
    console.log('   Recommendation: Clear cache and restart dev server')
  }
}

// Summary
console.log('\n📋 DIAGNOSTIC SUMMARY:')
console.log('======================')
if (missingFiles.length > 0) {
  console.log('❌ Missing files found:')
  missingFiles.forEach(file => console.log(`   - ${file}`))
} else {
  console.log('✅ All core files present')
}

console.log('\n🚀 RECOMMENDED ACTIONS:')
console.log('=======================')
console.log('1. Clear build cache: Remove-Item -Recurse -Force ".next"')
console.log('2. Clear node modules cache: npm ci')
console.log('3. Restart development server: npm run dev')
console.log('4. Check browser console for client-side errors')
console.log('5. Test API endpoints separately')

console.log('\n🧪 TESTING COMMANDS:')
console.log('====================')
console.log('# Test server accessibility:')
console.log('Invoke-WebRequest -Uri "http://localhost:3000/" -UseBasicParsing')
console.log('')
console.log('# Test API endpoint:')
console.log('$body = @{message="contact a person"; page="/contact"} | ConvertTo-Json')
console.log(
  'Invoke-RestMethod -Uri "http://localhost:3000/api/assistant" -Method POST -ContentType "application/json" -Body $body'
)
