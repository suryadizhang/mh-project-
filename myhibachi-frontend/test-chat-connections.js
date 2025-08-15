#!/usr/bin/env node

// Test script to validate Facebook and Instagram chat connections
// Run: node test-chat-connections.js

const https = require('https');

console.log('🔍 TESTING CHAT CONNECTIONS FOR MY HIBACHI\n');

// Test 1: Facebook Page Validation
console.log('1️⃣ Testing Facebook Page Connection...');
const facebookPageId = '61577483702847';
const facebookPageUrl = `https://www.facebook.com/${facebookPageId}`;

https.get(facebookPageUrl, (res) => {
  if (res.statusCode === 200) {
    console.log('✅ Facebook Page is accessible');
    console.log(`   URL: ${facebookPageUrl}`);
  } else {
    console.log(`❌ Facebook Page returned status: ${res.statusCode}`);
  }
}).on('error', (err) => {
  console.log(`❌ Facebook Page connection error: ${err.message}`);
});

// Test 2: Instagram Profile Validation
console.log('\n2️⃣ Testing Instagram Profile Connection...');
const instagramUsername = 'my_hibachi_chef';
const instagramUrl = `https://www.instagram.com/${instagramUsername}/`;

https.get(instagramUrl, (res) => {
  if (res.statusCode === 200) {
    console.log('✅ Instagram Profile is accessible');
    console.log(`   URL: ${instagramUrl}`);
    console.log(`   DM URL: https://ig.me/m/${instagramUsername}`);
  } else {
    console.log(`❌ Instagram Profile returned status: ${res.statusCode}`);
  }
}).on('error', (err) => {
  console.log(`❌ Instagram Profile connection error: ${err.message}`);
});

// Test 3: Configuration Summary
console.log('\n3️⃣ Configuration Summary:');
console.log('📱 FACEBOOK MESSENGER:');
console.log(`   Page ID: ${facebookPageId}`);
console.log(`   App ID: 1234567890123456 (placeholder - needs real FB App)`);
console.log(`   Page URL: ${facebookPageUrl}`);

console.log('\n📸 INSTAGRAM DM:');
console.log(`   Username: @${instagramUsername}`);
console.log(`   Profile: ${instagramUrl}`);
console.log(`   DM Link: https://ig.me/m/${instagramUsername}`);

console.log('\n4️⃣ Next Steps Required:');
console.log('🔧 FACEBOOK SETUP:');
console.log('   1. Create Facebook App at https://developers.facebook.com/');
console.log('   2. Add Messenger product to the app');
console.log('   3. Connect the Facebook page to the app');
console.log('   4. Get the real App ID and update .env.local');
console.log('   5. Add your domain to the whitelist');

console.log('\n🔧 INSTAGRAM VERIFICATION:');
console.log('   1. Verify @my_hibachi_chef Instagram account exists');
console.log('   2. Ensure business account has messaging enabled');
console.log('   3. Test DM link manually');

console.log('\n5️⃣ Current Chat Button Status:');
console.log('💬 Messenger Button: ⚠️  Will show warning (needs real FB App ID)');
console.log('📱 Instagram Button: ✅ Should work (if account exists)');

console.log('\n✨ Test complete! Check the results above.\n');
