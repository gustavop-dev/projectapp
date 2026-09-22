export const LINKTREE_DEFAULTS = {
  background_color: '#001713',
  accent_color: '#f0ff3d',
  text_color: '#ffffff',
  muted_color: '#809490',
  button_text_color: '#001713',
  font_family: 'Ubuntu',
};

export const isFontFamily = (value) => /^[A-Za-z][A-Za-z0-9 -]{0,99}$/.test(value);
export const googleFontUrl = (family) => {
  const safeFamily = isFontFamily(family) ? family : 'Ubuntu';
  // Custom families may have only one weight. Request their default face;
  // retain the original four weights for the existing Ubuntu design.
  const weights = safeFamily === 'Ubuntu' ? ':wght@300;400;500;700' : '';
  return `https://fonts.googleapis.com/css2?family=${encodeURIComponent(safeFamily)}${weights}&display=swap`;
};

export function linktreeTheme(tree = {}) {
  const colors = Object.fromEntries(Object.entries(LINKTREE_DEFAULTS)
    .filter(([key]) => key !== 'font_family')
    .map(([key, fallback]) => [key, /^#[0-9a-fA-F]{6}$/.test(tree[key]) ? tree[key] : fallback]));
  const family = isFontFamily(tree.font_family) ? tree.font_family : 'Ubuntu';
  return {
    '--lt-background': colors.background_color,
    '--lt-accent': colors.accent_color,
    '--lt-text': colors.text_color,
    '--lt-muted': colors.muted_color,
    '--lt-button-text': colors.button_text_color,
    '--lt-accent-soft': `${colors.accent_color}1f`,
    '--lt-accent-faint': `${colors.accent_color}0f`,
    '--lt-accent-border': `${colors.accent_color}57`,
    '--lt-muted-border': `${colors.muted_color}57`,
    '--lt-muted-line': `${colors.muted_color}33`,
    '--lt-muted-pending': `${colors.muted_color}99`,
    '--lt-font': `'${family}', system-ui, sans-serif`,
  };
}
