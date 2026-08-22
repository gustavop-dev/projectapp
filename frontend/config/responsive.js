/**
 * Canonical responsive contract for the internal panel.
 *
 * CSS, runtime components and Playwright import the same breakpoints so a
 * view cannot validate itself against a different definition of "tablet".
 */
export const PANEL_BREAKPOINTS = Object.freeze({
  portrait: 600,
  landscape: 1000,
  desktop: 1280,
  wide: 1920,
});

/**
 * Tailwind reserves `portrait:` and `landscape:` for orientation queries.
 * Panel aliases are namespaced so they always mean width.
 */
export const PANEL_SCREENS = Object.freeze({
  portrait: 'panel-portrait',
  landscape: 'panel-landscape',
  desktop: 'panel-desktop',
  wide: 'panel-wide',
});

export const PANEL_CONTENT_MAX_PX = 1440;

export const PANEL_VIEWPORTS = Object.freeze({
  compact: Object.freeze({ width: 412, height: 915 }),
  portrait: Object.freeze({ width: 835, height: 1194 }),
  landscape: Object.freeze({ width: 1195, height: 835 }),
  desktop: Object.freeze({ width: 1440, height: 900 }),
  wide: Object.freeze({ width: 2560, height: 1440 }),
});

export const PANEL_MEDIA = Object.freeze({
  portrait: `(min-width: ${PANEL_BREAKPOINTS.portrait}px)`,
  landscape: `(min-width: ${PANEL_BREAKPOINTS.landscape}px)`,
  desktop: `(min-width: ${PANEL_BREAKPOINTS.desktop}px)`,
  wide: `(min-width: ${PANEL_BREAKPOINTS.wide}px)`,
});
