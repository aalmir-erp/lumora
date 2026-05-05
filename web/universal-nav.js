/* Servia universal nav + footer.
 *
 * REGRESSED to a no-op for the moment. The previous version swapped
 * nav.innerHTML and footer.innerHTML on DOMContentLoaded, which caused
 * a visible layout shift after first paint — perceived by users as a
 * "jerk" right when the page appeared interactive.
 *
 * Until we finish baking the canonical nav directly into each page's
 * HTML (no JS swap), this file does nothing. Loaded on every page so
 * existing <script src="/universal-nav.js" defer> tags don't 404.
 */
(function () {
  if (window.__servia_universal_nav) return;
  window.__servia_universal_nav = true;
})();
