# Lighthouse Service Testing Guide

## 🚀 Overview

This document provides comprehensive testing instructions for the Lighthouse Service, which offers two main endpoints for SEO analysis:

1. **URL Audit** (`/audit`) - Analyze live websites
2. **HTML Content Audit** (`/audit-html`) - Analyze raw HTML content

## 📋 Prerequisites

### 1. Install Dependencies

```bash
cd SEOAgent/lighthouse-service
npm install
```

### 2. Start the Service

```bash
node server.js
```

**Expected Output:**

```
⚡ Lighthouse API listening on port 3001
📊 Available endpoints:
   POST /audit      - Audit live website URL
   POST /audit-html - Audit raw HTML content
```

## 🧪 Testing Methods

### Method 1: Using cURL (Command Line)

#### Test URL Audit Endpoint

```bash
curl -X POST http://localhost:3001/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

#### Test HTML Content Audit Endpoint

```bash
curl -X POST http://localhost:3001/audit-html \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<!DOCTYPE html><html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"
  }'
```

### Method 2: Using Postman

#### URL Audit Request

- **Method**: POST
- **URL**: `http://localhost:3001/audit`
- **Headers**: `Content-Type: application/json`
- **Body** (raw JSON):

```json
{
  "url": "https://example.com"
}
```

#### HTML Content Audit Request

- **Method**: POST
- **URL**: `http://localhost:3001/audit-html`
- **Headers**: `Content-Type: application/json`
- **Body** (raw JSON):

```json
{
  "html": "<!DOCTYPE html><html><head><title>Test Page</title><meta name=\"description\" content=\"Test description\"></head><body><h1>Hello World</h1><p>This is a test paragraph.</p></body></html>"
}
```

### Method 3: Using JavaScript/Node.js

#### Test Script

Create a file `test-lighthouse.js`:

```javascript
const axios = require("axios");

// Test URL audit
async function testUrlAudit() {
  try {
    const response = await axios.post("http://localhost:3001/audit", {
      url: "https://example.com",
    });
    console.log("✅ URL Audit Result:", response.data);
  } catch (error) {
    console.error("❌ URL Audit Error:", error.response?.data || error.message);
  }
}

// Test HTML content audit
async function testHtmlAudit() {
  const testHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Test SEO Page</title>
        <meta name="description" content="A test page for SEO analysis">
        <meta name="keywords" content="test, seo, lighthouse">
      </head>
      <body>
        <h1>Test Page Title</h1>
        <p>This is a test paragraph with some content.</p>
        <img src="test.jpg" alt="Test image">
      </body>
    </html>
  `;

  try {
    const response = await axios.post("http://localhost:3001/audit-html", {
      html: testHtml,
    });
    console.log("✅ HTML Audit Result:", response.data);
  } catch (error) {
    console.error(
      "❌ HTML Audit Error:",
      error.response?.data || error.message
    );
  }
}

// Run tests
async function runTests() {
  console.log("🧪 Testing Lighthouse Service...\n");

  console.log("1️⃣ Testing URL Audit...");
  await testUrlAudit();

  console.log("\n2️⃣ Testing HTML Content Audit...");
  await testHtmlAudit();
}

runTests();
```

**Run the test:**

```bash
npm install axios
node test-lighthouse.js
```

### Method 4: Using Python

#### Test Script

Create a file `test_lighthouse.py`:

```python
import requests
import json

# Test URL audit
def test_url_audit():
    try:
        response = requests.post('http://localhost:3001/audit',
                               json={'url': 'https://example.com'})
        print('✅ URL Audit Result:', response.json())
    except Exception as e:
        print('❌ URL Audit Error:', str(e))

# Test HTML content audit
def test_html_audit():
    test_html = '''
    <!DOCTYPE html>
    <html>
        <head>
            <title>Test SEO Page</title>
            <meta name="description" content="A test page for SEO analysis">
            <meta name="keywords" content="test, seo, lighthouse">
        </head>
        <body>
            <h1>Test Page Title</h1>
            <p>This is a test paragraph with some content.</p>
            <img src="test.jpg" alt="Test image">
        </body>
    </html>
    '''

    try:
        response = requests.post('http://localhost:3001/audit-html',
                               json={'html': test_html})
        print('✅ HTML Audit Result:', response.json())
    except Exception as e:
        print('❌ HTML Audit Error:', str(e))

