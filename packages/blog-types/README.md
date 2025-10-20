# @my-hibachi/blog-types

Shared TypeScript types for My Hibachi blog system.

## Installation

This package is part of the My Hibachi monorepo. Reference it using workspace protocol:

```json
{
  "dependencies": {
    "@my-hibachi/blog-types": "workspace:*"
  }
}
```

## Usage

```typescript
import type { BlogPost, BlogCategory, BlogAuthor } from '@my-hibachi/blog-types';

const post: BlogPost = {
  id: 1,
  title: 'Bay Area Hibachi Catering',
  slug: 'bay-area-hibachi-catering',
  // ...
};
```

## Type Reference

### Core Types

- **BlogPost** - Main blog post interface
- **BlogPostContent** - Post with full MDX/HTML content
- **BlogCategory** - Post categorization
- **BlogAuthor** - Content creator information
- **BlogTag** - Flexible post tagging
- **BlogSeries** - Multi-part content series

### Utility Types

- **BlogPagination** - Pagination metadata
- **BlogFilters** - Search and filter parameters
- **BlogSearchResult** - Search results with metadata
- **BlogFrontmatter** - MDX file metadata
- **BlogConfig** - Site-wide blog configuration

## Future Compatibility

These types are designed to work with:
- Current TypeScript array implementation
- File-based MDX content (Phase 1)
- Headless CMS (Phase 2)
- Database backend (Phase 3)

The `id` field supports both `number` (legacy) and `string` (CMS) for forward compatibility.
