/*
npm init -y
npm install express lighthouse chrome-launcher
*/

// server.js
const express       = require('express');
const lighthouse = require('lighthouse').default || require('lighthouse');
const chromeLauncher= require('chrome-launcher');

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

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`⚡ Lighthouse API listening on port ${PORT}`);
});
