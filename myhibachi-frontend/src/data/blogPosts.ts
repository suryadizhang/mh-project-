// SEO-Optimized Blog Posts Data for My Hibachi
// ===============================================

export interface BlogPost {
  id: number
  title: string
  slug: string
  excerpt: string
  content?: string
  metaDescription: string
  keywords: string[]
  author: string
  date: string
  readTime: string
  category: string
  serviceArea: string
  eventType: string
  featured?: boolean
  seasonal?: boolean
}

export const blogPosts: BlogPost[] = [
  // Featured/Priority Posts (Seasonal & High-Traffic)
  {
    id: 1,
    title: "Bay Area Hibachi Catering: Live Chef Entertainment",
    slug: "bay-area-hibachi-catering-live-chef-entertainment",
    excerpt: "Experience authentic hibachi catering in the Bay Area. Professional chefs bring the restaurant experience to your home for unforgettable events.",
    metaDescription: "Experience authentic hibachi catering in the Bay Area. Professional chefs bring the restaurant to your home for unforgettable events. Book today!",
    keywords: ["bay area hibachi", "mobile hibachi chef", "san francisco catering", "live cooking show", "hibachi at home"],
    author: "Chef Takeshi",
    date: "August 14, 2025",
    readTime: "6 min read",
    category: "Service Areas",
    serviceArea: "Bay Area",
    eventType: "General",
    featured: true
  },
  {
    id: 2,
    title: "Valentine's Day Hibachi: Romance at Home",
    slug: "valentines-day-hibachi-catering-date-night-home",
    excerpt: "Create the perfect Valentine's date night with hibachi catering at home. Romantic atmosphere, fresh ingredients, intimate dining experience.",
    metaDescription: "Valentine's Day hibachi catering creates perfect date nights at home. Romantic atmosphere, fresh ingredients, intimate dining experience.",
    keywords: ["valentines day hibachi", "romantic dinner at home", "date night catering", "couples hibachi", "romantic dining"],
    author: "Chef Maria",
    date: "August 10, 2025",
    readTime: "5 min read",
    category: "Seasonal",
    serviceArea: "All Areas",
    eventType: "Romantic",
    featured: true,
    seasonal: true
  },
  {
    id: 3,
    title: "Sacramento Birthday Party Hibachi: Make It Memorable",
    slug: "sacramento-birthday-party-hibachi-memorable",
    excerpt: "Transform Sacramento birthday parties with hibachi catering. Fresh ingredients, live entertainment that all ages love. Free quotes available!",
    metaDescription: "Transform Sacramento birthday parties with hibachi catering. Fresh ingredients, live entertainment, all ages love it. Free quotes available!",
    keywords: ["sacramento birthday party", "hibachi birthday", "mobile hibachi sacramento", "party catering sacramento", "birthday entertainment"],
    author: "Sarah Chen",
    date: "August 8, 2025",
    readTime: "7 min read",
    category: "Service Areas",
    serviceArea: "Sacramento",
    eventType: "Birthday",
    featured: true
  },
  {
    id: 4,
    title: "Corporate Hibachi Events San Jose: Team Building Fun",
    slug: "corporate-hibachi-events-san-jose-team-building",
    excerpt: "San Jose corporate events become exciting with hibachi catering. Build teams while enjoying premium Japanese cuisine with professional service.",
    metaDescription: "San Jose corporate events get exciting with hibachi catering. Build teams while enjoying premium Japanese cuisine. Professional service guaranteed.",
    keywords: ["san jose corporate events", "business catering san jose", "team building activities", "corporate hibachi", "office catering"],
    author: "David Kim",
    date: "February 6, 2025",
    readTime: "6 min read",
    category: "Corporate",
    serviceArea: "San Jose",
    eventType: "Corporate",
    featured: true
  },
  {
    id: 5,
    title: "Wedding Hibachi Catering Peninsula: Unique Receptions",
    slug: "wedding-hibachi-catering-peninsula-unique-receptions",
    excerpt: "Peninsula wedding receptions become unforgettable with hibachi catering. Interactive dining experience your guests will never forget.",
    metaDescription: "Peninsula wedding receptions become unforgettable with hibachi catering. Interactive dining experience your guests will never forget.",
    keywords: ["peninsula wedding catering", "unique wedding reception", "hibachi wedding", "interactive wedding dining", "bay area weddings"],
    author: "Chef Yuki",
    date: "February 4, 2025",
    readTime: "8 min read",
    category: "Weddings",
    serviceArea: "Peninsula",
    eventType: "Wedding"
  },
  {
    id: 6,
    title: "Oakland Graduation Party Hibachi: Celebrate in Style",
    slug: "oakland-graduation-party-hibachi-celebrate-style",
    excerpt: "Oakland graduation parties shine with hibachi catering. Fresh ingredients, live cooking, perfect for celebrating achievements together.",
    metaDescription: "Oakland graduation parties shine with hibachi catering. Fresh ingredients, live cooking, perfect for celebrating achievements together.",
    keywords: ["oakland graduation party", "hibachi graduation", "mobile chef oakland", "celebration catering oakland", "party entertainment"],
    author: "Michelle Park",
    date: "February 2, 2025",
    readTime: "5 min read",
    category: "Celebrations",
    serviceArea: "Oakland",
    eventType: "Graduation"
  },
  {
    id: 7,
    title: "Spring Hibachi Gardens: Fresh Ingredients Meet Fresh Air",
    slug: "spring-hibachi-gardens-fresh-ingredients-air",
    excerpt: "Spring hibachi catering showcases fresh seasonal ingredients in garden settings. Perfect outdoor weather, vibrant flavors, natural ambiance.",
    metaDescription: "Spring hibachi catering showcases fresh seasonal ingredients in garden settings. Perfect outdoor weather, vibrant flavors, natural ambiance.",
    keywords: ["spring hibachi catering", "outdoor hibachi spring", "garden party catering", "seasonal menu", "fresh ingredients"],
    author: "Chef Takeshi",
    date: "January 30, 2025",
    readTime: "6 min read",
    category: "Seasonal",
    serviceArea: "All Areas",
    eventType: "Outdoor",
    seasonal: true
  },
  {
    id: 8,
    title: "Fremont Holiday Party Catering: Hibachi Experience at Home",
    slug: "fremont-holiday-party-catering-hibachi-experience-home",
    excerpt: "Fremont holiday parties become memorable with hibachi catering. Warm gatherings, fresh food, entertainment all included in one package.",
    metaDescription: "Fremont holiday parties become memorable with hibachi catering. Warm gatherings, fresh food, entertainment all included in one package.",
    keywords: ["fremont holiday catering", "holiday party ideas", "mobile hibachi fremont", "winter party catering", "holiday entertaining"],
    author: "Carlos Rodriguez",
    date: "January 28, 2025",
    readTime: "5 min read",
    category: "Holidays",
    serviceArea: "Fremont",
    eventType: "Holiday"
  },
  {
    id: 9,
    title: "Summer Backyard Hibachi Parties: Beat the Heat in Style",
    slug: "summer-backyard-hibachi-parties-beat-heat-style",
    excerpt: "Summer hibachi parties bring restaurant excitement to your backyard. Fresh seafood, grilled meats, perfect for hot weather gatherings.",
    metaDescription: "Summer hibachi parties bring restaurant excitement to your backyard. Fresh seafood, grilled meats, perfect for hot weather gatherings.",
    keywords: ["summer hibachi party", "backyard catering", "outdoor hibachi", "summer party ideas", "mobile hibachi summer"],
    author: "Chef Maria",
    date: "January 26, 2025",
    readTime: "7 min read",
    category: "Seasonal",
    serviceArea: "All Areas",
    eventType: "Summer",
    seasonal: true
  },
  {
    id: 10,
    title: "Elk Grove Anniversary Hibachi: Romantic Dining at Home",
    slug: "elk-grove-anniversary-hibachi-romantic-dining-home",
    excerpt: "Elk Grove anniversary celebrations become intimate with hibachi catering. Romantic atmosphere, fresh ingredients, unforgettable memories.",
    metaDescription: "Elk Grove anniversary celebrations become intimate with hibachi catering. Romantic atmosphere, fresh ingredients, unforgettable memories.",
    keywords: ["elk grove anniversary", "romantic hibachi dinner", "anniversary catering", "intimate dining", "couples hibachi"],
    author: "Sophie Chen",
    date: "January 24, 2025",
    readTime: "5 min read",
    category: "Romantic",
    serviceArea: "Elk Grove",
    eventType: "Anniversary"
  },
  {
    id: 11,
    title: "Roseville Kids Birthday Hibachi: Entertainment They'll Love",
    slug: "roseville-kids-birthday-hibachi-entertainment-love",
    excerpt: "Roseville kids birthday parties get exciting with hibachi catering. Safe, fun, educational cooking show perfect for young audiences.",
    metaDescription: "Roseville kids birthday parties get exciting with hibachi catering. Safe, fun, educational cooking show perfect for young audiences.",
    keywords: ["roseville kids birthday", "children hibachi party", "kid-friendly catering", "birthday entertainment roseville", "family hibachi"],
    author: "Lisa Wong",
    date: "January 22, 2025",
    readTime: "6 min read",
    category: "Family",
    serviceArea: "Roseville",
    eventType: "Kids Birthday"
  },
  {
    id: 12,
    title: "Folsom Corporate Retreat Hibachi: Unique Team Experiences",
    slug: "folsom-corporate-retreat-hibachi-unique-team-experiences",
    excerpt: "Folsom corporate retreats become memorable with hibachi catering. Team building through shared dining, professional service included.",
    metaDescription: "Folsom corporate retreats become memorable with hibachi catering. Team building through shared dining, professional service included.",
    keywords: ["folsom corporate retreat", "team building catering", "business retreat dining", "corporate hibachi folsom", "group catering"],
    author: "Michael Kim",
    date: "January 20, 2025",
    readTime: "7 min read",
    category: "Corporate",
    serviceArea: "Folsom",
    eventType: "Corporate Retreat"
  },
  {
    id: 13,
    title: "Davis University Party Hibachi: Student-Friendly Fun",
    slug: "davis-university-party-hibachi-student-friendly-fun",
    excerpt: "Davis university parties get upgraded with hibachi catering. Affordable group rates, fresh ingredients, perfect for student celebrations.",
    metaDescription: "Davis university parties get upgraded with hibachi catering. Affordable group rates, fresh ingredients, perfect for student celebrations.",
    keywords: ["davis university party", "college hibachi", "student party catering", "affordable hibachi davis", "group discounts"],
    author: "Amanda Lee",
    date: "January 18, 2025",
    readTime: "5 min read",
    category: "Student",
    serviceArea: "Davis",
    eventType: "University Party"
  },
  {
    id: 14,
    title: "Stockton Family Reunion Hibachi: Bring Everyone Together",
    slug: "stockton-family-reunion-hibachi-bring-everyone-together",
    excerpt: "Stockton family reunions unite generations with hibachi catering. Large group accommodation, something for everyone, memorable experiences.",
    metaDescription: "Stockton family reunions unite generations with hibachi catering. Large group accommodation, something for everyone, memorable experiences.",
    keywords: ["stockton family reunion", "large group catering", "family hibachi", "reunion catering stockton", "multi-generational dining"],
    author: "Robert Martinez",
    date: "January 16, 2025",
    readTime: "6 min read",
    category: "Family",
    serviceArea: "Stockton",
    eventType: "Family Reunion"
  },
  {
    id: 15,
    title: "Modesto Quinceañera Hibachi: Traditional Meets Modern",
    slug: "modesto-quinceanera-hibachi-traditional-meets-modern",
    excerpt: "Modesto quinceañera celebrations blend tradition with hibachi excitement. Cultural fusion dining, entertainment, coming-of-age perfection.",
    metaDescription: "Modesto quinceañera celebrations blend tradition with hibachi excitement. Cultural fusion dining, entertainment, coming-of-age perfection.",
    keywords: ["modesto quinceanera", "cultural celebration catering", "hibachi quinceanera", "traditional party catering", "hispanic celebrations"],
    author: "Elena Flores",
    date: "January 14, 2025",
    readTime: "7 min read",
    category: "Cultural",
    serviceArea: "Modesto",
    eventType: "Quinceañera"
  },
  {
    id: 16,
    title: "Livermore Wine Country Hibachi: Perfect Pairing Experience",
    slug: "livermore-wine-country-hibachi-perfect-pairing-experience",
    excerpt: "Livermore wine country events pair perfectly with hibachi catering. Fresh cuisine complements local wines, sophisticated entertaining.",
    metaDescription: "Livermore wine country events pair perfectly with hibachi catering. Fresh cuisine complements local wines, sophisticated entertaining.",
    keywords: ["livermore wine country", "wine pairing hibachi", "livermore catering", "sophisticated dining", "wine country events"],
    author: "Chef Thomas",
    date: "January 12, 2025",
    readTime: "8 min read",
    category: "Wine Country",
    serviceArea: "Livermore",
    eventType: "Wine Tasting"
  },
  {
    id: 17,
    title: "Fall Hibachi Catering: Seasonal Ingredients & Warm Comfort",
    slug: "fall-hibachi-catering-seasonal-ingredients-warm-comfort",
    excerpt: "Fall hibachi catering features seasonal ingredients for cozy gatherings. Pumpkin specials, warm comfort food, autumn entertaining experience.",
    metaDescription: "Fall hibachi catering features seasonal ingredients for cozy gatherings. Pumpkin specials, warm comfort food, autumn entertaining experience.",
    keywords: ["fall hibachi catering", "seasonal hibachi menu", "autumn party catering", "seasonal ingredients", "fall entertaining"],
    author: "Chef Yuki",
    date: "January 10, 2025",
    readTime: "6 min read",
    category: "Seasonal",
    serviceArea: "All Areas",
    eventType: "Fall",
    seasonal: true
  },
  {
    id: 18,
    title: "New Year's Eve Hibachi Party: Ring in 2025 with Style",
    slug: "new-years-eve-hibachi-party-ring-2025-style",
    excerpt: "New Year's Eve hibachi parties create spectacular celebrations. Countdown while chefs perform, fresh ingredients, unforgettable midnight dining.",
    metaDescription: "New Year's Eve hibachi parties create spectacular celebrations. Countdown while chefs perform, fresh ingredients, unforgettable midnight dining.",
    keywords: ["new years eve hibachi", "nye party catering", "countdown celebration", "party hibachi", "holiday entertaining"],
    author: "DJ Park",
    date: "January 8, 2025",
    readTime: "5 min read",
    category: "Holidays",
    serviceArea: "All Areas",
    eventType: "New Years",
    seasonal: true
  },
  {
    id: 19,
    title: "Mother's Day Hibachi Brunch: Pamper Mom at Home",
    slug: "mothers-day-hibachi-brunch-pamper-mom-home",
    excerpt: "Mother's Day hibachi brunch brings restaurant luxury home. No cooking, pure pampering with fresh ingredients and entertainment.",
    metaDescription: "Mother's Day hibachi brunch brings restaurant luxury home to mom. No cooking, pure pampering with fresh ingredients and entertainment.",
    keywords: ["mothers day hibachi", "brunch catering", "pamper mom", "mothers day dining", "special occasion hibachi"],
    author: "Grace Liu",
    date: "January 6, 2025",
    readTime: "6 min read",
    category: "Holidays",
    serviceArea: "All Areas",
    eventType: "Mothers Day",
    seasonal: true
  },
  {
    id: 20,
    title: "Father's Day Hibachi Grilling: Dad's Favorite Experience",
    slug: "fathers-day-hibachi-grilling-dad-favorite-experience",
    excerpt: "Father's Day hibachi catering combines dad's love of grilling with entertainment. Interactive experience, fresh meats, perfect celebration.",
    metaDescription: "Father's Day hibachi catering combines dad's love of grilling with entertainment. Interactive experience, fresh meats, perfect masculine celebration.",
    keywords: ["fathers day hibachi", "dad party catering", "grilling entertainment", "fathers day dining", "masculine celebration"],
    author: "Chef Mike",
    date: "January 4, 2025",
    readTime: "5 min read",
    category: "Holidays",
    serviceArea: "All Areas",
    eventType: "Fathers Day",
    seasonal: true
  },
  {
    id: 21,
    title: "Baby Shower Hibachi: Gender Reveal with Culinary Flair",
    slug: "baby-shower-hibachi-gender-reveal-culinary-flair",
    excerpt: "Baby shower hibachi catering adds culinary excitement to gender reveals. Interactive cooking, fresh ingredients, memorable celebration dining.",
    metaDescription: "Baby shower hibachi catering adds culinary excitement to gender reveals. Interactive cooking, fresh ingredients, memorable celebration dining.",
    keywords: ["baby shower hibachi", "gender reveal catering", "baby celebration", "pregnancy party", "interactive baby shower"],
    author: "Jennifer Chen",
    date: "January 2, 2025",
    readTime: "5 min read",
    category: "Celebrations",
    serviceArea: "All Areas",
    eventType: "Baby Shower"
  },
  {
    id: 22,
    title: "Retirement Party Hibachi: Career Celebration Dining",
    slug: "retirement-party-hibachi-career-celebration-dining",
    excerpt: "Retirement party hibachi catering honors career achievements with dignity. Sophisticated dining, fresh ingredients, meaningful celebration.",
    metaDescription: "Retirement party hibachi catering honors career achievements with dignity. Sophisticated dining, fresh ingredients, meaningful celebration experience.",
    keywords: ["retirement party hibachi", "career celebration", "retirement catering", "achievement dining", "professional celebration"],
    author: "Harold Kim",
    date: "December 30, 2024",
    readTime: "6 min read",
    category: "Professional",
    serviceArea: "All Areas",
    eventType: "Retirement"
  },
  {
    id: 23,
    title: "Holiday Office Party Hibachi: Corporate Celebration Experience",
    slug: "holiday-office-party-hibachi-corporate-celebration-experience",
    excerpt: "Holiday office party hibachi catering transforms workplace celebrations. Team bonding, fresh ingredients, professional entertaining.",
    metaDescription: "Holiday office party hibachi catering transforms workplace celebrations. Team bonding, fresh ingredients, professional entertaining at its finest.",
    keywords: ["holiday office party", "corporate holiday catering", "workplace celebration", "team bonding dining", "business holiday party"],
    author: "Patricia Wong",
    date: "December 28, 2024",
    readTime: "7 min read",
    category: "Corporate",
    serviceArea: "All Areas",
    eventType: "Office Party"
  },
  {
    id: 24,
    title: "The Art of Hibachi: More Than Just Cooking",
    slug: "art-of-hibachi-more-than-just-cooking",
    excerpt: "Discover the rich history and cultural significance behind hibachi cooking and why it makes for such an entertaining dining experience.",
    metaDescription: "Discover the rich history and cultural significance behind hibachi cooking and why it makes for such an entertaining dining experience.",
    keywords: ["hibachi history", "japanese cooking culture", "hibachi entertainment", "cooking show", "cultural dining"],
    author: "Chef Takeshi",
    date: "December 26, 2024",
    readTime: "8 min read",
    category: "Educational",
    serviceArea: "All Areas",
    eventType: "Educational"
  },
  {
    id: 25,
    title: "Seasonal Hibachi: Fresh Ingredients for Every Season",
    slug: "seasonal-hibachi-fresh-ingredients-every-season",
    excerpt: "Learn how we adapt our menu throughout the year to incorporate the freshest seasonal ingredients for optimal flavor and quality.",
    metaDescription: "Learn about how we adapt our menu throughout the year to incorporate the freshest seasonal ingredients.",
    keywords: ["seasonal hibachi menu", "fresh ingredients", "seasonal cooking", "menu adaptation", "quality ingredients"],
    author: "Chef Maria",
    date: "December 24, 2024",
    readTime: "6 min read",
    category: "Educational",
    serviceArea: "All Areas",
    eventType: "Educational",
    seasonal: true
  }
]

