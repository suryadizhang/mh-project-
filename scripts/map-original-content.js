/**
 * Maps original 15 blog posts from blogContent.md to MDX files
 * This helps identify which MDX files should get the original high-quality content
 */

const fs = require('fs');
const path = require('path');

// The 15 original blog post topics from blogContent.md
const originalPosts = [
  {
    number: 1,
    topic: 'Backyard Party Hibachi',
    title: 'Transform Your Bay Area Backyard Party with Professional Hibachi Catering',
    keywords: ['backyard', 'bay area', 'backyard party'],
    location: 'Bay Area'
  },
  {
    number: 2,
    topic: 'Pool Party Hibachi',
    title: 'Poolside Hibachi Catering: The Ultimate Summer Party Experience in Sacramento',
    keywords: ['pool party', 'poolside', 'sacramento', 'summer'],
    location: 'Sacramento'
  },
  {
    number: 3,
    topic: 'School Party Hibachi',
    title: 'Safe & Fun School Hibachi Catering for Bay Area Educational Events',
    keywords: ['school', 'educational', 'bay area'],
    location: 'Bay Area'
  },
  {
    number: 4,
    topic: 'Corporate Hibachi Events',
    title: 'San Jose Corporate Hibachi Catering: Boost Team Morale with Interactive Dining',
    keywords: ['corporate', 'san jose', 'office', 'team building'],
    location: 'San Jose'
  },
  {
    number: 5,
    topic: 'Vineyard Hibachi Events',
    title: 'Luxury Vineyard Hibachi Catering: Wine Country Meets Japanese Excellence',
    keywords: ['vineyard', 'wine country', 'napa', 'winery'],
    location: 'Wine Country'
  },
  {
    number: 6,
    topic: 'Holiday Party Hibachi',
    title: 'Festive Holiday Hibachi Catering: Make Your Bay Area Celebration Unforgettable',
    keywords: ['holiday', 'christmas', 'festive', 'bay area'],
    location: 'Bay Area'
  },
  {
    number: 7,
    topic: 'Birthday Hibachi Celebrations',
    title: 'Sacramento Birthday Hibachi: Transform Any Age Celebration into Entertainment',
    keywords: ['birthday', 'sacramento', 'celebration'],
    location: 'Sacramento'
  },
  {
    number: 8,
    topic: 'Graduation Party Hibachi',
    title: 'Bay Area Graduation Hibachi: Celebrate Academic Success with Style',
    keywords: ['graduation', 'academic', 'bay area'],
    location: 'Bay Area'
  },
  {
    number: 9,
    topic: 'Wedding & Engagement Hibachi',
    title: 'Unique Bay Area Wedding Hibachi: Interactive Reception Dining Experience',
    keywords: ['wedding', 'engagement', 'reception', 'bay area'],
    location: 'Bay Area'
  },
  {
    number: 10,
    topic: 'Sports Viewing Party Hibachi',
    title: 'Game Day Hibachi Catering: Elevate Your Bay Area Sports Party Experience',
    keywords: ['sports', 'game day', 'super bowl', 'bay area'],
    location: 'Bay Area'
  },
  {
    number: 11,
    topic: 'Neighborhood Block Party Hibachi',
    title: 'Neighborhood Block Party Hibachi: Bring Communities Together in Sacramento',
    keywords: ['neighborhood', 'block party', 'community', 'sacramento'],
    location: 'Sacramento'
  },
  {
    number: 12,
    topic: 'Family Reunion Hibachi',
    title: 'Stockton Family Reunion Hibachi: Multi-Generational Dining That Unites',
    keywords: ['family reunion', 'stockton', 'multi-generational'],
    location: 'Stockton'
  },
  {
    number: 13,
    topic: 'Summer BBQ Alternative Hibachi',
    title: 'Beat the Heat: Sacramento Summer Hibachi as Your Ultimate BBQ Alternative',
    keywords: ['summer', 'bbq', 'alternative', 'sacramento'],
    location: 'Sacramento'
  },
  {
    number: 14,
    topic: "New Year's Eve Hibachi",
    title: "Ring in 2026 with Style: Bay Area New Year's Eve Hibachi Celebrations",
    keywords: ['new year', 'nye', 'countdown', 'bay area'],
    location: 'Bay Area'
  },
  {
    number: 15,
    topic: 'Seasonal Festival Hibachi',
    title: 'California Seasonal Festival Hibachi: Mobile Catering for Community Events',
    keywords: ['festival', 'seasonal', 'california', 'community'],
    location: 'California'
  }
];

