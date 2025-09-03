import Script from 'next/script'

import { type BlogPost } from '@/data/blogPosts'

interface BlogStructuredDataProps {
  post: BlogPost
}

export default function BlogStructuredData({ post }: BlogStructuredDataProps) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.metaDescription,
    image: 'https://myhibachi.com/images/myhibachi-logo.png', // Update with your actual domain
    author: {
      '@type': 'Person',
      name: post.author
    },
    publisher: {
      '@type': 'Organization',
      name: 'My Hibachi',
      logo: {
        '@type': 'ImageObject',
        url: 'https://myhibachi.com/images/myhibachi-logo.png'
      }
    },
    datePublished: new Date(post.date).toISOString(),
    dateModified: new Date(post.date).toISOString(),
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `https://myhibachi.com/blog/${post.slug}`
    },
    keywords: post.keywords.join(', '),
    articleSection: post.category,
    about: {
      '@type': 'Service',
      name: 'Hibachi Catering',
      serviceType: 'Mobile Catering',
      areaServed:
        post.serviceArea === 'All Areas'
          ? ['Bay Area', 'Sacramento', 'San Jose', 'Oakland', 'Fremont', 'Peninsula']
          : [post.serviceArea],
      provider: {
        '@type': 'Organization',
        name: 'My Hibachi'
      }
    }
  }

  return (
    <Script
      id={`blog-structured-data-${post.id}`}
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(structuredData)
      }}
    />
  )
}
