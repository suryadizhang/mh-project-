/**
 * MDX Content Loader for Blog Posts
 *
 * This module handles loading and parsing MDX blog posts from the file system.
 * It provides functions to:
 * - Load individual posts by slug
 * - Load multiple posts with filtering
 * - Generate searchable index for fast search
 * - Parse frontmatter into BlogPost interface
 *
 * @module contentLoader
 */

import fs from 'fs';
import path from 'path';

import type { BlogPost, BlogFilters, BlogPostContent } from '@my-hibachi/blog-types';
import matter from 'gray-matter';

// Content directory paths
const CONTENT_DIR = path.join(process.cwd(), 'content', 'blog', 'posts');

/**
 * Get all MDX file paths from content directory
 * Searches recursively through YYYY/MM structure
 */
function getAllMdxFiles(): string[] {
  const files: string[] = [];

  function scanDirectory(dir: string) {
    if (!fs.existsSync(dir)) {
      return;
    }

    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        scanDirectory(fullPath);
      } else if (entry.name.endsWith('.mdx') || entry.name.endsWith('.md')) {
        files.push(fullPath);
      }
    }
  }

  scanDirectory(CONTENT_DIR);
  return files;
}

/**
 * Parse MDX file and extract frontmatter + content
 * Converts frontmatter to BlogPost interface
 */
function parseMdxFile(filePath: string): BlogPostContent | null {
  try {
    const fileContents = fs.readFileSync(filePath, 'utf8');
    const { data, content } = matter(fileContents);

    // Extract slug from filename
    const fileName = path.basename(filePath, path.extname(filePath));
    const slug = data.slug || fileName;

    // Parse date from frontmatter or file path (YYYY/MM structure)
    let date = data.date;
    if (!date) {
      const pathParts = filePath.split(path.sep);
      const yearIndex = pathParts.findIndex((p) => /^\d{4}$/.test(p));
      if (yearIndex !== -1 && pathParts[yearIndex + 1]) {
        const year = pathParts[yearIndex];
        const month = pathParts[yearIndex + 1];
        date = `${year}-${month}-01`;
      }
    }

    // Build BlogPost object from frontmatter
    const post: BlogPost = {
      id: data.id || slug,
      title: data.title || 'Untitled',
      slug,
      excerpt: data.excerpt || data.description || '',
      content: data.content || content,
      author: data.author || 'My Hibachi Team',
      date: date || new Date().toISOString().split('T')[0],
      category: data.category || 'General',
      keywords: data.keywords || data.tags || [],
      readTime: data.readTime || `${Math.ceil(content.split(' ').length / 200)} min read`,
      featured: data.featured || false,
      image: data.image || data.imageUrl || '/images/blog/default.jpg',
      imageAlt: data.imageAlt || data.title || 'Blog post image',
      metaDescription: data.metaDescription || data.excerpt || data.description || '',
      serviceArea: data.serviceArea || 'All Areas',
      eventType: data.eventType || 'General',
    };

    return {
      post,
      mdxContent: content,
    };
  } catch (error) {
    console.error(`Error parsing MDX file ${filePath}:`, error);
    return null;
  }
}

/**
 * Get a single blog post by slug
 * @param slug - Post slug (filename without extension)
 * @returns BlogPostContent with post metadata and MDX content
 */
export async function getBlogPost(slug: string): Promise<BlogPostContent | null> {
  const files = getAllMdxFiles();

  // Find file matching slug
  const file = files.find((f) => {
    const fileName = path.basename(f, path.extname(f));
    return fileName === slug || f.includes(`/${slug}.`);
  });

  if (!file) {
    return null;
  }

  return parseMdxFile(file);
}

/**
 * Get multiple blog posts with optional filtering
 * @param filters - Optional filters for category, tags, search, etc.
 * @returns Array of BlogPost objects (without MDX content)
 */
