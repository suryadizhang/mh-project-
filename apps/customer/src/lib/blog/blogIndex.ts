/**
 * Blog Search Index using FlexSearch
 *
 * Provides fast, client-side search capabilities for blog posts.
 * Uses FlexSearch for fuzzy matching, stemming, and relevance ranking.
 *
 * @module blogIndex
 */

import type { BlogPost } from '@my-hibachi/blog-types';
import { Document } from 'flexsearch';

import { getAuthorName } from './helpers';

/**
 * Searchable document type with required index signature for FlexSearch
 * Contains flattened BlogPost data optimized for search
 */
interface SearchableDocument {
  id: string | number;
  title: string;
  excerpt: string;
  content: string;
  category: string;
  serviceArea: string;
  eventType: string;
  keywords: string;
  author: string;
  [key: string]: string | number;
}

/**
 * Convert BlogPost to SearchableDocument
 * Flattens arrays and ensures all fields are searchable strings
 */
function toSearchableDocument(post: BlogPost): SearchableDocument {
  return {
    id: post.id,
    title: post.title,
    excerpt: post.excerpt,
    content: post.content || '',
    category: post.category,
    serviceArea: post.serviceArea,
    eventType: post.eventType,
    keywords: post.keywords.join(' '),
    author: getAuthorName(post.author),
  };
}

// FlexSearch index instance
let searchIndex: Document<SearchableDocument, true> | null = null;
// Store original posts for returning full BlogPost objects
const postsStore: Map<string | number, BlogPost> = new Map();

/**
 * Initialize FlexSearch index with blog posts
 * Should be called once when the app starts or when posts are updated
 */
export async function initializeBlogSearch(
  posts: BlogPost[],
): Promise<Document<SearchableDocument, true>> {
  // Create new document index with custom configuration
  const index = new Document<SearchableDocument, true>({
    document: {
      id: 'id',
      index: [
        'title',
        'excerpt',
        'content',
        'category',
        'serviceArea',
        'eventType',
        'keywords',
        'author',
      ],
      store: true,
    },
    tokenize: 'forward',
    context: {
      resolution: 9,
      depth: 3,
      bidirectional: true,
    },
    cache: 100,
  });

  // Clear and rebuild posts store
  postsStore.clear();

  // Add all posts to index
  for (const post of posts) {
    const searchableDoc = toSearchableDocument(post);
    index.add(searchableDoc);
    postsStore.set(post.id, post);
  }

  searchIndex = index;
  return index;
}

/**
 * Search blog posts using FlexSearch
 * Returns posts ranked by relevance
 *
 * @param query - Search query string
 * @param limit - Maximum number of results (default: 10)
 * @returns Array of matching BlogPost objects
 */
export async function searchBlogPosts(query: string, limit: number = 10): Promise<BlogPost[]> {
  if (!searchIndex) {
    console.warn('Search index not initialized. Call initializeBlogSearch() first.');
    return [];
  }

  if (!query || query.trim().length < 2) {
    return [];
  }

  try {
    // Perform search across all indexed fields
    const results = await searchIndex.search(query, limit, {
      enrich: true,
    });

    // Extract posts from results and return original BlogPost objects
    const posts: BlogPost[] = [];
    const seenIds = new Set<string | number>();

    for (const fieldResults of results) {
      if (fieldResults.result) {
        for (const item of fieldResults.result) {
          const doc = (item as { doc: SearchableDocument }).doc;
          const post = postsStore.get(doc.id);

          // Avoid duplicates and ensure post exists
          if (post && !seenIds.has(post.id)) {
            seenIds.add(post.id);
            posts.push(post);

            if (posts.length >= limit) {
              break;
            }
          }
        }
      }

      if (posts.length >= limit) {
        break;
      }
    }

    return posts;
  } catch (error) {
    console.error('Error searching blog posts:', error);
    return [];
  }
}

/**
 * Search blog posts by category
 *
 * @param category - Category to filter by
 * @param limit - Maximum number of results
 * @returns Array of matching BlogPost objects
 */
export async function searchByCategory(category: string, limit: number = 10): Promise<BlogPost[]> {
  const results = await searchBlogPosts(category, limit * 2);
  return results.filter((post) => post.category === category).slice(0, limit);
}

/**
 * Search blog posts by service area
 *
 * @param serviceArea - Service area to filter by
 * @param limit - Maximum number of results
 * @returns Array of matching BlogPost objects
 */
export async function searchByServiceArea(
  serviceArea: string,
  limit: number = 10,
): Promise<BlogPost[]> {
  const results = await searchBlogPosts(serviceArea, limit * 2);
  return results.filter((post) => post.serviceArea === serviceArea).slice(0, limit);
}

/**
 * Search blog posts by event type
 *
 * @param eventType - Event type to filter by
 * @param limit - Maximum number of results
 * @returns Array of matching BlogPost objects
 */
export async function searchByEventType(
  eventType: string,
  limit: number = 10,
): Promise<BlogPost[]> {
  const results = await searchBlogPosts(eventType, limit * 2);
  return results.filter((post) => post.eventType === eventType).slice(0, limit);
}

/**
 * Get search suggestions based on partial query
 * Useful for autocomplete functionality
 *
 * @param query - Partial search query
 * @param limit - Maximum number of suggestions
 * @returns Array of suggested search terms (post titles)
 */
export async function getSearchSuggestions(query: string, limit: number = 5): Promise<string[]> {
  const posts = await searchBlogPosts(query, limit);
  return posts.map((post) => post.title);
}

/**
 * Clear and rebuild search index
 * Should be called when posts are added, updated, or removed
 */
export async function rebuildSearchIndex(posts: BlogPost[]): Promise<void> {
  searchIndex = null;
  postsStore.clear();
  await initializeBlogSearch(posts);
}

/**
 * Get search index status
 * Useful for debugging and monitoring
 */
export function getSearchIndexStatus(): {
  initialized: boolean;
  size: number;
} {
  return {
    initialized: searchIndex !== null,
    size: searchIndex ? Object.keys(searchIndex).length : 0,
  };
}
