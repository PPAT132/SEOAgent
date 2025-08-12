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

  let chrome;
  let tempServer;
  
  try {
    // 1) Create a temporary HTTP server to serve the HTML
    const tempPort = 3002; // Use a different port for temp server
    const tempApp = express();
    
    tempApp.get('/temp-page', (req, res) => {
      res.set('Content-Type', 'text/html');
      res.send(html);
    });
    
    tempServer = tempApp.listen(tempPort);
    console.log(`📄 Created temporary HTTP server on port ${tempPort}`);
    
    // 2) Create HTTP URL instead of file URL
    const tempUrl = `http://localhost:${tempPort}/temp-page`;
    console.log(`📄 Analyzing HTML content via HTTP URL: ${tempUrl}`);
    
    // 3) Launch headless Chrome
    chrome = await chromeLauncher.launch({ 
      chromeFlags: ['--headless'] 
    });

    // 4) Run Lighthouse (only the SEO category)
    const options = {
      logLevel: 'info',
      onlyCategories: ['seo'],
      port: chrome.port,
      output: 'json'
    };
    const runnerResult = await lighthouse(tempUrl, options);

    // 5) Parse report
    const reportJson = JSON.parse(runnerResult.report);
    const seoScore = reportJson.categories.seo.score * 100;

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
      tempServer: tempServer ? 'exists' : 'null'
    });
    res.status(500).json({ 
      error: err.message,
      details: err.stack,
      timestamp: new Date().toISOString()
    });
  } finally {
    // Cleanup
    if (chrome) {
      await chrome.kill();
    }
    if (tempServer) {
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
