import { createRouter, createWebHistory } from 'vue-router';
import { useLanguageStore } from '@/stores/language'; // Import the language store
import Home from '@/views/Home.vue';

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
router.afterEach((to, from) => {
  window.scrollTo(0, 0);
});

/**
 * Before each route, ensure the language messages for the view are loaded.
 * 
 * This global navigation guard ensures that:
 * - The user's browser language is detected if it hasn't been set.
 * - The language messages for the view being navigated to are loaded.
 */
router.beforeEach(async (to, from, next) => {
  const languageStore = useLanguageStore();

  // Detect the browser language if it hasn't been set yet
  if (!languageStore.currentLanguage) {
    languageStore.detectBrowserLanguage();
  }

  // Load the messages for the view being navigated to
  await languageStore.loadMessagesForView(to.name);

  // Continue to the next route
  next();
});

export default router;