// Helper functions for filtering and organizing blog posts
export const getFeaturedPosts = (): BlogPost[] => {
  return blogPosts.filter(post => post.featured).slice(0, 6)
}

export const getSeasonalPosts = (): BlogPost[] => {
  return blogPosts.filter(post => post.seasonal).slice(0, 4)
}

export const getPostsByServiceArea = (area: string): BlogPost[] => {
  return blogPosts.filter(post =>
    post.serviceArea === area || post.serviceArea === "All Areas"
  )
}

export const getPostsByEventType = (eventType: string): BlogPost[] => {
  return blogPosts.filter(post =>
    post.eventType.toLowerCase().includes(eventType.toLowerCase())
  )
}

export const getPostsByCategory = (category: string): BlogPost[] => {
  return blogPosts.filter(post => post.category === category)
}

export const getRecentPosts = (limit: number = 10): BlogPost[] => {
  return blogPosts.slice(0, limit)
}

export const searchPosts = (query: string): BlogPost[] => {
  const lowercaseQuery = query.toLowerCase()
  return blogPosts.filter(post =>
    post.title.toLowerCase().includes(lowercaseQuery) ||
    post.excerpt.toLowerCase().includes(lowercaseQuery) ||
    post.keywords.some(keyword => keyword.toLowerCase().includes(lowercaseQuery)) ||
    post.serviceArea.toLowerCase().includes(lowercaseQuery) ||
    post.eventType.toLowerCase().includes(lowercaseQuery)
  )
}

export default blogPosts
