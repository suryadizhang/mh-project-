// SEO Blog Post Conversion System
// Converts worldClassSEO.ts posts to standard blogPosts.ts format

import type { BlogPost } from '../data/blogPosts';

import { generateSEOBlogCalendar, type SEOBlogPost } from './worldClassSEO';

// Conversion function to transform SEO posts to regular blog posts
export const convertSEOToStandardBlogPosts = (): BlogPost[] => {
  const seoBlogs = generateSEOBlogCalendar();

  return seoBlogs.map(
    (seoPost: SEOBlogPost): BlogPost => ({
      id: seoPost.id,
      title: seoPost.title,
      slug: seoPost.slug,
      excerpt: seoPost.metaDescription, // Use metaDescription as excerpt
      content: undefined, // Will be generated based on content outline
      metaDescription: seoPost.metaDescription,
      keywords: [seoPost.primaryKeyword, ...seoPost.secondaryKeywords],
      author: seoPost.author,
      date: formatDate(seoPost.publishDate),
      readTime: calculateReadTime(seoPost.contentLength),
      category: mapEventToCategory(seoPost.eventType),
      serviceArea: seoPost.targetLocation,
      eventType: seoPost.eventType,
      featured: shouldBeFeatured(seoPost),
      seasonal: isSeasonalPost(seoPost),
    }),
  );
};

// Helper function to format date
const formatDate = (publishDate: string): string => {
  const date = new Date(publishDate);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

// Helper function to calculate read time based on content length
const calculateReadTime = (contentLength: number): string => {
  const wordsPerMinute = 200;
  const minutes = Math.ceil(contentLength / wordsPerMinute);
  return `${minutes} min read`;
};

// Map event types to categories for consistency
const mapEventToCategory = (eventType: string): string => {
  const categoryMap: Record<string, string> = {
    'Backyard Party': 'Outdoor Events',
    Corporate: 'Corporate',
    'Corporate Tech': 'Corporate',
    Birthday: 'Birthday',
    Wedding: 'Weddings',
    Graduation: 'Celebrations',
    Holiday: 'Holidays',
    'Pool Party': 'Summer Events',
    Engagement: 'Romantic',
    Anniversary: 'Romantic',
    'Baby Shower': 'Celebrations',
    Retirement: 'Professional',
    'Family Reunion': 'Family',
    Networking: 'Professional',
    Housewarming: 'Celebrations',
    'Summer BBQ': 'Summer Events',
    'Sports Party': 'Sports Events',
    'Block Party': 'Community Events',
    Festival: 'Community Events',
    'Tech Event': 'Corporate',
    University: 'Educational',
    Cultural: 'Cultural Events',
  };

  return categoryMap[eventType] || 'Events';
};

// Determine if post should be featured based on target location and event type
const shouldBeFeatured = (seoPost: SEOBlogPost): boolean => {
  const highPriorityLocations = ['San Jose', 'San Francisco', 'Oakland', 'Palo Alto', 'Bay Area'];
  const highPriorityEvents = ['Backyard Party', 'Corporate', 'Wedding', 'Birthday'];

  return (
    highPriorityLocations.includes(seoPost.targetLocation) &&
    highPriorityEvents.includes(seoPost.eventType)
  );
};

// Determine if post is seasonal
const isSeasonalPost = (seoPost: SEOBlogPost): boolean => {
  const seasonalKeywords = [
    'holiday',
    'summer',
    'winter',
    'spring',
    'fall',
    'thanksgiving',
    'christmas',
    'new year',
  ];
  const titleLower = seoPost.title.toLowerCase();
  const eventLower = seoPost.eventType.toLowerCase();

  return seasonalKeywords.some(
    (keyword) => titleLower.includes(keyword) || eventLower.includes(keyword),
  );
};

// Export converted posts for integration
export const getConvertedSEOPosts = (): BlogPost[] => {
  return convertSEOToStandardBlogPosts();
};

// Helper function to merge with existing blog posts
export const mergeWithExistingPosts = (existingPosts: BlogPost[]): BlogPost[] => {
  const convertedPosts = getConvertedSEOPosts();

  // Sort all posts by ID to maintain order
  return [...existingPosts, ...convertedPosts].sort((a, b) => a.id - b.id);
};

const SEOConverter = {
  convertSEOToStandardBlogPosts,
  getConvertedSEOPosts,
  mergeWithExistingPosts,
};

export default SEOConverter;
