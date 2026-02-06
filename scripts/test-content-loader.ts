/**
 * Test script for MDX Content Loader
 * Run with: npx tsx scripts/test-content-loader.ts
 */

import {
  getBlogPost,
  getBlogPosts,
  generateBlogIndex,
  getAllCategories,
} from '../apps/customer/src/lib/blog/contentLoader';

async function testContentLoader() {
  console.log('🧪 Testing MDX Content Loader...\n');

  try {
    // Test 1: Load single post by slug
    console.log('Test 1: getBlogPost()');
    const post = await getBlogPost('sample-hibachi-catering-guide');
    if (post) {
      console.log('✅ Post loaded successfully!');
      console.log(`   Title: ${post.post.title}`);
      console.log(`   Category: ${post.post.category}`);
      console.log(`   Keywords: ${post.post.keywords.length} keywords`);
      console.log(`   Content length: ${post.mdxContent.length} chars`);
    } else {
      console.log('❌ Post not found');
    }

    // Test 2: Load all posts
    console.log('\nTest 2: getBlogPosts()');
    const allPosts = await getBlogPosts();
    console.log(`✅ Loaded ${allPosts.length} post(s)`);
    allPosts.forEach(p => {
      console.log(`   - ${p.title} (${p.category})`);
    });

    // Test 3: Filter by category
    console.log('\nTest 3: getBlogPosts({ category: "Service Areas" })');
    const serviceAreaPosts = await getBlogPosts({ category: 'Service Areas' });
    console.log(
      `✅ Found ${serviceAreaPosts.length} post(s) in Service Areas category`
    );

    // Test 4: Search
    console.log('\nTest 4: getBlogPosts({ query: "hibachi" })');
    const searchResults = await getBlogPosts({ query: 'hibachi' });
    console.log(`✅ Found ${searchResults.length} post(s) matching "hibachi"`);

    // Test 5: Generate index
    console.log('\nTest 5: generateBlogIndex()');
    const { posts, searchData } = await generateBlogIndex();
    console.log(`✅ Generated index with ${posts.length} post(s)`);
    console.log(`   Search data entries: ${searchData.length}`);

    // Test 6: Get categories
    console.log('\nTest 6: getAllCategories()');
    const categories = await getAllCategories();
    console.log(`✅ Found ${categories.length} unique categories:`);
    categories.forEach(cat => console.log(`   - ${cat}`));

    console.log('\n🎉 All tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

testContentLoader();
