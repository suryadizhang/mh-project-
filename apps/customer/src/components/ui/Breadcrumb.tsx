'use client';

import { ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

import styles from './Breadcrumb.module.css';

interface BreadcrumbItem {
  label: string;
  href: string;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  className?: string;
  lightBackground?: boolean;
}

export default function Breadcrumb({
  items,
  className = '',
  lightBackground = false,
}: BreadcrumbProps) {
  const pathname = usePathname();

  // Auto-generate breadcrumbs if not provided
  const breadcrumbItems = items || generateBreadcrumbs(pathname || '/');

  if (breadcrumbItems.length <= 1) {
    return null; // Don't show breadcrumbs for home page or single level
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn(styles.nav, lightBackground && styles.lightBackground, className)}
    >
      <ol className={styles.list}>
        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1;

          return (
            <li key={item.href} className={styles.item}>
              {isLast ? (
                <span className={styles.current} aria-current="page">
                  {item.label}
                </span>
              ) : (
                <>
                  <Link href={item.href} className={styles.link}>
                    {item.label}
                  </Link>
                  <span className={styles.separator} aria-hidden="true">
                    <ChevronRight size={14} />
                  </span>
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Auto-generate breadcrumbs from pathname
function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [{ label: 'Home', href: '/' }];

  let currentPath = '';

  segments.forEach((segment) => {
    currentPath += `/${segment}`;

    // Convert segment to readable label
    const label = formatSegmentLabel(segment);

    breadcrumbs.push({
      label,
      href: currentPath,
    });
  });

  return breadcrumbs;
}

// Format URL segment to readable label
function formatSegmentLabel(segment: string): string {
  // Handle special cases
  const specialCases: Record<string, string> = {
    BookUs: 'Book Us',
    GetQuote: 'Get Quote',
    faqs: 'FAQs',
    blog: 'Blog',
    menu: 'Menu',
    contact: 'Contact',
    quote: 'Get Quote',
    locations: 'Service Areas',
    'san-francisco': 'San Francisco',
    'san-jose': 'San Jose',
    'palo-alto': 'Palo Alto',
    'mountain-view': 'Mountain View',
    'santa-clara': 'Santa Clara',
    sacramento: 'Sacramento',
    oakland: 'Oakland',
    fremont: 'Fremont',
    sunnyvale: 'Sunnyvale',
  };

  if (specialCases[segment]) {
    return specialCases[segment];
  }

  // Default formatting: replace hyphens with spaces and capitalize
  return segment.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

// Export function for generating structured data
export function generateBreadcrumbStructuredData(
  items: BreadcrumbItem[],
  baseUrl: string = 'https://myhibachichef.com',
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.label,
      item: `${baseUrl}${item.href}`,
    })),
  };
}
