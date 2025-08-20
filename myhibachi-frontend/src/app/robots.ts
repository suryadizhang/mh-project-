import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/admin/',
          '/api/',
          '/private/',
          '/_next/',
          '/test/',
        ],
      },
      {
        userAgent: 'Googlebot',
        allow: '/',
        disallow: [
          '/admin/',
          '/api/',
          '/private/',
        ],
      },
    ],
    sitemap: 'https://myhibachi.com/sitemap.xml',
    host: 'https://myhibachi.com',
  }
}
