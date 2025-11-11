import type { BlogPost } from '@my-hibachi/blog-types';

/**
 * Get author name from author field (handles both string and object formats)
 */
export const getAuthorName = (author: BlogPost['author']): string => {
  return typeof author === 'string' ? author : author?.name || 'My Hibachi Team';
};
