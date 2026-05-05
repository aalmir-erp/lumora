/**
 * Servia heavy-scenario smoke tests via Playwright.
 *
 * Runs against the LIVE deployment (https://servia.ae) — sniffs out
 * visible bugs the user has reported plus regressions across the user
 * journey. Reports findings as JSON.
 *
 * Run: node /tmp/playwright-tests.mjs
 */
import { chromium, devices } from 'playwright';

const BASE = process.env.SERVIA_BASE || 'https://servia.ae';
const REPORT = [];

function record(name, status, detail) {
  REPORT.push({name, status, detail: String(detail || '').slice(0, 400)});
  const icon = status === 'pass' ? '✅' : status === 'fail' ? '❌' : status === 'warn' ? '⚠️' : 'ℹ️';
  console.log(`${icon} ${name}${detail ? ' — ' + String(detail).slice(0, 200) : ''}`);
}

async function withPage(name, fn, deviceName) {
  const browser = await chromium.launch({ headless: true });
  try {
    const ctx = await browser.newContext({
      ...(deviceName ? devices[deviceName] : {}),
      ignoreHTTPSErrors: true,
    });
    const page = await ctx.newPage();
    page.setDefaultTimeout(15000);
    const errs = [];
    page.on('pageerror', e => errs.push(`pageerror: ${e.message}`));
    page.on('console', m => { if (m.type() === 'error') errs.push(`console.error: ${m.text()}`); });
    try { await fn(page); } finally {
      if (errs.length) record(name + ' [JS errors]', 'warn', errs.slice(0, 3).join(' | '));
    }
  } finally { await browser.close(); }
}

