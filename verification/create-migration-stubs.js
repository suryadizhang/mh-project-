#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Load the migration analysis
const analysisPath = './verification/api-migration-analysis.json';
const analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf8'));

const routesToMigrate = analysis.categories.MIGRATE_TO_BACKEND;

// Generate 410 Gone stub template
function generate410Stub(routePath) {
  const apiPath = routePath.replace('myhibachi-frontend/src/app/api', '');
  const cleanPath = apiPath.replace('/route.ts', '');
  
  // Map to backend equivalent
  let backendPath;
  if (cleanPath.includes('/payments/') || cleanPath.includes('/stripe/') || cleanPath.includes('/webhooks/')) {
    backendPath = `/api/stripe${cleanPath}`;
  } else if (cleanPath.includes('/v1/')) {
    backendPath = cleanPath.replace('/v1/', '/api/v1/');
  } else {
    backendPath = `/api${cleanPath}`;
  }
  
  return `import { NextResponse } from 'next/server'

/**
 * ⚠️  MIGRATED TO BACKEND ⚠️
 * 
 * This endpoint has been migrated to the FastAPI backend.
 * 
 * OLD: ${cleanPath}
 * NEW: \${NEXT_PUBLIC_API_URL}${backendPath}
 * 
 * This stub returns HTTP 410 Gone to indicate permanent migration.
 * Update your frontend code to use the new backend endpoint.
 * 
 * Migration Date: ${new Date().toISOString()}
 * Backend Route: FastAPI backend - ${backendPath}
 */

export async function GET() {
  return NextResponse.json(
    {
      error: "Endpoint migrated to backend",
      migration: {
        from: "${cleanPath}",
        to: \`\${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${backendPath}\`,
        status: "MIGRATED",
        date: new Date().toISOString(),
        instructions: "Update frontend to use backend API endpoint"
      }
    },
    { status: 410 }
  )
}

export async function POST() {
  return NextResponse.json(
    {
      error: "Endpoint migrated to backend",
      migration: {
        from: "${cleanPath}",
        to: \`\${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${backendPath}\`,
        status: "MIGRATED",
        date: new Date().toISOString(),
        instructions: "Update frontend to use backend API endpoint"
      }
    },
    { status: 410 }
  )
}

export async function PUT() {
  return NextResponse.json(
    {
      error: "Endpoint migrated to backend",
      migration: {
        from: "${cleanPath}",
        to: \`\${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${backendPath}\`,
        status: "MIGRATED",
        date: new Date().toISOString(),
        instructions: "Update frontend to use backend API endpoint"
      }
    },
    { status: 410 }
  )
}

export async function DELETE() {
  return NextResponse.json(
    {
      error: "Endpoint migrated to backend",
      migration: {
        from: "${cleanPath}",
        to: \`\${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${backendPath}\`,
        status: "MIGRATED",
        date: new Date().toISOString(),
        instructions: "Update frontend to use backend API endpoint"
      }
    },
    { status: 410 }
  )
}
`;
}

function createMigrationStubs() {
  console.log('🚀 Creating 410 Gone stubs for migrated routes...\n');
  
  const migrations = [];
  
  for (const route of routesToMigrate) {
    try {
      const fullPath = route.path.replace(/\\/g, '/');
      const apiPath = fullPath.replace('myhibachi-frontend/src/app/api', '');
      const cleanPath = apiPath.replace('/route.ts', '');
      
      // Create backup of original file
      const backupPath = fullPath + '.backup';
      if (fs.existsSync(fullPath) && !fs.existsSync(backupPath)) {
        fs.copyFileSync(fullPath, backupPath);
        console.log(`📦 Backed up: ${fullPath} → ${backupPath}`);
      }
      
      // Generate 410 stub
      const stubContent = generate410Stub(fullPath);
      fs.writeFileSync(fullPath, stubContent);
      
      console.log(`✅ Created 410 stub: ${cleanPath}`);
      
      migrations.push({
        from: cleanPath,
        to: cleanPath.includes('/payments/') || cleanPath.includes('/stripe/') 
          ? `/api/stripe${cleanPath}` 
          : cleanPath.replace('/v1/', '/api/v1/'),
        file: fullPath,
        backup: backupPath
      });
      
    } catch (error) {
      console.error(`❌ Failed to create stub for ${route.path}:`, error.message);
    }
  }
  
  // Save migration map
  const migrationMap = {
    timestamp: new Date().toISOString(),
    migrations,
    instructions: [
      "Update frontend fetch() calls to use backend URLs",
      "Test all affected functionality",
      "Update Stripe webhook configurations",
      "Deploy backend before removing stubs"
    ]
  };
  
  fs.writeFileSync('./verification/migration-map.json', JSON.stringify(migrationMap, null, 2));
  
  console.log(`\n💾 Migration map saved to verification/migration-map.json`);
  console.log(`📊 Created ${migrations.length} migration stubs`);
  
  return migrationMap;
}

