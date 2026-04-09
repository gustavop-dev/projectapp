/**
 * Tests for the useSeoJsonLd composable.
 *
 * Covers: useJsonLd, useOrganizationJsonLd, useServiceJsonLd,
 * useBlogPostJsonLd, useBlogListJsonLd, useWebPageJsonLd,
 * and buildBreadcrumbs (via public API).
 *
 * Strategy: Set useHead/useRoute as globals (Nuxt auto-import pattern),
 * then resetModules + require() to pick up the mocks.
 */

let mockUseHead;
let mod;

beforeEach(() => {
  mockUseHead = jest.fn();
  global.useHead = mockUseHead;
  global.useRoute = () => ({ params: {}, query: {}, path: '/', fullPath: '/' });

  jest.resetModules();
  mod = require('../../composables/useSeoJsonLd');
});

function getHeadScript() {
  const call = mockUseHead.mock.calls[mockUseHead.mock.calls.length - 1];
  return call[0].script[0];
}

function getJsonLd() {
  const script = getHeadScript();
  return typeof script.innerHTML === 'string'
    ? JSON.parse(script.innerHTML)
    : script.innerHTML;
}

describe('useSeoJsonLd', () => {
  // ── useJsonLd ──────────────────────────────────────────────────────────────

  describe('useJsonLd', () => {
    it('calls useHead with JSON-LD script tag for object input', () => {
      const data = { '@type': 'Organization', name: 'Test' };
      mod.useJsonLd(data);

      expect(mockUseHead).toHaveBeenCalledTimes(1);
      const script = getHeadScript();
      expect(script.type).toBe('application/ld+json');
      expect(JSON.parse(script.innerHTML)).toEqual(data);
    });

    it('passes function directly when jsonLd is a function', () => {
      const fn = () => ({ '@type': 'Thing' });
      mod.useJsonLd(fn);

      const script = getHeadScript();
      expect(script.innerHTML).toBe(fn);
    });
  });

  // ── useOrganizationJsonLd ──────────────────────────────────────────────────

  describe('useOrganizationJsonLd', () => {
    it('injects Organization and WebSite in @graph', () => {
      mod.useOrganizationJsonLd();

      const jsonLd = getJsonLd();
      expect(jsonLd['@context']).toBe('https://schema.org');
      const types = jsonLd['@graph'].map((item) => item['@type']);
      expect(types).toContain('Organization');
      expect(types).toContain('WebSite');
    });

    it('includes correct organization details', () => {
      mod.useOrganizationJsonLd();

      const jsonLd = getJsonLd();
      const org = jsonLd['@graph'].find((item) => item['@type'] === 'Organization');
      expect(org.name).toBe('Project App.');
      expect(org.url).toBe('https://projectapp.co');
      expect(org.logo['@type']).toBe('ImageObject');
      expect(org.sameAs).toBeInstanceOf(Array);
      expect(org.contactPoint.contactType).toBe('customer service');
    });
  });

  // ── useServiceJsonLd ───────────────────────────────────────────────────────

  describe('useServiceJsonLd', () => {
    it('creates Service JSON-LD with name, description, url', () => {
      mod.useServiceJsonLd({ name: 'Web Dev', description: 'Custom web', url: '/services/web' });

      const jsonLd = getJsonLd();
      const service = jsonLd['@graph'].find((item) => item['@type'] === 'Service');
      expect(service.name).toBe('Web Dev');
      expect(service.description).toBe('Custom web');
      expect(service.url).toBe('https://projectapp.co/services/web');
      expect(service.serviceType).toBe('Software Development');
    });

    it('includes BreadcrumbList with Home and service item', () => {
      mod.useServiceJsonLd({ name: 'Web Dev', description: 'Custom', url: '/services/web' });

      const jsonLd = getJsonLd();
      const breadcrumbs = jsonLd['@graph'].find((item) => item['@type'] === 'BreadcrumbList');
      expect(breadcrumbs.itemListElement).toHaveLength(2);
      expect(breadcrumbs.itemListElement[0].name).toBe('Home');
      expect(breadcrumbs.itemListElement[0].position).toBe(1);
      expect(breadcrumbs.itemListElement[1].name).toBe('Web Dev');
      expect(breadcrumbs.itemListElement[1].position).toBe(2);
    });
  });

  // ── useBlogPostJsonLd ──────────────────────────────────────────────────────

  describe('useBlogPostJsonLd', () => {
    const basePost = {
      slug: 'test-post',
      title: 'Test Post',
      meta_title: 'Meta Title',
      meta_description: 'Meta desc',
      excerpt: 'Excerpt text',
      published_at: '2026-01-15',
      updated_at: '2026-02-01',
    };

    it('does nothing when post is null', () => {
      mod.useBlogPostJsonLd(null, 'en');

      expect(mockUseHead).not.toHaveBeenCalled();
    });

    it('creates BlogPosting with headline and dates', () => {
      mod.useBlogPostJsonLd(basePost, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.headline).toBe('Meta Title');
      expect(posting.description).toBe('Meta desc');
      expect(posting.datePublished).toBe('2026-01-15');
      expect(posting.dateModified).toBe('2026-02-01');
    });

    it('falls back to title when meta_title is missing', () => {
      mod.useBlogPostJsonLd({ ...basePost, meta_title: null }, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.headline).toBe('Test Post');
    });

    it('falls back to excerpt when meta_description is missing', () => {
      mod.useBlogPostJsonLd({ ...basePost, meta_description: null }, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.description).toBe('Excerpt text');
    });

    it('sets correct language for English locale', () => {
      mod.useBlogPostJsonLd(basePost, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.inLanguage).toBe('en-US');
    });

    it('sets correct language for Spanish locale', () => {
      mod.useBlogPostJsonLd(basePost, 'es');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.inLanguage).toBe('es-CO');
    });

    it('includes image when post has cover_image', () => {
      mod.useBlogPostJsonLd({ ...basePost, cover_image: 'https://cdn.example.com/img.jpg' }, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.image['@type']).toBe('ImageObject');
      expect(posting.image.url).toBe('https://cdn.example.com/img.jpg');
    });

    it('excludes image when post has no cover_image', () => {
      mod.useBlogPostJsonLd(basePost, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.image).toBeUndefined();
    });

    it('includes timeRequired when post has read_time_minutes', () => {
      mod.useBlogPostJsonLd({ ...basePost, read_time_minutes: 5 }, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.timeRequired).toBe('PT5M');
    });

    it('includes keywords when post has meta_keywords', () => {
      mod.useBlogPostJsonLd({ ...basePost, meta_keywords: 'vue, nuxt, testing' }, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.keywords).toBe('vue, nuxt, testing');
    });

    it('includes BreadcrumbList with Home, Blog, and post', () => {
      mod.useBlogPostJsonLd(basePost, 'en');

      const jsonLd = getJsonLd();
      const breadcrumbs = jsonLd['@graph'].find((item) => item['@type'] === 'BreadcrumbList');
      expect(breadcrumbs.itemListElement).toHaveLength(3);
      expect(breadcrumbs.itemListElement[0].name).toBe('Home');
      expect(breadcrumbs.itemListElement[1].name).toBe('Blog');
      expect(breadcrumbs.itemListElement[2].name).toBe('Test Post');
    });

    it('uses published_at as dateModified when updated_at is missing', () => {
      mod.useBlogPostJsonLd({ ...basePost, updated_at: null }, 'en');

      const jsonLd = getJsonLd();
      const posting = jsonLd['@graph'].find((item) => item['@type'] === 'BlogPosting');
      expect(posting.dateModified).toBe('2026-01-15');
    });
  });

  // ── useBlogListJsonLd ──────────────────────────────────────────────────────

  describe('useBlogListJsonLd', () => {
    const posts = Array.from({ length: 15 }, (_, i) => ({
      title: `Post ${i + 1}`,
      slug: `post-${i + 1}`,
      published_at: '2026-01-01',
      cover_image: i < 3 ? `https://cdn.example.com/img${i}.jpg` : null,
    }));

    it('creates CollectionPage with Blog for English locale', () => {
      mod.useBlogListJsonLd(posts, 'en');

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'CollectionPage');
      expect(page).toBeDefined();
      expect(page.mainEntity['@type']).toBe('Blog');
      expect(page.mainEntity.inLanguage).toBe('en-US');
    });

    it('creates CollectionPage with Blog for Spanish locale', () => {
      mod.useBlogListJsonLd(posts, 'es');

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'CollectionPage');
      expect(page.mainEntity.inLanguage).toBe('es-CO');
    });

    it('includes up to 10 blogPost items when posts provided', () => {
      mod.useBlogListJsonLd(posts, 'en');

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'CollectionPage');
      expect(page.mainEntity.blogPost).toHaveLength(10);
      expect(page.mainEntity.blogPost[0].headline).toBe('Post 1');
    });

    it('omits blogPost when posts array is empty', () => {
      mod.useBlogListJsonLd([], 'en');

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'CollectionPage');
      expect(page.mainEntity.blogPost).toBeUndefined();
    });

    it('omits blogPost when posts is null', () => {
      mod.useBlogListJsonLd(null, 'en');

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'CollectionPage');
      expect(page.mainEntity.blogPost).toBeUndefined();
    });

    it('includes BreadcrumbList with Home and Blog', () => {
      mod.useBlogListJsonLd(posts, 'en');

      const jsonLd = getJsonLd();
      const breadcrumbs = jsonLd['@graph'].find((item) => item['@type'] === 'BreadcrumbList');
      expect(breadcrumbs.itemListElement).toHaveLength(2);
      expect(breadcrumbs.itemListElement[1].name).toBe('Blog');
    });
  });

  // ── useWebPageJsonLd ───────────────────────────────────────────────────────

  describe('useWebPageJsonLd', () => {
    it('creates WebPage JSON-LD with default pageType', () => {
      mod.useWebPageJsonLd({ name: 'About', description: 'About us', url: '/about' });

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'WebPage');
      expect(page.name).toBe('About');
      expect(page.description).toBe('About us');
      expect(page.url).toBe('https://projectapp.co/about');
    });

    it('uses custom pageType when provided', () => {
      mod.useWebPageJsonLd({ name: 'Contact', description: 'Contact us', url: '/contact', pageType: 'ContactPage' });

      const jsonLd = getJsonLd();
      const page = jsonLd['@graph'].find((item) => item['@type'] === 'ContactPage');
      expect(page).toBeDefined();
      expect(page.name).toBe('Contact');
    });

    it('includes BreadcrumbList with Home and page', () => {
      mod.useWebPageJsonLd({ name: 'About', description: 'About us', url: '/about' });

      const jsonLd = getJsonLd();
      const breadcrumbs = jsonLd['@graph'].find((item) => item['@type'] === 'BreadcrumbList');
      expect(breadcrumbs.itemListElement).toHaveLength(2);
      expect(breadcrumbs.itemListElement[1].name).toBe('About');
      expect(breadcrumbs.itemListElement[1].item).toBe('https://projectapp.co/about');
    });
  });
});
