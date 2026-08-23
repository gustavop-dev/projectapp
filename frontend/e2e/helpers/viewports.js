// ProjectApp viewport source for responsive E2E and the fleet ledger.
// The product contract lives in config/responsive.js; this helper only exposes
// the test.use() shape expected by the responsive standard.
import { PANEL_VIEWPORTS } from '../../config/responsive.js';

export { PANEL_VIEWPORTS };
export const VIEWPORTS = PANEL_VIEWPORTS;

export function viewportUse(alias) {
  const viewport = VIEWPORTS[alias];
  if (!viewport) throw new Error(`Viewport responsivo desconocido: ${alias}`);

  return {
    viewport,
    hasTouch: ['compact', 'portrait', 'landscape'].includes(alias),
  };
}
