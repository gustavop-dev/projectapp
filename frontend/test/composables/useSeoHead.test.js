/**
 * Tests for the useSeoHead composable.
 *
 * Covers: useHead called with correct meta structure,
 * default options, custom image/type overrides.
 */
import { ref } from 'vue';

let mockT;
let mockUseHead;
let useSeoHead;
let localeRef;
let localeHeadRef;
let routeRef;

beforeEach(() => {
  mockT = jest.fn((key) => key);
  mockUseHead = jest.fn();
  localeRef = ref('en-us');
  localeHeadRef = ref({ htmlAttrs: { lang: 'en' }, link: [{ rel: 'alternate' }] });
  routeRef = { name: 'index___en-us', params: {}, query: {}, path: '/', fullPath: '/en-us' };

  global.useI18n = () => ({ t: mockT, locale: localeRef });
  global.useLocaleHead = () => localeHeadRef;
  global.useRoute = () => routeRef;
  global.useHead = mockUseHead;

  jest.resetModules();
  const mod = require('../../composables/useSeoHead');
  useSeoHead = mod.useSeoHead;
});

describe('useSeoHead', () => {
  it('does not set <title> (public pages use the global default)', () => {
    useSeoHead('aboutUs');

    expect(mockUseHead).toHaveBeenCalledTimes(1);
    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.title).toBeUndefined();
  });

  it('generates correct description meta', () => {
    useSeoHead('contact');

    const arg = mockUseHead.mock.calls[0][0];
    const descMeta = arg.meta.find((m) => m.name === 'description');
    descMeta.content();
    expect(mockT).toHaveBeenCalledWith('meta.contact.description');
  });

  it('generates correct keywords meta', () => {
    useSeoHead('hosting');

    const arg = mockUseHead.mock.calls[0][0];
    const keyMeta = arg.meta.find((m) => m.name === 'keywords');
    keyMeta.content();
    expect(mockT).toHaveBeenCalledWith('meta.hosting.keywords');
  });

  it('sets og:type to website by default', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogType = arg.meta.find((m) => m.property === 'og:type');
    expect(ogType.content).toBe('website');
  });

  it('uses default og:image URL', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogImage = arg.meta.find((m) => m.property === 'og:image');
    expect(ogImage.content).toBe('https://projectapp.co/img/og-image.webp');
  });

  it('accepts custom image option', () => {
    useSeoHead('aboutUs', { image: 'https://cdn.example.com/custom.png' });

    const arg = mockUseHead.mock.calls[0][0];
    const ogImage = arg.meta.find((m) => m.property === 'og:image');
    expect(ogImage.content).toBe('https://cdn.example.com/custom.png');
  });

  it('accepts custom type option', () => {
    useSeoHead('blog', { type: 'article' });

    const arg = mockUseHead.mock.calls[0][0];
    const ogType = arg.meta.find((m) => m.property === 'og:type');
    expect(ogType.content).toBe('article');
  });

  it('sets og:url with route fullPath', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogUrl = arg.meta.find((m) => m.property === 'og:url');
    const url = ogUrl.content();
    expect(url).toBe('https://projectapp.co/en-us');
  });

  it('sets og:site_name', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const siteName = arg.meta.find((m) => m.property === 'og:site_name');
    expect(siteName.content).toBe('Project App.');
  });

  it('sets twitter:card to summary_large_image', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const twitterCard = arg.meta.find((m) => m.name === 'twitter:card');
    expect(twitterCard.content).toBe('summary_large_image');
  });

  it('sets htmlAttrs lang from i18nHead', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.htmlAttrs.lang).toBe('en');
  });

  it('includes canonical and link tags from i18nHead', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.link).toHaveLength(2);
    expect(arg.link[0]).toMatchObject({ rel: 'canonical' });
    expect(typeof arg.link[0].href).toBe('function');
    expect(arg.link[0].href()).toBe('https://projectapp.co/en-us');
    expect(arg.link[1]).toEqual({ rel: 'alternate' });
  });

  it('sets og:locale to en_US for non-Spanish locales', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogLocale = arg.meta.find((m) => m.property === 'og:locale');
    expect(ogLocale.content()).toBe('en_US');
  });

  it('sets og:locale to es_CO for es-co locale', () => {
    localeRef.value = 'es-co';
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogLocale = arg.meta.find((m) => m.property === 'og:locale');
    expect(ogLocale.content()).toBe('es_CO');
  });

  it('uses the route fullPath for the canonical href callback', () => {
    routeRef.fullPath = '/es-co/contact';
    useSeoHead('contact');

    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.link[0].href()).toBe('https://projectapp.co/es-co/contact');
  });

  it('invokes og:title content callback', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogTitle = arg.meta.find((m) => m.property === 'og:title');
    ogTitle.content();
    expect(mockT).toHaveBeenCalledWith('meta.aboutUs.title');
  });

  it('invokes og:description content callback', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const ogDesc = arg.meta.find((m) => m.property === 'og:description');
    ogDesc.content();
    expect(mockT).toHaveBeenCalledWith('meta.aboutUs.description');
  });

  it('invokes twitter:title content callback', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const twitterTitle = arg.meta.find((m) => m.name === 'twitter:title');
    twitterTitle.content();
    expect(mockT).toHaveBeenCalledWith('meta.aboutUs.title');
  });

  it('invokes twitter:description content callback', () => {
    useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    const twitterDesc = arg.meta.find((m) => m.name === 'twitter:description');
    twitterDesc.content();
    expect(mockT).toHaveBeenCalledWith('meta.aboutUs.description');
  });

  it('falls back to canonical-only link array when i18nHead link is undefined', () => {
    global.useLocaleHead = () => ref({ htmlAttrs: { lang: 'en' }, link: undefined });
    jest.resetModules();
    const mod = require('../../composables/useSeoHead');
    mod.useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.link).toHaveLength(1);
    expect(arg.link[0]).toMatchObject({ rel: 'canonical' });
    expect(typeof arg.link[0].href).toBe('function');
  });

  it('returns undefined lang when htmlAttrs is undefined', () => {
    localeHeadRef = ref({ link: [{ rel: 'alternate' }] });
    jest.resetModules();
    const mod = require('../../composables/useSeoHead');
    mod.useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.htmlAttrs.lang).toBeUndefined();
  });

  it('passes through all alternate links from useLocaleHead', () => {
    localeHeadRef = ref({
      htmlAttrs: { lang: 'es' },
      link: [
        { rel: 'alternate', hreflang: 'es-co', href: 'https://projectapp.co/es-co' },
        { rel: 'alternate', hreflang: 'en-us', href: 'https://projectapp.co/en-us' },
      ],
    });
    jest.resetModules();
    const mod = require('../../composables/useSeoHead');
    mod.useSeoHead('aboutUs');

    const arg = mockUseHead.mock.calls[0][0];
    expect(arg.link[1]).toEqual(
      expect.objectContaining({ rel: 'alternate', hreflang: 'es-co' }),
    );
    expect(arg.link[2]).toEqual(
      expect.objectContaining({ rel: 'alternate', hreflang: 'en-us' }),
    );
  });
});
