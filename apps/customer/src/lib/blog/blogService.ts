/**
 * Blog Service - Data Access Layer
 *
 * This service provides a clean abstraction over the blog data source.
 * Now uses MDX content loader for scalable, file-based blog content.
 * Can easily be swapped to Headless CMS or database without touching components.
 *
 * Benefits:
 * - Single source of truth for blog data access
 * - Easy to mock for testing
 * - Future-proof: swap implementation without component changes
 * - Type-safe with TypeScript
 * - Consistent error handling
 * - Scalable: supports 500+ posts with ISR
 *
 * @example
 * ```typescript
 * import { blogService } from '@/lib/blog/blogService';
 *
 * // Get all posts
 * const posts = await blogService.getAllPosts();
 *
 * // Get single post
 * const post = await blogService.getPostBySlug('bay-area-hibachi');
 *
 * // Search posts
 * const results = await blogService.searchPosts('birthday party');
 * ```
 */

import type { BlogFilters, BlogPost, BlogSearchResult } from '@my-hibachi/blog-types';

import {
  getBlogPost,
  getBlogPosts,
  getAllCategories,
  getAllServiceAreas,
  getAllEventTypes
} from './contentLoader';

/**
 * Blog Service Interface
 * Define the contract for blog data access
 */
export interface IBlogService {
  getAllPosts(): Promise<BlogPost[]>;
  getPostBySlug(slug: string): Promise<BlogPost | null>;
  getPostById(id: number | string): Promise<BlogPost | null>;
  getPostsByCategory(category: string): Promise<BlogPost[]>;
  getPostsByServiceArea(serviceArea: string): Promise<BlogPost[]>;
  getPostsByEventType(eventType: string): Promise<BlogPost[]>;
  getFeaturedPosts(limit?: number): Promise<BlogPost[]>;
  getSeasonalPosts(limit?: number): Promise<BlogPost[]>;
  getRecentPosts(limit?: number): Promise<BlogPost[]>;
  searchPosts(query: string): Promise<BlogPost[]>;
  filterPosts(filters: BlogFilters): Promise<BlogSearchResult>;
  getCategories(): Promise<string[]>;
  getServiceAreas(): Promise<string[]>;
  getEventTypes(): Promise<string[]>;
  getAllTags(): Promise<string[]>;
}

/**
 * Blog Service Implementation
 * Currently uses in-memory TypeScript array
 * Can be easily replaced with MDX loader, CMS client, or API calls
 */
export class BlogService implements IBlogService {
  /**
   * Get all published blog posts
   * @returns Array of all blog posts
   */
  async getAllPosts(): Promise<BlogPost[]> {
    return await getBlogPosts();
  }

  /**
   * Get a single blog post by slug
   * @param slug - URL-safe slug (e.g., 'bay-area-hibachi-catering')
   * @returns Blog post or null if not found
   */
  async getPostBySlug(slug: string): Promise<BlogPost | null> {
    const result = await getBlogPost(slug);
    return result?.post || null;
  }

  /**
   * Get a single blog post by ID
   * @param id - Numeric ID or string ID (CMS compatibility)
   * @returns Blog post or null if not found
   */
  async getPostById(id: number | string): Promise<BlogPost | null> {
    const posts = await getBlogPosts();
    const post = posts.find((p: BlogPost) => p.id === id);
    return post || null;
  }

  /**
   * Get all posts in a specific category
   * @param category - Category name (e.g., 'Service Areas', 'Seasonal')
   * @returns Array of matching posts
   */
  async getPostsByCategory(category: string): Promise<BlogPost[]> {
    return await getBlogPosts({ category });
  }

  /**
   * Get all posts for a specific service area
   * @param serviceArea - Service area name (e.g., 'Bay Area', 'Sacramento')
   * @returns Array of matching posts
   */
  async getPostsByServiceArea(serviceArea: string): Promise<BlogPost[]> {
    const posts = await getBlogPosts({ serviceArea });
    // Also include posts for "All Areas"
    const allAreasPosts = await getBlogPosts({ serviceArea: 'All Areas' });
    // Combine and deduplicate by ID
    const combined = [...posts, ...allAreasPosts];
    const unique = Array.from(new Map(combined.map(p => [p.id, p])).values());
    return unique;
  }

