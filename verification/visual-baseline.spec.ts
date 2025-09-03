import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const BASELINE_DIR = './verification/baseline';
const ROUTES_FILE = path.join(BASELINE_DIR, 'discovered-routes.json');

// Load discovered routes
const routesData = JSON.parse(fs.readFileSync(ROUTES_FILE, 'utf8'));
const routes = routesData.routes;

const breakpoints = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 720 }
];

test.describe('Visual Baseline Creation', () => {
  for (const route of routes) {
    for (const bp of breakpoints) {
      test(`${route} - ${bp.name}`, async ({ page }) => {
        // Set viewport
        await page.setViewportSize({ width: bp.width, height: bp.height });
        
        try {
          // Navigate to route
          await page.goto(`http://localhost:3000${route}`, {
            waitUntil: 'networkidle',
            timeout: 30000
          });
          
          // Wait for any loading to complete
          await page.waitForTimeout(2000);
          
          // Hide dynamic elements that might cause flaky tests
          await page.addStyleTag({
            content: `
              [data-testid="timestamp"],
              .timestamp,
              .current-time,
              .chat-widget,
              .analytics-tag { opacity: 0 !important; }
            `
          });
          
          // Take screenshot
          const filename = `${route.replace(/\//g, '_') || 'home'}_${bp.name}.png`;
          await page.screenshot({
            path: path.join(BASELINE_DIR, 'screens', filename),
            fullPage: true
          });
          
          // Save DOM snapshot
          const domContent = await page.content();
          const cleanDom = domContent
            .replace(/data-reactroot="[^"]*"/g, '')
            .replace(/data-react-[^=]*="[^"]*"/g, '')
            .replace(/<!--.*?-->/gs, '')
            .replace(/\s+/g, ' ');
            
          fs.writeFileSync(
            path.join(BASELINE_DIR, 'dom', `${filename.replace('.png', '.html')}`),
            cleanDom
          );
          
          // Extract metadata
          const title = await page.title();
          const description = await page.getAttribute('meta[name="description"]', 'content');
          const canonical = await page.getAttribute('link[rel="canonical"]', 'href');
          
          const metadata = {
            title,
            description,
            canonical,
            url: route,
            viewport: bp,
            timestamp: new Date().toISOString()
          };
          
          fs.writeFileSync(
            path.join(BASELINE_DIR, 'dom', `${filename.replace('.png', '.meta.json')}`),
            JSON.stringify(metadata, null, 2)
          );
          
        } catch (error) {
          console.error(`Failed to capture ${route} at ${bp.name}:`, error.message);
          // Continue with other routes
        }
      });
    }
  }
});
