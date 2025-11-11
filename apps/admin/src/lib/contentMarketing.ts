// Content Marketing & Social Media Helper Functions
// ================================================

import { type BlogPost, blogPosts } from '@/data/blogPosts';

// Generate social media post content from blog posts
export const generateSocialMediaContent = (postId: number) => {
  const post = blogPosts.find((p: BlogPost) => p.id === postId);
  if (!post) return null;

  const baseUrl = 'https://myhibachi.com';

  return {
    twitter: {
      text: `${post.title.slice(0, 120)}... 🍤🔥\n\n#hibachi #catering #${post.serviceArea.replace(
        ' ',
        ''
      )} #${post.eventType.replace(' ', '')}\n\n${baseUrl}/blog/${post.slug}`,
      hashtags: [
        'hibachi',
        'catering',
        post.serviceArea.replace(' ', ''),
        post.eventType.replace(' ', ''),
      ],
    },
    facebook: {
      text: `🍤 ${post.title}\n\n${post.excerpt}\n\nRead the complete guide: ${baseUrl}/blog/${
        post.slug
      }\n\n#HibachiCatering #${post.serviceArea.replace(' ', '')}Events #InteractiveDining`,
      image: `${baseUrl}/images/hibachi-social.jpg`, // You'll need to add this image
    },
    instagram: {
      caption: `🔥 ${post.title}\n\n${post.excerpt.slice(0, 150)}...\n\n📍 Serving ${
        post.serviceArea
      }\n🎉 Perfect for ${
        post.eventType
      } events\n\nLink in bio for full guide!\n\n#hibachi #catering #${post.serviceArea
        .replace(' ', '')
        .toLowerCase()} #${post.eventType
        .replace(' ', '')
        .toLowerCase()} #mobilechef #interactivedining #partycatering`,
      hashtags: [
        'hibachi',
        'catering',
        post.serviceArea.replace(' ', '').toLowerCase(),
        post.eventType.replace(' ', '').toLowerCase(),
        'mobilechef',
        'interactivedining',
        'partycatering',
      ],
    },
    linkedin: {
      text: `${post.title}\n\n${
        post.excerpt
      }\n\nOur professional hibachi catering services bring restaurant-quality dining and entertainment directly to your ${post.eventType.toLowerCase()} event in ${
        post.serviceArea
      }.\n\nRead the complete guide: ${baseUrl}/blog/${
        post.slug
      }\n\n#ProfessionalCatering #CorporateEvents #TeamBuilding #HibachCatering`,
    },
  };
};

// Generate email newsletter content
export const generateNewsletterContent = (
  featured: number[] = [],
  seasonal: number[] = []
) => {
  const featuredPosts = featured
    .map((id: number) => blogPosts.find((p: BlogPost) => p.id === id))
    .filter(Boolean);
  const seasonalPosts = seasonal
    .map((id: number) => blogPosts.find((p: BlogPost) => p.id === id))
    .filter(Boolean);

  const currentMonth = new Date().toLocaleDateString('en-US', {
    month: 'long',
  });

  return {
    subject: `${currentMonth} Hibachi Event Ideas & Seasonal Menu Updates`,
    preheader: `Fresh hibachi catering ideas for your upcoming ${currentMonth.toLowerCase()} celebrations`,
    featured: featuredPosts,
    seasonal: seasonalPosts,
    ctaText: 'Book Your Hibachi Event',
    ctaUrl: 'https://myhibachi.com/booking',
  };
};

// Generate local business directory listings
export const generateBusinessListings = () => {
  const businessInfo = {
    name: 'My Hibachi',
    description:
      'Professional hibachi catering services bringing interactive Japanese dining experiences directly to your location. Serving Bay Area, Sacramento, San Jose, and surrounding communities with premium ingredients and entertaining chef performances.',
    services: [
      'Birthday Party Hibachi Catering',
      'Corporate Event Hibachi',
      'Wedding Reception Hibachi',
      'Pool Party Catering',
      'Holiday Party Hibachi',
      'Graduation Celebration Catering',
      'Family Reunion Hibachi',
      'Backyard Party Catering',
    ],
    serviceAreas: [
      'San Francisco Bay Area',
      'Sacramento',
      'San Jose',
      'Oakland',
      'Fremont',
      'Stockton',
      'Napa Valley',
      'Peninsula',
    ],
    keywords:
      'hibachi catering, mobile hibachi chef, Japanese catering, interactive dining, live cooking show, party catering, corporate catering, wedding catering',
    website: 'https://myhibachi.com',
    blog: 'https://myhibachi.com/blog',
  };

  return {
    google: {
      ...businessInfo,
      category: 'Catering Service',
      attributes: [
        'Offers takeout',
        'Offers delivery',
        'Good for groups',
        'Accepts credit cards',
      ],
    },
    yelp: {
      ...businessInfo,
      categories: ['Caterers', 'Japanese', 'Event Planning & Services'],
      specialties:
        'Interactive hibachi cooking shows, premium ingredients, professional mobile setup',
    },
    nextdoor: {
      ...businessInfo,
      type: 'Professional Service',
      serviceType: 'Catering & Event Services',
    },
  };
};

