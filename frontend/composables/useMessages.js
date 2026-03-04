import { computed } from 'vue';

/**
 * Map Nuxt route names to i18n message keys.
 * Nuxt i18n generates route names like 'index___en-us', 'slug___en-us', etc.
 */
const routeToViewKey = {
  'index': 'softwareHome',
  'landing-web-design': 'home',
  'about-us': 'aboutUs',
  'web-designs': 'webDesigns',
  '3d-animations': '3dAnimations',
  'custom-software': 'customSoftware',
  'e-commerce-prices': 'eCommercePrices',
  'hosting': 'hosting',
  'portfolio-works': 'portfolioWorks',
  'contact': 'contact',
  'contact-success': 'contactSuccess',
  'slug': 'home',
};

/**
 * Composable to get language messages for the current view/route.
 * 
 * Uses @nuxtjs/i18n's tm() to return raw message objects that components
 * can access with the same `messages?.section?.key` pattern as before.
 * 
 * @param {string} [viewKeyOverride] - Optional explicit view key (e.g., 'home', 'aboutUs')
 * @returns {object} - An object containing the computed messages for the current view.
 */
export function useMessages(viewKeyOverride) {
  const { tm } = useI18n();
  const route = useRoute();

  const messages = computed(() => {
    if (viewKeyOverride) {
      return tm(viewKeyOverride) || {};
    }

    // Determine view key from Nuxt route name
    const routeName = typeof route.name === 'string' ? route.name : '';
    
    // Nuxt i18n route names: 'index___en-us', 'slug___en-us'
    const baseRouteName = routeName.split('___')[0];
    
    // Map to view key
    const viewKey = routeToViewKey[baseRouteName] || baseRouteName || 'home';
    
    return tm(viewKey) || {};
  });

  return {
    messages,
  };
}

/**
 * Composable to get global messages for a specific section.
 * 
 * @param {string} section - The section of the global messages to retrieve (e.g., 'navbar', 'footer').
 * @returns {object} - An object containing the global messages for the specified section.
 */
export function useGlobalMessages(section) {
  const { tm } = useI18n();

  const globalMessages = computed(() => {
    const global = tm('global') || {};
    return global[section] || {};
  });

  return {
    globalMessages,
  };
}
