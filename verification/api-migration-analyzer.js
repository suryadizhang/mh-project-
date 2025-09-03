#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const API_DIR = './myhibachi-frontend/src/app/api';

// Categories of API routes
const routeCategories = {
  MIGRATE_TO_BACKEND: [],
  ALREADY_MIGRATED: [],
  KEEP_IN_FRONTEND: [],
  UNKNOWN: []
};

// Keywords that indicate backend functionality
const backendKeywords = [
  'stripe', 'webhook', 'secret', 'process.env.STRIPE_SECRET',
  'database', 'sql', 'prisma', 'mongoose',
  'payment', 'billing', 'invoice', 'refund',
  'admin', 'authentication', 'jwt',
  'email', 'smtp', 'sendgrid', 'nodemailer'
];

// Keywords that indicate frontend-appropriate functionality
const frontendKeywords = [
  'contact', 'feedback', 'static', 'config',
  'healthcheck', 'ping', 'status'
];

// Keywords for already migrated routes
const migratedKeywords = [
  'MIGRATED TO BACKEND', '410 Gone', 'HTTP 410',
  'endpoint migrated', 'stub returns'
];

function analyzeRoute(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const relativePath = path.relative('.', filePath);
    
    // Check if already migrated
    const isMigrated = migratedKeywords.some(keyword => 
      content.toLowerCase().includes(keyword.toLowerCase())
    );
    
    if (isMigrated) {
      return {
        category: 'ALREADY_MIGRATED',
        path: relativePath,
        reason: 'Contains migration stub markers'
      };
    }
    
    // Check for backend functionality
    const hasBackendFunctionality = backendKeywords.some(keyword => 
      content.toLowerCase().includes(keyword.toLowerCase())
    );
    
    // Check for frontend-appropriate functionality
    const hasFrontendFunctionality = frontendKeywords.some(keyword => 
      content.toLowerCase().includes(keyword.toLowerCase())
    );
    
    // Check for actual logic vs. simple passthrough
    const hasComplexLogic = content.includes('await') && 
                           (content.includes('database') || 
                            content.includes('process.env') ||
                            content.includes('crypto') ||
                            content.includes('bcrypt') ||
                            content.length > 1000);
    
    if (hasBackendFunctionality || hasComplexLogic) {
      return {
        category: 'MIGRATE_TO_BACKEND',
        path: relativePath,
        reason: hasBackendFunctionality ? 'Contains backend keywords' : 'Complex server logic'
      };
    }
    
    if (hasFrontendFunctionality) {
      return {
        category: 'KEEP_IN_FRONTEND',
        path: relativePath,
        reason: 'Simple frontend-appropriate functionality'
      };
    }
    
    return {
      category: 'UNKNOWN',
      path: relativePath,
      reason: 'Needs manual review',
      size: content.length
    };
    
  } catch (error) {
    return {
      category: 'UNKNOWN',
      path: filePath,
      reason: `Error reading file: ${error.message}`
    };
  }
}

function walkDirectory(dir) {
  if (!fs.existsSync(dir)) {
    console.log(`Directory ${dir} does not exist`);
    return;
  }
  
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      walkDirectory(fullPath);
    } else if (item === 'route.ts' || item === 'route.js') {
      const analysis = analyzeRoute(fullPath);
      routeCategories[analysis.category].push(analysis);
    }
  }
}

function generateMigrationPlan() {
  console.log('🔍 Analyzing API routes for migration plan...\n');
  
  walkDirectory(API_DIR);
  
  console.log('📊 ANALYSIS RESULTS:\n');
  
  console.log(`✅ ALREADY MIGRATED (${routeCategories.ALREADY_MIGRATED.length}):`);
  routeCategories.ALREADY_MIGRATED.forEach(route => {
    console.log(`  • ${route.path} - ${route.reason}`);
  });
  
  console.log(`\n🚀 NEEDS MIGRATION TO BACKEND (${routeCategories.MIGRATE_TO_BACKEND.length}):`);
  routeCategories.MIGRATE_TO_BACKEND.forEach(route => {
    console.log(`  • ${route.path} - ${route.reason}`);
  });
  
  console.log(`\n🏠 KEEP IN FRONTEND (${routeCategories.KEEP_IN_FRONTEND.length}):`);
  routeCategories.KEEP_IN_FRONTEND.forEach(route => {
    console.log(`  • ${route.path} - ${route.reason}`);
  });
  
  console.log(`\n❓ NEEDS MANUAL REVIEW (${routeCategories.UNKNOWN.length}):`);
  routeCategories.UNKNOWN.forEach(route => {
    console.log(`  • ${route.path} - ${route.reason} (${route.size || 0} bytes)`);
  });
  
  // Generate plan for link rewiring
  console.log(`\n🔗 FRONTEND LINK REWIRING PLAN:\n`);
  
  const toMigrate = routeCategories.MIGRATE_TO_BACKEND;
  const alreadyMigrated = routeCategories.ALREADY_MIGRATED;
  
  const allNeedingRewire = [...toMigrate, ...alreadyMigrated];
  
  console.log('Frontend fetch() calls that need updating to backend URLs:');
  allNeedingRewire.forEach(route => {
    const apiPath = route.path.replace('myhibachi-frontend/src/app/api', '');
    const backendPath = apiPath.replace('/v1/', '/api/stripe/v1/').replace('/api/', '/api/');
    console.log(`  fetch('${apiPath}') → fetch('${process.env.NEXT_PUBLIC_API_URL || '${NEXT_PUBLIC_API_URL}'}${backendPath}')`);
  });
  
  // Save analysis to file
  const analysis = {
    timestamp: new Date().toISOString(),
    categories: routeCategories,
    summary: {
      total: Object.values(routeCategories).reduce((sum, arr) => sum + arr.length, 0),
      alreadyMigrated: routeCategories.ALREADY_MIGRATED.length,
      needsMigration: routeCategories.MIGRATE_TO_BACKEND.length,
      keepInFrontend: routeCategories.KEEP_IN_FRONTEND.length,
      needsReview: routeCategories.UNKNOWN.length
    }
  };
  
  fs.writeFileSync('./verification/api-migration-analysis.json', JSON.stringify(analysis, null, 2));
  
  console.log(`\n💾 Analysis saved to verification/api-migration-analysis.json`);
  
  return analysis;
}

if (require.main === module) {
  generateMigrationPlan();
}

module.exports = { generateMigrationPlan };