// Generate content calendar suggestions
export const generateContentCalendar = () => {
  const months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];

  const seasonalEvents = {
    January: [
      'New Year parties',
      'winter corporate events',
      'indoor celebrations',
    ],
    February: [
      "Valentine's Day",
      'winter sports parties',
      'indoor romantic dinners',
    ],
    March: ['spring celebrations', "St. Patrick's Day", 'school fundraisers'],
    April: [
      'Easter celebrations',
      'spring outdoor events',
      'graduation planning',
    ],
    May: ["Mother's Day", 'graduation parties', 'outdoor season start'],
    June: ["Father's Day", 'wedding season', 'graduation celebrations'],
    July: ['summer pool parties', 'Fourth of July', 'vacation gatherings'],
    August: ['back-to-school parties', 'late summer events', 'family reunions'],
    September: [
      'fall season start',
      'harvest celebrations',
      'corporate retreats',
    ],
    October: ['Halloween parties', 'fall festivals', 'holiday planning'],
    November: [
      'Thanksgiving alternatives',
      'holiday corporate events',
      'family gatherings',
    ],
    December: ['holiday parties', 'New Year planning', 'winter celebrations'],
  };

  return months.map(month => ({
    month,
    seasonalEvents: seasonalEvents[month as keyof typeof seasonalEvents],
    contentIdeas: [
      `${month} Hibachi Menu Highlights`,
      `Perfect ${month} Events for Hibachi Catering`,
      `${month} Party Planning with Hibachi`,
      `Seasonal Ingredients in ${month}`,
    ],
    socialMediaThemes: [
      `#${month}Hibachi`,
      `#${month}Events`,
      `#SeasonalMenu`,
      `#PartyPlanning`,
    ],
  }));
};

// Generate blog post performance tracking
export const generateContentMetrics = () => {
  return blogPosts.map((post: BlogPost) => ({
    id: post.id,
    title: post.title,
    slug: post.slug,
    category: post.category,
    serviceArea: post.serviceArea,
    eventType: post.eventType,
    keywords: post.keywords,
    featured: post.featured || false,
    seasonal: post.seasonal || false,
    estimatedSEOValue: calculateSEOValue(post),
    socialMediaPotential: calculateSocialPotential(post),
    conversionPotential: calculateConversionPotential(post),
  }));
};

// Helper function to calculate SEO value
function calculateSEOValue(post: BlogPost): number {
  let score = 0;

  // Keyword density and variety
  score += post.keywords.length * 2;

  // Location-specific content
  if (post.serviceArea !== 'All Areas') score += 10;

  // Event-specific content
  if (post.eventType !== 'General') score += 10;

  // Featured status
  if (post.featured) score += 15;

  // Recent content
  const postDate = new Date(post.date);
  const isRecent = Date.now() - postDate.getTime() < 90 * 24 * 60 * 60 * 1000; // 90 days
  if (isRecent) score += 10;

  return Math.min(score, 100); // Cap at 100
}

// Helper function to calculate social media potential
function calculateSocialPotential(post: BlogPost): number {
  let score = 0;

  // Visual content potential
  if (post.eventType.includes('Party') || post.eventType.includes('Wedding'))
    score += 20;

  // Seasonal relevance
  if (post.seasonal) score += 15;

  // Local interest
  if (post.serviceArea !== 'All Areas') score += 10;

  // Trending events
  const trendingEvents = ['Birthday', 'Wedding', 'Corporate', 'Pool Party'];
  if (trendingEvents.some((event: string) => post.eventType.includes(event)))
    score += 15;

  return Math.min(score, 100);
}

// Helper function to calculate conversion potential
function calculateConversionPotential(post: BlogPost): number {
  let score = 0;

  // High-intent event types
  const highIntentEvents = ['Wedding', 'Corporate', 'Birthday', 'Graduation'];
  if (highIntentEvents.some((event: string) => post.eventType.includes(event)))
    score += 25;

  // Specific service areas (local intent)
  if (post.serviceArea !== 'All Areas') score += 20;

  // Featured content
  if (post.featured) score += 15;

  // Comprehensive guides (longer read time)
  const wordCount = post.excerpt.length * 10; // Estimate based on excerpt
  if (wordCount > 500) score += 10;

  return Math.min(score, 100);
}

const contentMarketingHelpers = {
  generateSocialMediaContent,
  generateNewsletterContent,
  generateBusinessListings,
  generateContentCalendar,
  generateContentMetrics,
};

export default contentMarketingHelpers;
