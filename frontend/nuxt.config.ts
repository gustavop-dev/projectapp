// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@nuxtjs/i18n',
  ],

  // Hybrid rendering: key pages SSR, rest SPA
  routeRules: {
    '/': { ssr: true },
    '/en-us': { ssr: true },
    '/es-co': { ssr: true },
    '/en-us/about-us': { ssr: true },
    '/es-co/about-us': { ssr: true },
    '/en-us/web-designs': { ssr: true },
    '/es-co/web-designs': { ssr: true },
    '/en-us/portfolio-works': { ssr: true },
    '/es-co/portfolio-works': { ssr: true },
    '/en-us/custom-software': { ssr: true },
    '/es-co/custom-software': { ssr: true },
    '/en-us/3d-animations': { ssr: true },
    '/es-co/3d-animations': { ssr: true },
    '/es-co/**': { ssr: false },
    '/en-us/**': { ssr: false },
    '/**': { ssr: false },
  },

  // Proxy API calls to Django backend
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://127.0.0.1:8000/api',
        changeOrigin: true,
      },
    },
  },

  // Alias @ to project root (like src/ was before)
  alias: {
    '@': '.',
  },

  // CSS
  css: [
    '~/assets/styles/main.css',
  ],

  // Tailwind config
  tailwindcss: {
    configPath: '~/tailwind.config.js',
  },

  // i18n configuration
  i18n: {
    locales: [
      {
        code: 'es-co',
        language: 'es-CO',
        name: 'Español (Colombia)',
        file: 'es-co.ts',
      },
      {
        code: 'en-us',
        language: 'en-US',
        name: 'English (United States)',
        file: 'en-us.ts',
      },
    ],
    defaultLocale: 'en-us',
    lazy: true,
    strategy: 'prefix',
    detectBrowserLanguage: false,
    // SEO
    baseUrl: 'https://projectapp.co',
  },

  // App head (Facebook Pixel, Cal.com, meta)
  app: {
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      title: 'Project App.',
      link: [
        { rel: 'icon', href: '/img/icons/icon-logo-192x192.png' },
      ],
      script: [
        {
          children: `!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','1870177640258815');fbq('track','PageView');`,
        },
        {
          children: `(function(C,A,L){let p=function(a,ar){a.q.push(ar)};let d=C.document;C.Cal=C.Cal||function(){let cal=C.Cal;let ar=arguments;if(!cal.loaded){cal.ns={};cal.q=cal.q||[];d.head.appendChild(d.createElement("script")).src=A;cal.loaded=true}if(ar[0]===L){const api=function(){p(api,arguments)};const namespace=ar[1];api.q=api.q||[];if(typeof namespace==="string"){cal.ns[namespace]=cal.ns[namespace]||api;p(cal.ns[namespace],ar);p(cal,["initNamespace",namespace])}else{p(cal,ar)}return}p(cal,ar)}})(window,"https://app.cal.com/embed/embed.js","init");Cal("init","discovery-call-projectapp",{origin:"https://app.cal.com"});Cal.ns["discovery-call-projectapp"]("ui",{theme:"dark",hideEventTypeDetails:false,layout:"week_view"});`,
        },
      ],
      noscript: [
        {
          children: '<img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=1870177640258815&ev=PageView&noscript=1" />',
        },
      ],
    },
  },

  compatibilityDate: '2024-11-01',
})