export async function getBlogPosts(filters?: BlogFilters): Promise<BlogPost[]> {
  const files = getAllMdxFiles();
  const posts: BlogPost[] = [];

  // Parse all files
  for (const file of files) {
    const result = parseMdxFile(file);
    if (result) {
      posts.push(result.post);
    }
  }

  // Apply filters if provided
  let filteredPosts = posts;

  if (filters) {
    filteredPosts = posts.filter((post) => {
      // Category filter
      if (filters.category && post.category !== filters.category) {
        return false;
      }

      // Tags filter (match any tag)
      if (filters.tags && filters.tags.length > 0) {
        const hasMatchingTag = filters.tags.some((tag) =>
          post.keywords.some((keyword) => keyword.toLowerCase().includes(tag.toLowerCase())),
        );
        if (!hasMatchingTag) {
          return false;
        }
      }

      // Service area filter
      if (filters.serviceArea && post.serviceArea !== filters.serviceArea) {
        return false;
      }

      // Event type filter
      if (filters.eventType && post.eventType !== filters.eventType) {
        return false;
      }

      // Featured filter
      if (filters.featured !== undefined && post.featured !== filters.featured) {
        return false;
      }

      // Search query (title, excerpt, keywords)
      if (filters.query) {
        const query = filters.query.toLowerCase();
        const searchableText = [post.title, post.excerpt, post.category, ...post.keywords]
          .join(' ')
          .toLowerCase();

        if (!searchableText.includes(query)) {
          return false;
        }
      }

      return true;
    });
  }

  // Sort by date (newest first)
  filteredPosts.sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateB - dateA;
  });

  // Apply pagination if specified
  if (filters?.limit) {
    const offset = filters.page ? (filters.page - 1) * filters.limit : 0;
    filteredPosts = filteredPosts.slice(offset, offset + filters.limit);
  }

  return filteredPosts;
}

/**
 * Generate blog index for search
 * Creates a searchable index of all posts with their content
 * Used by FlexSearch for fast full-text search
 */
export async function generateBlogIndex(): Promise<{
  posts: BlogPost[];
  searchData: Array<{ id: string | number; title: string; content: string; keywords: string[] }>;
}> {
  const files = getAllMdxFiles();
  const posts: BlogPost[] = [];
  const searchData: Array<{
    id: string | number;
    title: string;
    content: string;
    keywords: string[];
  }> = [];

  for (const file of files) {
    const result = parseMdxFile(file);
    if (result) {
      posts.push(result.post);

      // Add to search index
      searchData.push({
        id: result.post.id,
        title: result.post.title,
        content: `${result.post.title} ${result.post.excerpt} ${result.mdxContent}`,
        keywords: result.post.keywords,
      });
    }
  }

  return { posts, searchData };
}

/**
 * Get all unique categories from blog posts
 */
export async function getAllCategories(): Promise<string[]> {
  const posts = await getBlogPosts();
  const categories = new Set(posts.map((p) => p.category));
  return Array.from(categories).sort();
}

/**
 * Get all unique service areas from blog posts
 */
export async function getAllServiceAreas(): Promise<string[]> {
  const posts = await getBlogPosts();
  const areas = new Set(posts.map((p) => p.serviceArea));
  return Array.from(areas).sort();
}

/**
 * Get all unique event types from blog posts
 */
export async function getAllEventTypes(): Promise<string[]> {
  const posts = await getBlogPosts();
  const types = new Set(posts.map((p) => p.eventType));
  return Array.from(types).sort();
}

/**
 * Get post count statistics
 */
export async function getPostStats(): Promise<{
  total: number;
  featured: number;
  byCategory: Record<string, number>;
  byServiceArea: Record<string, number>;
  byEventType: Record<string, number>;
}> {
  const posts = await getBlogPosts();

  const byCategory: Record<string, number> = {};
  const byServiceArea: Record<string, number> = {};
  const byEventType: Record<string, number> = {};

  for (const post of posts) {
    byCategory[post.category] = (byCategory[post.category] || 0) + 1;
    byServiceArea[post.serviceArea] = (byServiceArea[post.serviceArea] || 0) + 1;
    byEventType[post.eventType] = (byEventType[post.eventType] || 0) + 1;
  }

  return {
    total: posts.length,
    featured: posts.filter((p) => p.featured).length,
    byCategory,
    byServiceArea,
    byEventType,
  };
}
