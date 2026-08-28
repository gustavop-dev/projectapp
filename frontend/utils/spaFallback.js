const META_REFRESH_PATTERN = /http-equiv\s*=\s*["']?refresh\b/i;
const NUXT_MOUNT_PATTERN = /<[^>]+\bid\s*=\s*(["'])__nuxt\1/i;

/**
 * Reject generated fallback documents that cannot bootstrap the Nuxt SPA.
 *
 * The production catch-all serves 200.html for every non-prerendered route,
 * including the panel, platform and proposal applications. A redirect page is
 * therefore not a degraded fallback: it makes every deep route unavailable.
 */
export function assertValidSpaFallbackHtml(html) {
  if (typeof html !== 'string' || html.trim() === '') {
    throw new Error('fallback HTML is empty');
  }

  if (META_REFRESH_PATTERN.test(html)) {
    throw new Error('fallback HTML contains a meta refresh redirect');
  }

  if (!NUXT_MOUNT_PATTERN.test(html)) {
    throw new Error('fallback HTML does not contain the #__nuxt mount');
  }
}
