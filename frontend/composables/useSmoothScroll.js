/**
 * Smooth scroll utility using requestAnimationFrame with easing.
 * Provides a controlled, silky-smooth scroll animation instead of
 * relying on the browser's native `behavior: 'smooth'` which can
 * feel abrupt on long distances.
 */

/**
 * Easing function: ease-out cubic — fast start, gentle deceleration.
 * @param {number} t - Progress from 0 to 1
 * @returns {number} Eased value
 */
function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * Smoothly scroll the window to a target Y position.
 *
 * @param {number} targetY - The target scrollY position
 * @param {number} [duration=600] - Animation duration in ms
 * @returns {Promise<void>} Resolves when the scroll animation completes
 */
export function smoothScrollTo(targetY, duration = 600) {
  return new Promise((resolve) => {
    const startY = window.scrollY;
    const diff = targetY - startY;

    if (Math.abs(diff) < 1) {
      resolve();
      return;
    }

    let startTime = null;

    function step(timestamp) {
      if (startTime === null) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);

      window.scrollTo(0, startY + diff * eased);

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        resolve();
      }
    }

    requestAnimationFrame(step);
  });
}

/**
 * Smoothly scroll the window so that a given element is visible,
 * placing it at a specific vertical position within the viewport.
 *
 * @param {Element} el - The DOM element to scroll to
 * @param {object} [options]
 * @param {number} [options.duration=600] - Animation duration in ms
 * @param {number} [options.viewportOffset=0.15] - Fraction of viewport height
 *   to use as top offset (0.15 = element placed 15% from top)
 * @returns {Promise<void>}
 */
export function smoothScrollToElement(el, { duration = 600, viewportOffset = 0.15 } = {}) {
  const rect = el.getBoundingClientRect();
  const targetY = window.scrollY + rect.top - window.innerHeight * viewportOffset;
  return smoothScrollTo(Math.max(0, targetY), duration);
}
