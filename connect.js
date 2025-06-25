const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.connect({
    browserURL: "http://localhost:9222",
    defaultViewport: null,
    protocolTimeout:  30000, // Add extra 30 seconds buffer to total timeout
  });


  const page = await browser.newPage();
  await page.goto('https://labs.google/fx/tools/image-fx');
})();
