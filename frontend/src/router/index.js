import { createRouter, createWebHistory } from 'vue-router';
import { useLanguageStore } from '@/stores/language'; // Import the language store
import Home from '@/views/Home.vue';

// Import metadata translations for both languages
import enMeta from '@/locales/router/en';
import esMeta from '@/locales/router/es';

const router = createRouter({
  /**
   * Configures the router for the application using the history mode.
   * 
   * The routes array defines all the different paths and their associated components in the application.
   */
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home, // Home component for the main landing page
    },
    {
      path: '/web_UI_section_category',
      name: 'webDevelopments',
      component: () => import("@/views/webDevelopment/List.vue"), // Lazy-loaded Web Developments list
    },
    {
      path: '/web_UI_section_category/detail/:development_id/:section_id/:component_id',
      name: 'webDevelopmentsDetail',
      component: () => import("@/views/webDevelopment/Detail.vue"), // Lazy-loaded Web Development details
    },
    {
      path: '/web_designs',
      name: 'webDesigns',
      component: () => import("@/views/webDesigns/List.vue"), // Lazy-loaded Web Designs list
    },
    {
      path: '/3d-animations',
      name: '3dAnimations',
      component: () => import("@/views/3dAnimations/List.vue"), // Lazy-loaded 3D Animations list
    },
    {
      path: '/about-us',
      name: 'aboutUs',
      component: () => import("@/views/AboutUs.vue"), // Lazy-loaded About Us page
    },
    {
      path: '/custom-software',
      name: 'customSoftware',
      component: () => import("@/views/CustomSoftware.vue"), // Lazy-loaded Custom Software page
    },
    {
      path: '/e-commerce-prices',
      name: 'eCommercePrices',
      component: () => import("@/views/Prices.vue"), // Lazy-loaded eCommerce Prices page
    },
    {
      path: '/hosting',
      name: 'hosting',
      component: () => import("@/views/Hosting.vue"), // Lazy-loaded Hosting page
    },
  ],
});

/**
 * Scroll to the top of the page after each route change.
 * 
 * This hook ensures that the page is scrolled to the top after navigating to a new route.
 */
router.afterEach(() => {
  window.scrollTo(0, 0);
});

/**
 * Before each route, ensure the language messages for the view are loaded and metadata is set.
 * 
 * This global navigation guard performs the following:
 * - Detects the user's browser language if not previously set.
 * - Loads the messages for the current view based on the selected language.
 * - Sets the page's title, description, and keywords based on the view's metadata.
 */
router.beforeEach(async (to, from, next) => {
  const languageStore = useLanguageStore();

  // Detect the browser language if it hasn't been set yet
  if (!languageStore.currentLanguage) {
    languageStore.detectBrowserLanguage();
  }

  // Load the messages for the view being navigated to
  await languageStore.loadMessagesForView(to.name);

  // Load the appropriate metadata based on the current language
  const metaTexts = languageStore.currentLanguage === 'es' ? esMeta : enMeta;
  const pageMeta = metaTexts[to.name];

  // If metadata exists for the view, set the page title, description, and keywords
  if (pageMeta) {
    // Set the page title
    document.title = pageMeta.title || 'Imagine Apps';

    // Set the meta description
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', pageMeta.description);
    } else {
      const descriptionElement = document.createElement('meta');
      descriptionElement.name = 'description';
      descriptionElement.content = pageMeta.description;
      document.head.appendChild(descriptionElement);
    }

    // Set the meta keywords
    const metaKeywords = document.querySelector('meta[name="keywords"]');
    if (metaKeywords) {
      metaKeywords.setAttribute('content', pageMeta.keywords);
    } else {
      const keywordsElement = document.createElement('meta');
      keywordsElement.name = 'keywords';
      keywordsElement.content = pageMeta.keywords;
      document.head.appendChild(keywordsElement);
    }
  }

  // Continue to the next route
  next();
});

export default router;