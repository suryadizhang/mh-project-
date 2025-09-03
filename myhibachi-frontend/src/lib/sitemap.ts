import { BlogPost } from '@/data/blogPosts'

export interface SitemapUrl {
  url: string
  lastModified: string
  changeFrequency: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never'
  priority: number
}

export class BlogSitemapGenerator {
  private baseUrl: string
  private posts: BlogPost[]

  constructor(baseUrl: string, posts: BlogPost[]) {
    this.baseUrl = baseUrl.replace(/\/$/, '') // Remove trailing slash
    this.posts = posts
  }

  generateSitemap(): SitemapUrl[] {
    const urls: SitemapUrl[] = []

    // Main blog page
    urls.push({
      url: `${this.baseUrl}/blog`,
      lastModified: new Date().toISOString(),
      changeFrequency: 'daily',
      priority: 0.8
    })

    // Individual blog posts
    this.posts.forEach(post => {
      urls.push({
        url: `${this.baseUrl}/blog/${post.slug}`,
        lastModified: new Date(post.date).toISOString(),
        changeFrequency: 'monthly',
        priority: post.featured ? 0.9 : 0.7
      })
    })

    // Category pages
    const categories = [...new Set(this.posts.map(post => post.category))]
    categories.forEach(category => {
      const categorySlug = this.slugify(category)
      urls.push({
        url: `${this.baseUrl}/blog/category/${categorySlug}`,
        lastModified: new Date().toISOString(),
        changeFrequency: 'weekly',
        priority: 0.6
      })
    })

    // Author pages
    const authors = [...new Set(this.posts.map(post => post.author))]
    authors.forEach(author => {
      const authorSlug = this.slugify(author)
      urls.push({
        url: `${this.baseUrl}/blog/author/${authorSlug}`,
        lastModified: new Date().toISOString(),
        changeFrequency: 'weekly',
        priority: 0.5
      })
    })

    // Service area pages
    const serviceAreas = [...new Set(this.posts.map(post => post.serviceArea).filter(Boolean))]
    serviceAreas.forEach(area => {
      const areaSlug = this.slugify(area!)
      urls.push({
        url: `${this.baseUrl}/blog/location/${areaSlug}`,
        lastModified: new Date().toISOString(),
        changeFrequency: 'weekly',
        priority: 0.6
      })
    })

    // Archive pages (yearly)
    const years = [...new Set(this.posts.map(post => new Date(post.date).getFullYear()))]
    years.forEach(year => {
      urls.push({
        url: `${this.baseUrl}/blog/archive/${year}`,
        lastModified: new Date().toISOString(),
        changeFrequency: 'monthly',
        priority: 0.4
      })
    })

    // Tag pages (for popular tags)
    const allTags = this.posts.flatMap(post => post.keywords || [])
    const tagCounts = allTags.reduce(
      (acc, tag) => {
        acc[tag] = (acc[tag] || 0) + 1
        return acc
      },
      {} as Record<string, number>
    )

    const popularTags = Object.entries(tagCounts)
      .filter(([, count]) => count >= 3) // Only tags with 3+ posts
      .map(([tag]) => tag)

    popularTags.forEach(tag => {
      const tagSlug = this.slugify(tag)
      urls.push({
        url: `${this.baseUrl}/blog/tag/${tagSlug}`,
        lastModified: new Date().toISOString(),
        changeFrequency: 'weekly',
        priority: 0.5
      })
    })

    return urls.sort((a, b) => b.priority - a.priority)
  }

  generateXMLSitemap(): string {
    const urls = this.generateSitemap()

    const xmlUrls = urls
      .map(
        url => `
  <url>
    <loc>${this.escapeXml(url.url)}</loc>
    <lastmod>${url.lastModified}</lastmod>
    <changefreq>${url.changeFrequency}</changefreq>
    <priority>${url.priority}</priority>
  </url>`
      )
      .join('')

    return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${xmlUrls}
</urlset>`
  }

  generateNewsSitemap(): string {
    // News sitemap for recent posts (last 2 days)
    const recentPosts = this.posts.filter(post => {
      const postDate = new Date(post.date)
      const twoDaysAgo = new Date()
      twoDaysAgo.setDate(twoDaysAgo.getDate() - 2)
      return postDate >= twoDaysAgo
    })

    if (recentPosts.length === 0) {
      return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" 
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
</urlset>`
    }

    const newsUrls = recentPosts
      .map(
        post => `
  <url>
    <loc>${this.escapeXml(`${this.baseUrl}/blog/${post.slug}`)}</loc>
    <news:news>
      <news:publication>
        <news:name>My Hibachi Blog</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${new Date(post.date).toISOString()}</news:publication_date>
      <news:title>${this.escapeXml(post.title)}</news:title>
      <news:keywords>${this.escapeXml((post.keywords || []).join(', '))}</news:keywords>
    </news:news>
  </url>`
      )
      .join('')

    return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" 
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
${newsUrls}
</urlset>`
  }

  generateImageSitemap(): string {
    const imageUrls = this.posts
      .filter(post => post.image)
      .map(
        post => `
  <url>
    <loc>${this.escapeXml(`${this.baseUrl}/blog/${post.slug}`)}</loc>
    <image:image>
      <image:loc>${this.escapeXml(`${this.baseUrl}${post.image}`)}</image:loc>
      <image:title>${this.escapeXml(post.title)}</image:title>
      <image:caption>${this.escapeXml(post.imageAlt || post.excerpt)}</image:caption>
    </image:image>
  </url>`
      )
      .join('')

    return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
${imageUrls}
</urlset>`
  }

  generateSitemapIndex(): string {
    const lastModified = new Date().toISOString()

    return `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>${this.baseUrl}/sitemap-blog.xml</loc>
    <lastmod>${lastModified}</lastmod>
  </sitemap>
  <sitemap>
    <loc>${this.baseUrl}/sitemap-blog-news.xml</loc>
    <lastmod>${lastModified}</lastmod>
  </sitemap>
  <sitemap>
    <loc>${this.baseUrl}/sitemap-blog-images.xml</loc>
    <lastmod>${lastModified}</lastmod>
  </sitemap>
</sitemapindex>`
  }

  private slugify(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '') // Remove special characters
      .replace(/[\s_-]+/g, '-') // Replace spaces/underscores with hyphens
      .replace(/^-+|-+$/g, '') // Remove leading/trailing hyphens
  }

  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;')
  }

  // Helper method to get SEO statistics
  getSEOStatistics() {
    const urls = this.generateSitemap()
    const categories = [...new Set(this.posts.map(post => post.category))]
    const authors = [...new Set(this.posts.map(post => post.author))]
    const serviceAreas = [...new Set(this.posts.map(post => post.serviceArea).filter(Boolean))]

    return {
      totalUrls: urls.length,
      blogPosts: this.posts.length,
      featuredPosts: this.posts.filter(post => post.featured).length,
      categories: categories.length,
      authors: authors.length,
      serviceAreas: serviceAreas.length,
      postsWithImages: this.posts.filter(post => post.image).length,
      averagePriority: urls.reduce((sum, url) => sum + url.priority, 0) / urls.length,
      lastUpdated: new Date().toISOString()
    }
  }
}
