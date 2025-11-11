/**
 * Blog Migration Script: TypeScript Array → MDX Files
 * 
 * This script converts 84 blog posts from blogPosts.ts to individual MDX files.
 * 
 * Features:
 * - Extracts all frontmatter fields
 * - Creates YAML frontmatter blocks
 * - Organizes by date (YYYY/MM directory structure)
 * - Generates Markdown content
 * - Preserves all metadata
 * 
 * Usage:
 *   npx tsx scripts/migrate-to-mdx.ts
 *   npx tsx scripts/migrate-to-mdx.ts --test  (5 posts only)
 *   npx tsx scripts/migrate-to-mdx.ts --force  (overwrite existing)
 * 
 * @example
 * Before: apps/customer/src/data/blogPosts.ts (2255 KB, 84 posts)
 * After:  content/blog/posts/YYYY/MM/slug.mdx (84 files, ~30KB each)
 */

import { mkdir, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { pathToFileURL } from 'url';

// Import blog posts from existing data
const blogPostsPath = join(process.cwd(), 'apps/customer/src/data/blogPosts.ts');

interface BlogPost {
  id: number | string;
  title: string;
  slug: string;
  excerpt: string;
  content?: string;
  metaDescription: string;
  keywords: string[];
  author: string;
  date: string;
  readTime: string;
  category: string;
  serviceArea: string;
  eventType: string;
  featured?: boolean;
  seasonal?: boolean;
  image?: string;
  imageAlt?: string;
}

/**
 * Parse date string to get year and month
 */
function parseDate(dateStr: string): { year: string; month: string } {
  // Handle various date formats: "August 14, 2025", "2025-08-14", etc.
  const date = new Date(dateStr);
  
  if (isNaN(date.getTime())) {
    // Fallback to current date if parsing fails
    console.warn(`⚠️  Invalid date format: "${dateStr}", using current date`);
    const now = new Date();
    return {
      year: now.getFullYear().toString(),
      month: (now.getMonth() + 1).toString().padStart(2, '0')
    };
  }
  
  return {
    year: date.getFullYear().toString(),
    month: (date.getMonth() + 1).toString().padStart(2, '0')
  };
}

/**
 * Convert date to ISO format (YYYY-MM-DD)
 */
function toISODate(dateStr: string): string {
  const date = new Date(dateStr);
  
  if (isNaN(date.getTime())) {
    console.warn(`⚠️  Invalid date: "${dateStr}"`);
    return new Date().toISOString().split('T')[0];
  }
  
  return date.toISOString().split('T')[0];
}

/**
 * Generate frontmatter YAML block
 */
function generateFrontmatter(post: BlogPost): string {
  const lines: string[] = ['---'];
  
  // Required fields
  lines.push(`id: '${post.id}'`);
  lines.push(`title: '${post.title.replace(/'/g, "''")}'`);
  lines.push(`slug: '${post.slug}'`);
  lines.push(`excerpt: '${post.excerpt.replace(/'/g, "''")}'`);
  lines.push(`author: '${post.author}'`);
  lines.push(`date: '${toISODate(post.date)}'`);
  lines.push(`category: '${post.category}'`);
  lines.push(`serviceArea: '${post.serviceArea}'`);
  lines.push(`eventType: '${post.eventType}'`);
  
  // Keywords array
  if (post.keywords && post.keywords.length > 0) {
    lines.push('keywords:');
    post.keywords.forEach(keyword => {
      lines.push(`  - '${keyword.replace(/'/g, "''")}'`);
    });
  }
  
  // Optional fields
  lines.push(`readTime: '${post.readTime}'`);
  
  if (post.featured !== undefined) {
    lines.push(`featured: ${post.featured}`);
  }
  
  if (post.seasonal !== undefined) {
    lines.push(`seasonal: ${post.seasonal}`);
  }
  
  if (post.image) {
    lines.push(`image: '${post.image}'`);
  }
  
  if (post.imageAlt) {
    lines.push(`imageAlt: '${post.imageAlt.replace(/'/g, "''")}'`);
  }
  
  lines.push(`metaDescription: '${post.metaDescription.replace(/'/g, "''")}'`);
  lines.push('published: true');
  lines.push('---');
  
  return lines.join('\n');
}

/**
 * Generate Markdown content
 */
function generateContent(post: BlogPost): string {
  if (post.content) {
    // If content exists, use it (may need HTML to Markdown conversion)
    return post.content;
  }
  
  // Generate basic content from excerpt
  return `# ${post.title}

${post.excerpt}

## Overview

This is a placeholder content for the blog post. The original post data did not include full content.

**Category:** ${post.category}  
**Service Area:** ${post.serviceArea}  
**Event Type:** ${post.eventType}

## Key Features

- Professional hibachi chefs
- Fresh, high-quality ingredients
- Interactive cooking experience
- Customizable menu options
- Full-service event catering

## Why Choose My Hibachi?

My Hibachi brings the authentic Japanese hibachi experience directly to your location. Our professional chefs create memorable dining experiences with:

1. **Expert Culinary Skills** - Trained hibachi chefs with years of experience
2. **Premium Ingredients** - Fresh, high-quality meats, seafood, and vegetables
3. **Entertainment Value** - Knife tricks, jokes, and interactive cooking show
4. **Flexible Service** - We adapt to your event needs and preferences

## Book Your Event

Ready to create an unforgettable experience? Contact us today for a free quote!

---

*Read time: ${post.readTime}*  
*Author: ${post.author}*
`;
}

/**
 * Create MDX file for a blog post
 */
async function createMDXFile(
  post: BlogPost,
  options: { force?: boolean; dryRun?: boolean } = {}
): Promise<{ success: boolean; path: string; message: string }> {
  try {
    const { year, month } = parseDate(post.date);
    const dirPath = join(process.cwd(), 'content', 'blog', 'posts', year, month);
    const filePath = join(dirPath, `${post.slug}.mdx`);
    
    // Check if file exists
    if (!options.force && existsSync(filePath)) {
      return {
        success: false,
        path: filePath,
        message: `File already exists (use --force to overwrite)`
      };
    }
    
    // Create directory if it doesn't exist
    if (!options.dryRun) {
      await mkdir(dirPath, { recursive: true });
    }
    
    // Generate MDX content
    const frontmatter = generateFrontmatter(post);
    const content = generateContent(post);
    const mdxContent = `${frontmatter}\n\n${content}\n`;
    
    // Write file
    if (!options.dryRun) {
      await writeFile(filePath, mdxContent, 'utf-8');
    }
    
    return {
      success: true,
      path: filePath,
      message: options.dryRun ? 'Would create' : 'Created successfully'
    };
  } catch (error) {
    return {
      success: false,
      path: '',
      message: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Main migration function
 */
async function migrate() {
  console.log('🚀 Starting blog migration: TypeScript → MDX\n');
  
  // Parse command line arguments
  const args = process.argv.slice(2);
  const testMode = args.includes('--test');
  const force = args.includes('--force');
  const dryRun = args.includes('--dry-run');
  
  if (dryRun) {
    console.log('🔍 DRY RUN MODE - No files will be created\n');
  }
  
  if (testMode) {
    console.log('🧪 TEST MODE - Processing first 5 posts only\n');
  }
  
  if (force) {
    console.log('⚠️  FORCE MODE - Will overwrite existing files\n');
  }
  
  // Import blog posts dynamically
  let blogPosts: BlogPost[];
  try {
    // Convert Windows path to file:// URL for ESM import
    const fileUrl = pathToFileURL(blogPostsPath).href;
    const module = await import(fileUrl);
    blogPosts = module.blogPosts;
    console.log(`📚 Found ${blogPosts.length} blog posts\n`);
  } catch (error) {
    console.error('❌ Failed to import blog posts:', error);
    process.exit(1);
  }
  
  // Limit posts in test mode
  const postsToMigrate = testMode ? blogPosts.slice(0, 5) : blogPosts;
  
  console.log(`📝 Migrating ${postsToMigrate.length} posts...\n`);
  
  // Track results
  const results = {
    success: 0,
    failed: 0,
    skipped: 0,
    errors: [] as { post: BlogPost; error: string }[]
  };
  
  // Migrate each post
  for (const post of postsToMigrate) {
    const result = await createMDXFile(post, { force, dryRun });
    
    if (result.success) {
      results.success++;
      const relativePath = result.path.replace(process.cwd(), '.');
      console.log(`✅ [${post.id}] ${post.title}`);
      console.log(`   → ${relativePath}`);
    } else if (result.message.includes('already exists')) {
      results.skipped++;
      console.log(`⏭️  [${post.id}] ${post.title}`);
      console.log(`   → ${result.message}`);
    } else {
      results.failed++;
      results.errors.push({ post, error: result.message });
      console.log(`❌ [${post.id}] ${post.title}`);
      console.log(`   → Error: ${result.message}`);
    }
  }
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 MIGRATION SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Posts:     ${postsToMigrate.length}`);
  console.log(`✅ Success:      ${results.success}`);
  console.log(`⏭️  Skipped:      ${results.skipped}`);
  console.log(`❌ Failed:       ${results.failed}`);
  console.log('='.repeat(60));
  
  // Print errors if any
  if (results.errors.length > 0) {
    console.log('\n❌ ERRORS:\n');
    results.errors.forEach(({ post, error }) => {
      console.log(`  [${post.id}] ${post.title}`);
      console.log(`      ${error}\n`);
    });
  }
  
  // Print next steps
  if (results.success > 0) {
    console.log('\n✅ NEXT STEPS:\n');
    console.log('  1. Verify MDX files: ls content/blog/posts/*/*/*.mdx');
    console.log('  2. Test content loader: npx tsx scripts/test-content-loader.ts');
    console.log('  3. Check file count: (Get-ChildItem content/blog/posts -Recurse -File).Count');
    console.log('  4. Update BlogService to use contentLoader (Step 5)');
  }
  
  if (testMode) {
    console.log('\n🧪 Test complete! Run without --test to migrate all posts.');
  }
  
  if (dryRun) {
    console.log('\n🔍 Dry run complete! Run without --dry-run to create files.');
  }
  
  // Exit with appropriate code
  process.exit(results.failed > 0 ? 1 : 0);
}

// Run migration
migrate().catch(error => {
  console.error('\n💥 Fatal error:', error);
  process.exit(1);
});
