import { chromium } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:3000';
const API_URL = process.env.CLAWAUDIT_API || 'http://127.0.0.1:8765';
const CHROME_PATH = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

async function assertOk(condition, message) {
  if (!condition) throw new Error(message);
}

async function testApi() {
  const health = await fetch(`${API_URL}/health`);
  await assertOk(health.ok, `health failed: ${health.status}`);
  const healthJson = await health.json();
  await assertOk(healthJson.ok === true, 'health JSON did not report ok=true');

  const audit = await fetch(`${API_URL}/api/audit/latest`);
  await assertOk(audit.ok, `latest audit failed: ${audit.status}`);
  const auditJson = await audit.json();
  await assertOk(typeof auditJson.safety_score === 'number', 'missing numeric safety_score');
  await assertOk(Array.isArray(auditJson.findings), 'missing findings array');
  await assertOk(Array.isArray(auditJson.items), 'missing items array');
}

async function testHtml() {
  const response = await fetch(FRONTEND_URL);
  await assertOk(response.ok, `frontend failed: ${response.status}`);
  const html = await response.text();
  await assertOk(html.includes('ClawAudit'), 'frontend HTML did not include ClawAudit');

  const support = await fetch(`${FRONTEND_URL}/support`);
  await assertOk(support.ok, `support page failed: ${support.status}`);
  const supportHtml = await support.text();
  await assertOk(supportHtml.includes('Support the project'), 'support HTML did not include support copy');
}

async function testBrowser() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME_PATH,
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const messages = [];
  page.on('console', (msg) => {
    const text = msg.text();
    if (msg.type() === 'error' || /width\(-1\)|height\(-1\)|blocked cross-origin|hydration/i.test(text)) {
      messages.push(`${msg.type()}: ${text}`);
    }
  });
  page.on('pageerror', (err) => messages.push(`pageerror: ${err.message}`));

  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: /Audit your agent before it acts alone/i }).waitFor({ timeout: 10000 });
  await page.getByRole('button', { name: /Run audit/i }).click();
  await page.getByText(/Scanning your setup/i).waitFor({ timeout: 10000 });
  await page.getByRole('dialog', { name: /Audit complete/i }).waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: /Review results/i }).click();
  await page.getByRole('tab', { name: /Findings/i }).click();
  await page.getByRole('tab', { name: /Inventory/i }).click();
  await page.getByRole('tab', { name: /History/i }).click();
  await page.getByRole('button', { name: /Load history/i }).click();
  await page.getByText(/Before \/ after/i).waitFor({ timeout: 10000 });
  await page.getByRole('tab', { name: /Export/i }).click();

  const visibleText = await page.locator('body').innerText();
  await assertOk(!/Python|FastAPI|Next\.js|Tailwind|shadcn|Motion\.dev/i.test(visibleText), 'visible UI leaked implementation wording');

  await page.getByRole('link', { name: /Support/i }).click();
  await page.getByRole('heading', { name: /Help keep ClawAudit sharp/i }).waitFor({ timeout: 10000 });
  await page.getByText(/Make a donation/i).waitFor({ timeout: 10000 });
  await page.locator('#paypal-container-WFK2UQN9QTC5G').waitFor({ state: 'attached', timeout: 10000 });

  await page.screenshot({ path: 'tests/clawaudit-smoke.png', fullPage: true });
  await browser.close();

  await assertOk(messages.length === 0, `browser console/page errors:\n${messages.join('\n')}`);
}

async function main() {
  await testApi();
  await testHtml();
  await testBrowser();
  console.log('web smoke tests passed');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
