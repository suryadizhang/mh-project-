/**
 * Blog Posts Migration Script - TypeScript Array → MDX Files
 * 
 * Converts the hardcoded blogPosts.ts array into individual MDX files
 * organized by year/month structure for scalability.
 * 
 * Usage:
 *   npx tsx scripts/migrate-blog-to-mdx.ts
 * 
 * Output:
 *   apps/customer/content/blog/posts/YYYY/MM/slug.mdx
 */

import * as fs from 'fs';
import * as path from 'path';
import { blogPosts } from '../apps/customer/src/data/blogPosts';

interface BlogPost {
  id: number | string;
  title: string;
  slug: string;
  excerpt: string;
  content?: string;
  author: {
    name: string;
    role: string;
    avatar: string;
  };
  category: string;
  keywords: string[];
  date: string;
  readTime: string;
  featured?: boolean;
  seasonal?: boolean;
  serviceArea?: string;
  eventType?: string;
  images?: {
    thumbnail?: string;
    hero?: string;
    gallery?: string[];
  };
  seo?: {
    metaTitle: string;
    metaDescription: string;
    canonicalUrl?: string;
    ogImage?: string;
  };
}

const OUTPUT_DIR = path.join(__dirname, '../apps/customer/content/blog/posts');

/**
 * Escape special characters in YAML values
 */
function escapeYaml(str: string): string {
  if (typeof str !== 'string') return str;
  
  // If contains special characters, wrap in quotes and escape
  if (str.includes(':') || str.includes('#') || str.includes('"') || str.includes("'") || 
      str.includes('[') || str.includes(']') || str.includes('{') || str.includes('}') ||
      str.includes('|') || str.includes('&') || str.includes('*')) {
    return `"${str.replace(/"/g, '\\"')}"`;
  }
  
  return str;
}

/**
 * Convert blog post to MDX frontmatter + content
 */
function convertToMdx(post: BlogPost): string {
  const frontmatter = [
    '---',
    `id: ${post.id}`,
    `title: ${escapeYaml(post.title)}`,
    `slug: ${post.slug}`,
    `excerpt: ${escapeYaml(post.excerpt)}`,
    `date: '${post.date}'`,
    `readTime: '${post.readTime}'`,
    `category: '${post.category}'`,
    `keywords:`,
    ...post.keywords.map(k => `  - '${escapeYaml(k)}'`),
    `author:`,
    `  name: '${post.author.name}'`,
    `  role: '${post.author.role}'`,
    `  avatar: '${post.author.avatar}'`,
  ];

  if (post.featured) {
    frontmatter.push(`featured: true`);
  }

  if (post.seasonal) {
    frontmatter.push(`seasonal: true`);
  }

  if (post.serviceArea) {
    frontmatter.push(`serviceArea: '${post.serviceArea}'`);
  }

  if (post.eventType) {
    frontmatter.push(`eventType: '${post.eventType}'`);
  }

  // Images (handle missing images property)
  if (post.images) {
    frontmatter.push(`images:`);
    if (post.images.thumbnail) {
      frontmatter.push(`  thumbnail: '${post.images.thumbnail}'`);
    }
    if (post.images.hero) {
      frontmatter.push(`  hero: '${post.images.hero}'`);
    }
    if (post.images.gallery && post.images.gallery.length > 0) {
      frontmatter.push(`  gallery:`);
      post.images.gallery.forEach(img => {
        frontmatter.push(`    - '${img}'`);
      });
    }
  }

  // SEO (handle missing seo property)
  if (post.seo) {
    frontmatter.push(`seo:`);
    frontmatter.push(`  metaTitle: ${escapeYaml(post.seo.metaTitle)}`);
    frontmatter.push(`  metaDescription: ${escapeYaml(post.seo.metaDescription)}`);
    if (post.seo.canonicalUrl) {
      frontmatter.push(`  canonicalUrl: '${post.seo.canonicalUrl}'`);
    }
    if (post.seo.ogImage) {
      frontmatter.push(`  ogImage: '${post.seo.ogImage}'`);
    }
  }

  frontmatter.push('---');
  frontmatter.push('');

  // Content
  const content = post.content || 'No content available';

  return frontmatter.join('\n') + '\n' + content + '\n';
}

/**
 * Get year/month from date string
 */
function getYearMonth(dateStr: string): { year: string; month: string } {
  const date = new Date(dateStr);
  const year = date.getFullYear().toString();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  return { year, month };
}

/**
 * Main migration function
 */
async function migrateBlogPosts() {
  console.log('🚀 Starting Blog Migration: TypeScript Array → MDX Files\n');
  console.log(`📊 Total posts to migrate: ${blogPosts.length}\n`);

  let successCount = 0;
  let errorCount = 0;
  const errors: Array<{ post: string; error: string }> = [];

  for (const post of blogPosts) {
    try {
      // Get year/month for directory structure
      const { year, month } = getYearMonth(post.date);
      
      // Create directory path
      const dirPath = path.join(OUTPUT_DIR, year, month);
      fs.mkdirSync(dirPath, { recursive: true });
      
      // Create file path
      const fileName = `${post.slug}.mdx`;
      const filePath = path.join(dirPath, fileName);
      
      // Convert to MDX
      const mdxContent = convertToMdx(post);
      
      // Write file
      fs.writeFileSync(filePath, mdxContent, 'utf-8');
      
      console.log(`✅ ${year}/${month}/${fileName}`);
      successCount++;
      
    } catch (error) {
      console.error(`❌ Failed: ${post.slug} - ${error}`);
      errorCount++;
      errors.push({
        post: post.slug,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }

  console.log('\n' + '='.repeat(70));
  console.log('📈 Migration Summary:');
  console.log('='.repeat(70));
  console.log(`✅ Successfully migrated: ${successCount} posts`);
  console.log(`❌ Failed: ${errorCount} posts`);
  console.log(`📁 Output directory: ${OUTPUT_DIR}`);
  
  if (errors.length > 0) {
    console.log('\n⚠️  Errors encountered:');
    errors.forEach(({ post, error }) => {
      console.log(`   - ${post}: ${error}`);
    });
  }

  // Verify file count
  const verifyCount = countMdxFiles(OUTPUT_DIR);
  console.log(`\n🔍 Verification: Found ${verifyCount} MDX files in output directory`);
  
  if (verifyCount === blogPosts.length) {
    console.log('✅ Migration COMPLETE - All posts successfully migrated!\n');
  } else {
    console.log(`⚠️  Warning: Expected ${blogPosts.length} files, found ${verifyCount}\n`);
  }
}

/**
 * Count MDX files recursively
 */
function countMdxFiles(dir: string): number {
  let count = 0;
  
  function traverse(currentDir: string) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        traverse(fullPath);
      } else if (item.endsWith('.mdx')) {
        count++;
      }
    }
  }
  
  if (fs.existsSync(dir)) {
    traverse(dir);
  }
  
  return count;
}

// Run migration
migrateBlogPosts().catch(error => {
  console.error('💥 Migration failed:', error);
  process.exit(1);
});
