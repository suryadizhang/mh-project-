// Local Landing Page Generator for Hyper-Targeted SEO
// ===================================================

import { getHyperLocalKeywords } from './seo'

interface LocationData {
  tagline: string
  speciality: string
  uniqueFeatures: string[]
  neighborhoods: string[]
  popularEvents: string[]
  localPartners: string[]
  priceRange: string
}

// Generate location-specific landing page content
export const generateLocationPage = (location: string) => {
  const locationData = getLocationInfo(location)
  const localKeywords = getHyperLocalKeywords().find(loc => loc.location === location)

  return {
    title: `${location} Hibachi Catering | ${locationData.tagline}`,
    metaDescription: `Professional ${location.toLowerCase()} hibachi catering with private chefs. ${
      locationData.speciality
    }. Book your interactive dining experience today!`,
    h1: `${location} Hibachi Catering: ${locationData.tagline}`,
    content: generateLocationContent(location, locationData),
    keywords: localKeywords?.keywords || [],
    schema: generateLocationSchema(location, locationData),
    serviceAreas: locationData.neighborhoods,
    ctaText: `Book ${location} Hibachi Catering`,
    relatedPosts: localKeywords?.posts || []
  }
}

// Location-specific information database
function getLocationInfo(location: string) {
  const locationDatabase = {
    'San Francisco': {
      tagline: 'Private Chef Experience in the City',
      speciality: 'Perfect for SF apartment parties, rooftop events, and urban celebrations',
      uniqueFeatures: [
        'Urban apartment setup expertise',
        'Rooftop and small space adaptability',
        'City logistics and parking handled',
        'Fresh ingredients from SF farmers markets'
      ],
      neighborhoods: [
        'SOMA',
        'Financial District',
        'Nob Hill',
        'Russian Hill',
        'Pacific Heights',
        'Mission',
        'Castro',
        'Richmond',
        'Sunset'
      ],
      popularEvents: [
        'Tech executive dinners',
        'Rooftop birthday parties',
        'Urban holiday celebrations',
        'Apartment housewarming'
      ],
      localPartners: ['Ferry Building vendors', 'Farmers Market suppliers'],
      priceRange: '$$$'
    },
    'San Jose': {
      tagline: "Silicon Valley's Interactive Dining Experience",
      speciality: 'Specializing in tech company events and Silicon Valley celebrations',
      uniqueFeatures: [
        'Tech company corporate events',
        'Multi-cultural menu options',
        'Large backyard party expertise',
        'Team building entertainment'
      ],
      neighborhoods: [
        'Downtown San Jose',
        'Santana Row',
        'Willow Glen',
        'Almaden Valley',
        'East San Jose',
        'Evergreen'
      ],
      popularEvents: [
        'Startup celebrations',
        'Employee birthday parties',
        'Corporate team building',
        'Tech family gatherings'
      ],
      localPartners: ['Local tech cafeterias', 'Silicon Valley suppliers'],
      priceRange: '$$-$$$'
    },
    Oakland: {
      tagline: 'East Bay Entertainment at Home',
      speciality: 'Bringing hibachi shows to East Bay backyards and celebrations',
      uniqueFeatures: [
        'East Bay backyard expertise',
        'Multi-generational family events',
        'Cultural fusion menus',
        'Community-focused service'
      ],
      neighborhoods: [
        'Downtown Oakland',
        'Rockridge',
        'Temescal',
        'Lake Merritt',
        'Hills',
        'Fruitvale'
      ],
      popularEvents: [
        'Family reunions',
        'Graduation parties',
        'Wedding receptions',
        'Cultural celebrations'
      ],
      localPartners: ['Oakland farmers markets', 'Bay Area suppliers'],
      priceRange: '$$'
    },
    'Palo Alto': {
      tagline: 'Luxury Stanford Area Private Chef Experience',
      speciality: 'Elegant hibachi catering for Stanford area luxury events',
      uniqueFeatures: [
        'Luxury presentation standards',
        'Stanford University connections',
        'High-end ingredient sourcing',
        'Sophisticated service protocols'
      ],
      neighborhoods: [
        'Downtown Palo Alto',
        'University Avenue',
        'Professorville',
        'Crescent Park',
        'Old Palo Alto',
        'Barron Park'
      ],
      popularEvents: [
        'Faculty celebrations',
        'Luxury weddings',
        'Stanford graduations',
        'Executive dinners'
      ],
      localPartners: ['Stanford suppliers', 'Luxury ingredient sources'],
      priceRange: '$$$$'
    },
    'Mountain View': {
      tagline: 'Tech Party Catering for Silicon Valley Homes',
      speciality: 'Specialized in Google area tech company and home celebrations',
      uniqueFeatures: [
        'Tech campus event expertise',
        'Google area service focus',
        'Innovation in presentation',
        'Tech-friendly scheduling'
      ],
      neighborhoods: [
        'Downtown Mountain View',
        'Whisman',
        'Bubb Road',
        'Old Mountain View',
        'Willows',
        'Moffett Field area'
      ],
      popularEvents: [
        'Google employee parties',
        'Startup celebrations',
        'Tech family events',
        'Product launch parties'
      ],
      localPartners: ['Google cafeterias', 'Tech company vendors'],
      priceRange: '$$-$$$'
    },
    'Santa Clara': {
      tagline: 'Silicon Valley Corporate & Backyard Events',
      speciality: 'Perfect for Santa Clara University and corporate celebrations',
      uniqueFeatures: [
        'University event expertise',
        'Corporate facility setup',
        'Multi-venue adaptability',
        'Academic celebration focus'
      ],
      neighborhoods: [
        'Downtown Santa Clara',
        'Mission',
        'Rivermark',
        'Laurelwood',
        'Santa Clara University area'
      ],
      popularEvents: [
        'SCU graduations',
        'Corporate events',
        'Academic celebrations',
        'Family gatherings'
      ],
      localPartners: ['SCU vendors', 'Corporate suppliers'],
      priceRange: '$$-$$$'
    },
    Sunnyvale: {
      tagline: 'Private Home Dining Experience',
      speciality: 'Family-focused hibachi catering for Sunnyvale homes',
      uniqueFeatures: [
        'Family-friendly service',
        'Backyard setup expertise',
        'Multi-generational menus',
        'Residential area focus'
      ],
      neighborhoods: [
        'Downtown Sunnyvale',
        'Cherry',
        'Lakewood',
        'Fair Oaks',
        'Ponderosa',
        'Lawrence'
      ],
      popularEvents: [
        'Family reunions',
        'Birthday celebrations',
        'Graduation parties',
        'Anniversary dinners'
      ],
      localPartners: ['Local family suppliers', 'Community vendors'],
      priceRange: '$$'
    }
  }

  return (
    locationDatabase[location as keyof typeof locationDatabase] || {
      tagline: 'Professional Hibachi Catering',
      speciality: 'Interactive dining experiences for your special events',
      uniqueFeatures: ['Professional service', 'Fresh ingredients', 'Interactive entertainment'],
      neighborhoods: [],
      popularEvents: [],
      localPartners: [],
      priceRange: '$$'
    }
  )
}

