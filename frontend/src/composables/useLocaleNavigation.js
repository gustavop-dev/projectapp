import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useLanguageStore } from '@/stores/language';

/**
 * Composable for locale-aware navigation.
 * 
 * Provides methods for navigating between different locales and creating
 * locale-aware URLs for better SEO.
 */
export function useLocaleNavigation() {
  const router = useRouter();
  const route = useRoute();
  const languageStore = useLanguageStore();

  /**
   * Navigate to a specific route with the current locale prefix.
   * 
   * @param {string} routeName - The base route name (without locale suffix)
   * @param {object} params - Route parameters
   * @param {object} query - Query parameters
   */
  const navigateToRoute = (routeName, params = {}, query = {}) => {
    const currentLocale = languageStore.currentLocale || 'es-co';
    const localeRouteName = `${routeName}-${currentLocale}`;
    
    router.push({
      name: localeRouteName,
      params,
      query
    });
  };

  /**
   * Switch to a different locale while maintaining the current route.
   * 
   * @param {string} targetLocale - The target locale (e.g., 'es-co' or 'en-us')
   */
  const switchLocale = (targetLocale) => {
    // Update the language store
    languageStore.setCurrentLocale(targetLocale);
    
    // Get current route name without locale suffix
    let baseRouteName = route.name;
    if (baseRouteName) {
      baseRouteName = baseRouteName.replace(/-es-co$|-en-us$/, '');
    }
    
    // Navigate to the same route but with the new locale
    if (baseRouteName) {
      const newRouteName = `${baseRouteName}-${targetLocale}`;
      router.push({
        name: newRouteName,
        params: route.params,
        query: route.query
      });
    } else {
      // Fallback: just change the locale prefix in the path
      const pathSegments = route.path.split('/').filter(Boolean);
      pathSegments[0] = targetLocale;
      const newPath = '/' + pathSegments.join('/');
      router.push(newPath);
    }
  };

  /**
   * Get a locale-aware URL for a given route.
   * 
   * @param {string} routeName - The base route name
   * @param {object} params - Route parameters
   * @param {string} locale - Target locale (defaults to current locale)
   * @returns {string} - The complete URL with locale prefix
   */
  const getLocaleUrl = (routeName, params = {}, locale = null) => {
    const targetLocale = locale || languageStore.currentLocale || 'es-co';
    const localeRouteName = `${routeName}-${targetLocale}`;
    
    const resolvedRoute = router.resolve({
      name: localeRouteName,
      params
    });
    
    return resolvedRoute.href;
  };

  /**
   * Check if a given locale is currently active.
   * 
   * @param {string} locale - The locale to check
   * @returns {boolean} - True if the locale is currently active
   */
  const isActiveLocale = (locale) => {
    return languageStore.currentLocale === locale;
  };

  /**
   * Get the current base route name (without locale suffix).
   */
  const currentBaseRouteName = computed(() => {
    if (!route.name) return null;
    return route.name.replace(/-es-co$|-en-us$/, '');
  });

  /**
   * Get available locales with their display names.
   */
  const availableLocales = computed(() => [
    {
      code: 'es-co',
      name: 'Español (Colombia)',
      flag: '🇨🇴'
    },
    {
      code: 'en-us',
      name: 'English (United States)',
      flag: '🇺🇸'
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