// Get all MDX files
const postsDir = path.join(__dirname, '../apps/customer/content/blog/posts');
const mdxFiles = [];

function getAllMdxFiles(dir) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      getAllMdxFiles(fullPath);
    } else if (file.endsWith('.mdx')) {
      mdxFiles.push({
        name: file,
        path: fullPath,
        slug: file.replace('.mdx', '')
      });
    }
  });
}

getAllMdxFiles(postsDir);

console.log('\n========================================');
console.log('  ORIGINAL CONTENT MAPPING');
console.log('========================================\n');

console.log(`Found ${mdxFiles.length} MDX files`);
console.log(`Mapping ${originalPosts.length} original posts\n`);

const matches = [];

originalPosts.forEach(original => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Original Post #${original.number}: ${original.topic}`);
  console.log(`${'='.repeat(60)}`);
  console.log(`Title: ${original.title}`);
  console.log(`Keywords: ${original.keywords.join(', ')}`);
  console.log(`Location: ${original.location}\n`);

  // Find matching MDX files
  const potentialMatches = mdxFiles.filter(file => {
    const slug = file.slug.toLowerCase();
    // Check if keywords appear in slug
    return original.keywords.some(keyword => 
      slug.includes(keyword.toLowerCase().replace(/\s+/g, '-'))
    );
  });

  if (potentialMatches.length > 0) {
    console.log(`✅ Found ${potentialMatches.length} potential match(es):\n`);
    potentialMatches.forEach((match, idx) => {
      console.log(`   ${idx + 1}. ${match.name}`);
      
      // Read the file to check title
      const content = fs.readFileSync(match.path, 'utf8');
      const titleMatch = content.match(/title:\s*["'](.+)["']/);
      if (titleMatch) {
        console.log(`      Title: ${titleMatch[1]}`);
      }
      
      matches.push({
        original: original.number,
        originalTopic: original.topic,
        mdxFile: match.name,
        mdxPath: match.path,
        mdxTitle: titleMatch ? titleMatch[1] : 'Unknown'
      });
    });
  } else {
    console.log(`⚠️  No direct match found. Manual review needed.`);
  }
});

console.log('\n\n========================================');
console.log('  MAPPING SUMMARY');
console.log('========================================\n');

// Group by original post
const grouped = {};
originalPosts.forEach(original => {
  grouped[original.number] = {
    topic: original.topic,
    matches: matches.filter(m => m.original === original.number)
  };
});

Object.keys(grouped).forEach(num => {
  const data = grouped[num];
  console.log(`\n${num}. ${data.topic}`);
  if (data.matches.length > 0) {
    data.matches.forEach(match => {
      console.log(`   ✅ ${match.mdxFile}`);
    });
  } else {
    console.log(`   ⚠️  NO MATCH - Needs manual mapping`);
  }
});

// Save mapping to JSON file
const mappingFile = path.join(__dirname, 'original-content-mapping.json');
fs.writeFileSync(mappingFile, JSON.stringify({
  generatedAt: new Date().toISOString(),
  originalPosts: originalPosts.length,
  mdxFiles: mdxFiles.length,
  matches: matches,
  grouped: grouped
}, null, 2));

console.log(`\n\n✅ Mapping saved to: ${mappingFile}`);
console.log('\nNext steps:');
console.log('1. Review the mapping above');
console.log('2. Manually verify any ambiguous matches');
console.log('3. Run the content recovery script to copy original content to MDX files');
