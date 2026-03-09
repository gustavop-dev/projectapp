import { computed } from 'vue';

/**
 * Map legacy Vue Router route names to Nuxt paths.
 */
const legacyRouteNameToPath = {
  'home': '/',
  'aboutUs': '/about-us',
  'portfolioWorks': '/portfolio-works',
  'contact': '/contact',
  'contactSuccess': '/contact-success',
};

/**
 * Composable for locale-aware navigation.
 * 
 * Uses @nuxtjs/i18n's switchLocalePath and localePath for locale management.
 * Provides backward-compatible API for existing components.
 */
export function useLocaleNavigation() {
  const { locale, locales } = useI18n();
  const switchLocalePath = useSwitchLocalePath();
  const localePath = useLocalePath();
  const router = useRouter();
  const route = useRoute();

  /**
   * Navigate to a specific route with the current locale prefix.
   * Accepts legacy route names (e.g., 'home', 'aboutUs') and maps them to paths.
   * 
   * @param {string} routeName - The base route name (without locale suffix)
   * @param {object} params - Route parameters
   * @param {object} query - Query parameters
   */
  const navigateToRoute = (routeName, params = {}, query = {}) => {
    let targetPath = legacyRouteNameToPath[routeName] || `/${routeName}`;
    
    // Append params if present (e.g., /hosting/:plan)
    if (params && Object.keys(params).length > 0) {
      const paramValues = Object.values(params).filter(Boolean);
      if (paramValues.length > 0) {
        targetPath += '/' + paramValues.join('/');
      }
    }
    
    const path = localePath(targetPath);
    router.push({ path, query });
  };

  /**
   * Switch to a different locale while maintaining the current route.
   * 
   * @param {string} targetLocale - The target locale (e.g., 'es-co' or 'en-us')
   */
  const switchLocale = (targetLocale) => {
    const path = switchLocalePath(targetLocale);
    if (path) {
      try { localStorage.setItem('preferred_locale', targetLocale); } catch {}
      router.push(path);
    }
  };

  /**
   * Get a locale-aware URL for a given route.
   * 
   * @param {string} routeName - The base route name
   * @param {object} params - Route parameters
   * @param {string} targetLocale - Target locale (defaults to current locale)
   * @returns {string} - The complete URL with locale prefix
   */
  const getLocaleUrl = (routeName, params = {}, targetLocale = null) => {
    return localePath({ name: routeName, params }, targetLocale || locale.value);
  };

  /**
   * Check if a given locale is currently active.
   * 
   * @param {string} localeCode - The locale to check
   * @returns {boolean} - True if the locale is currently active
   */
  const isActiveLocale = (localeCode) => {
    return locale.value === localeCode;
  };

  /**
   * Get the current base route name (without locale suffix).
   */
  const currentBaseRouteName = computed(() => {
    const name = route.name;
    if (!name || typeof name !== 'string') return null;
    // Nuxt i18n route names: 'index___en-us'
    return name.split('___')[0];
  });

  /**
   * Get available locales with their display names.
   */
  const availableLocales = computed(() => [
    {
      code: 'es-co',
      name: 'Español (Colombia)',
      flag: '\u{1F1E8}\u{1F1F4}'
    },
    {
      code: 'en-us',
      name: 'English (United States)',
      flag: '\u{1F1FA}\u{1F1F8}'
    }
  ]);

  return {
    navigateToRoute,
    switchLocale,
    getLocaleUrl,
    isActiveLocale,
    currentBaseRouteName,
    availableLocales
  };
}