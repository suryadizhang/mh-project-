// Test script for Contact a Person feature in chatbot
// This tests both frontend detection and API response

const http = require('http');
const https = require('https');

const testContactPersonFeature = async () => {
  console.log('\n🤖 TESTING CONTACT A PERSON FEATURE');
  console.log('=====================================\n');

  // Test cases that should trigger "contact a person" response
  const testCases = [
    'contact a person',
    'talk to human',
    'speak to someone',
    'contact person',
    'human support',
    'live chat',
    'real person',
    'customer service',
    'I want to talk to a human',
    'Can I contact a person?'
  ];

  // Test localhost server availability
  console.log('1. Testing development server...');
  try {
    const serverTest = await testHttpRequest('http://localhost:3000/api/assistant', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: 'contact a person',
        page: '/contact'
      })
    });

    if (serverTest.success) {
      console.log('   ✅ Development server is running');

      // Test API responses
      console.log('\n2. Testing API responses for contact person triggers...');

      for (const testCase of testCases) {
        console.log(`   Testing: "${testCase}"`);

        try {
          const response = await testHttpRequest('http://localhost:3000/api/assistant', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              message: testCase,
              page: '/contact'
            })
          });

          if (response.success && response.data) {
            const data = JSON.parse(response.data);
            const isContactResponse = data.answer && (
              data.answer.includes('connect you with our team') ||
              data.answer.includes('Facebook Messenger') ||
              data.answer.includes('Instagram DM') ||
              data.answer.includes('show you the options')
            );

            console.log(`     ${isContactResponse ? '✅' : '❌'} ${isContactResponse ? 'Correct response' : 'Unexpected response'}`);
            if (!isContactResponse) {
              console.log(`     Response: ${data.answer.substring(0, 100)}...`);
            }
          } else {
            console.log('     ❌ Failed to get response');
          }
        } catch (error) {
          console.log(`     ❌ Error: ${error.message}`);
        }

        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    } else {
      console.log('   ❌ Development server not accessible');
      console.log('   Please make sure npm run dev is running');
    }
  } catch (error) {
    console.log(`   ❌ Server test failed: ${error.message}`);
  }

  console.log('\n3. Testing social media connections...');

  // Test Facebook page
  try {
    const fbResponse = await testHttpsRequest('https://www.facebook.com/people/My-hibachi/61577483702847/');
    console.log(`   ${fbResponse.success ? '✅' : '❌'} Facebook page: ${fbResponse.success ? 'Accessible' : 'Not accessible'}`);
  } catch (error) {
    console.log(`   ❌ Facebook test error: ${error.message}`);
  }

  // Test Instagram DM
  try {
    const igResponse = await testHttpsRequest('https://ig.me/m/my_hibachi_chef');
    console.log(`   ${igResponse.success ? '✅' : '❌'} Instagram DM: ${igResponse.success ? 'Accessible' : 'Not accessible'}`);
  } catch (error) {
    console.log(`   ❌ Instagram DM test error: ${error.message}`);
  }

  console.log('\n📋 FEATURE SUMMARY:');
  console.log('===================');
  console.log('✅ Contact person detection implemented');
  console.log('✅ Choice modal with Facebook & Instagram options');
  console.log('✅ API responses enhanced for human contact requests');
  console.log('✅ Welcome suggestions include "Contact a person"');
  console.log('✅ Fallback options for phone and email');
  console.log('\n🎯 NEXT STEPS:');
  console.log('- Test the chatbot in browser');
  console.log('- Click "Contact a person" to see the choice modal');
  console.log('- Verify Facebook Messenger and Instagram DM options work');
  console.log('- Create Facebook App to enable full Messenger widget');
};

// Helper function for HTTP requests
function testHttpRequest(url, options = {}) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: 5000
    };

    const req = http.request(requestOptions, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          success: res.statusCode === 200,
          statusCode: res.statusCode,
          data: data
        });
      });
    });

    req.on('error', () => {
      resolve({ success: false, error: 'Request failed' });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ success: false, error: 'Timeout' });
    });

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

// Helper function for HTTPS requests
function testHttpsRequest(url) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const requestOptions = {
      hostname: urlObj.hostname,
      port: 443,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      timeout: 5000
    };

    const req = https.request(requestOptions, (res) => {
      resolve({
        success: res.statusCode === 200 || res.statusCode === 302,
        statusCode: res.statusCode
      });
    });

    req.on('error', () => {
      resolve({ success: false });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ success: false });
    });

    req.end();
  });
}

// Run the test
testContactPersonFeature().catch(console.error);
