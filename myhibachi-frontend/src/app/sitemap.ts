import { MetadataRoute } from 'next'
import blogPosts from '@/data/blogPosts'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://myhibachi.com'

  // Static pages
  const staticPages = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 1,
    },
    {
      url: `${baseUrl}/menu`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.9,
    },
    {
      url: `${baseUrl}/booking`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    {
      url: `${baseUrl}/contact`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    },
    {
      url: `${baseUrl}/blog`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.8,
    },
    {
      url: `${baseUrl}/faqs`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.7,
    },
  ]

  // Blog posts
  const blogPages = blogPosts.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: new Date(post.date),
    changeFrequency: 'monthly' as const,
    priority: post.featured ? 0.8 : 0.6,
  }))

  // Location-specific pages
  const locations = ['San Francisco', 'San Jose', 'Oakland', 'Palo Alto', 'Mountain View', 'Santa Clara', 'Sunnyvale']
  const locationPages = locations.map((location) => ({
    url: `${baseUrl}/${location.toLowerCase().replace(' ', '-')}-hibachi-catering`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.7,
  }))

  return [...staticPages, ...blogPages, ...locationPages]
}
