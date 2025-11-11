// SEO Helper Functions for Blog Content
// ====================================

import { blogPosts, type BlogPost } from '@/data/blogPosts'

// Generate structured data for blog listing page
export const generateBlogListingStructuredData = () => {
  return {
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: 'My Hibachi Blog',
    description:
      'Complete hibachi catering guides for every event: birthdays, weddings, corporate events, pool parties, and more. Expert tips for Bay Area, Sacramento, San Jose celebrations.',
    url: 'https://myhibachi.com/blog',
    publisher: {
      '@type': 'Organization',
      name: 'My Hibachi',
      url: 'https://myhibachi.com'
    },
    blogPost: blogPosts.map((post: BlogPost) => ({
      '@type': 'BlogPosting',
      headline: post.title,
      description: post.excerpt,
      url: `https://myhibachi.com/blog/${post.slug}`,
      datePublished: new Date(post.date).toISOString(),
      author: {
        '@type': 'Person',
        name: post.author
      },
      keywords: post.keywords.join(', '),
      articleSection: post.category
    }))
  }
}

// Generate URL list for sitemap
export const getBlogSitemapUrls = () => {
  const blogUrls = blogPosts.map((post: BlogPost) => ({
    url: `/blog/${post.slug}`,
    lastModified: new Date(post.date),
    priority: post.featured ? 0.8 : 0.6,
    changeFrequency: 'monthly' as const
  }))

  return [
    {
      url: '/blog',
      lastModified: new Date(),
      priority: 0.8,
      changeFrequency: 'weekly' as const
    },
    ...blogUrls
  ]
}

