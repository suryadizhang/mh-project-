// Quick test script to check redirect behavior
const http = require('http');

function testUrl(path) {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: path,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    };

    const req = http.request(options, (res) => {
      resolve({
        path,
        status: res.statusCode,
        location: res.headers.location || 'none'
      });
    });

    req.on('error', (e) => {
      resolve({ path, error: e.message });
    });

    req.end();
  });
}

async function main() {
  console.log('Testing redirect behavior...\n');

  const tests = [
    '/BookUs/',
    '/BookUs',
    '/bookus/',
    '/bookus',
    '/'
  ];

  for (const path of tests) {
    const result = await testUrl(path);
    console.log(`${result.path} => Status: ${result.status}, Location: ${result.location}`);
  }
}

main();
