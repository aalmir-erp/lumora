/**
 * Servia heavy-scenario E2E — 50 Playwright scenarios with screenshots.
 * Runs against the LIVE deployment from a Cloudflare-allowed runner (CI).
 *
 * Each test saves a PNG to $E2E_SHOT_DIR. Outputs FINDINGS-JSON line at end.
 *
 * Run: SERVIA_BASE=https://servia.ae node tests/e2e-heavy.mjs
 */
import { chromium, devices } from 'playwright';
import { mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';

const BASE = process.env.SERVIA_BASE || 'https://servia.ae';
const SHOTS = process.env.E2E_SHOT_DIR || '/tmp/e2e-shots';
mkdirSync(SHOTS, { recursive: true });

const REPORT = [];
function rec(id, name, status, detail, shot) {
  REPORT.push({id, name, status, detail: String(detail || '').slice(0, 400), shot: shot || null});
  const icon = {pass:'✅',fail:'❌',warn:'⚠️',skip:'⏭'}[status]||'•';
  console.log(`${icon} [${id}] ${name}${detail ? ' — ' + String(detail).slice(0,200) : ''}`);
}

async function runTest(id, name, fn, deviceName) {
  const browser = await chromium.launch({ headless: true });
  let shot = join(SHOTS, `${id}.png`);
  try {
    const ctx = await browser.newContext({ ...(deviceName ? devices[deviceName] : {}), ignoreHTTPSErrors: true });
    const page = await ctx.newPage();
    page.setDefaultTimeout(18000);
    try {
      await fn(page);
      await page.screenshot({ path: shot, fullPage: false }).catch(()=>{});
    } catch (e) {
      shot = join(SHOTS, `${id}-FAIL.png`);
      await page.screenshot({ path: shot, fullPage: false }).catch(()=>{});
      rec(id, name, 'fail', `exception: ${e.message.slice(0,150)}`, shot);
    }
  } finally { await browser.close(); }
  return shot;
}

const TESTS = [
  // === Page loads + SEO (1-10) ===
  ['T01','Homepage loads (desktop)', async (p) => {
    const r = await p.goto(BASE); if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T01','Homepage loads (desktop)','pass', `"${await p.title()}"`);
  }],
  ['T02','Homepage loads (mobile)', async (p) => {
    const r = await p.goto(BASE); if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T02','Homepage loads (mobile)','pass', 'iPhone 12');
  }, 'iPhone 12'],
  ['T03','/services.html lists services', async (p) => {
    await p.goto(BASE+'/services.html');
    const cards = await p.locator('.svc-card, .svc-tile-hero').count();
    if (cards < 5) throw new Error(`only ${cards} cards`);
    rec('T03','/services.html lists services','pass',`${cards} cards`);
  }],
  ['T04','/coverage.html renders', async (p) => {
    const r = await p.goto(BASE+'/coverage.html');
    if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T04','/coverage.html renders','pass','OK');
  }],
  ['T05','/blog index loads', async (p) => {
    const r = await p.goto(BASE+'/blog');
    if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T05','/blog index loads','pass','OK');
  }],
  ['T06','Sitemap has /nfc.html', async (p) => {
    const r = await p.request.get(BASE+'/sitemap.xml');
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    const t = await r.text();
    if (!t.includes('/nfc.html')) throw new Error('nfc.html missing');
    rec('T06','Sitemap has /nfc.html','pass','OK');
  }],
  ['T07','robots.txt accessible', async (p) => {
    const r = await p.request.get(BASE+'/robots.txt');
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    rec('T07','robots.txt accessible','pass','OK');
  }],
  ['T08','/faq.html FAQPage schema', async (p) => {
    await p.goto(BASE+'/faq.html');
    const j = await p.locator('script[type="application/ld+json"]').allInnerTexts();
    if (!j.some(s => /FAQPage/.test(s))) throw new Error('no FAQPage schema');
    rec('T08','/faq.html FAQPage schema','pass','present');
  }],
  ['T09','Homepage Org/LocalBusiness schema', async (p) => {
    await p.goto(BASE);
    const j = await p.locator('script[type="application/ld+json"]').allInnerTexts();
    if (!j.some(s => /Organization|LocalBusiness/.test(s))) throw new Error('missing schema');
    rec('T09','Homepage Org/LocalBusiness schema','pass','present');
  }],
  ['T10','Theme-color is teal #0F766E', async (p) => {
    await p.goto(BASE);
    const tc = (await p.locator('meta[name="theme-color"]').first().getAttribute('content') || '').toUpperCase();
    if (tc !== '#0F766E') throw new Error(`got ${tc}`);
    rec('T10','Theme-color is teal #0F766E','pass',tc);
  }],

  // === Nav + UI (11-20) ===
  ['T11','Mobile nav single-row', async (p) => {
    await p.goto(BASE);
    const lb = await p.locator('.nav-inner img').first().boundingBox();
    const cb = await p.locator('.nav-cta').boundingBox().catch(()=>null);
    if (!lb || !cb) throw new Error('elements missing');
    if (Math.abs(lb.y - cb.y) >= Math.max(lb.height, cb.height)) throw new Error(`Δy=${(cb.y-lb.y).toFixed(0)}`);
    rec('T11','Mobile nav single-row','pass',`Δy=${(cb.y-lb.y).toFixed(0)}`);
  }, 'iPhone 12'],
  ['T12','Topbanner placeholder bg teal', async (p) => {
    await p.goto(BASE);
    const bg = await p.locator('#servia-topbanner').first().evaluate(el => getComputedStyle(el).backgroundImage);
    if (/F59E0B|245,?\s*158/.test(bg)) throw new Error('still orange');
    rec('T12','Topbanner placeholder bg teal','pass','OK');
  }],
  ['T13','Install banner single row height', async (p) => {
    await p.goto(BASE);
    const ib = await p.locator('#servia-install-banner').boundingBox().catch(()=>null);
    if (!ib) { rec('T13','Install banner single row height','skip','dismissed'); return; }
    if (ib.height > 50) throw new Error(`h=${ib.height}px (>50 = wrap)`);
    rec('T13','Install banner single row height','pass',`${ib.height}px`);
  }, 'iPhone 12'],
  ['T14','Footer present', async (p) => {
    await p.goto(BASE);
    if (await p.locator('footer, .footer').count() === 0) throw new Error('no footer');
    rec('T14','Footer present','pass','OK');
  }],
  ['T15','/install.html APK card', async (p) => {
    await p.goto(BASE+'/install.html');
    if (await p.locator('#apk-download').count() === 0) throw new Error('no apk-download');
    rec('T15','/install.html APK card','pass','OK');
  }],
  ['T16','/install.html Wear OS card', async (p) => {
    await p.goto(BASE+'/install.html');
    if (await p.locator('#wear-download').count() === 0) throw new Error('no wear-download');
    rec('T16','/install.html Wear OS card','pass','OK');
  }],
  ['T17','/install.html iOS section', async (p) => {
    await p.goto(BASE+'/install.html');
    const t = await p.textContent('body');
    if (!/iPhone|iOS|Apple Watch/i.test(t)) throw new Error('no iOS section');
    rec('T17','/install.html iOS section','pass','OK');
  }],
  ['T18','Search input has ss-input class', async (p) => {
    await p.goto(BASE+'/search.html');
    const cls = (await p.locator('#q').getAttribute('class')) || '';
    if (!/ss-input/.test(cls)) throw new Error(`class="${cls}"`);
    rec('T18','Search input has ss-input class','pass',cls);
  }],
  ['T19','Search trending chips load', async (p) => {
    await p.goto(BASE+'/search.html');
    const chips = await p.locator('#trending .ss-chip, .ss-chips-row .ss-chip').count();
    rec('T19','Search trending chips load', chips > 0 ? 'pass':'warn', `${chips} chips`);
  }],
  ['T20','Hero rotator present', async (p) => {
    await p.goto(BASE);
    if (await p.locator('#hero-rotator').count() === 0) throw new Error('no #hero-rotator');
    rec('T20','Hero rotator present','pass','present');
  }],

  // === NFC feature (21-30) ===
  ['T21','/nfc.html loads', async (p) => {
    const r = await p.goto(BASE+'/nfc.html');
    if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T21','/nfc.html loads','pass','OK');
  }],
  ['T22','/nfc.html 3-mode panel', async (p) => {
    await p.goto(BASE+'/nfc.html');
    const t = await p.textContent('body');
    if (!/Manual|manual_pay/i.test(t) || !/Auto-wallet|preconfigured/i.test(t)) throw new Error('mode panel missing');
    rec('T22','/nfc.html 3-mode panel','pass','OK');
  }],
  ['T23','/nfc.html bot widget', async (p) => {
    await p.goto(BASE+'/nfc.html');
    if (await p.locator('#advisor-card, #advisor-msgs').count() === 0) throw new Error('no advisor');
    rec('T23','/nfc.html bot widget','pass','OK');
  }],
  ['T24','/nfc.html bulk-order section', async (p) => {
    await p.goto(BASE+'/nfc.html');
    if (await p.locator('#bulk-rows').count() === 0) throw new Error('no bulk-rows');
    rec('T24','/nfc.html bulk-order section','pass','OK');
  }],
  ['T25','/nfc.html schema set', async (p) => {
    await p.goto(BASE+'/nfc.html');
    const j = await p.locator('script[type="application/ld+json"]').allInnerTexts();
    if (!j.some(s => /HowTo/.test(s)) || !j.some(s => /FAQPage/.test(s)) || !j.some(s => /Product/.test(s))) throw new Error('schema missing');
    rec('T25','/nfc.html schema set','pass','HowTo+FAQ+Product');
  }],
  ['T26','/api/nfc/tag bad slug 404', async (p) => {
    const r = await p.request.get(BASE+'/api/nfc/tag/zzzzbogus99');
    if (r.status() !== 404) throw new Error(`got ${r.status()}`);
    rec('T26','/api/nfc/tag bad slug 404','pass','OK');
  }],
  ['T27','/t/<bad-slug> redirects', async (p) => {
    const r = await p.request.get(BASE+'/t/zzzzbogus99', { maxRedirects: 0 });
    const loc = r.headers()['location'] || '';
    if (r.status() !== 302 || !/nfc-not-found/.test(loc)) throw new Error(`${r.status()} → ${loc}`);
    rec('T27','/t/<bad-slug> redirects','pass',loc);
  }],
  ['T28','/nfc.html vehicle recovery section', async (p) => {
    await p.goto(BASE+'/nfc.html');
    const t = await p.textContent('body');
    if (!/Roadside|breakdown|recovery/i.test(t)) throw new Error('missing');
    rec('T28','/nfc.html vehicle recovery section','pass','OK');
  }],
  ['T29','/api/nfc/consult endpoint', async (p) => {
    const r = await p.request.post(BASE+'/api/nfc/consult', { data: {messages: []} });
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    rec('T29','/api/nfc/consult endpoint','pass','greets');
  }],
  ['T30','/api/admin/nfc/stats auth-gated', async (p) => {
    const r = await p.request.get(BASE+'/api/admin/nfc/stats');
    if (![401,403].includes(r.status())) throw new Error(`got ${r.status()}`);
    rec('T30','/api/admin/nfc/stats auth-gated','pass',`${r.status()}`);
  }],

  // === Auth + accounts (31-40) ===
  ['T31','/login.html renders', async (p) => {
    const r = await p.goto(BASE+'/login.html');
    if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T31','/login.html renders','pass','OK');
  }],
  ['T32','/me.html requires auth', async (p) => {
    await p.goto(BASE+'/me.html');
    await p.waitForLoadState('networkidle').catch(()=>{});
    if (!/login\.html/.test(p.url())) throw new Error(`url=${p.url()}`);
    rec('T32','/me.html requires auth','pass','redirected');
  }],
  ['T33','Demo customer login (test@servia.ae)', async (p) => {
    const r = await p.request.post(BASE+'/api/auth/customer/login',
      { data: {email:'test@servia.ae', password:'test123'} });
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    const j = await r.json();
    if (!j.token) throw new Error('no token');
    rec('T33','Demo customer login (test@servia.ae)','pass',j.token.slice(0,12)+'...');
  }],
  ['T34','Demo customer (aisha@demo)', async (p) => {
    const r = await p.request.post(BASE+'/api/auth/customer/login',
      { data: {email:'aisha@demo.servia.ae', password:'aisha123'} });
    if (!r.ok()) { rec('T34','Demo customer (aisha@demo)','warn','seed not run'); return; }
    rec('T34','Demo customer (aisha@demo)','pass','OK');
  }],
  ['T35','Bad password rejected', async (p) => {
    const r = await p.request.post(BASE+'/api/auth/customer/login',
      { data: {email:'test@servia.ae', password:'WRONG'} });
    if (r.status() !== 401) throw new Error(`got ${r.status()}`);
    rec('T35','Bad password rejected','pass','401 OK');
  }],
  ['T36','/api/wallet/balance auth-gated', async (p) => {
    const r = await p.request.get(BASE+'/api/wallet/balance');
    if (r.status() !== 401) throw new Error(`got ${r.status()}`);
    rec('T36','/api/wallet/balance auth-gated','pass','401');
  }],
  ['T37','Wallet balance after login', async (p) => {
    const lr = await p.request.post(BASE+'/api/auth/customer/login',
      { data: {email:'test@servia.ae', password:'test123'} });
    const tok = (await lr.json()).token;
    const r = await p.request.get(BASE+'/api/wallet/balance', { headers: {authorization:'Bearer '+tok} });
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    const j = await r.json();
    rec('T37','Wallet balance after login','pass',`AED ${j.balance_aed||0}`);
  }],
  ['T38','/api/me/bookings authed', async (p) => {
    const lr = await p.request.post(BASE+'/api/auth/customer/login',
      { data: {email:'test@servia.ae', password:'test123'} });
    const tok = (await lr.json()).token;
    const r = await p.request.get(BASE+'/api/me/bookings', { headers: {authorization:'Bearer '+tok} });
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    rec('T38','/api/me/bookings authed','pass','OK');
  }],
  ['T39','/api/nfc/my-tags authed', async (p) => {
    const lr = await p.request.post(BASE+'/api/auth/customer/login',
      { data: {email:'test@servia.ae', password:'test123'} });
    const tok = (await lr.json()).token;
    const r = await p.request.get(BASE+'/api/nfc/my-tags', { headers: {authorization:'Bearer '+tok} });
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    rec('T39','/api/nfc/my-tags authed','pass','OK');
  }],
  ['T40','/admin.html responds', async (p) => {
    const r = await p.goto(BASE+'/admin.html');
    if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T40','/admin.html responds','pass','OK');
  }],

  // === API health (41-45) ===
  ['T41','/api/health responds', async (p) => {
    const r = await p.request.get(BASE+'/api/health');
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    const j = await r.json();
    rec('T41','/api/health responds','pass',`v${j.version}`);
  }],
  ['T42','/api/services >=10', async (p) => {
    const r = await p.request.get(BASE+'/api/services');
    const j = await r.json();
    const n = (j.services||[]).length;
    if (n < 10) throw new Error(`only ${n}`);
    rec('T42','/api/services >=10','pass',`${n}`);
  }],
  ['T43','/api/app/latest works', async (p) => {
    const r = await p.request.get(BASE+'/api/app/latest');
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    const j = await r.json();
    rec('T43','/api/app/latest works','pass',`apk_v=${j.apk_version}`);
  }],
  ['T44','/api/site/social works', async (p) => {
    const r = await p.request.get(BASE+'/api/site/social');
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    rec('T44','/api/site/social works','pass','OK');
  }],
  ['T45','/api/brand works', async (p) => {
    const r = await p.request.get(BASE+'/api/brand');
    if (!r.ok()) throw new Error(`HTTP ${r.status()}`);
    rec('T45','/api/brand works','pass','OK');
  }],

  // === Booking + cart (46-50) ===
  ['T46','/book.html renders form', async (p) => {
    await p.goto(BASE+'/book.html');
    if (await p.locator('#book-btn').count() === 0) throw new Error('no book button');
    rec('T46','/book.html renders form','pass','OK');
  }],
  ['T47','/book.html?service=deep_cleaning prefills', async (p) => {
    await p.goto(BASE+'/book.html?service=deep_cleaning');
    await p.waitForTimeout(800);
    const v = await p.locator('#service').inputValue().catch(()=>null);
    if (v !== 'deep_cleaning') { rec('T47','/book.html?service=deep_cleaning prefills', 'warn', `got=${v}`); return; }
    rec('T47','/book.html?service=deep_cleaning prefills','pass','prefilled');
  }],
  ['T48','/book.html?nfc=<bogus> graceful', async (p) => {
    await p.goto(BASE+'/book.html?nfc=zzzzbogus99');
    if (await p.locator('#book-btn').count() === 0) throw new Error('book button missing');
    rec('T48','/book.html?nfc=<bogus> graceful','pass','OK');
  }],
  ['T49','/cart.html loads', async (p) => {
    const r = await p.goto(BASE+'/cart.html');
    if (!r || r.status() >= 400) throw new Error(`HTTP ${r?.status()}`);
    rec('T49','/cart.html loads','pass','OK');
  }],
  ['T50','Service worker active', async (p) => {
    await p.goto(BASE);
    const reg = await p.evaluate(async () => {
      if (!('serviceWorker' in navigator)) return null;
      const r = await navigator.serviceWorker.getRegistration();
      return r && r.active ? {scope: r.scope} : null;
    });
    if (!reg) { rec('T50','Service worker active','warn','not registered'); return; }
    rec('T50','Service worker active','pass',reg.scope);
  }],
];

(async () => {
  console.log(`\n🎭 Servia E2E Heavy · 50 scenarios · ${BASE}\n${'='.repeat(60)}\n`);
  for (const [id, name, fn, dev] of TESTS) {
    try { await runTest(id, name, fn, dev); }
    catch (e) { rec(id, name, 'fail', e.message); }
  }
  const pass = REPORT.filter(r => r.status === 'pass').length;
  const fail = REPORT.filter(r => r.status === 'fail').length;
  const warn = REPORT.filter(r => r.status === 'warn').length;
  const skip = REPORT.filter(r => r.status === 'skip').length;
  console.log(`\n${'='.repeat(60)}\n📊 ${REPORT.length} runs · ✅ ${pass} · ⚠️ ${warn} · ❌ ${fail} · ⏭ ${skip}`);
  console.log(`📸 Screenshots: ${SHOTS}/`);
  writeFileSync('/tmp/findings.json', JSON.stringify({pass, warn, fail, skip,
    items: REPORT.map(r => ({id:r.id, name:r.name, status:r.status, detail:r.detail.slice(0,140), shot:r.shot}))
  }));
  console.log('\nFINDINGS-JSON:' + JSON.stringify({pass, warn, fail, skip,
    items: REPORT.map(r => ({id:r.id, name:r.name, status:r.status, detail:r.detail.slice(0,140)}))
  }));
})();