// Generate location-specific page content
function generateLocationContent(location: string, locationData: LocationData) {
  return `
# ${location} Hibachi Catering: ${locationData.tagline}

Transform your ${location} celebration with professional hibachi catering that brings restaurant-quality entertainment directly to your location. ${
    locationData.speciality
  }

## Why ${location} Chooses Our Hibachi Catering

${locationData.uniqueFeatures
  .map((feature: string) => `**${feature}**: Professional expertise tailored to ${location} events`)
  .join('\n')}

## Popular ${location} Hibachi Events
${locationData.popularEvents.map((event: string) => `- 🎉 ${event}`).join('\n')}

## ${location} Service Areas
${locationData.neighborhoods.map((area: string) => `- ${area}`).join('\n')}

## What Makes Our ${location} Service Special

Our ${location} hibachi catering team understands the unique needs of ${location} events. From logistics and setup to menu customization and entertainment, we ensure your celebration is perfectly tailored to ${location}'s style and preferences.

### Fresh, Local Ingredients
We partner with ${locationData.localPartners.join(
    ' and '
  )} to source the freshest ingredients for your ${location} hibachi experience.

### Professional Setup
Our experienced team handles all aspects of setup and logistics specific to ${location} venues and residential areas.

## Book Your ${location} Hibachi Experience

Ready to create an unforgettable ${location} celebration? Our professional hibachi chefs bring restaurant-quality entertainment and dining directly to your location.

**Call now for your free ${location} hibachi catering quote!**
`
}

// Generate location-specific schema markup
function generateLocationSchema(location: string, locationData: LocationData) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: `${location} Hibachi Catering`,
    description: `Professional hibachi catering service in ${location}. ${locationData.speciality}`,
    provider: {
      '@type': 'Organization',
      name: 'My Hibachi',
      url: 'https://myhibachichef.com'
    },
    areaServed: {
      '@type': 'City',
      name: location
    },
    serviceType: 'Hibachi Catering',
    priceRange: locationData.priceRange,
    availableChannel: {
      '@type': 'ServiceChannel',
      url: `https://myhibachichef.com/locations/${location.toLowerCase().replace(' ', '-')}`
    }
  }
}

// Generate all location pages
export const generateAllLocationPages = () => {
  const locations = [
    'San Francisco',
    'San Jose',
    'Oakland',
    'Palo Alto',
    'Mountain View',
    'Santa Clara',
    'Sunnyvale'
  ]

  return locations.map(location => ({
    location,
    slug: location.toLowerCase().replace(' ', '-'),
    ...generateLocationPage(location)
  }))
}

// Generate location-specific social media content
export const generateLocationSocialContent = (location: string) => {
  const locationData = getLocationInfo(location)

  return {
    facebook: {
      text: `🍤 Now serving ${location}! Professional hibachi catering bringing interactive dining to your ${location} celebrations. ${
        locationData.speciality
      }

Book your ${location} hibachi experience today! #${location.replace(
        ' ',
        ''
      )}Hibachi #InteractiveDining`,
      hashtags: [`${location.replace(' ', '')}Hibachi`, 'InteractiveDining', 'PrivateChef']
    },
    instagram: {
      caption: `🔥 ${location} hibachi is here!

${locationData.speciality}

Perfect for:
${locationData.popularEvents.map((event: string) => `🎉 ${event}`).join('\n')}

Serving: ${locationData.neighborhoods.slice(0, 3).join(', ')} and more!

Book your ${location} experience 👆 link in bio

#${location.replace(' ', '')}Hibachi #PrivateChef #InteractiveDining #${location.replace(
        ' ',
        ''
      )}Events`,
      hashtags: [`${location.replace(' ', '')}Hibachi`, 'PrivateChef', 'InteractiveDining']
    },
    twitter: {
      text: `🍤 ${location} hibachi catering now available! ${locationData.tagline}

${locationData.speciality}

Book: myhibachi.com/${location.toLowerCase().replace(' ', '-')}

#${location.replace(' ', '')}Hibachi #InteractiveDining`,
      hashtags: [`${location.replace(' ', '')}Hibachi`, 'InteractiveDining', 'PrivateChef']
    }
  }
}

const locationHelpers = {
  generateLocationPage,
  generateAllLocationPages,
  generateLocationSocialContent,
  getLocationInfo
}

export default locationHelpers
