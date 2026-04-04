/**
 * Composable for injecting JSON-LD structured data into the page head.
 * Provides helpers for common schema.org types used across the site.
 */

const BASE_URL = 'https://projectapp.co'

const ORGANIZATION = {
  '@type': 'Organization',
  '@id': `${BASE_URL}/#organization`,
  name: 'Project App.',
  url: BASE_URL,
  logo: {
    '@type': 'ImageObject',
    url: `${BASE_URL}/img/icons/icon-logo-192x192.png`,
    width: 192,
    height: 192,
  },
  sameAs: [
    'https://www.instagram.com/projectapp.co/',
    'https://www.facebook.com/projectapp.co',
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    email: 'team@projectapp.co',
    contactType: 'customer service',
    availableLanguage: ['English', 'Spanish'],
  },
  address: {
    '@type': 'PostalAddress',
    addressCountry: 'CO',
  },
}

/**
 * Inject a JSON-LD script tag into the page head.
 * @param {object|function} jsonLd - The JSON-LD object or a function returning one
 */
export function useJsonLd(jsonLd) {
  useHead({
    script: [
      {
        type: 'application/ld+json',
        innerHTML: typeof jsonLd === 'function' ? jsonLd : JSON.stringify(jsonLd),
      },
    ],
  })
}

/**
 * Inject Organization + WebSite JSON-LD (use once in default layout or app.vue).
 */
export function useOrganizationJsonLd() {
  const route = useRoute()

  useJsonLd({
    '@context': 'https://schema.org',
    '@graph': [
      ORGANIZATION,
      {
        '@type': 'WebSite',
        '@id': `${BASE_URL}/#website`,
        url: BASE_URL,
        name: 'Project App.',
        publisher: { '@id': `${BASE_URL}/#organization` },
        inLanguage: ['en-US', 'es-CO'],
      },
    ],
  })
}

/**
 * Inject Service JSON-LD for landing/service pages.
 * @param {object} opts - { name, description, url }
 */
export function useServiceJsonLd({ name, description, url }) {
  const breadcrumbs = buildBreadcrumbs([{ name, url }])

  useJsonLd({
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Service',
        name,
        description,
        url: `${BASE_URL}${url}`,
        provider: { '@id': `${BASE_URL}/#organization` },
        areaServed: {
          '@type': 'Place',
          name: 'Worldwide',
        },
        serviceType: 'Software Development',
      },
      breadcrumbs,
    ],
  })
}

/**
 * Inject BlogPosting JSON-LD for individual blog articles.
 * @param {object} post - The blog post object from the store
 * @param {string} locale - Current locale code
 */
export function useBlogPostJsonLd(post, locale) {
  if (!post) return

  const isEnglish = locale.startsWith('en')
  const articleUrl = `${BASE_URL}/${locale}/blog/${post.slug}`

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': articleUrl,
    },
    headline: post.meta_title || post.title,
    description: post.meta_description || post.excerpt,
    datePublished: post.published_at,
    dateModified: post.updated_at || post.published_at,
    author: {
      '@type': 'Organization',
      name: 'Project App.',
      url: BASE_URL,
    },
    publisher: { '@id': `${BASE_URL}/#organization` },
    inLanguage: isEnglish ? 'en-US' : 'es-CO',
    url: articleUrl,
  }

  if (post.cover_image) {
    jsonLd.image = {
      '@type': 'ImageObject',
      url: post.cover_image,
    }
  }

  if (post.read_time_minutes) {
    jsonLd.timeRequired = `PT${post.read_time_minutes}M`
  }

  if (post.meta_keywords) {
    jsonLd.keywords = post.meta_keywords
  }

  const breadcrumbs = buildBreadcrumbs([
    { name: 'Blog', url: `/${locale}/blog` },
    { name: post.title, url: `/${locale}/blog/${post.slug}` },
  ])

  useJsonLd({
    '@context': 'https://schema.org',
    '@graph': [jsonLd, breadcrumbs],
  })
}

/**
 * Inject Blog listing JSON-LD for the blog index page.
 * @param {Array} posts - Array of blog post objects
 * @param {string} locale - Current locale code
 */
export function useBlogListJsonLd(posts, locale) {
  const isEnglish = locale.startsWith('en')
  const blogUrl = `${BASE_URL}/${locale}/blog`

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    mainEntity: {
      '@type': 'Blog',
      '@id': `${blogUrl}/#blog`,
      name: 'Project App. Blog',
      description: isEnglish
        ? 'Insights and trends in AI, software development, and digital transformation.'
        : 'Novedades y tendencias en IA, desarrollo de software y transformación digital.',
      url: blogUrl,
      inLanguage: isEnglish ? 'en-US' : 'es-CO',
      publisher: { '@id': `${BASE_URL}/#organization` },
    },
    url: blogUrl,
    name: 'Blog — Project App.',
    description: isEnglish
      ? 'Insights and trends in AI, software development, and digital transformation.'
      : 'Novedades y tendencias en IA, desarrollo de software y transformación digital.',
  }

  if (posts && posts.length > 0) {
    jsonLd.mainEntity.blogPost = posts.slice(0, 10).map((post) => ({
      '@type': 'BlogPosting',
      headline: post.title,
      url: `${BASE_URL}/${locale}/blog/${post.slug}`,
      datePublished: post.published_at,
      ...(post.cover_image ? { image: post.cover_image } : {}),
    }))
  }

  const breadcrumbs = buildBreadcrumbs([
    { name: 'Blog', url: `/${locale}/blog` },
  ])

  useJsonLd({
    '@context': 'https://schema.org',
    '@graph': [jsonLd, breadcrumbs],
  })
}

/**
 * Inject WebPage JSON-LD for generic pages (About, Contact, Portfolio, etc.).
 * @param {object} opts - { name, description, url, pageType }
 */
export function useWebPageJsonLd({ name, description, url, pageType = 'WebPage' }) {
  const breadcrumbs = buildBreadcrumbs([{ name, url }])

  useJsonLd({
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': pageType,
        name,
        description,
        url: `${BASE_URL}${url}`,
        isPartOf: { '@id': `${BASE_URL}/#website` },
        about: { '@id': `${BASE_URL}/#organization` },
      },
      breadcrumbs,
    ],
  })
}

/**
 * Build a BreadcrumbList JSON-LD object.
 * @param {Array<{name: string, url: string}>} items - Breadcrumb items (after Home)
 * @returns {object} BreadcrumbList JSON-LD
 */
function buildBreadcrumbs(items) {
  const list = [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Home',
      item: BASE_URL,
    },
  ]

  items.forEach((item, idx) => {
    list.push({
      '@type': 'ListItem',
      position: idx + 2,
      name: item.name,
      item: `${BASE_URL}${item.url}`,
    })
  })

  return {
    '@type': 'BreadcrumbList',
    itemListElement: list,
  }
}
