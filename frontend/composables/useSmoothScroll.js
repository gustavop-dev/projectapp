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

/**
 * Walk up the DOM from `el` looking for the nearest ancestor that is itself
 * scrollable (overflow-y === 'auto' | 'scroll' AND scrollHeight > clientHeight).
 * Returns `null` if none found before reaching `document.body`.
 *
 * @param {Element} el
 * @returns {Element|null}
 */
export function findScrollableAncestor(el) {
  if (!el) return null;
  let parent = el.parentElement;
  while (parent && parent !== document.body) {
    const style = window.getComputedStyle(parent);
    const overflowY = style.overflowY;
    if (
      (overflowY === 'auto' || overflowY === 'scroll') &&
      parent.scrollHeight > parent.clientHeight
    ) {
      return parent;
    }
    parent = parent.parentElement;
  }
  return null;
}

/**
 * Smoothly scroll a scrollable container so that `el` lands centered (or at
 * the top) inside the container's viewport. RAF-driven with ease-out cubic
 * so the motion has perceptible deceleration vs the browser's native
 * `behavior: 'smooth'` which is uncontrollable and often feels abrupt.
 * No-op when the element is already close enough (delta < 4 px).
 *
 * @param {Element} container - Scrollable container (overflow-y-auto/scroll)
 * @param {Element} el - Target element inside the container
 * @param {object} [options]
 * @param {number} [options.duration=700] - Animation duration in ms
 * @param {'center'|'start'} [options.block='center'] - Placement of `el`
 * @returns {Promise<void>}
 */
export function smoothScrollContainerToElement(
  container,
  el,
  { duration = 700, block = 'center' } = {},
) {
  return new Promise((resolve) => {
    if (!container || !el) { resolve(); return; }

    const containerRect = container.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    // Relative top of `el` within container's scrollTop coordinate space.
    const relativeTop = elRect.top - containerRect.top + container.scrollTop;
    let targetTop;
    if (block === 'center') {
      targetTop = relativeTop - container.clientHeight / 2 + el.clientHeight / 2;
    } else {
      targetTop = relativeTop;
    }
    // Clamp to the valid scrollable range.
    const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight);
    targetTop = Math.max(0, Math.min(targetTop, maxScroll));

    const startTop = container.scrollTop;
    const diff = targetTop - startTop;
    if (Math.abs(diff) < 4) { resolve(); return; }

    let startTime = null;
    function step(timestamp) {
      if (startTime === null) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);
      container.scrollTop = startTop + diff * eased;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        resolve();
      }
    }
    requestAnimationFrame(step);
  });
}