  /**
   * Get all posts for a specific event type
   * @param eventType - Event type (e.g., 'Birthday', 'Corporate', 'Wedding')
   * @returns Array of matching posts
   */
  async getPostsByEventType(eventType: string): Promise<BlogPost[]> {
    const posts = await getBlogPosts({ eventType });
    // Also include posts for "General" event type
    const generalPosts = await getBlogPosts({ eventType: 'General' });
    // Combine and deduplicate by ID
    const combined = [...posts, ...generalPosts];
    const unique = Array.from(new Map(combined.map(p => [p.id, p])).values());
    return unique;
  }

  /**
   * Get featured posts (homepage highlights)
   * @param limit - Maximum number of posts to return (default: all)
   * @returns Array of featured posts
   */
  async getFeaturedPosts(limit?: number): Promise<BlogPost[]> {
    const featured = await getBlogPosts({ featured: true, limit });
    return featured;
  }

  /**
   * Get seasonal posts (holidays, special events)
   * @param limit - Maximum number of posts to return (default: all)
   * @returns Array of seasonal posts
   */
  async getSeasonalPosts(limit?: number): Promise<BlogPost[]> {
    // Get posts in "Seasonal" category
    const seasonal = await getBlogPosts({ category: 'Seasonal', limit });
    return seasonal;
  }

  /**
   * Get most recent posts
   * @param limit - Maximum number of posts to return (default: 10)
   * @returns Array of recent posts, sorted by date (newest first)
   */
  async getRecentPosts(limit: number = 10): Promise<BlogPost[]> {
    // getBlogPosts() already sorts by date (newest first)
    return await getBlogPosts({ limit });
  }

  /**
   * Search posts by query string
   * Searches in: title, excerpt, keywords, metaDescription
   * @param query - Search query
   * @returns Array of matching posts
   */
  async searchPosts(query: string): Promise<BlogPost[]> {
    if (!query || query.trim() === '') {
      return [];
    }

    // Use getBlogPosts with query filter (it searches title, excerpt, keywords)
    return await getBlogPosts({ query });
  }

  /**
   * Filter posts with multiple criteria
   * @param filters - Filter parameters
   * @returns Search result with posts and metadata
   */
  /**
   * Filter posts with multiple criteria
   * @param filters - Filter parameters
   * @returns Search result with posts and metadata
   */
  async filterPosts(filters: BlogFilters): Promise<BlogSearchResult> {
    // Use getBlogPosts with filters - it handles all the filtering logic
    const results = await getBlogPosts(filters);

    // Calculate pagination metadata
    const page = filters.page || 1;
    const limit = filters.limit || 20;
    
    // Get total count without pagination
    const allResults = await getBlogPosts({
      ...filters,
      page: undefined,
      limit: undefined,
    });
    const totalPosts = allResults.length;
    const totalPages = Math.ceil(totalPosts / limit);

    return {
      posts: results,
      pagination: {
        currentPage: page,
        totalPages,
        totalPosts,
        postsPerPage: limit,
        hasPrevious: page > 1,
        hasNext: page < totalPages,
      },
      filters,
      stats: {
        totalMatches: totalPosts,
        searchTime: 0,
      },
    };
  }

  /**
   * Get list of all unique categories
   * @returns Array of category names
   */
  async getCategories(): Promise<string[]> {
    return await getAllCategories();
  }

  /**
   * Get list of all unique service areas
   * @returns Array of service area names
   */
  async getServiceAreas(): Promise<string[]> {
    return await getAllServiceAreas();
  }

  /**
   * Get list of all unique event types
   * @returns Array of event type names
   */
  async getEventTypes(): Promise<string[]> {
    return await getAllEventTypes();
  }

  /**
   * Get list of all unique tags/keywords
   * @returns Array of unique tags, sorted alphabetically
   */
  async getAllTags(): Promise<string[]> {
    const posts = await getBlogPosts();
    const tags = new Set<string>();
    posts.forEach((post: BlogPost) => {
      post.keywords.forEach((keyword: string) => tags.add(keyword));
    });
    return Array.from(tags).sort();
  }
}

/**
 * Singleton instance
 * Use this throughout the application for consistent data access
 */
export const blogService = new BlogService();

/**
 * Re-export types for convenience
 */
export type { BlogPost, BlogFilters, BlogSearchResult } from '@my-hibachi/blog-types';
