#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BASELINE_DIR = './verification/baseline';
const FRONTEND_DIR = './myhibachi-frontend';

// Ensure baseline directories exist
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

ensureDir(`${BASELINE_DIR}/screens`);
ensureDir(`${BASELINE_DIR}/dom`);
ensureDir(`${BASELINE_DIR}/assets`);
ensureDir(`${BASELINE_DIR}/api`);

// 1. Route Discovery from App Router
function discoverRoutes() {
  console.log('🔍 Discovering routes from App Router...');
  
  const routes = [];
  const appDir = path.join(FRONTEND_DIR, 'src/app');
  
  function walkDir(dir, currentPath = '') {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        // Skip API routes for now
        if (item === 'api') continue;
        
        // Check for page.tsx in this directory
        const pagePath = path.join(fullPath, 'page.tsx');
        if (fs.existsSync(pagePath)) {
          const routePath = currentPath + '/' + item;
          routes.push(routePath === '/page' ? '/' : routePath);
        }
        
        // Recurse into subdirectories
        walkDir(fullPath, currentPath + '/' + item);
      }
    }
  }
  
  // Check for root page
  if (fs.existsSync(path.join(appDir, 'page.tsx'))) {
    routes.push('/');
  }
  
  walkDir(appDir);
  
  // Clean up routes
  const cleanRoutes = routes
    .map(route => route.replace(/\/page$/, ''))
    .filter(route => !route.includes('[') && !route.includes('('))
    .sort();
    
  console.log(`Found ${cleanRoutes.length} routes:`, cleanRoutes);
  
  fs.writeFileSync(
    `${BASELINE_DIR}/discovered-routes.json`,
    JSON.stringify({ routes: cleanRoutes, timestamp: new Date().toISOString() }, null, 2)
  );
  
  return cleanRoutes;
}

// 2. API Route Discovery
function discoverApiRoutes() {
  console.log('🔍 Discovering API routes...');
  
  const apiRoutes = [];
  const apiDir = path.join(FRONTEND_DIR, 'src/app/api');
  
  function walkApiDir(dir, currentPath = '') {
    if (!fs.existsSync(dir)) return;
    
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        walkApiDir(fullPath, currentPath + '/' + item);
      } else if (item === 'route.ts' || item === 'route.js') {
        const routePath = '/api' + currentPath;
        apiRoutes.push(routePath);
      }
    }
  }
  
  walkApiDir(apiDir);
  
  console.log(`Found ${apiRoutes.length} API routes:`, apiRoutes);
  
  fs.writeFileSync(
    `${BASELINE_DIR}/api-routes.json`,
    JSON.stringify({ apiRoutes, timestamp: new Date().toISOString() }, null, 2)
  );
  
  return apiRoutes;
}

// 3. Asset Baseline
function createAssetBaseline() {
  console.log('📸 Creating asset baseline...');
  
  const assets = {
    css: [],
    images: [],
    fonts: [],
    icons: []
  };
  
  // Scan public directory
  const publicDir = path.join(FRONTEND_DIR, 'public');
  if (fs.existsSync(publicDir)) {
    function scanAssets(dir, type, extensions) {
      if (!fs.existsSync(dir)) return;
      
      const items = fs.readdirSync(dir, { withFileTypes: true });
      for (const item of items) {
        if (item.isFile()) {
          const ext = path.extname(item.name).toLowerCase();
          if (extensions.includes(ext)) {
            const relativePath = path.relative(publicDir, path.join(dir, item.name));
            assets[type].push('/' + relativePath.replace(/\\/g, '/'));
          }
        } else if (item.isDirectory()) {
          scanAssets(path.join(dir, item.name), type, extensions);
        }
      }
    }
    
    scanAssets(publicDir, 'images', ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']);
    scanAssets(publicDir, 'fonts', ['.woff', '.woff2', '.ttf', '.otf']);
    scanAssets(publicDir, 'icons', ['.ico', '.png']);
  }
  
  // Hash main files
  const mainFiles = [
    path.join(FRONTEND_DIR, 'tailwind.config.ts'),
    path.join(FRONTEND_DIR, 'next.config.js'),
    path.join(FRONTEND_DIR, 'package.json')
  ];
  
  const hashes = {};
  for (const file of mainFiles) {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const hash = require('crypto').createHash('md5').update(content).digest('hex');
      hashes[path.basename(file)] = hash;
    }
  }
  
  const baseline = {
    assets,
    configHashes: hashes,
    timestamp: new Date().toISOString()
  };
  
  fs.writeFileSync(`${BASELINE_DIR}/asset-baseline.json`, JSON.stringify(baseline, null, 2));
  
  return baseline;
}

// 4. Build Current State
function buildCurrentState() {
  console.log('🏗️ Building current frontend state...');
  
  try {
    process.chdir(FRONTEND_DIR);
    
    // Install dependencies if needed
    if (!fs.existsSync('node_modules')) {
      console.log('Installing dependencies...');
      execSync('npm install', { stdio: 'inherit' });
    }
    
    // Build the project
    console.log('Building Next.js project...');
    execSync('npm run build', { stdio: 'inherit' });
    
    process.chdir('..');
    return true;
  } catch (error) {
    console.error('Build failed:', error.message);
    process.chdir('..');
    return false;
  }
}

// Main execution
async function main() {
  console.log('🚀 Starting Golden Baseline Creation...');
  
  // 1. Discover routes and APIs
  const routes = discoverRoutes();
  const apiRoutes = discoverApiRoutes();
  
  // 2. Create asset baseline
  const assetBaseline = createAssetBaseline();
  
  // 3. Build current state
  const buildSuccess = buildCurrentState();
  
  // 4. Create summary
  const summary = {
    created: new Date().toISOString(),
    routes: routes.length,
    apiRoutes: apiRoutes.length,
    assets: {
      images: assetBaseline.assets.images.length,
      fonts: assetBaseline.assets.fonts.length,
      icons: assetBaseline.assets.icons.length
    },
    buildSuccess,
    nextSteps: [
      'Run Playwright for visual baseline',
      'Extract DOM snapshots',
      'Run Lighthouse audits',
      'Create link map'
    ]
  };
  
  fs.writeFileSync(`${BASELINE_DIR}/baseline-summary.json`, JSON.stringify(summary, null, 2));
  
  console.log('✅ Golden Baseline Creation Complete!');
  console.log(`📊 Summary: ${routes.length} routes, ${apiRoutes.length} API routes, Build: ${buildSuccess ? 'SUCCESS' : 'FAILED'}`);
  
  return summary;
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { discoverRoutes, discoverApiRoutes, createAssetBaseline };
