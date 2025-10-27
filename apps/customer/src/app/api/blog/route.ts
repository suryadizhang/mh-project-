/**
 * Blog API Route - Server-side data loading
 *
 * This API route handles blog data loading on the server side,
 * allowing client components to fetch data without bundling fs module.
 */

import { NextRequest, NextResponse } from 'next/server';

import { blogService } from '@/lib/blog/blogService';

export const dynamic = 'force-dynamic';

/**
 * GET /api/blog
 *
 * Query params:
 * - type: 'featured' | 'seasonal' | 'recent' | 'all' | 'search' | 'tags' | 'categories'
 * - limit: number (optional)
 * - query: string (for search)
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const type = searchParams.get('type') || 'all';
    const limit = searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : undefined;
    const query = searchParams.get('query') || '';

    let data;

    switch (type) {
      case 'featured':
        data = { posts: await blogService.getFeaturedPosts(limit) };
        break;

      case 'seasonal':
        data = { posts: await blogService.getSeasonalPosts(limit) };
        break;

      case 'recent':
        data = { posts: await blogService.getRecentPosts(limit || 10) };
        break;

      case 'all':
        data = { posts: await blogService.getAllPosts() };
        break;

      case 'search':
        data = { posts: await blogService.searchPosts(query) };
        break;

      case 'tags':
        data = { tags: await blogService.getAllTags() };
        break;

      case 'categories':
        data = { categories: await blogService.getCategories() };
        break;

      case 'serviceAreas':
        data = { serviceAreas: await blogService.getServiceAreas() };
        break;

      case 'eventTypes':
        data = { eventTypes: await blogService.getEventTypes() };
        break;

      default:
        return NextResponse.json(
          { error: 'Invalid type parameter' },
          { status: 400 }
        );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Blog API error:', error);
    return NextResponse.json(
      { error: 'Failed to load blog posts' },
      { status: 500 }
    );
  }
}
