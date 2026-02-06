/**
 * Recovery Script: Restore original blog content to MDX files
 *
 * This script extracts the 15 original high-quality blog posts from blogContent.md
 * and inserts them into the corresponding MDX files, replacing "No content available"
 */

const fs = require('fs');
const path = require('path');

// Best match for each original post (based on manual review of mapping results)
const CONTENT_MAPPING = [
  {
    original: 1,
    topic: 'Backyard Party Hibachi',
    mdxFile: 'bay-area-backyard-party-hibachi-catering.mdx',
    startMarker: '## 1. Backyard Party Hibachi',
    endMarker: '## 2. Pool Party Hibachi',
  },
  {
    original: 2,
    topic: 'Pool Party Hibachi',
    mdxFile: 'pool-party-hibachi-summer-entertainment-experience.mdx',
    startMarker: '## 2. Pool Party Hibachi',
    endMarker: '## 3. School Party Hibachi',
  },
  {
    original: 3,
    topic: 'School Party Hibachi',
    mdxFile: 'school-party-hibachi-educational-fun-dining.mdx',
    startMarker: '## 3. School Party Hibachi',
    endMarker: '## 4. Corporate Hibachi Events',
  },
  {
    original: 4,
    topic: 'Corporate Hibachi Events',
    mdxFile: 'corporate-hibachi-events-san-jose-team-building.mdx',
    startMarker: '## 4. Corporate Hibachi Events',
    endMarker: '## 5. Vineyard Hibachi Events',
  },
  {
    original: 5,
    topic: 'Vineyard Hibachi Events',
    mdxFile: 'vineyard-hibachi-events-wine-country-japanese-culinary.mdx',
    startMarker: '## 5. Vineyard Hibachi Events',
    endMarker: '## 6. Holiday Party Hibachi',
  },
  {
    original: 6,
    topic: 'Holiday Party Hibachi',
    mdxFile: 'holiday-party-hibachi-seasonal-celebrations-entertainment.mdx',
    startMarker: '## 6. Holiday Party Hibachi',
    endMarker: '## 7. Birthday Hibachi Celebrations',
  },
  {
    original: 7,
    topic: 'Birthday Hibachi Celebrations',
    mdxFile: 'sacramento-birthday-hibachi-age-celebration-entertainment.mdx',
    startMarker: '## 7. Birthday Hibachi Celebrations',
    endMarker: '## 8. Graduation Party Hibachi',
  },
  {
    original: 8,
    topic: 'Graduation Party Hibachi',
    mdxFile: 'bay-area-graduation-hibachi-academic-success-style.mdx',
    startMarker: '## 8. Graduation Party Hibachi',
    endMarker: '## 9. Wedding & Engagement Hibachi',
  },
  {
    original: 9,
    topic: 'Wedding & Engagement Hibachi',
    mdxFile: 'unique-bay-area-wedding-hibachi-reception-dining.mdx',
    startMarker: '## 9. Wedding & Engagement Hibachi',
    endMarker: '## 10. Sports Viewing Party Hibachi',
  },
  {
    original: 10,
    topic: 'Sports Viewing Party Hibachi',
    mdxFile: 'game-day-hibachi-catering-bay-area-sports-party.mdx',
    startMarker: '## 10. Sports Viewing Party Hibachi',
    endMarker: '## 11. Neighborhood Block Party Hibachi',
  },
  {
    original: 11,
    topic: 'Neighborhood Block Party Hibachi',
    mdxFile: 'neighborhood-block-party-hibachi-communities-sacramento.mdx',
    startMarker: '## 11. Neighborhood Block Party Hibachi',
    endMarker: '## 12. Family Reunion Hibachi',
  },
  {
    original: 12,
    topic: 'Family Reunion Hibachi',
    mdxFile: 'stockton-family-reunion-hibachi-multi-generational-dining.mdx',
    startMarker: '## 12. Family Reunion Hibachi',
    endMarker: '## 13. Summer BBQ Alternative Hibachi',
  },
  {
    original: 13,
    topic: 'Summer BBQ Alternative Hibachi',
    mdxFile: 'sacramento-summer-hibachi-ultimate-bbq-alternative.mdx',
    startMarker: '## 13. Summer BBQ Alternative Hibachi',
    endMarker: "## 14. New Year's Eve Hibachi",
  },
  {
    original: 14,
    topic: "New Year's Eve Hibachi",
    mdxFile: 'bay-area-new-years-eve-hibachi-celebrations-2026.mdx',
    startMarker: "## 14. New Year's Eve Hibachi",
    endMarker: '## 15. Seasonal Festival Hibachi',
  },
  {
    original: 15,
    topic: 'Seasonal Festival Hibachi',
    mdxFile: 'california-seasonal-festival-hibachi-mobile-catering.mdx',
    startMarker: '## 15. Seasonal Festival Hibachi',
    endMarker: '## Summary', // Last post ends before summary section
  },
];

const BLOG_CONTENT_FILE = path.join(
  __dirname,
  '../apps/customer/src/data/blogContent.md'
);
const POSTS_DIR = path.join(__dirname, '../apps/customer/content/blog/posts');

console.log('\n========================================');
console.log('  BLOG CONTENT RECOVERY');
console.log('========================================\n');

