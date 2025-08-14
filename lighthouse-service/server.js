/*
npm init -y
npm install express lighthouse chrome-launcher
*/

// server.js
const express       = require('express');
const lighthouse = require('lighthouse').default || require('lighthouse');
const chromeLauncher= require('chrome-launcher');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
app.use(express.json());

app.post('/audit', async (req, res) => {
  const { url } = req.body;
  if (!url) {
    return res.status(400).json({ error: 'Missing url in request body' });
  }

  let chrome;
  try {
    // 1) Launch headless Chrome
    chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });

    // 2) Run Lighthouse (only the SEO category)
    const options = {
      logLevel: 'info',
      onlyCategories: ['seo'],
      port: chrome.port,
      output: 'json'
    };
    const runnerResult = await lighthouse(url, options);

    // 3) Parse report
    const reportJson = JSON.parse(runnerResult.report);
    const seoScore = reportJson.categories.seo.score * 100;

    // 4) Return just the score + audits
    res.json({
      seoScore: Math.round(seoScore * 100) / 100,  // e.g. 92.34
      audits: reportJson.audits
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  } finally {
    if (chrome) {
      await chrome.kill();
    }
  }
});

// HTML analysis endpoint - Uses temporary HTTP server for Lighthouse
app.post('/audit-html', async (req, res) => {
  const { html } = req.body;
  if (!html) {
    return res.status(400).json({ error: 'Missing html in request body' });
  }

  console.log(`🔍 Starting HTML audit...`);
  console.log(`📏 HTML content length: ${html.length} characters`);
  console.log(`📄 HTML preview (first 200 chars): ${html.substring(0, 200)}...`);

  let chrome;
  let tempServer;
  
  try {
    // 1) Create a temporary HTTP server to serve the HTML
    const tempPort = 3002; // Use a different port for temp server
    const tempApp = express();
    
    tempApp.get('/temp-page', (req, res) => {
      console.log(`🌐 Temp server received request for /temp-page`);
      res.set('Content-Type', 'text/html');
      res.send(html);
      console.log(`✅ Temp server sent HTML response`);
    });
    
    // Handle meta refresh redirects to prevent 404 errors
    tempApp.get('/redirect/landing', (req, res) => {
      console.log(`🔄 Temp server received redirect request for /redirect/landing`);
      // Return the same HTML content for redirect target
      res.set('Content-Type', 'text/html');
      res.send(html);
      console.log(`✅ Temp server sent HTML response for redirect target`);
    });
    
    // Handle any other paths that might be referenced in the HTML
    tempApp.use((req, res) => {
      console.log(`🌐 Temp server received request for: ${req.path}`);
      // Return the same HTML content for any path
      res.set('Content-Type', 'text/html');
      res.send(html);
      console.log(`✅ Temp server sent HTML response for path: ${req.path}`);
    });
    
    tempServer = tempApp.listen(tempPort);
    console.log(`📄 Created temporary HTTP server on port ${tempPort}`);
    
    // Wait a moment for server to start
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Test if temp server is working
    try {
      const testResponse = await fetch(`http://localhost:${tempPort}/temp-page`);
      console.log(`🧪 Temp server test response status: ${testResponse.status}`);
      if (testResponse.ok) {
        const testHtml = await testResponse.text();
        console.log(`🧪 Temp server test HTML length: ${testHtml.length} characters`);
      }
    } catch (testErr) {
      console.error(`❌ Temp server test failed:`, testErr.message);
    }
    
    // 2) Create HTTP URL instead of file URL
    const tempUrl = `http://localhost:${tempPort}/temp-page`;
    console.log(`📄 Analyzing HTML content via HTTP URL: ${tempUrl}`);
    
    // 3) Launch headless Chrome
    console.log(`🚀 Launching headless Chrome...`);
    chrome = await chromeLauncher.launch({ 
      chromeFlags: ['--headless'] 
    });
    console.log(`✅ Chrome launched on port ${chrome.port}`);

    // 4) Run Lighthouse (only the SEO category)
    console.log(`🔍 Running Lighthouse analysis...`);
    const options = {
      logLevel: 'info',
      onlyCategories: ['seo'],
      port: chrome.port,
      output: 'json'
    };
    
    console.log(`⚙️ Lighthouse options:`, JSON.stringify(options, null, 2));
    console.log(`🎯 Target URL: ${tempUrl}`);
    
    const runnerResult = await lighthouse(tempUrl, options);
    console.log(`✅ Lighthouse analysis completed`);

    // 5) Parse report
    const reportJson = JSON.parse(runnerResult.report);
    const seoScore = reportJson.categories.seo.score * 100;
    
    console.log(`📊 SEO Score: ${seoScore}`);
    console.log(`📋 Audits count: ${Object.keys(reportJson.audits).length}`);
    console.log(`🔍 Sample audit:`, Object.keys(reportJson.audits)[0]);

    // 6) Return complete JSON for LLM processing
    res.json({
      seoScore: Math.round(seoScore * 100) / 100,
      audits: reportJson.audits,
      categories: reportJson.categories,
      fullReport: reportJson,  // Complete Lighthouse JSON
      source: 'html_content',
      tempUrl: tempUrl
    });
    
  } catch (err) {
    console.error('❌ HTML audit error:', err);
    console.error('Error details:', {
      message: err.message,
      stack: err.stack,
      tempServer: tempServer ? 'exists' : 'null',
      tempServerPort: tempServer ? tempServer.address()?.port : 'N/A'
    });
    
    // Additional debugging for temp server
    if (tempServer) {
      try {
        const address = tempServer.address();
        console.log(`🔍 Temp server address:`, address);
        if (address) {
          console.log(`🔍 Temp server is listening on port ${address.port}`);
        }
      } catch (addrErr) {
        console.error(`❌ Could not get temp server address:`, addrErr.message);
      }
    }
    
    res.status(500).json({ 
      error: err.message,
      details: err.stack,
      timestamp: new Date().toISOString()
    });
  } finally {
    // Cleanup
    if (chrome) {
      console.log(`🧹 Cleaning up Chrome...`);
      await chrome.kill();
      console.log(`✅ Chrome killed`);
    }
    if (tempServer) {
      console.log(`🧹 Closing temporary HTTP server...`);
      tempServer.close();
      console.log(`🗑️ Closed temporary HTTP server`);
    }
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`⚡ Lighthouse API listening on port ${PORT}`);
  console.log(`📊 Available endpoints:`);
  console.log(`   POST /audit      - Audit live website URL`);
  console.log(`   POST /audit-html - Audit raw HTML content`);
});