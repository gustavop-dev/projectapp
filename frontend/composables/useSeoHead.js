/**
 * Reusable SEO head composable for all pages.
 * Sets title, description, keywords, Open Graph, Twitter Card, canonical, and i18n hreflang.
 *
 * @param {string} metaKey - Key in the meta (router) locale file, e.g. 'aboutUs'
 * @param {object} [options] - Optional overrides { image, type }
 */
export function useSeoHead(metaKey, options = {}) {
  const { t, locale } = useI18n()
  const i18nHead = useLocaleHead({ addSeoAttributes: true })
  const route = useRoute()
  const baseUrl = 'https://projectapp.co'

  const {
    image = `${baseUrl}/img/og-image.webp`,
    type = 'website',
  } = options

  const ogLocale = () => locale.value === 'es-co' ? 'es_CO' : 'en_US'

  useHead({
    meta: [
      { name: 'description', content: () => t(`meta.${metaKey}.description`) },
      { name: 'keywords', content: () => t(`meta.${metaKey}.keywords`) },
      // Open Graph
      { property: 'og:title', content: () => t(`meta.${metaKey}.title`) },
      { property: 'og:description', content: () => t(`meta.${metaKey}.description`) },
      { property: 'og:type', content: type },
      { property: 'og:url', content: () => `${baseUrl}${route.fullPath}` },
      { property: 'og:image', content: image },
      { property: 'og:site_name', content: 'Project App.' },
      { property: 'og:locale', content: ogLocale },
      // Twitter Card
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:site', content: '@projectappco' },
      { name: 'twitter:title', content: () => t(`meta.${metaKey}.title`) },
      { name: 'twitter:description', content: () => t(`meta.${metaKey}.description`) },
      { name: 'twitter:image', content: image },
    ],
    htmlAttrs: {
      lang: i18nHead.value.htmlAttrs?.lang,
    },
    link: [
      { rel: 'canonical', href: () => `${baseUrl}${route.fullPath}` },
      ...(i18nHead.value.link || []),
    ],
  })
}