// Read the original content file
console.log('📖 Reading original content from blogContent.md...');
const originalContent = fs.readFileSync(BLOG_CONTENT_FILE, 'utf8');

// Function to find MDX file path recursively
function findMdxFile(filename) {
  const findRecursive = dir => {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);
      if (stat.isDirectory()) {
        const result = findRecursive(fullPath);
        if (result) return result;
      } else if (file === filename) {
        return fullPath;
      }
    }
    return null;
  };
  return findRecursive(POSTS_DIR);
}

// Process each mapping
let successCount = 0;
let failCount = 0;
const results = [];

console.log(`\nProcessing ${CONTENT_MAPPING.length} blog posts...\n`);

CONTENT_MAPPING.forEach(mapping => {
  console.log(`${'='.repeat(60)}`);
  console.log(`${mapping.original}. ${mapping.topic}`);
  console.log(`${'='.repeat(60)}`);
  console.log(`Target: ${mapping.mdxFile}`);

  try {
    // Extract content from blogContent.md
    const startIdx = originalContent.indexOf(mapping.startMarker);
    const endIdx = originalContent.indexOf(mapping.endMarker);

    if (startIdx === -1) {
      throw new Error(`Start marker not found: ${mapping.startMarker}`);
    }
    if (endIdx === -1) {
      throw new Error(`End marker not found: ${mapping.endMarker}`);
    }

    // Extract the section between markers
    let section = originalContent.substring(startIdx, endIdx).trim();

    // Remove the section header (e.g., "## 1. Backyard Party Hibachi")
    section = section.replace(/^##\s+\d+\.\s+.+\n+/, '').trim();

    // Skip metadata lines (Title, Meta Description, Keywords)
    const contentMarkerIndex = section.indexOf('**Content:**');
    if (contentMarkerIndex !== -1) {
      section = section
        .substring(contentMarkerIndex + '**Content:**'.length)
        .trim();
    }

    // Remove the divider line at the end if present
    section = section.replace(/\n+---\s*$/, '').trim();

    console.log(`✅ Extracted ${section.length} characters of content`);

    // Find the MDX file
    const mdxPath = findMdxFile(mapping.mdxFile);
    if (!mdxPath) {
      throw new Error(`MDX file not found: ${mapping.mdxFile}`);
    }

    console.log(`📁 Found: ${mdxPath}`);

    // Read the MDX file
    const mdxContent = fs.readFileSync(mdxPath, 'utf8');

    // Split frontmatter and content
    const frontmatterMatch = mdxContent.match(
      /^---\n([\s\S]+?)\n---\n([\s\S]*)$/
    );
    if (!frontmatterMatch) {
      throw new Error('Invalid MDX format: No frontmatter found');
    }

    const frontmatter = frontmatterMatch[1];
    const oldContent = frontmatterMatch[2].trim();

    // Check if it has placeholder content
    if (oldContent === 'No content available') {
      console.log('✅ Confirmed placeholder content found');
    } else {
      console.log(
        `⚠️  Warning: Content is not placeholder (${oldContent.substring(0, 50)}...)`
      );
    }

    // Create new MDX content
    const newMdxContent = `---\n${frontmatter}\n---\n\n${section}`;

    // Write the updated file
    fs.writeFileSync(mdxPath, newMdxContent, 'utf8');

    console.log('✅ SUCCESS: Content updated!\n');
    successCount++;
    results.push({
      number: mapping.original,
      topic: mapping.topic,
      status: 'SUCCESS',
      file: mapping.mdxFile,
      contentLength: section.length,
    });
  } catch (error) {
    console.log(`❌ FAILED: ${error.message}\n`);
    failCount++;
    results.push({
      number: mapping.original,
      topic: mapping.topic,
      status: 'FAILED',
      file: mapping.mdxFile,
      error: error.message,
    });
  }
});

// Summary
console.log('\n========================================');
console.log('  RECOVERY SUMMARY');
console.log('========================================\n');

console.log(`Total posts: ${CONTENT_MAPPING.length}`);
console.log(`✅ Successful: ${successCount}`);
console.log(`❌ Failed: ${failCount}`);

console.log('\nDetailed Results:\n');
results.forEach(result => {
  const icon = result.status === 'SUCCESS' ? '✅' : '❌';
  console.log(`${icon} ${result.number}. ${result.topic}`);
  console.log(`   File: ${result.file}`);
  if (result.status === 'SUCCESS') {
    console.log(`   Content: ${result.contentLength} characters`);
  } else {
    console.log(`   Error: ${result.error}`);
  }
  console.log('');
});

// Save results to JSON
const resultsFile = path.join(__dirname, 'recovery-results.json');
fs.writeFileSync(
  resultsFile,
  JSON.stringify(
    {
      timestamp: new Date().toISOString(),
      total: CONTENT_MAPPING.length,
      successful: successCount,
      failed: failCount,
      results,
    },
    null,
    2
  )
);

console.log(`\n📊 Results saved to: ${resultsFile}`);

if (successCount === CONTENT_MAPPING.length) {
  console.log('\n🎉 SUCCESS! All original content has been restored!');
  console.log('\nNext steps:');
  console.log('1. Run: npm run dev');
  console.log('2. Visit: http://localhost:3000/blog');
  console.log('3. Verify posts display with original content');
} else {
  console.log('\n⚠️  Some posts failed to recover. Review errors above.');
}
