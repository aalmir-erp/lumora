#!/usr/bin/env node
/**
 * Bubblewrap init bypass — calls @bubblewrap/core API directly to scaffold
 * a TWA project without going through the interactive CLI prompts. The CLI
 * prompts are unscriptable via stdin pipe (they ignore line breaks and
 * accumulate input as one string).
 *
 * Usage: node scripts/twa-init.js <manifest_url> <target_dir> <package_id>
 */
const path = require("path");
const fs = require("fs");

(async () => {
  const [manifestUrl, targetDir, packageId] = process.argv.slice(2);
  if (!manifestUrl || !targetDir || !packageId) {
    console.error("Usage: twa-init.js <manifest_url> <target_dir> <package_id>");
    process.exit(2);
  }
  // Find @bubblewrap/core regardless of where bubblewrap was installed.
  // After `npm install -g @bubblewrap/cli`, core sits at:
  //   <npm root -g>/@bubblewrap/cli/node_modules/@bubblewrap/core
  const npmRoot = require("child_process")
    .execSync("npm root -g", { encoding: "utf8" }).trim();
  const corePath = path.join(npmRoot, "@bubblewrap/cli/node_modules/@bubblewrap/core/dist/lib");
  if (!fs.existsSync(corePath)) {
    console.error(`@bubblewrap/core not found at ${corePath}.`);
    console.error("Install with: npm install -g @bubblewrap/cli");
    process.exit(2);
  }
  console.log("→ Using @bubblewrap/core from:", corePath);
  const { TwaManifest } = require(path.join(corePath, "TwaManifest.js"));
  const { TwaGenerator } = require(path.join(corePath, "TwaGenerator.js"));
  const { ConsoleLog } = require(path.join(corePath, "Log.js"));

  console.log("→ Fetching PWA manifest:", manifestUrl);
  const tm = await TwaManifest.fromWebManifest(manifestUrl);

  // Override what the user wants different from the auto-derived defaults.
  tm.packageId = packageId;
  tm.host = "servia.ae";  // make sure host is the public domain even though
                          // we're fetching from localhost in CI
  tm.startUrl = "/?source=twa";
  tm.appVersion = "1.0.0";
  tm.appVersionCode = 1;
  tm.fallbackType = "customtabs";
  // Brand the splash screen — teal background instead of generic white.
  // Bubblewrap's Color type wraps via the `color` npm package, so we have
  // to construct one rather than assign a hex string.
  try {
    const { Color } = require(path.join(corePath, "../../color/index.js"));
    tm.backgroundColor = new Color("#0D9488");
    // v1.22.90: themeColor sets the OS status-bar tint in TWA standalone
    // mode. Match it to the topbanner's amber so the status bar visually
    // flows into the rotating banner instead of looking like an extra
    // empty teal strip above it.
    tm.themeColor = new Color("#F59E0B");
    tm.navigationColor = new Color("#0F172A");
    tm.navigationDividerColor = new Color("#0F172A");
  } catch (_) {
    // Fallback: rely on the manifest's background_color value as-is.
  }
  tm.splashScreenFadeOutDuration = 300;

  // We DON'T rewrite shortcut URLs to servia.ae here — Bubblewrap fetches
  // shortcut icons during generation from those URLs, and Cloudflare blocks
  // the GitHub runner from servia.ae (host_not_allowed 403). Let bubblewrap
  // resolve them against the localhost manifest URL (icons download fine),
  // then post-generation we'll patch the URLs in the generated res/xml/
  // shortcuts.xml to point at the production domain.
  // Force HTTPS scheme on origin URLs so post-init updates work cleanly.
  tm.fullScopeUrl = new URL("https://servia.ae/");
  // KEEP webManifestUrl pointing at the localhost server while bubblewrap
  // is generating the project — it tries to fetch the manifest a 2nd time
  // to copy it into Android resources, and the live servia.ae URL gets a
  // 403 from Cloudflare for non-browser User-Agents. Post-generation we
  // patch it to the production URL.
  tm.webManifestUrl = new URL(manifestUrl);

  // Log the resolved manifest before generating
  console.log("→ Resolved TWA manifest:");
  console.log(JSON.stringify({
    packageId: tm.packageId, host: tm.host, name: tm.name,
    launcherName: tm.launcherName, startUrl: tm.startUrl,
    appVersion: tm.appVersion, appVersionCode: tm.appVersionCode,
    iconUrl: tm.iconUrl, fullScopeUrl: tm.fullScopeUrl?.toString(),
  }, null, 2));

  fs.mkdirSync(targetDir, { recursive: true });
  process.chdir(targetDir);

  const log = new ConsoleLog("twa-init");
  console.log("→ Generating Android Studio project at", targetDir);
  await new TwaGenerator().createTwaProject(targetDir, tm, log);

  // Patch webManifestUrl back to the production URL before persisting,
  // so when the user later inspects twa-manifest.json or runs `bubblewrap
  // update` post-deployment, the manifest URL is correct.
  tm.webManifestUrl = new URL("https://servia.ae/manifest.webmanifest");

  // Post-process: rewrite shortcut URLs in the generated shortcuts.xml +
  // strings.xml from localhost to servia.ae (the user's phone obviously
  // can't reach our CI's localhost server).
  function rewriteFile(p) {
    if (!fs.existsSync(p)) return;
    const re = /https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?/g;
    const before = fs.readFileSync(p, "utf8");
    const after = before.replace(re, "https://servia.ae");
    if (after !== before) {
      fs.writeFileSync(p, after);
      console.log("→ Patched localhost → servia.ae in", path.relative(targetDir, p));
    }
  }
  const candidates = [
    path.join(targetDir, "app/src/main/res/xml/shortcuts.xml"),
    path.join(targetDir, "app/src/main/res/values/strings.xml"),
    path.join(targetDir, "app/src/main/AndroidManifest.xml"),
  ];
  candidates.forEach(rewriteFile);
  fs.writeFileSync(
    path.join(targetDir, "twa-manifest.json"),
    JSON.stringify(tm.toJson(), null, 2)
  );
  console.log("→ Done. Wrote twa-manifest.json");
})().catch(e => {
  console.error("FAILED:", e.message);
  if (e.stack) console.error(e.stack);
  process.exit(1);
});
