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
   * Now includes locale-specific routing for SEO optimization with backward compatibility.
   */
  history: createWebHistory(),
  routes: [
    // Original routes for backward compatibility (these will redirect)
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/web-designs',
      name: 'webDesigns',
      component: () => import("@/views/webDesigns/List.vue"),
    },
    {
      path: '/3d-animations',
      name: '3dAnimations',
      component: () => import("@/views/3dAnimations/List.vue"),
    },
    {
      path: '/about-us',
      name: 'aboutUs',
      component: () => import("@/views/AboutUs.vue"),
    },
    {
      path: '/custom-software',
      name: 'customSoftware',
      component: () => import("@/views/CustomSoftware.vue"),
    },
    {
      path: '/e-commerce-prices',
      name: 'eCommercePrices',
      component: () => import("@/views/Prices.vue"),
    },
    {
      path: '/hosting/:plan?',
      name: 'hosting',
      component: () => import("@/views/Hosting.vue"),
    },
    {
      path: '/portfolio-works/:example?',
      name: 'portfolioWorks',
      component: () => import("@/views/PortfolioWorks.vue"),
    },
    {
      path: '/contact',
      name: 'contact',
      component: () => import("@/views/Contact.vue"),
    },
    {
      path: '/contact-success',
      name: 'contactSuccess',
      component: () => import("@/views/ContactSuccess.vue"),
    },
    {
      path: '/business-proposal/:slug',
      name: 'businessProposal',
      component: () => import("@/views/business-proposal/BusinessProposal.vue"),
    },
    
    // Locale-specific routes for es-co (Spanish Colombia)
    {
      path: '/es-co',
      children: [
        {
          path: '',
          name: 'home-es-co',
          component: Home,
        },
        {
          path: 'web-designs',
          name: 'webDesigns-es-co',
          component: () => import("@/views/webDesigns/List.vue"),
        },
        {
          path: '3d-animations',
          name: '3dAnimations-es-co',
          component: () => import("@/views/3dAnimations/List.vue"),
        },
        {
          path: 'about-us',
          name: 'aboutUs-es-co',
          component: () => import("@/views/AboutUs.vue"),
        },
        {
          path: 'custom-software',
          name: 'customSoftware-es-co',
          component: () => import("@/views/CustomSoftware.vue"),
        },
        {
          path: 'e-commerce-prices',
          name: 'eCommercePrices-es-co',
          component: () => import("@/views/Prices.vue"),
        },
        {
          path: 'hosting/:plan?',
          name: 'hosting-es-co',
          component: () => import("@/views/Hosting.vue"),
        },
        {
          path: 'portfolio-works/:example?',
          name: 'portfolioWorks-es-co',
          component: () => import("@/views/PortfolioWorks.vue"),
        },
        {
          path: 'contact',
          name: 'contact-es-co',
          component: () => import("@/views/Contact.vue"),
        },
        {
          path: 'contact-success',
          name: 'contactSuccess-es-co',
          component: () => import("@/views/ContactSuccess.vue"),
        },
        {
          path: 'business-proposal/:slug',
          name: 'businessProposal-es-co',
          component: () => import("@/views/business-proposal/BusinessProposal.vue"),
        },
      ]
    },
    
    // Locale-specific routes for en-us (English United States)
    {
      path: '/en-us',
      children: [
        {
          path: '',
          name: 'home-en-us',
          component: Home,
        },
        {
          path: 'web-designs',
          name: 'webDesigns-en-us',
          component: () => import("@/views/webDesigns/List.vue"),
        },
        {
          path: '3d-animations',
          name: '3dAnimations-en-us',
          component: () => import("@/views/3dAnimations/List.vue"),
        },
        {
          path: 'about-us',
          name: 'aboutUs-en-us',
          component: () => import("@/views/AboutUs.vue"),
        },
        {
          path: 'custom-software',
          name: 'customSoftware-en-us',
          component: () => import("@/views/CustomSoftware.vue"),
        },
        {
          path: 'e-commerce-prices',
          name: 'eCommercePrices-en-us',
          component: () => import("@/views/Prices.vue"),
        },
        {
          path: 'hosting/:plan?',
          name: 'hosting-en-us',
          component: () => import("@/views/Hosting.vue"),
        },
        {
          path: 'portfolio-works/:example?',
          name: 'portfolioWorks-en-us',
          component: () => import("@/views/PortfolioWorks.vue"),
        },
        {
          path: 'contact',
          name: 'contact-en-us',
          component: () => import("@/views/Contact.vue"),
        },
        {
          path: 'contact-success',
          name: 'contactSuccess-en-us',
          component: () => import("@/views/ContactSuccess.vue"),
        },
        {
          path: 'business-proposal/:slug',
          name: 'businessProposal-en-us',
          component: () => import("@/views/business-proposal/BusinessProposal.vue"),
        },
      ]
    },
    
    // 404 route
    {
      path: '/:pathMatch(.*)*',
      name: '404View',
      component: () => import("@/views/NotFound.vue"),
    }
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
 * Before each route, handle locale detection/redirection and ensure language messages are loaded.
 * 
 * This global navigation guard performs the following:
 * - Detects the user's browser language and region if not previously set.
 * - Redirects to appropriate locale-prefixed routes.
 * - Loads the messages for the current view based on the selected language.
 * - Sets the page's title, description, and keywords based on the view's metadata.
 */
router.beforeEach(async (to, from, next) => {
  const languageStore = useLanguageStore();

  // Extract locale from path
  const pathSegments = to.path.split('/').filter(Boolean);
  const potentialLocale = pathSegments[0];
  const supportedLocales = ['es-co', 'en-us'];
  
  // Initialize language store if not set
  if (!languageStore.currentLocale) {
    await languageStore.detectBrowserLanguageAndRegion();
  }

  // Check if we're on a locale-prefixed route
  if (supportedLocales.includes(potentialLocale)) {
    // Update store with the locale from URL and load correct global messages
    if (languageStore.currentLocale !== potentialLocale) {
      languageStore.setCurrentLocale(potentialLocale);
      await languageStore.loadMessages(languageStore.currentLanguage);
    }
  } else {
    // Handle legacy routes - redirect to locale-prefixed version
    const targetLocale = languageStore.currentLocale || 'es-co';
    
    if (to.path === '/') {
      return next(`/${targetLocale}`);
    } else {
      // Redirect other routes to their locale-prefixed versions
      const redirectPath = `/${targetLocale}${to.path}`;
      return next(redirectPath);
    }
  }

  // Extract the actual route name without locale suffix
  let routeName = to.name;
  if (routeName) {
    // Remove locale suffix from route name for message loading
    routeName = routeName.replace(/-es-co$|-en-us$/, '');
  }

  // Load the messages for the view being navigated to
  if (routeName) {
    await languageStore.loadMessagesForView(routeName);
  }

  // Load the appropriate metadata based on the current language
  const metaTexts = languageStore.currentLanguage === 'es' ? esMeta : enMeta;

  // Exception for 3dAnimations view to use Animations3D in metadata
  const metaKey = routeName === '3dAnimations' ? 'animations3D' : routeName;
  const pageMeta = metaTexts[metaKey];

  // If metadata exists for the view, set the page title, description, and keywords
  if (pageMeta) {
    // Set the page title
    document.title = pageMeta.title || 'Project App.';

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