// Generate keyword clusters for SEO analysis
export const getKeywordClusters = () => {
  const keywords = blogPosts.flatMap((post: BlogPost) => post.keywords)
  const keywordCount = keywords.reduce(
    (acc: Record<string, number>, keyword: string) => {
      acc[keyword] = (acc[keyword] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return Object.entries(keywordCount)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 50) // Top 50 keywords
}

// Generate location-based content mapping
export const getLocationContentMap = () => {
  const locations = [
    'Bay Area',
    'Sacramento',
    'San Jose',
    'Oakland',
    'Fremont',
    'Stockton',
    'Napa Valley',
    'San Francisco',
    'Palo Alto',
    'Mountain View',
    'Sunnyvale',
    'Santa Clara'
  ]

  return locations.map((location: string) => ({
    location,
    posts: blogPosts.filter(
      (post: BlogPost) =>
        post.serviceArea.includes(location) ||
        post.title.includes(location) ||
        post.keywords.some((keyword: string) => keyword.includes(location))
    ),
    count: blogPosts.filter(
      (post: BlogPost) =>
        post.serviceArea.includes(location) ||
        post.title.includes(location) ||
        post.keywords.some((keyword: string) => keyword.includes(location))
    ).length
  }))
}

// Generate hyper-local keyword clusters for specific cities
export const getHyperLocalKeywords = () => {
  const locationKeywords = {
    'San Francisco': [
      'San Francisco hibachi catering',
      'private hibachi chef San Francisco',
      'San Francisco party catering',
      'Bay Area hibachi chef in San Francisco',
      'SF birthday & holiday hibachi'
    ],
    'San Jose': [
      'San Jose hibachi catering',
      'Silicon Valley hibachi chef',
      'San Jose corporate catering hibachi',
      'tech company party catering San Jose',
      'hibachi for San Jose backyard parties'
    ],
    Oakland: [
      'Oakland hibachi catering',
      'East Bay hibachi chef for parties',
      'Oakland birthday party catering',
      'hibachi show in East Bay backyard',
      'private hibachi chef Oakland'
    ],
    'Palo Alto': [
      'Palo Alto hibachi catering',
      'Stanford hibachi private chef',
      'Palo Alto backyard hibachi parties',
      'luxury hibachi catering Palo Alto',
      'wedding hibachi chef Palo Alto'
    ],
    'Mountain View': [
      'Mountain View hibachi catering',
      'tech party hibachi Mountain View',
      'hibachi chef for Mountain View homes',
      'backyard hibachi party Mountain View',
      'corporate hibachi catering in Mountain View'
    ],
    'Santa Clara': [
      'Santa Clara hibachi catering',
      'corporate hibachi chef Santa Clara',
      'Silicon Valley hibachi dining',
      'Santa Clara backyard hibachi',
      'Santa Clara party catering hibachi'
    ],
    Sunnyvale: [
      'Sunnyvale hibachi catering',
      'backyard hibachi chef Sunnyvale',
      'Sunnyvale party catering',
      'hibachi dining experience Sunnyvale',
      'private hibachi chef for Sunnyvale homes'
    ]
  }

  return Object.entries(locationKeywords).map(([location, keywords]: [string, string[]]) => ({
    location,
    keywords,
    posts: blogPosts.filter(
      (post: BlogPost) =>
        post.serviceArea === location ||
        post.title.includes(location) ||
        post.keywords.some((keyword: string) =>
          keywords.some((locKeyword: string) => keyword.toLowerCase().includes(locKeyword.toLowerCase()))
        )
    )
  }))
}

// Generate location + event type combinations for content ideas
export const getLocationEventCombinations = () => {
  const locations = [
    'San Francisco',
    'San Jose',
    'Oakland',
    'Palo Alto',
    'Mountain View',
    'Santa Clara',
    'Sunnyvale'
  ]
  const events = ['Birthday', 'Wedding', 'Corporate', 'Graduation', 'Holiday', 'Backyard Party']

  const combinations = []
  for (const location of locations) {
    for (const event of events) {
      const existingPost = blogPosts.find(
        (post: BlogPost) => post.serviceArea === location && post.eventType.includes(event)
      )

      combinations.push({
        location,
        event,
        hasContent: !!existingPost,
        postId: existingPost?.id,
        suggestedTitle: `${location} ${event} Hibachi: ${getEventDescription(event, location)}`,
        suggestedKeywords: [
          `${location.toLowerCase()} ${event.toLowerCase()} hibachi`,
          `${event.toLowerCase()} hibachi ${location.toLowerCase()}`,
          `${location.toLowerCase()} party catering`,
          `hibachi chef ${location.toLowerCase()}`
        ]
      })
    }
  }

  return combinations
}

// Helper function for event descriptions
function getEventDescription(event: string, location: string): string {
  const descriptions = {
    Birthday: `Celebrate in Style`,
    Wedding: `Unique Reception Dining`,
    Corporate: `Team Building Excellence`,
    Graduation: `Academic Success Celebration`,
    Holiday: `Seasonal Entertainment`,
    'Backyard Party': `Private Chef Experience`
  }

  const techCities = ['San Jose', 'Mountain View', 'Santa Clara', 'Sunnyvale', 'Palo Alto']
  if (techCities.includes(location) && event === 'Corporate') {
    return 'Silicon Valley Team Building'
  }

  if (location === 'Palo Alto' && event === 'Corporate') {
    return 'Stanford Area Business Events'
  }

  return descriptions[event as keyof typeof descriptions] || 'Premium Catering'
} // Generate event-type content mapping
export const getEventTypeContentMap = () => {
  const eventTypes = [
    'Birthday',
    'Wedding',
    'Corporate',
    'Pool Party',
    'Graduation',
    'Holiday',
    'Backyard Party'
  ]

  return eventTypes.map((eventType: string) => ({
    eventType,
    posts: blogPosts.filter(
      (post: BlogPost) =>
        post.eventType.includes(eventType) ||
        post.keywords.some((keyword: string) => keyword.toLowerCase().includes(eventType.toLowerCase()))
    ),
    count: blogPosts.filter(
      (post: BlogPost) =>
        post.eventType.includes(eventType) ||
        post.keywords.some((keyword: string) => keyword.toLowerCase().includes(eventType.toLowerCase()))
    ).length
  }))
}

// Generate related content suggestions
export const getRelatedContentSuggestions = (currentPost: BlogPost) => {
  // Find posts with similar event types
  const eventMatches = blogPosts
    .filter((post: BlogPost) => post.id !== currentPost.id && post.eventType === currentPost.eventType)
    .slice(0, 3)

  // Find posts in same service area
  const locationMatches = blogPosts
    .filter(
      (post: BlogPost) =>
        post.id !== currentPost.id &&
        post.serviceArea === currentPost.serviceArea &&
        !eventMatches.includes(post)
    )
    .slice(0, 2)

  // Find posts with similar keywords
  const keywordMatches = blogPosts
    .filter(
      (post: BlogPost) =>
        post.id !== currentPost.id &&
        !eventMatches.includes(post) &&
        !locationMatches.includes(post) &&
        post.keywords.some((keyword: string) => currentPost.keywords.includes(keyword))
    )
    .slice(0, 2)

  return [...eventMatches, ...locationMatches, ...keywordMatches].slice(0, 6)
}

// Export all blog posts with enhanced SEO data
export const getBlogPostsWithSEO = () => {
  return blogPosts.map((post: BlogPost) => ({
    ...post,
    fullUrl: `https://myhibachi.com/blog/${post.slug}`,
    structuredData: {
      '@context': 'https://schema.org',
      '@type': 'BlogPosting',
      headline: post.title,
      description: post.excerpt,
      image: 'https://myhibachi.com/images/hibachi-og.jpg', // Add your OG image
      url: `https://myhibachi.com/blog/${post.slug}`,
      datePublished: new Date(post.date).toISOString(),
      dateModified: new Date(post.date).toISOString(),
      author: {
        '@type': 'Person',
        name: post.author
      },
      publisher: {
        '@type': 'Organization',
        name: 'My Hibachi',
        url: 'https://myhibachi.com'
      },
      keywords: post.keywords.join(', '),
      articleSection: post.category,
      about: [
        {
          '@type': 'Thing',
          name: 'Hibachi Catering'
        },
        {
          '@type': 'Place',
          name: post.serviceArea
        },
        {
          '@type': 'Event',
          name: post.eventType
        }
      ]
    }
  }))
}

const seoHelpers = {
  generateBlogListingStructuredData,
  getBlogSitemapUrls,
  getKeywordClusters,
  getLocationContentMap,
  getEventTypeContentMap,
  getRelatedContentSuggestions,
  getBlogPostsWithSEO,
  getHyperLocalKeywords,
  getLocationEventCombinations
}

export default seoHelpers