if __name__ == '__main__':
    print('🧪 Testing Lighthouse Service...\n')

    print('1️⃣ Testing URL Audit...')
    test_url_audit()

    print('\n2️⃣ Testing HTML Content Audit...')
    test_html_audit()
```

**Run the test:**

```bash
pip install requests
python test_lighthouse.py
```

## 📊 Expected Response Format

### Successful Response

```json
{
  "seoScore": 92.34,
  "audits": {
    "meta-description": {
      "score": 1,
      "title": "Document has a meta description",
      "description": "Meta descriptions are important..."
    }
    // ... more audit results
  },
  "categories": {
    "seo": {
      "score": 0.92,
      "title": "SEO"
    }
  },
  "fullReport": {
    // Complete Lighthouse JSON report
  },
  "source": "html_content",
  "tempUrl": "http://localhost:3002/temp-page"
}
```

### Error Response

```json
{
  "error": "Error message",
  "details": "Full error stack trace",
  "timestamp": "2024-01-XX..."
}
```

## 🔍 Testing Scenarios

### 1. Basic HTML Testing

Test with minimal HTML to ensure basic functionality:

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Test</title>
  </head>
  <body>
    <h1>Hello</h1>
  </body>
</html>
```

### 2. SEO-Optimized HTML Testing

Test with SEO-friendly HTML:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>SEO Optimized Page</title>
    <meta name="description" content="A well-optimized page for testing" />
    <meta name="keywords" content="seo, testing, lighthouse" />
    <meta name="robots" content="index, follow" />
    <link rel="canonical" href="https://example.com/page" />
  </head>
  <body>
    <header>
      <h1>Main Page Title</h1>
      <nav>
        <ul>
          <li><a href="/about">About</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </nav>
    </header>
    <main>
      <article>
        <h2>Article Title</h2>
        <p>This is the main content of the article.</p>
        <img src="image.jpg" alt="Descriptive image alt text" />
      </article>
    </main>
    <footer>
      <p>&copy; 2024 Test Company</p>
    </footer>
  </body>
</html>
```

### 3. Error Testing

Test error handling with invalid inputs:

- Empty HTML content
- Malformed HTML
- Very long HTML content
- Special characters in HTML

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**

   ```
   Error: listen EADDRINUSE: address already in use :::3001
   ```

   **Solution**: Kill existing process or change port in server.js

2. **Chrome Launch Failed**

   ```
   Error: Failed to launch chrome
   ```

   **Solution**: Ensure Chrome is installed or use different Chrome flags

3. **Lighthouse Analysis Failed**
   ```
   Error: INVALID_URL
   ```
   **Solution**: Check if the temporary HTTP server is working correctly

### Debug Mode

Enable detailed logging by modifying the server:

```javascript
const options = {
  logLevel: "verbose", // Change from 'info' to 'verbose'
  onlyCategories: ["seo"],
  port: chrome.port,
  output: "json",
};
```

## 📈 Performance Testing

### Load Testing

Test with multiple concurrent requests:

```bash
# Using Apache Bench (if available)
ab -n 100 -c 10 -p test-data.json -T application/json http://localhost:3001/audit-html
```

### Memory Testing

Monitor memory usage during testing:

```bash
# Monitor Node.js process
ps aux | grep node
# Or use htop/htop for real-time monitoring
```

## ✅ Test Checklist

- [ ] Service starts without errors
- [ ] URL audit endpoint responds correctly
- [ ] HTML content audit endpoint responds correctly
- [ ] Error handling works for invalid inputs
- [ ] Temporary HTTP server creates and closes properly
- [ ] Chrome instances are properly cleaned up
- [ ] Response format matches expected structure
- [ ] SEO scores are reasonable (0-100 range)
- [ ] Service handles concurrent requests
- [ ] Memory usage remains stable

## 🎯 Next Steps

After successful testing:

1. Integrate with the main SEO Agent backend
2. Add authentication if needed
3. Implement rate limiting
4. Add monitoring and logging
5. Set up automated testing pipeline

---

**Happy Testing! 🚀**