function updateFrontendFetchCalls() {
  console.log('\n🔗 Updating frontend fetch calls to use backend URLs...\n');
  
  const srcDir = './myhibachi-frontend/src';
  const updatedFiles = [];
  
  function updateFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      let updated = content;
      let hasChanges = false;
      
      // Update fetch calls for migrated endpoints
      for (const route of routesToMigrate) {
        const apiPath = route.path.replace('myhibachi-frontend/src/app/api', '');
        const cleanPath = apiPath.replace('/route.ts', '');
        
        // Pattern: fetch('/api/...') or fetch("/api/...")
        const escapedPath = cleanPath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const patterns = [
          new RegExp(`fetch\\s*\\(\\s*['"]${escapedPath}['"]`, 'g'),
          new RegExp(`fetch\\s*\\(\\s*\`${escapedPath}\``, 'g')
        ];
        
        let backendPath;
        if (cleanPath.includes('/payments/') || cleanPath.includes('/stripe/') || cleanPath.includes('/webhooks/')) {
          backendPath = `/api/stripe${cleanPath}`;
        } else if (cleanPath.includes('/v1/')) {
          backendPath = cleanPath.replace('/v1/', '/api/v1/');
        } else {
          backendPath = `/api${cleanPath}`;
        }
        
        for (const pattern of patterns) {
          const replacement = `fetch(\`\${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${backendPath}\``;
          const newContent = updated.replace(pattern, replacement);
          if (newContent !== updated) {
            updated = newContent;
            hasChanges = true;
            console.log(`  ✅ Updated: ${cleanPath} → ${backendPath}`);
          }
        }
      }
      
      if (hasChanges) {
        fs.writeFileSync(filePath, updated);
        updatedFiles.push(filePath);
      }
      
    } catch (error) {
      console.error(`❌ Failed to update ${filePath}:`, error.message);
    }
  }
  
  function walkDirectory(dir) {
    if (!fs.existsSync(dir)) return;
    
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !item.includes('node_modules') && !item.includes('.next')) {
        walkDirectory(fullPath);
      } else if (item.endsWith('.ts') || item.endsWith('.tsx') || item.endsWith('.js') || item.endsWith('.jsx')) {
        updateFile(fullPath);
      }
    }
  }
  
  walkDirectory(srcDir);
  
  console.log(`\n📊 Updated ${updatedFiles.length} files with new backend URLs`);
  return updatedFiles;
}

function main() {
  console.log('🚀 Starting API Migration to Backend...\n');
  
  // Create 410 stubs
  const migrationMap = createMigrationStubs();
  
  // Update frontend fetch calls
  const updatedFiles = updateFrontendFetchCalls();
  
  console.log('\n✅ API Migration Complete!');
  console.log(`📊 Summary: ${migrationMap.migrations.length} routes migrated, ${updatedFiles.length} files updated`);
  console.log(`🔗 Next steps: Test functionality, update webhook configs, deploy backend`);
  
  return { migrationMap, updatedFiles };
}

if (require.main === module) {
  main();
}

module.exports = { createMigrationStubs, updateFrontendFetchCalls };
