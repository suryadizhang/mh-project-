/* eslint-disable @typescript-eslint/no-explicit-any */
import { BlogPost } from '@/data/blogPosts'

export interface StructuredDataConfig {
  baseUrl: string
  siteName: string
  publisherName: string
  publisherLogo: string
  socialProfiles: string[]
}

export class BlogSchemaGenerator {
  private config: StructuredDataConfig

  constructor(config: StructuredDataConfig) {
    this.config = config
  }

  generateArticleSchema(post: BlogPost): Record<string, any> {
    const schema: Record<string, any> = {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: post.title,
      description: post.metaDescription || post.excerpt,
      image: post.image ? `${this.config.baseUrl}${post.image}` : undefined,
      author: {
        '@type': 'Person',
        name: post.author,
        url: `${this.config.baseUrl}/blog/author/${this.slugify(post.author)}`
      },
      publisher: {
        '@type': 'Organization',
        name: this.config.publisherName,
        logo: {
          '@type': 'ImageObject',
          url: this.config.publisherLogo
        }
      },
      datePublished: new Date(post.date).toISOString(),
      dateModified: new Date(post.date).toISOString(),
      mainEntityOfPage: {
        '@type': 'WebPage',
        '@id': `${this.config.baseUrl}/blog/${post.slug}`
      },
      articleSection: post.category,
      keywords: post.keywords?.join(', '),
      wordCount: this.estimateWordCount(post.content || post.excerpt),
      inLanguage: 'en-US',
      isAccessibleForFree: true,
      ...(post.featured && { 
        about: {
          '@type': 'Thing',
          name: 'Hibachi Catering',
          description: 'Professional hibachi catering services'
        }
      })
    }

    // Add local business context for location-specific posts
    if (post.serviceArea && post.serviceArea !== 'All Areas') {
      schema.spatialCoverage = {
        '@type': 'Place',
        name: post.serviceArea,
        geo: this.getLocationCoordinates(post.serviceArea)
      }
    }

    // Add event context for event-specific posts
    if (post.eventType && post.eventType !== 'General') {
      schema.mentions = {
        '@type': 'Event',
        name: `${post.eventType} with Hibachi Catering`,
        description: `Professional hibachi catering for ${post.eventType.toLowerCase()} events`
      }
    }

    return schema
  }

