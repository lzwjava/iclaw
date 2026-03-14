const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const userDataDir = path.join(process.env.HOME, '.openclaw', 'browser-profiles', 'openclaw');
  console.log('--- GITHUB DEVICE AUTHORIZATION ---');
  
  const browser = await chromium.launchPersistentContext(userDataDir, { headless: true });
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to GitHub device login...');
    await page.goto('https://github.com/login/device', { waitUntil: 'load', timeout: 60000 });

    console.log('Detecting page state... current URL:', page.url());
    await page.screenshot({ path: 'github-debug-1.png' });

    if (page.url().includes('/login') && !page.url().includes('/device')) {
      console.log('ERROR: Redirected to login. Not authenticated.');
      process.exit(1);
    }

    console.log('Looking for user-code input...');
    const input = page.locator('#user-code');
    await input.waitFor({ state: 'visible', timeout: 5000 });
    
    await input.fill('837A-E26D');
    await page.keyboard.press('Enter');

    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'github-debug-2.png' });

    const authorizeBtn = page.locator('button:has-text("Authorize"), button:has-text("Continue")');
    if (await authorizeBtn.isVisible()) {
      console.log('Clicking Authorize button...');
      await authorizeBtn.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'github-debug-3.png' });
    }

    console.log('Final URL:', page.url());
    if (page.url().includes('success') || await page.isVisible('text=Congratulations')) {
      console.log('SUCCESS: Device authorized!');
      process.exit(0);
    } else {
      console.log('Verification failed.');
      process.exit(1);
    }

  } catch (err) {
    console.error('CRITICAL ERROR:', err.message);
    await page.screenshot({ path: 'github-error.png' });
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
