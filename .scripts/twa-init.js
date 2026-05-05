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
  // Without this the splash flashes a white card with a small icon, which
  // looks unfinished. Teal matches the brand and makes the launch feel
  // intentional.
  tm.backgroundColor = "#0D9488";   // teal — matches the navigation chrome
  tm.themeColor = "#0D9488";
  tm.themeColorDark = "#0F172A";
  tm.navigationColor = "#0D9488";
  tm.navigationColorDark = "#0F172A";
  tm.splashScreenFadeOutDuration = 300;

  // Rewrite shortcut URLs to absolute https://servia.ae paths. Bubblewrap
  // resolved them against the localhost manifest URL, which would make the
  // TWA's long-press shortcuts point at localhost:8080 — broken on real
  // phones. Without this fix, every long-press shortcut just opens the
  // home page (404 → fallback).
  if (Array.isArray(tm.shortcuts)) {
    tm.shortcuts = tm.shortcuts.map(s => {
      const sc = Object.assign({}, s);
      if (sc.url) {
        try {
          const u = new URL(sc.url);
          // Replace whatever host the URL has with servia.ae.
          u.protocol = "https:";
          u.host = "servia.ae";
          sc.url = u.toString();
        } catch (_) {}
      }
      // Same for shortcut iconUrl — it'll fail to download otherwise.
      if (sc.chosenIconUrl) {
        try {
          const u = new URL(sc.chosenIconUrl);
          u.protocol = "https:"; u.host = "servia.ae";
          sc.chosenIconUrl = u.toString();
        } catch (_) {}
      }
      return sc;
    });
  }
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
