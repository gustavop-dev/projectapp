// v-auto-resize: grows a <textarea> with its content so no inner scroll is
// needed. The `rows` attribute still defines the minimum height.
export const vAutoResize = {
  mounted(el) {
    el.style.overflow = 'hidden';

    const computeMinHeight = () => {
      const rows = parseInt(el.getAttribute('rows'), 10) || 3;
      const cs = window.getComputedStyle(el);
      const lineHeight =
        parseFloat(cs.lineHeight) ||
        parseFloat(cs.fontSize) * 1.5;
      const paddingY =
        parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
      const borderY =
        parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
      return rows * lineHeight + paddingY + borderY;
    };

    el._autoResizeMinHeight = computeMinHeight();
    el._autoResizeHandler = () => {
      el.style.height = 'auto';
      const next = Math.max(el.scrollHeight, el._autoResizeMinHeight);
      if (el._autoResizeLastHeight === next) return;
      el._autoResizeLastHeight = next;
      el.style.height = next + 'px';
    };
    el.addEventListener('input', el._autoResizeHandler);
    el._autoResizeHandler();
  },
  updated(el) {
    if (!el._autoResizeHandler) return;
    el._autoResizeHandler();
  },
  beforeUnmount(el) {
    el.removeEventListener('input', el._autoResizeHandler);
  },
};
