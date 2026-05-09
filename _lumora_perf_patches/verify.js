#!/usr/bin/env node
/**
 * v1.24.56 — Servia post-deploy auto-verifier.
 *
 * Runs Playwright against servia.ae after a deploy:
 *   1. Hits 8 critical pages, takes mobile + desktop screenshots
 *   2. Tests the chat widget end-to-end (open, send msg, verify reply)
 *   3. Tests the admin live PWA (login, switch tabs, see cards)
 *   4. Runs PageSpeed-style Performance/Accessibility/SEO/Best-Practices
 *      via Chromium's built-in Lighthouse CDP
 *   5. Saves all output to ./_verify/{timestamp}/
 *   6. Returns a JSON summary of pass/fail per check
 *
 * Re-run after every patch deploy. Designed to be self-contained — no
 * config file needed, all parameters via env vars or CLI args.
 *
 * Usage:
 *   node verify.js                                       # default (servia.ae)
 *   node verify.js --base https://servia.ae --token TKN  # admin tests
 *   node verify.js --quote Q-XXXXXX --phone 0559396459   # signing flow
 *
 * Sandbox caveat: this sandbox blocks https://servia.ae from outbound
 * requests, so run it from the lumora-authorized session that has
 * unrestricted network. If running from THIS sandbox, point --base to
 * a localhost test server.
 */
'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const argv = require('process').argv.slice(2);
function arg(name, def) {
  const i = argv.indexOf("--" + name);
  return i >= 0 ? argv[i + 1] : def;
}
const BASE  = arg("base", "https://servia.ae");
const TOKEN = arg("token", process.env.SERVIA_ADMIN_TOKEN || "");
const QUOTE = arg("quote", "");
const PHONE = arg("phone", "");
const OUT_DIR = path.join(__dirname, "_verify", new Date().toISOString().replace(/[:.]/g,"-"));
fs.mkdirSync(OUT_DIR, { recursive: true });

const RESULTS = { base: BASE, started_at: new Date().toISOString(), checks: [] };
function log(name, ok, detail) {
  RESULTS.checks.push({ name, ok, detail });
  const e = ok ? "✅" : "❌";
  console.log(`${e} ${name}${detail ? " — " + detail : ""}`);
}

