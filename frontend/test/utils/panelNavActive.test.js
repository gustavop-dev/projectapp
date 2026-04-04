import { stripLocalePrefix, isPanelNavItemActive } from '../../utils/panelNavActive';

describe('stripLocalePrefix', () => {
  it('removes a two-letter locale prefix before a path segment', () => {
    expect(stripLocalePrefix('/en/panel/proposals')).toBe('/panel/proposals');
  });

  it('leaves unprefixed paths unchanged', () => {
    expect(stripLocalePrefix('/panel')).toBe('/panel');
  });

  it('returns empty string when path is empty', () => {
    expect(stripLocalePrefix('')).toBe('');
  });

  it('returns empty string when path is null', () => {
    expect(stripLocalePrefix(null)).toBe('');
  });
});

describe('isPanelNavItemActive', () => {
  it('matches exact path when matchExact is true', () => {
    expect(
      isPanelNavItemActive('/panel', { href: '/panel', matchExact: true }),
    ).toBe(true);
    expect(
      isPanelNavItemActive('/panel/proposals', { href: '/panel', matchExact: true }),
    ).toBe(false);
  });

  it('matches prefix for nested routes when matchExact is false', () => {
    const item = { href: '/panel/proposals' };
    expect(isPanelNavItemActive('/panel/proposals/1/edit', item)).toBe(true);
    expect(isPanelNavItemActive('/panel/clients', item)).toBe(false);
  });

  it('returns false for external items', () => {
    expect(
      isPanelNavItemActive('/panel', {
        href: '/admin/',
        external: true,
      }),
    ).toBe(false);
  });

  it('treats root routePath as / when path strips to empty', () => {
    expect(isPanelNavItemActive('/', { href: '/panel' })).toBe(false);
  });

  it('treats root href as / when href strips to empty', () => {
    expect(isPanelNavItemActive('/panel', { href: '/' })).toBe(false);
  });

  it('matches exact path when matchExact is false and paths are equal', () => {
    expect(isPanelNavItemActive('/panel', { href: '/panel' })).toBe(true);
  });
});
