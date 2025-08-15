#!/usr/bin/env node

/**
 * Complete Connection Verification Test
 * Tests all Facebook and Instagram connections, configurations, and functionality
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

console.log('🔍 COMPLETE CONNECTION VERIFICATION TEST');
console.log('=====================================\n');

// Test configuration
const testConfig = {
  baseUrl: 'http://localhost:3003',
  timeoutMs: 10000,
  expectedFacebookPageId: '61577483702847',
  expectedInstagramUsername: 'my_hibachi_chef',
  expectedFacebookUrl: 'https://www.facebook.com/people/My-hibachi/61577483702847/',
  expectedInstagramUrl: 'https://www.instagram.com/my_hibachi_chef/',
  expectedInstagramDmUrl: 'https://ig.me/m/my_hibachi_chef'
};

// Utility function to make HTTP requests
function makeRequest(url, options = {}) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      timeout: testConfig.timeoutMs,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        ...options.headers
      }
    };

    const client = urlObj.protocol === 'https:' ? https : require('http');
    const req = client.request(requestOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: data,
          url: url,
          redirected: res.statusCode >= 300 && res.statusCode < 400
        });
      });
    });

    req.on('error', (error) => {
      resolve({
        status: 'ERROR',
        error: error.message,
        url: url
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        status: 'TIMEOUT',
        error: 'Request timeout',
        url: url
      });
    });

    req.end();
  });
}

// Test 1: Configuration Files
async function testConfigurationFiles() {
  console.log('📋 1. CONFIGURATION FILES TEST');
  console.log('--------------------------------');

  const contactJsonPath = path.join(__dirname, 'src', 'data', 'contact.json');
  const contactDataPath = path.join(__dirname, 'src', 'lib', 'contactData.ts');

  try {
    // Check contact.json
    if (fs.existsSync(contactJsonPath)) {
      const contactData = JSON.parse(fs.readFileSync(contactJsonPath, 'utf8'));
      console.log('✅ contact.json exists and is valid JSON');
      console.log(`   📱 Facebook Page ID: ${contactData.facebookPageId}`);
      console.log(`   📸 Instagram Username: ${contactData.instagramUsername}`);
      console.log(`   📧 Email: ${contactData.email}`);
      console.log(`   📞 Phone: ${contactData.phone}`);

      // Verify expected values
      if (contactData.facebookPageId === testConfig.expectedFacebookPageId) {
        console.log('✅ Facebook Page ID matches expected value');
      } else {
        console.log(`❌ Facebook Page ID mismatch: expected ${testConfig.expectedFacebookPageId}, got ${contactData.facebookPageId}`);
      }

      if (contactData.instagramUsername === testConfig.expectedInstagramUsername) {
        console.log('✅ Instagram Username matches expected value');
      } else {
        console.log(`❌ Instagram Username mismatch: expected ${testConfig.expectedInstagramUsername}, got ${contactData.instagramUsername}`);
      }
    } else {
      console.log('❌ contact.json not found');
    }

    // Check contactData.ts
    if (fs.existsSync(contactDataPath)) {
      console.log('✅ contactData.ts exists');
    } else {
      console.log('❌ contactData.ts not found');
    }

  } catch (error) {
    console.log(`❌ Configuration files error: ${error.message}`);
  }
  console.log();
}

// Test 2: Local Development Server
async function testLocalServer() {
  console.log('🌐 2. LOCAL DEVELOPMENT SERVER TEST');
  console.log('-----------------------------------');

  try {
    const response = await makeRequest(`${testConfig.baseUrl}/contact`);

    if (response.status === 200) {
      console.log('✅ Contact page loads successfully');

      // Check for chat components in HTML
      if (response.body.includes('InlineMessengerButton') || response.body.includes('messenger-chat-button')) {
        console.log('✅ Messenger chat component found in page');
      } else {
        console.log('⚠️  Messenger chat component not found in page HTML');
      }

      if (response.body.includes('InlineInstagramButton') || response.body.includes('instagram-chat-button')) {
        console.log('✅ Instagram chat component found in page');
      } else {
        console.log('⚠️  Instagram chat component not found in page HTML');
      }

      // Check for Facebook Page ID in HTML
      if (response.body.includes(testConfig.expectedFacebookPageId)) {
        console.log('✅ Facebook Page ID found in page HTML');
      } else {
        console.log('⚠️  Facebook Page ID not found in page HTML');
      }

      // Check for Instagram username in HTML
      if (response.body.includes(testConfig.expectedInstagramUsername)) {
        console.log('✅ Instagram username found in page HTML');
      } else {
        console.log('⚠️  Instagram username not found in page HTML');
      }

    } else {
      console.log(`❌ Contact page failed to load: HTTP ${response.status}`);
    }
  } catch (error) {
    console.log(`❌ Local server test error: ${error.message}`);
  }
  console.log();
}

// Test 3: Facebook Connections
async function testFacebookConnections() {
  console.log('📘 3. FACEBOOK CONNECTIONS TEST');
  console.log('-------------------------------');

  try {
    // Test main Facebook page
    const fbPageResponse = await makeRequest(testConfig.expectedFacebookUrl);
    console.log(`📘 Facebook Page: ${fbPageResponse.status === 200 ? '✅' : fbPageResponse.status >= 300 && fbPageResponse.status < 400 ? '🔄' : '❌'} Status: ${fbPageResponse.status}`);
    if (fbPageResponse.redirected) {
      console.log('   🔄 Response indicates redirect (normal for Facebook)');
    }

    // Test Facebook Graph API (basic)
    const graphApiUrl = `https://graph.facebook.com/${testConfig.expectedFacebookPageId}`;
    const graphResponse = await makeRequest(graphApiUrl);
    console.log(`🔍 Facebook Graph API: ${graphResponse.status === 200 ? '✅' : graphResponse.status === 400 ? '⚠️' : '❌'} Status: ${graphResponse.status}`);
    if (graphResponse.status === 400) {
      console.log('   ⚠️  Access token required for full Graph API access (expected)');
    }

    // Test Facebook Messenger Customer Chat SDK
    const messengerSdkUrl = 'https://connect.facebook.net/en_US/sdk/xfbml.customerchat.js';
    const sdkResponse = await makeRequest(messengerSdkUrl);
    console.log(`💬 Messenger SDK: ${sdkResponse.status === 200 ? '✅' : '❌'} Status: ${sdkResponse.status}`);

  } catch (error) {
    console.log(`❌ Facebook connections test error: ${error.message}`);
  }
  console.log();
}

// Test 4: Instagram Connections
async function testInstagramConnections() {
  console.log('📸 4. INSTAGRAM CONNECTIONS TEST');
  console.log('--------------------------------');

  try {
    // Test Instagram profile page
    const igProfileResponse = await makeRequest(testConfig.expectedInstagramUrl);
    console.log(`📸 Instagram Profile: ${igProfileResponse.status === 200 ? '✅' : igProfileResponse.status >= 300 && igProfileResponse.status < 400 ? '🔄' : '❌'} Status: ${igProfileResponse.status}`);
    if (igProfileResponse.redirected) {
      console.log('   🔄 Response indicates redirect (normal for Instagram)');
    }

    // Test Instagram DM URL
    const igDmResponse = await makeRequest(testConfig.expectedInstagramDmUrl);
    console.log(`💬 Instagram DM URL: ${igDmResponse.status === 200 ? '✅' : igDmResponse.status >= 300 && igDmResponse.status < 400 ? '🔄' : '❌'} Status: ${igDmResponse.status}`);

  } catch (error) {
    console.log(`❌ Instagram connections test error: ${error.message}`);
  }
  console.log();
}

// Test 5: Component Files
async function testComponentFiles() {
  console.log('🧩 5. COMPONENT FILES TEST');
  console.log('---------------------------');

  const filesToCheck = [
    { path: 'src/app/contact/page.tsx', name: 'Contact Page' },
    { path: 'src/components/chat/MetaMessenger.tsx', name: 'Meta Messenger Component' },
    { path: 'src/components/consent/ConsentBar.tsx', name: 'Consent Bar Component' },
    { path: 'src/styles/contact.css', name: 'Contact CSS Styles' }
  ];

  filesToCheck.forEach(file => {
    const fullPath = path.join(__dirname, file.path);
    if (fs.existsSync(fullPath)) {
      console.log(`✅ ${file.name} exists`);

      // Check for key content
      const content = fs.readFileSync(fullPath, 'utf8');

      if (file.path.includes('contact/page.tsx')) {
        if (content.includes('InlineMessengerButton')) {
          console.log('   ✅ Contains InlineMessengerButton');
        } else {
          console.log('   ❌ Missing InlineMessengerButton');
        }

        if (content.includes('InlineInstagramButton')) {
          console.log('   ✅ Contains InlineInstagramButton');
        } else {
          console.log('   ❌ Missing InlineInstagramButton');
        }
      }

      if (file.path.includes('MetaMessenger.tsx')) {
        if (content.includes(testConfig.expectedFacebookPageId)) {
          console.log('   ✅ Contains correct Facebook Page ID configuration');
        } else {
          console.log('   ⚠️  Facebook Page ID not found in component');
        }
      }

    } else {
      console.log(`❌ ${file.name} not found at ${file.path}`);
    }
  });
  console.log();
}

// Test 6: Environment Variables
async function testEnvironmentVariables() {
  console.log('🔧 6. ENVIRONMENT VARIABLES TEST');
  console.log('---------------------------------');

  const envPath = path.join(__dirname, '.env.local');

  if (fs.existsSync(envPath)) {
    console.log('✅ .env.local file exists');
    const envContent = fs.readFileSync(envPath, 'utf8');

    if (envContent.includes('NEXT_PUBLIC_FB_PAGE_ID')) {
      console.log('✅ Facebook Page ID environment variable configured');
    } else {
      console.log('⚠️  Facebook Page ID environment variable not found');
    }

    if (envContent.includes('NEXT_PUBLIC_FB_APP_ID')) {
      console.log('✅ Facebook App ID environment variable configured');
    } else {
      console.log('⚠️  Facebook App ID environment variable not found');
    }

  } else {
    console.log('⚠️  .env.local file not found (using contact.json configuration)');
  }
  console.log();
}

// Main test runner
async function runAllTests() {
  console.log('🚀 Starting comprehensive connection verification...\n');

  await testConfigurationFiles();
  await testLocalServer();
  await testFacebookConnections();
  await testInstagramConnections();
  await testComponentFiles();
  await testEnvironmentVariables();

  console.log('🏁 COMPLETE VERIFICATION SUMMARY');
  console.log('================================');
  console.log('✅ = Working correctly');
  console.log('🔄 = Redirect (normal for social media)');
  console.log('⚠️  = Warning or partial functionality');
  console.log('❌ = Error or missing');
  console.log('\n📝 NEXT STEPS FOR FULL FACEBOOK MESSENGER INTEGRATION:');
  console.log('1. Create Facebook App at https://developers.facebook.com/');
  console.log('2. Add "Messenger" product to your Facebook App');
  console.log('3. Connect your Facebook Page to the app');
  console.log('4. Update Facebook App ID in contact.json or environment variables');
  console.log('5. Test Messenger widget functionality on live site');

  console.log('\n🔗 VERIFIED URLS:');
  console.log(`Facebook Page: ${testConfig.expectedFacebookUrl}`);
  console.log(`Instagram Profile: ${testConfig.expectedInstagramUrl}`);
  console.log(`Instagram DM: ${testConfig.expectedInstagramDmUrl}`);
  console.log(`Local Contact Page: ${testConfig.baseUrl}/contact`);
}

// Run the tests
runAllTests().catch(console.error);
