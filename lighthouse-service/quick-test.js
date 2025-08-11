#!/usr/bin/env node

/**
 * Quick Test Script for Lighthouse Service
 * Run this to quickly verify the service is working
 */

const axios = require('axios');

const BASE_URL = 'http://localhost:3001';

// Test data
const testHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test SEO Page</title>
    <meta name="description" content="A test page for SEO analysis with Lighthouse">
    <meta name="keywords" content="test, seo, lighthouse, optimization">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://example.com/test-page">
</head>
<body>
    <header>
        <h1>Test Page for Lighthouse Analysis</h1>
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
            <p>This is the main content of the article. It contains enough text to make it meaningful for SEO analysis.</p>
            <img src="test-image.jpg" alt="A descriptive alt text for the test image">
            <h3>Subsection</h3>
            <p>More content to improve the page structure and SEO score.</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2024 Test Company. All rights reserved.</p>
    </footer>
</body>
</html>
`;

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSuccess(message) {
    log(`✅ ${message}`, 'green');
}

function logError(message) {
    log(`❌ ${message}`, 'red');
}

function logInfo(message) {
    log(`ℹ️  ${message}`, 'blue');
}

function logWarning(message) {
    log(`⚠️  ${message}`, 'yellow');
}

// Test functions
async function testServiceHealth() {
    try {
        logInfo('Testing service health...');
        const response = await axios.get(`${BASE_URL}/health`, { timeout: 5000 });
        logSuccess('Service is responding');
        return true;
    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            logError('Service is not running. Please start the service with: node server.js');
            return false;
        }
        logWarning('Service health check failed (this is normal if /health endpoint is not implemented)');
        return true; // Continue with other tests
    }
}

async function testUrlAudit() {
    try {
        logInfo('Testing URL audit endpoint...');
        const response = await axios.post(`${BASE_URL}/audit`, {
            url: 'https://example.com'
        }, { timeout: 30000 });
        
        if (response.data.seoScore !== undefined) {
            logSuccess(`URL audit successful! SEO Score: ${response.data.seoScore}`);
            return true;
        } else {
            logError('URL audit failed: Invalid response format');
            return false;
        }
    } catch (error) {
        logError(`URL audit failed: ${error.response?.data?.error || error.message}`);
        return false;
    }
}

async function testHtmlAudit() {
    try {
        logInfo('Testing HTML content audit endpoint...');
        const response = await axios.post(`${BASE_URL}/audit-html`, {
            html: testHtml
        }, { timeout: 30000 });
        
        if (response.data.seoScore !== undefined) {
            logSuccess(`HTML audit successful! SEO Score: ${response.data.seoScore}`);
            
            // Show some audit details
            if (response.data.audits) {
                const auditCount = Object.keys(response.data.audits).length;
                logInfo(`Found ${auditCount} audit results`);
            }
            
            return true;
        } else {
            logError('HTML audit failed: Invalid response format');
            return false;
        }
    } catch (error) {
        logError(`HTML audit failed: ${error.response?.data?.error || error.message}`);
        return false;
    }
}

async function runAllTests() {
    log('🧪 Lighthouse Service Quick Test', 'bright');
    log('================================', 'bright');
    
    const results = {
        health: false,
        urlAudit: false,
        htmlAudit: false
    };
    
    // Test 1: Service Health
    results.health = await testServiceHealth();
    
    if (!results.health) {
        log('\n❌ Service is not running. Please start it first.', 'red');
        process.exit(1);
    }
    
    // Test 2: URL Audit
    results.urlAudit = await testUrlAudit();
    
    // Test 3: HTML Content Audit
    results.htmlAudit = await testHtmlAudit();
    
    // Summary
    log('\n📊 Test Summary', 'bright');
    log('==============', 'bright');
    log(`Service Health: ${results.health ? '✅ PASS' : '❌ FAIL'}`);
    log(`URL Audit: ${results.urlAudit ? '✅ PASS' : '❌ FAIL'}`);
    log(`HTML Audit: ${results.htmlAudit ? '✅ PASS' : '❌ FAIL'}`);
    
    const passedTests = Object.values(results).filter(Boolean).length;
    const totalTests = Object.keys(results).length;
    
    log(`\nOverall: ${passedTests}/${totalTests} tests passed`, passedTests === totalTests ? 'green' : 'red');
    
    if (passedTests === totalTests) {
        log('\n🎉 All tests passed! Lighthouse service is working correctly.', 'green');
    } else {
        log('\n⚠️  Some tests failed. Check the error messages above.', 'yellow');
    }
}

// Handle errors gracefully
process.on('unhandledRejection', (reason, promise) => {
    logError('Unhandled Rejection at:');
    logError(`Promise: ${promise}`);
    logError(`Reason: ${reason}`);
    process.exit(1);
});

// Run tests
if (require.main === module) {
    runAllTests().catch(error => {
        logError(`Test runner failed: ${error.message}`);
        process.exit(1);
    });
}

module.exports = { testServiceHealth, testUrlAudit, testHtmlAudit };
