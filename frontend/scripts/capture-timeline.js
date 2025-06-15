const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:3000/timeline');
  await page.waitForSelector('#timeline-chart');          // Adjust to actual chart selector
  await page.screenshot({ path: 'docs/assets/timeline_demo.png' });
  await browser.close();
})();