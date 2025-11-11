#!/usr/bin/env node
/**
 * Button Migration Helper Script
 * 
 * This script helps identify all button usages across the app that need
 * to be migrated to the HibachiButton component.
 * 
 * Usage: node scripts/find-buttons.js
 */

const fs = require('fs');
const path = require('path');

const CUSTOMER_APP_DIR = path.join(__dirname, '..', 'apps', 'customer', 'src', 'app');

const buttonPatterns = [
  { pattern: /className="[^"]*btn[^"]*"/g, type: 'Bootstrap Button Classes' },
  { pattern: /className="[^"]*bg-gradient-to-r[^"]*from-red[^"]*"/g, type: 'Inline Gradient Buttons' },
  { pattern: /className="[^"]*border-2[^"]*border-red[^"]*"/g, type: 'Inline Outline Buttons' },
];

function findButtonsInFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const results = [];

  buttonPatterns.forEach(({ pattern, type }) => {
    const matches = content.matchAll(pattern);
    for (const match of matches) {
      const lineNumber = content.substring(0, match.index).split('\n').length;
      results.push({
        file: filePath,
        line: lineNumber,
        type,
        match: match[0],
      });
    }
  });

  return results;
}

function walkDirectory(dir) {
  const files = fs.readdirSync(dir);
  const results = [];

  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      results.push(...walkDirectory(filePath));
    } else if (file.endsWith('.tsx') || file.endsWith('.jsx')) {
      results.push(...findButtonsInFile(filePath));
    }
  });

  return results;
}

function main() {
  console.log('🔍 Scanning for buttons to migrate...\n');

  const results = walkDirectory(CUSTOMER_APP_DIR);

  if (results.length === 0) {
    console.log('✅ No buttons found that need migration!');
    return;
  }

  console.log(`Found ${results.length} button(s) that should be migrated:\n`);

  const grouped = results.reduce((acc, result) => {
    if (!acc[result.type]) acc[result.type] = [];
    acc[result.type].push(result);
    return acc;
  }, {});

  Object.entries(grouped).forEach(([type, items]) => {
    console.log(`\n📌 ${type} (${items.length})`);
    console.log('─'.repeat(80));
    items.forEach(item => {
      const relativePath = path.relative(process.cwd(), item.file);
      console.log(`  ${relativePath}:${item.line}`);
      console.log(`    ${item.match.substring(0, 80)}...`);
    });
  });

  console.log('\n\n💡 Migration Steps:');
  console.log('1. Import: import { HibachiButton } from "@/components/ui/button"');
  console.log('2. Replace <a> with <HibachiButton>');
  console.log('3. Add props: href, variant, size');
  console.log('4. Test the page');
  console.log('\nSee BUTTON_COMPONENT_GUIDE.md for examples!\n');
}

main();
