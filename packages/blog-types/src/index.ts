/**
 * Blog Types Package
 * Shared TypeScript interfaces for My Hibachi blog system
 *
 * This package provides type-safe interfaces for blog posts, categories,
 * authors, and related entities. Can be used across customer, admin,
 * and any future applications.
 */

/**
 * Main blog post interface
 * Represents a single blog article with all metadata
 */
export interface BlogPost {
  /** Unique identifier (numeric for legacy, string for CMS) */
  id: number | string;

  /** SEO-friendly title */
  title: string;

  /** URL-safe slug (used in /blog/:slug routes) */
  slug: string;

  /** Short preview text (150-200 chars) */
  excerpt: string;

  /** Full article content (optional for index pages) */
  content?: string;

  /** SEO meta description */
  metaDescription: string;

  /** SEO keywords for search engines */
  keywords: string[];

  /** Author name or reference (can be string or object) */
  author: string | { name?: string; role?: string; avatar?: string };

  /** Publication date (ISO 8601 format or human-readable) */
  date: string;

  /** Estimated reading time */
  readTime: string;

  /** Primary category (Service Areas, Seasonal, etc.) */
  category: string;

  /** Geographic service area (Bay Area, Sacramento, etc.) */
  serviceArea: string;

  /** Event type (Birthday, Corporate, Wedding, etc.) */
  eventType: string;

  /** Featured on homepage? */
  featured?: boolean;

  /** Seasonal content (Valentine's, Christmas, etc.) */
  seasonal?: boolean;

  /** Hero image URL */
  image?: string;

  /** Image alt text for accessibility */
  imageAlt?: string;

  /** Publication status (for CMS integration) */
  published?: boolean;

  /** Scheduled publish date (for future posts) */
  scheduledDate?: string;
}

/**
 * Blog post with full MDX/HTML content
 * Used when rendering individual blog pages
 */
export interface BlogPostContent {
  /** Blog post metadata and frontmatter */
  post: BlogPost;

  /** Raw MDX/Markdown content for rendering */
  mdxContent: string;

  /** Compiled MDX source (for next-mdx-remote) */
  mdxSource?: any;
}

/**
 * Blog category
 * Groups related posts together
 */
export interface BlogCategory {
  /** Unique identifier */
  id: string;

  /** Display name */
  name: string;

  /** URL-safe slug */
  slug: string;

  /** Category description */
  description: string;

  /** Number of posts in category (optional) */
  postCount?: number;

  /** Category icon or image */
  icon?: string;
}

/**
 * Blog author
 * Represents content creators
 */
export interface BlogAuthor {
  /** Unique identifier */
  id: string;

  /** Full name */
  name: string;

  /** Professional title */
  title?: string;

  /** Short biography */
  bio?: string;

  /** Profile photo URL */
  avatar?: string;

  /** Email address */
  email?: string;

  /** Social media links */
  social?: {
    twitter?: string;
    linkedin?: string;
    instagram?: string;
  };
}

/**
 * Blog tag
 * For flexible content categorization
 */
export interface BlogTag {
  /** Unique identifier */
  id: string;

  /** Display name */
  name: string;

  /** URL-safe slug */
  slug: string;

  /** Number of posts with this tag */
  postCount?: number;
}

/**
 * Blog series
 * Groups related posts into a multi-part series
 */
export interface BlogSeries {
  /** Unique identifier */
  id: string;

  /** Series title */
  title: string;

  /** URL-safe slug */
  slug: string;

  /** Series description */
  description: string;

  /** Posts in series (ordered) */
  posts: BlogPost[];

  /** Series thumbnail */
  image?: string;
}

/**
 * Pagination metadata
 * Used for blog list pages
 */
export interface BlogPagination {
  /** Current page number (1-indexed) */
  currentPage: number;

  /** Total number of pages */
  totalPages: number;

  /** Total number of posts */
  totalPosts: number;

  /** Posts per page */
  postsPerPage: number;

  /** Has previous page? */
  hasPrevious: boolean;

  /** Has next page? */
  hasNext: boolean;
}

/**
 * Blog search filters
 * Used for querying blog posts
 */
export interface BlogFilters {
  /** Search query string */
  query?: string;

  /** Filter by category */
  category?: string;

  /** Filter by service area */
  serviceArea?: string;

  /** Filter by event type */
  eventType?: string;

  /** Filter by author */
  author?: string;

  /** Filter by tags */
  tags?: string[];

  /** Show only featured posts */
  featured?: boolean;

  /** Show only seasonal posts */
  seasonal?: boolean;

  /** Date range filter */
  dateRange?: {
    from?: string;
    to?: string;
  };

  /** Sort order */
  sortBy?: 'date' | 'title' | 'readTime' | 'views';

  /** Sort direction */
  sortOrder?: 'asc' | 'desc';

  /** Pagination */
  page?: number;
  limit?: number;
}

/**
 * Blog search result
 * Contains posts + metadata
 */
export interface BlogSearchResult {
  /** Matching posts */
  posts: BlogPost[];

  /** Pagination info */
  pagination: BlogPagination;

  /** Applied filters */
  filters: BlogFilters;

  /** Search statistics */
  stats?: {
    totalMatches: number;
    searchTime: number;
  };
}

/**
 * Blog frontmatter
 * YAML metadata at top of MDX files
 */
export interface BlogFrontmatter {
  id: number | string;
  title: string;
  slug: string;
  excerpt: string;
  metaDescription: string;
  keywords: string[];
  author: string | { name?: string; role?: string; avatar?: string };
  date: string;
  readTime: string;
  category: string;
  serviceArea: string;
  eventType: string;
  featured?: boolean;
  seasonal?: boolean;
  image?: string;
  imageAlt?: string;
  published?: boolean;
  scheduledDate?: string;
}

/**
 * Blog configuration
 * Site-wide blog settings
 */
export interface BlogConfig {
  /** Blog title */
  title: string;

  /** Blog description */
  description: string;

  /** Posts per page */
  postsPerPage: number;

  /** Enable comments? */
  commentsEnabled: boolean;

  /** Enable social sharing? */
  socialSharingEnabled: boolean;

  /** Default author */
  defaultAuthor: string;

  /** Available categories */
  categories: BlogCategory[];

  /** Available service areas */
  serviceAreas: string[];

  /** Available event types */
  eventTypes: string[];
}
