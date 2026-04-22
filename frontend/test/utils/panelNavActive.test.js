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

  it('removes a five-letter locale prefix with region', () => {
    expect(stripLocalePrefix('/en-us/panel/proposals')).toBe('/panel/proposals');
  });

  it('returns empty string when input is empty', () => {
    expect(stripLocalePrefix('')).toBe('');
  });

  it('returns empty string when input is null', () => {
    expect(stripLocalePrefix(null)).toBe('');
  });

  it('returns original path when stripping would produce empty string', () => {
    expect(stripLocalePrefix('/en')).toBe('/en');
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

  it('strips trailing slashes on both sides before comparing', () => {
    expect(
      isPanelNavItemActive('/panel/', { href: '/panel', matchExact: true }),
    ).toBe(true);
  });

  it('treats empty-post-strip path as root', () => {
    expect(
      isPanelNavItemActive('/en/', { href: '/en/', matchExact: true }),
    ).toBe(true);
  });

  it('rejects root path against a deeper item href', () => {
    expect(
      isPanelNavItemActive('/', { href: '/panel' }),
    ).toBe(false);
  });

  it('matches locale-prefixed route against unprefixed item href', () => {
    expect(
      isPanelNavItemActive('/en-us/panel/clients', { href: '/panel/clients' }),
    ).toBe(true);
  });
});