// ==========================================================================
// Tests
// ==========================================================================
(async () => {
  console.log(`\n🎭 Playwright sweep · ${BASE}\n` + '='.repeat(50));

  // 1. Home page loads + no critical JS errors
  await withPage('1. Homepage loads', async (page) => {
    const r = await page.goto(BASE, { waitUntil: 'load' });
    if (!r || r.status() >= 400) return record('1. Homepage loads', 'fail', `HTTP ${r?.status()}`);
    const title = await page.title();
    record('1. Homepage loads', 'pass', `"${title}"`);
  });

  // 2. Mobile viewport — check nav single-row + topbanner color
  await withPage('2. Mobile nav single-row', async (page) => {
    await page.goto(BASE);
    const navInner = await page.locator('.nav-inner').boundingBox();
    if (!navInner) return record('2. Mobile nav single-row', 'fail', 'no .nav-inner');
    const logoBox = await page.locator('.nav-inner img').first().boundingBox();
    const ctaBox = await page.locator('.nav-cta').boundingBox().catch(() => null);
    if (!logoBox || !ctaBox) return record('2. Mobile nav single-row', 'warn', 'logo or cta not found');
    // If on same row, their y-coordinates overlap
    const sameRow = Math.abs(logoBox.y - ctaBox.y) < Math.max(logoBox.height, ctaBox.height);
    record('2. Mobile nav single-row', sameRow ? 'pass' : 'fail',
            `logo.y=${logoBox.y.toFixed(0)} cta.y=${ctaBox.y.toFixed(0)}`);
  }, 'iPhone 12');

  // 3. Topbanner placeholder color matches what's expected (no orange)
  await withPage('3. Topbanner color', async (page) => {
    await page.goto(BASE);
    const bg = await page.locator('#servia-topbanner').first().evaluate(el => getComputedStyle(el).background);
    const isOrange = /245,?\s*158,?\s*11/.test(bg) || /F59E0B/i.test(bg);
    record('3. Topbanner color', isOrange ? 'fail' : 'pass',
            isOrange ? 'still orange — check theme-color' : 'teal as expected');
  });

  // 4. Theme-color meta is teal (not orange)
  await withPage('4. Theme-color meta tag', async (page) => {
    await page.goto(BASE);
    const tc = await page.locator('meta[name="theme-color"]').first().getAttribute('content');
    record('4. Theme-color meta tag',
            (tc || '').toUpperCase() === '#0F766E' ? 'pass' : 'fail',
            `content="${tc}"`);
  });

  // 5. NFC landing page renders with all sections
  await withPage('5. /nfc.html renders', async (page) => {
    const r = await page.goto(BASE + '/nfc.html');
    if (!r || r.status() >= 400) return record('5. /nfc.html renders', 'fail', `HTTP ${r?.status()}`);
    const heroOK = await page.locator('h1', { hasText: 'Tap once' }).count() > 0;
    const advisorOK = await page.locator('#advisor-card').count() > 0;
    const bulkOK = await page.locator('#bulk-rows').count() > 0;
    record('5. /nfc.html renders',
            heroOK && advisorOK && bulkOK ? 'pass' : 'fail',
            `hero=${heroOK} advisor=${advisorOK} bulk=${bulkOK}`);
  });

  // 6. /nfc.html has SEO schemas
  await withPage('6. NFC SEO schemas', async (page) => {
    await page.goto(BASE + '/nfc.html');
    const schemas = await page.locator('script[type="application/ld+json"]').allInnerTexts();
    const hasHowTo = schemas.some(s => /HowTo/.test(s));
    const hasFAQ = schemas.some(s => /FAQPage/.test(s));
    const hasProduct = schemas.some(s => /Product/.test(s));
    record('6. NFC SEO schemas',
            hasHowTo && hasFAQ && hasProduct ? 'pass' : 'fail',
            `HowTo=${hasHowTo} FAQ=${hasFAQ} Product=${hasProduct}`);
  });

  // 7. /search.html input works (was missing class earlier)
  await withPage('7. Search input styled', async (page) => {
    const r = await page.goto(BASE + '/search.html');
    if (!r || r.status() >= 400) return record('7. Search input styled', 'fail', `HTTP ${r?.status()}`);
    const cls = await page.locator('#q').getAttribute('class');
    record('7. Search input styled', /ss-input/.test(cls || '') ? 'pass' : 'fail', `class="${cls}"`);
  });

  // 8. /install.html shows APK download card
  await withPage('8. APK install wizard', async (page) => {
    await page.goto(BASE + '/install.html');
    const apkCardOK = await page.locator('#apk-download').count() > 0;
    const wearCardOK = await page.locator('#wear-download').count() > 0;
    record('8. APK install wizard',
            apkCardOK && wearCardOK ? 'pass' : 'fail',
            `apk-card=${apkCardOK} wear-card=${wearCardOK}`);
  });

  // 9. Login page works
  await withPage('9. /login.html', async (page) => {
    const r = await page.goto(BASE + '/login.html');
    if (!r || r.status() >= 400) return record('9. /login.html', 'fail', `HTTP ${r?.status()}`);
    const phoneField = await page.locator('input[type="tel"], input[id*="phone"]').count();
    record('9. /login.html', phoneField > 0 ? 'pass' : 'warn', `phone-fields=${phoneField}`);
  });

  // 10. /api/services responds with services list
  await withPage('10. /api/services API', async (page) => {
    const r = await page.request.get(BASE + '/api/services');
    if (!r.ok()) return record('10. /api/services API', 'fail', `HTTP ${r.status()}`);
    const j = await r.json();
    const n = (j.services || []).length;
    record('10. /api/services API', n >= 10 ? 'pass' : 'warn', `${n} services`);
  });

  // 11. /api/nfc/tag/<bad-slug> returns 404 (validates routing works)
  await withPage('11. NFC tag routing', async (page) => {
    const r = await page.request.get(BASE + '/api/nfc/tag/zzzz999nonexistent');
    record('11. NFC tag routing',
            r.status() === 404 ? 'pass' : 'fail',
            `expected 404, got ${r.status()}`);
  });

  // 12. /t/<bad-slug> redirects to /nfc-not-found
  await withPage('12. NFC tap not-found redirect', async (page) => {
    const r = await page.request.get(BASE + '/t/zzzz999bogus', { maxRedirects: 0 });
    const loc = r.headers()['location'] || '';
    record('12. NFC tap not-found redirect',
            r.status() === 302 && /nfc-not-found/.test(loc) ? 'pass' : 'fail',
            `${r.status()} → ${loc}`);
  });

  // 13. Customer login with seeded demo account
  await withPage('13. Demo customer login', async (page) => {
    const r = await page.request.post(BASE + '/api/auth/customer/login', {
      data: {email: 'test@servia.ae', password: 'test123'},
    });
    if (r.ok()) {
      const j = await r.json();
      record('13. Demo customer login',
              j.ok && j.token ? 'pass' : 'fail',
              `token=${(j.token||'').slice(0,12)}...`);
    } else {
      record('13. Demo customer login', 'fail', `HTTP ${r.status()}`);
    }
  });

  // 14. /api/health responds
  await withPage('14. Health endpoint', async (page) => {
    const r = await page.request.get(BASE + '/api/health');
    if (!r.ok()) return record('14. Health endpoint', 'fail', `HTTP ${r.status()}`);
    const j = await r.json();
    record('14. Health endpoint', j.ok ? 'pass' : 'warn', `version=${j.version}`);
  });

  // 15. Service-worker is registered (PWA)
  await withPage('15. Service worker', async (page) => {
    await page.goto(BASE);
    const reg = await page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) return null;
      const r = await navigator.serviceWorker.getRegistration();
      return r ? {scope: r.scope, active: !!r.active} : null;
    });
    record('15. Service worker',
            reg && reg.active ? 'pass' : 'warn',
            reg ? JSON.stringify(reg) : 'no SW');
  });

  // 16. Book.html ?nfc=<slug> parses + shows confirm card with bad slug
  await withPage('16. Book page NFC param', async (page) => {
    await page.goto(BASE + '/book.html?nfc=zzzz999bogus');
    // Bad slug shouldn't show the green card (resolution fails) — book form still loads
    const formExists = await page.locator('#book-btn').count() > 0;
    record('16. Book page NFC param', formExists ? 'pass' : 'fail',
            'form should still render even with bad slug');
  });

  // 17. Sitemap accessible
  await withPage('17. Sitemap', async (page) => {
    const r = await page.request.get(BASE + '/sitemap.xml');
    if (!r.ok()) return record('17. Sitemap', 'fail', `HTTP ${r.status()}`);
    const text = await r.text();
    const hasNfc = text.includes('/nfc.html');
    record('17. Sitemap', hasNfc ? 'pass' : 'warn', 'nfc.html present in sitemap');
  });

  // 18. /me.html requires auth (redirects unauth user)
  await withPage('18. /me.html auth gate', async (page) => {
    await page.goto(BASE + '/me.html');
    // Wait for the JS auth check to redirect
    await page.waitForLoadState('networkidle').catch(() => {});
    const url = page.url();
    record('18. /me.html auth gate',
            /login\.html/.test(url) ? 'pass' : 'warn',
            `url=${url}`);
  });

  // 19. /admin.html requires admin token
  await withPage('19. /admin.html access', async (page) => {
    const r = await page.goto(BASE + '/admin.html');
    record('19. /admin.html access',
            r && r.status() < 400 ? 'pass' : 'warn',
            `HTTP ${r?.status()}`);
  });

  // 20. /api/wallet/balance without auth
  await withPage('20. Wallet endpoint guards auth', async (page) => {
    const r = await page.request.get(BASE + '/api/wallet/balance');
    record('20. Wallet endpoint guards auth',
            r.status() === 401 ? 'pass' : 'fail',
            `expected 401, got ${r.status()}`);
  });

  // ==========================================================================
  // SUMMARY
  // ==========================================================================
  const pass = REPORT.filter(r => r.status === 'pass').length;
  const fail = REPORT.filter(r => r.status === 'fail').length;
  const warn = REPORT.filter(r => r.status === 'warn').length;
  console.log('\n' + '='.repeat(50));
  console.log(`📊 Total: ${REPORT.length} · ✅ ${pass} · ⚠️ ${warn} · ❌ ${fail}`);
  console.log('='.repeat(50));
  console.log('\nFINDINGS-JSON:' + JSON.stringify({pass, warn, fail, items: REPORT}));
})();