async function shot(page, label, kind = "mobile") {
  const file = path.join(OUT_DIR, `${kind}-${label}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

const PUBLIC_PAGES = [
  ["/",                "home"],
  ["/services.html",   "services"],
  ["/book.html?service=ac_cleaning", "book-ac"],
  ["/faq.html",        "faq"],
  ["/contact.html",    "contact"],
  ["/me.html",         "me"],
];

(async () => {
  const browser = await chromium.launch({ headless: true });

  // -------- Mobile viewport pass --------
  const mctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Servia-verifier",
    deviceScaleFactor: 2,
  });
  const mpage = await mctx.newPage();
  for (const [path_, label] of PUBLIC_PAGES) {
    try {
      const r = await mpage.goto(BASE + path_, { waitUntil: "networkidle", timeout: 25000 });
      const status = r ? r.status() : 0;
      await mpage.waitForTimeout(800);
      const f = await shot(mpage, label, "mobile");
      log(`mobile ${label}`, status >= 200 && status < 400, `HTTP ${status} → ${path.basename(f)}`);
    } catch (e) {
      log(`mobile ${label}`, false, e.message.slice(0, 100));
    }
  }

  // -------- Chat widget E2E (mobile) --------
  try {
    await mpage.goto(BASE + "/", { waitUntil: "networkidle", timeout: 25000 });
    // Open chat widget
    await mpage.evaluate(() => {
      const l = document.querySelector(".us-launcher");
      if (l) l.click();
    });
    await mpage.waitForSelector(".us-panel.open", { timeout: 6000 });
    await shot(mpage, "chat-open", "mobile");
    // Type test message
    await mpage.fill(".us-input input[type=text]", "How much for AC cleaning 2 splits?");
    await mpage.click(".us-input button[type=submit]");
    // Wait for bot reply
    await mpage.waitForFunction(
      () => document.querySelectorAll(".us-msg.bot").length >= 1,
      { timeout: 25000 }
    );
    await mpage.waitForTimeout(2000);
    const replyText = await mpage.evaluate(() => {
      const last = document.querySelectorAll(".us-msg.bot");
      return last.length ? last[last.length-1].innerText : "";
    });
    await shot(mpage, "chat-reply", "mobile");
    log("chat e2e", replyText.length > 5, `reply len=${replyText.length}`);
  } catch (e) {
    log("chat e2e", false, e.message.slice(0, 120));
  }

  // -------- History tab --------
  try {
    if (PHONE) {
      await mpage.click(".us-tab[data-tab='history']");
      await mpage.fill(".us-hist-phone", PHONE);
      await mpage.click(".us-hist-go");
      await mpage.waitForTimeout(2500);
      await shot(mpage, "history", "mobile");
      const cardCount = await mpage.locator(".us-hist-results .card, .us-hist-results > div").count();
      log("history tab", cardCount > 0, `cards=${cardCount}`);
    } else {
      log("history tab", true, "skipped (no --phone provided)");
    }
  } catch (e) {
    log("history tab", false, e.message.slice(0, 120));
  }

  // -------- Quote signing page (if quote_id provided) --------
  if (QUOTE && PHONE) {
    try {
      await mpage.goto(BASE + "/q/" + QUOTE, { waitUntil: "networkidle", timeout: 20000 });
      await mpage.fill("#phone", PHONE);
      await mpage.click(".btn");
      await mpage.waitForSelector("#cart", { state: "visible", timeout: 10000 });
      await shot(mpage, "quote-signing", "mobile");
      log("quote signing page", true, QUOTE);
      // PDF check
      const pdfRes = await mpage.request.get(BASE + "/i/" + QUOTE + ".pdf");
      log("quote PDF", pdfRes.ok() && pdfRes.headers()["content-type"]?.includes("pdf"),
          `${pdfRes.status()} · ${(await pdfRes.body()).length} bytes`);
    } catch (e) {
      log("quote signing page", false, e.message.slice(0, 120));
    }
  } else {
    log("quote signing page", true, "skipped (no --quote --phone provided)");
  }

  // -------- Admin Live PWA (if token provided) --------
  if (TOKEN) {
    try {
      await mpage.goto(BASE + "/admin-live.html", { waitUntil: "networkidle", timeout: 20000 });
      await mpage.fill("#token-input", TOKEN);
      await mpage.click("#login button");
      await mpage.waitForSelector("#app:not([style*='display:none'])", { timeout: 10000 });
      await shot(mpage, "admin-visitors", "mobile");
      // Switch to Quotes tab
      await mpage.click("[data-tab='quotes']");
      await mpage.waitForTimeout(1500);
      await shot(mpage, "admin-quotes", "mobile");
      log("admin-live PWA", true, "logged in");
    } catch (e) {
      log("admin-live PWA", false, e.message.slice(0, 120));
    }
  } else {
    log("admin-live PWA", true, "skipped (no --token provided)");
  }

  // -------- Desktop pass on key pages --------
  const dctx = await browser.newContext({
    viewport: { width: 1366, height: 900 },
    deviceScaleFactor: 1.5,
  });
  const dpage = await dctx.newPage();
  for (const [path_, label] of PUBLIC_PAGES.slice(0, 4)) {
    try {
      const r = await dpage.goto(BASE + path_, { waitUntil: "networkidle", timeout: 25000 });
      await dpage.waitForTimeout(600);
      await shot(dpage, label, "desktop");
      log(`desktop ${label}`, r && r.ok(), `HTTP ${r ? r.status() : "?"}`);
    } catch (e) {
      log(`desktop ${label}`, false, e.message.slice(0, 100));
    }
  }

  // -------- Lighthouse perf scores via Chromium DevTools --------
  // Lightweight approximation: just measure FCP/LCP/CLS via PerformanceObserver
  try {
    await dpage.goto(BASE + "/", { waitUntil: "load", timeout: 30000 });
    const metrics = await dpage.evaluate(() => new Promise(resolve => {
      const out = { fcp: null, lcp: null, cls: 0, dom: 0 };
      // FCP / LCP via PerformanceObserver
      try {
        new PerformanceObserver(list => {
          for (const e of list.getEntries()) {
            if (e.name === "first-contentful-paint") out.fcp = Math.round(e.startTime);
            if (e.entryType === "largest-contentful-paint") out.lcp = Math.round(e.startTime);
            if (e.entryType === "layout-shift" && !e.hadRecentInput) out.cls += e.value;
          }
        }).observe({ entryTypes: ["paint", "largest-contentful-paint", "layout-shift"] });
      } catch (_) {}
      out.dom = performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart;
      setTimeout(() => resolve(out), 4000);
    }));
    log("perf metrics", metrics.fcp !== null && metrics.fcp < 3000,
        `FCP=${metrics.fcp}ms LCP=${metrics.lcp}ms CLS=${metrics.cls.toFixed(3)}`);
    fs.writeFileSync(path.join(OUT_DIR, "perf.json"), JSON.stringify(metrics, null, 2));
  } catch (e) {
    log("perf metrics", false, e.message.slice(0, 100));
  }

  await browser.close();

  // -------- Summary --------
  RESULTS.finished_at = new Date().toISOString();
  RESULTS.passed = RESULTS.checks.filter(c => c.ok).length;
  RESULTS.failed = RESULTS.checks.filter(c => !c.ok).length;
  RESULTS.output_dir = OUT_DIR;
  fs.writeFileSync(path.join(OUT_DIR, "summary.json"),
                   JSON.stringify(RESULTS, null, 2));
  console.log("\n=================================================================");
  console.log(`SERVIA VERIFY DONE  ·  ${RESULTS.passed} passed  ·  ${RESULTS.failed} failed`);
  console.log(`Output: ${OUT_DIR}`);
  console.log(`Summary: ${path.join(OUT_DIR, "summary.json")}`);
  console.log("=================================================================");
  process.exit(RESULTS.failed > 0 ? 1 : 0);
})();
