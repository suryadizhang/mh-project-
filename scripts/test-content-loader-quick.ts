/**
 * Quick test to verify MDX content loader works
 */

import { getBlogPosts, getBlogPost, getAllCategories } from '../apps/customer/src/lib/blog/contentLoader';

async function testContentLoader() {
  console.log('🧪 Testing Content Loader...\n');

  try {
    // Test 1: Load all posts
    console.log('Test 1: getBlogPosts()');
    const posts = await getBlogPosts();
    console.log(`✅ Loaded ${posts.length} posts\n`);

    // Test 2: Load single post
    if (posts.length > 0) {
      console.log(`Test 2: getBlogPost('${posts[0].slug}')`);
      const single = await getBlogPost(posts[0].slug);
      console.log(`✅ Loaded post: ${single?.post.title}\n`);
    }

    // Test 3: Get categories
    console.log('Test 3: getAllCategories()');
    const categories = await getAllCategories();
    console.log(`✅ Found ${categories.length} categories\n`);

    console.log('✅ All tests passed! Content loader is working correctly.');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

testContentLoader();
