
// @ts-nocheck


export const localeCodes =  [
  "es-co",
  "en-us"
]

export const localeLoaders = {
  "es-co": [
    {
      key: "locale_es_45co_46ts_af849a9a",
      load: () => import("#nuxt-i18n/af849a9a" /* webpackChunkName: "locale_es_45co_46ts_af849a9a" */),
      cache: false
    }
  ],
  "en-us": [
    {
      key: "locale_en_45us_46ts_b856a102",
      load: () => import("#nuxt-i18n/b856a102" /* webpackChunkName: "locale_en_45us_46ts_b856a102" */),
      cache: false
    }
  ]
}

export const vueI18nConfigs = []

export const nuxtI18nOptions = {
  restructureDir: "i18n",
  experimental: {
    localeDetector: "",
    switchLocalePathLinkSSR: false,
    autoImportTranslationFunctions: false,
    typedPages: true,
    typedOptionsAndMessages: false,
    generatedLocaleFilePathFormat: "absolute",
    alternateLinkCanonicalQueries: false,
    hmr: true
  },
  bundle: {
    compositionOnly: true,
    runtimeOnly: false,
    fullInstall: true,
    dropMessageCompiler: false,
    optimizeTranslationDirective: true
  },
  compilation: {
    strictMessage: true,
    escapeHtml: false
  },
  customBlocks: {
    defaultSFCLang: "json",
    globalSFCScope: false
  },
  locales: [
    {
      code: "es-co",
      language: "es-CO",
      name: "Español (Colombia)",
      files: [
        {
          path: "/home/cerrotico/work/projectapp_clean/frontend/i18n/locales/es-co.ts",
          cache: undefined
        }
      ]
    },
    {
      code: "en-us",
      language: "en-US",
      name: "English (United States)",
      files: [
        {
          path: "/home/cerrotico/work/projectapp_clean/frontend/i18n/locales/en-us.ts",
          cache: undefined
        }
      ]
    }
  ],
  defaultLocale: "en-us",
  defaultDirection: "ltr",
  routesNameSeparator: "___",
  trailingSlash: false,
  defaultLocaleRouteNameSuffix: "default",
  strategy: "prefix",
  lazy: true,
  langDir: "locales",
  rootRedirect: undefined,
  detectBrowserLanguage: false,
  differentDomains: false,
  baseUrl: "https://projectapp.co",
  customRoutes: "page",
  pages: {},
  skipSettingLocaleOnNavigate: false,
  types: "composition",
  debug: false,
  parallelPlugin: false,
  multiDomainLocales: false,
  i18nModules: []
}

export const normalizedLocales = [
  {
    code: "es-co",
    language: "es-CO",
    name: "Español (Colombia)",
    files: [
      {
        path: "/home/cerrotico/work/projectapp_clean/frontend/i18n/locales/es-co.ts",
        cache: undefined
      }
    ]
  },
  {
    code: "en-us",
    language: "en-US",
    name: "English (United States)",
    files: [
      {
        path: "/home/cerrotico/work/projectapp_clean/frontend/i18n/locales/en-us.ts",
        cache: undefined
      }
    ]
  }
]

export const NUXT_I18N_MODULE_ID = "@nuxtjs/i18n"
export const parallelPlugin = false
export const isSSG = false
export const hasPages = true

export const DEFAULT_COOKIE_KEY = "i18n_redirected"
export const DEFAULT_DYNAMIC_PARAMS_KEY = "nuxtI18nInternal"
export const SWITCH_LOCALE_PATH_LINK_IDENTIFIER = "nuxt-i18n-slp"
/** client **/
if(import.meta.hot) {

function deepEqual(a, b, ignoreKeys = []) {
  // Same reference?
  if (a === b) return true

  // Check if either is null or not an object
  if (a == null || b == null || typeof a !== 'object' || typeof b !== 'object') {
    return false
  }

  // Get top-level keys, excluding ignoreKeys
  const keysA = Object.keys(a).filter(k => !ignoreKeys.includes(k))
  const keysB = Object.keys(b).filter(k => !ignoreKeys.includes(k))

  // Must have the same number of keys (after ignoring)
  if (keysA.length !== keysB.length) {
    return false
  }

  // Check each property
  for (const key of keysA) {
    if (!keysB.includes(key)) {
      return false
    }

    const valA = a[key]
    const valB = b[key]

    // Compare functions stringified
    if (typeof valA === 'function' && typeof valB === 'function') {
      if (valA.toString() !== valB.toString()) {
        return false
      }
    }
    // If nested, do a normal recursive check (no ignoring at deeper levels)
    else if (typeof valA === 'object' && typeof valB === 'object') {
      if (!deepEqual(valA, valB)) {
        return false
      }
    }
    // Compare primitive values
    else if (valA !== valB) {
      return false
    }
  }

  return true
}



async function loadCfg(config) {
  const nuxt = useNuxtApp()
  const { default: resolver } = await config()
  return typeof resolver === 'function' ? await nuxt.runWithContext(() => resolver()) : resolver
}


  import.meta.hot.accept("../i18n/locales/es-co.ts", async mod => {
    localeLoaders["es-co"][0].load = () => Promise.resolve(mod.default)
    await useNuxtApp()._nuxtI18nDev.resetI18nProperties("es-co")
  })

  import.meta.hot.accept("../i18n/locales/en-us.ts", async mod => {
    localeLoaders["en-us"][0].load = () => Promise.resolve(mod.default)
    await useNuxtApp()._nuxtI18nDev.resetI18nProperties("en-us")
  })



}
/** client-end **/