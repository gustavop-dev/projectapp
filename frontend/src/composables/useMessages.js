import { computed } from 'vue';
import { useLanguageStore } from '@/stores/language';
import { useRoute } from 'vue-router';

/**
 * Composable to get language messages for the current view/route.
 * 
 * This composable accesses the language store and retrieves the messages
 * specific to the view that corresponds to the current route.
 * 
 * @returns {object} - An object containing the computed messages for the current view.
 */
export function useMessages() {
  const languageStore = useLanguageStore();
  const route = useRoute();

  // Computed property that returns the messages for the current route/view
  // Remove locale suffix from route name to match the folder structure
  const messages = computed(() => {
    let routeName = route.name;
    if (routeName) {
      // Remove locale suffix (-es-co or -en-us) to get the base route name
      routeName = routeName.replace(/-es-co$|-en-us$/, '');
    }
    return languageStore.getMessagesForView(routeName);
  });

  return {
    messages,
  };
}

/**
 * Composable to get global messages for a specific section.
 * 
 * This composable accesses the language store and retrieves the global messages
 * for the specified section of the application (e.g., navbar, footer).
 * 
 * @param {string} section - The section of the global messages to retrieve.
 * @returns {object} - An object containing the global messages for the specified section.
 */
export function useGlobalMessages(section) {
  const languageStore = useLanguageStore();

  // Retrieve the global messages for the specific section as a reactive computed
  const globalMessages = computed(() => {
    return languageStore.messages?.global?.[section] || {};
  });

  return {
    globalMessages,
  };
}