  generateBreadcrumbSchema(post: BlogPost): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: [
        {
          '@type': 'ListItem',
          position: 1,
          name: 'Home',
          item: this.config.baseUrl
        },
        {
          '@type': 'ListItem',
          position: 2,
          name: 'Blog',
          item: `${this.config.baseUrl}/blog`
        },
        {
          '@type': 'ListItem',
          position: 3,
          name: post.category,
          item: `${this.config.baseUrl}/blog/category/${this.slugify(post.category)}`
        },
        {
          '@type': 'ListItem',
          position: 4,
          name: post.title,
          item: `${this.config.baseUrl}/blog/${post.slug}`
        }
      ]
    }
  }

  generateWebsiteSchema(): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: this.config.siteName,
      url: this.config.baseUrl,
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: `${this.config.baseUrl}/blog?search={search_term_string}`
        },
        'query-input': 'required name=search_term_string'
      },
      publisher: {
        '@type': 'Organization',
        name: this.config.publisherName,
        logo: this.config.publisherLogo,
        sameAs: this.config.socialProfiles
      }
    }
  }

  generateOrganizationSchema(): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: this.config.publisherName,
      url: this.config.baseUrl,
      logo: this.config.publisherLogo,
      sameAs: this.config.socialProfiles,
      contactPoint: {
        '@type': 'ContactPoint',
        contactType: 'Customer Service',
        availableLanguage: 'English'
      },
      areaServed: [
        {
          '@type': 'Place',
          name: 'San Francisco Bay Area'
        },
        {
          '@type': 'Place', 
          name: 'Sacramento'
        },
        {
          '@type': 'Place',
          name: 'San Jose'
        }
      ],
      serviceType: 'Hibachi Catering Services'
    }
  }

  generateBlogSchema(posts: BlogPost[]): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'Blog',
      name: 'My Hibachi Blog',
      description: 'Expert hibachi catering insights, seasonal menus, and event planning tips',
      url: `${this.config.baseUrl}/blog`,
      publisher: {
        '@type': 'Organization',
        name: this.config.publisherName,
        logo: this.config.publisherLogo
      },
      blogPost: posts.slice(0, 10).map(post => ({
        '@type': 'BlogPosting',
        headline: post.title,
        url: `${this.config.baseUrl}/blog/${post.slug}`,
        datePublished: new Date(post.date).toISOString(),
        author: {
          '@type': 'Person',
          name: post.author
        }
      })),
      inLanguage: 'en-US'
    }
  }

  generateFAQSchema(post: BlogPost): object | null {
    // Extract FAQ-like content from blog posts
    const content = post.content || post.excerpt
    const faqPatterns = [
      /Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)/gi,
      /\?\s*(.+?)\s*-\s*(.+?)(?=\?|$)/gi
    ]

    const faqs: Array<{question: string, answer: string}> = []
    
    for (const pattern of faqPatterns) {
      let match
      while ((match = pattern.exec(content)) !== null) {
        faqs.push({
          question: match[1].trim(),
          answer: match[2].trim()
        })
      }
    }

    if (faqs.length === 0) return null

    return {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faqs.map(faq => ({
        '@type': 'Question',
        name: faq.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: faq.answer
        }
      }))
    }
  }

  generateHowToSchema(post: BlogPost): object | null {
    // Detect how-to content in blog posts
    const content = post.content || post.excerpt
    const hasHowToKeywords = [
      'how to', 'step by step', 'guide', 'tutorial', 
      'instructions', 'process', 'method'
    ].some(keyword => 
      post.title.toLowerCase().includes(keyword) || 
      content.toLowerCase().includes(keyword)
    )

    if (!hasHowToKeywords) return null

    // Extract steps (simplified)
    const stepPattern = /(\d+\.|\bstep\s+\d+|\bfirst\b|\bsecond\b|\bthird\b|\bnext\b|\bfinally\b)/gi
    const hasSteps = stepPattern.test(content)

    if (!hasSteps) return null

    return {
      '@context': 'https://schema.org',
      '@type': 'HowTo',
      name: post.title,
      description: post.excerpt,
      image: post.image ? `${this.config.baseUrl}${post.image}` : undefined,
      totalTime: this.extractDuration(post.readTime),
      supply: [
        {
          '@type': 'HowToSupply',
          name: 'Hibachi grill'
        },
        {
          '@type': 'HowToSupply', 
          name: 'Fresh ingredients'
        }
      ],
      tool: [
        {
          '@type': 'HowToTool',
          name: 'Spatula'
        },
        {
          '@type': 'HowToTool',
          name: 'Cooking utensils'
        }
      ],
      step: [
        {
          '@type': 'HowToStep',
          name: 'Planning',
          text: 'Plan your hibachi event according to guest count and preferences'
        },
        {
          '@type': 'HowToStep',
          name: 'Preparation',
          text: 'Prepare ingredients and set up cooking area'
        },
        {
          '@type': 'HowToStep',
          name: 'Cooking',
          text: 'Cook hibachi-style with entertainment and interaction'
        }
      ]
    }
  }

  generateRecipeSchema(post: BlogPost): object | null {
    // Check if post contains recipe content
    const hasRecipeKeywords = [
      'recipe', 'ingredients', 'cooking', 'preparation',
      'serves', 'portions', 'cook time'
    ].some(keyword => 
      post.title.toLowerCase().includes(keyword) || 
      (post.keywords || []).some(k => k.toLowerCase().includes(keyword))
    )

    if (!hasRecipeKeywords) return null

    return {
      '@context': 'https://schema.org',
      '@type': 'Recipe',
      name: post.title,
      description: post.excerpt,
      image: post.image ? `${this.config.baseUrl}${post.image}` : undefined,
      author: {
        '@type': 'Person',
        name: post.author
      },
      datePublished: new Date(post.date).toISOString(),
      prepTime: 'PT15M',
      cookTime: 'PT30M',
      totalTime: 'PT45M',
      recipeYield: '4-6 servings',
      recipeCategory: 'Hibachi',
      recipeCuisine: 'Japanese',
      keywords: post.keywords?.join(', '),
      recipeIngredient: [
        'Fresh vegetables',
        'Premium meat or seafood',
        'Hibachi sauce',
        'Rice',
        'Seasonings'
      ],
      recipeInstructions: [
        {
          '@type': 'HowToStep',
          text: 'Prepare and organize all ingredients'
        },
        {
          '@type': 'HowToStep',
          text: 'Heat hibachi grill to proper temperature'
        },
        {
          '@type': 'HowToStep',
          text: 'Cook with hibachi techniques and entertainment'
        }
      ],
      nutrition: {
        '@type': 'NutritionInformation',
        servingSize: '1 portion'
      }
    }
  }

  private slugify(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '')
  }

  private estimateWordCount(text: string): number {
    return text.split(/\s+/).length
  }

  private extractDuration(readTime: string): string {
    const match = readTime.match(/(\d+)/)
    if (match) {
      return `PT${match[1]}M`
    }
    return 'PT5M'
  }

  private getLocationCoordinates(location: string): object {
    const coordinates: Record<string, {lat: number, lng: number}> = {
      'San Francisco': { lat: 37.7749, lng: -122.4194 },
      'San Jose': { lat: 37.3382, lng: -121.8863 },
      'Sacramento': { lat: 38.5816, lng: -121.4944 },
      'Oakland': { lat: 37.8044, lng: -122.2712 },
      'Silicon Valley': { lat: 37.4419, lng: -122.1430 },
      'Peninsula': { lat: 37.5630, lng: -122.3255 },
      'South Bay': { lat: 37.3541, lng: -121.9552 },
      'East Bay': { lat: 37.8272, lng: -122.2913 }
    }

    const coords = coordinates[location] || coordinates['San Jose']
    
    return {
      '@type': 'GeoCoordinates',
      latitude: coords.lat,
      longitude: coords.lng
    }
  }
}
