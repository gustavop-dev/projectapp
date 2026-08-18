/**
 * Inline chevron for native `<select>` controls.
 *
 * The arrow ships as a data-URI background image, so its colour is baked into
 * the string and cannot be reached from CSS. A select painted on a solid
 * background (BaseMobileTabSelect's `nav` variant) therefore needs its own
 * light copy — the grey one is invisible on `bg-primary`.
 */
function arrowStyle(stroke) {
  return `background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='${stroke}' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e"); background-position: right 0.5rem center; background-repeat: no-repeat; background-size: 1.5em 1.5em; padding-right: 2.5rem;`;
}

export const SELECT_ARROW_STYLE = arrowStyle('%236b7280');
export const SELECT_ARROW_STYLE_INVERTED = arrowStyle('%23ffffff');
