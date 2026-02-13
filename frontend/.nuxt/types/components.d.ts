
import type { DefineComponent, SlotsType } from 'vue'
type IslandComponent<T> = DefineComponent<{}, {refresh: () => Promise<void>}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, SlotsType<{ fallback: { error: unknown } }>> & T

type HydrationStrategies = {
  hydrateOnVisible?: IntersectionObserverInit | true
  hydrateOnIdle?: number | true
  hydrateOnInteraction?: keyof HTMLElementEventMap | Array<keyof HTMLElementEventMap> | true
  hydrateOnMediaQuery?: string
  hydrateAfter?: number
  hydrateWhen?: boolean
  hydrateNever?: true
}
type LazyComponent<T> = DefineComponent<HydrationStrategies, {}, {}, {}, {}, {}, {}, { hydrated: () => void }> & T

interface _GlobalComponents {
  BusinessProposalContextDiagnostic: typeof import("../../components/BusinessProposal/ContextDiagnostic.vue")['default']
  BusinessProposalConversionStrategy: typeof import("../../components/BusinessProposal/ConversionStrategy.vue")['default']
  BusinessProposalCreativeSupport: typeof import("../../components/BusinessProposal/CreativeSupport.vue")['default']
  BusinessProposalDesignUX: typeof import("../../components/BusinessProposal/DesignUX.vue")['default']
  BusinessProposalDevelopmentStages: typeof import("../../components/BusinessProposal/DevelopmentStages.vue")['default']
  BusinessProposalExecutiveSummary: typeof import("../../components/BusinessProposal/ExecutiveSummary.vue")['default']
  BusinessProposalFinalNote: typeof import("../../components/BusinessProposal/FinalNote.vue")['default']
  BusinessProposalFunctionalRequirements: typeof import("../../components/BusinessProposal/FunctionalRequirements.vue")['default']
  BusinessProposalGreeting: typeof import("../../components/BusinessProposal/Greeting.vue")['default']
  BusinessProposalInvestment: typeof import("../../components/BusinessProposal/Investment.vue")['default']
  BusinessProposalNextSteps: typeof import("../../components/BusinessProposal/NextSteps.vue")['default']
  BusinessProposalTimeline: typeof import("../../components/BusinessProposal/Timeline.vue")['default']
  BusinessProposal: typeof import("../../components/BusinessProposal/index")['default']
  LocaleSwitcher: typeof import("../../components/LocaleSwitcher.vue")['default']
  VideoModal: typeof import("../../components/VideoModal.vue")['default']
  AnimationsPreloaderAnimation: typeof import("../../components/animations/PreloaderAnimation.vue")['default']
  HomeBentoGrid: typeof import("../../components/home/BentoGrid.vue")['default']
  HomeBookCallSection: typeof import("../../components/home/BookCallSection.vue")['default']
  HomeContactSection: typeof import("../../components/home/ContactSection.vue")['default']
  HomeContractSection: typeof import("../../components/home/ContractSection.vue")['default']
  HomeHero: typeof import("../../components/home/Hero.vue")['default']
  HomeInitialVideo: typeof import("../../components/home/InitialVideo.vue")['default']
  HomeInitialVideoMobile: typeof import("../../components/home/InitialVideoMobile.vue")['default']
  HomeMarqueeStrips: typeof import("../../components/home/MarqueeStrips.vue")['default']
  HomeServicesCards: typeof import("../../components/home/ServicesCards.vue")['default']
  HomeStudyCases: typeof import("../../components/home/StudyCases.vue")['default']
  HomeTechStack: typeof import("../../components/home/TechStack.vue")['default']
  HomeUnrepeatableSection: typeof import("../../components/home/UnrepeatableSection.vue")['default']
  LayoutsAssetPreloader: typeof import("../../components/layouts/AssetPreloader.vue")['default']
  LayoutsContact: typeof import("../../components/layouts/Contact.vue")['default']
  LayoutsEmail: typeof import("../../components/layouts/Email.vue")['default']
  LayoutsFooter: typeof import("../../components/layouts/Footer.vue")['default']
  LayoutsFooterDesktop: typeof import("../../components/layouts/FooterDesktop.vue")['default']
  LayoutsFooterMobile: typeof import("../../components/layouts/FooterMobile.vue")['default']
  LayoutsImageLoader: typeof import("../../components/layouts/ImageLoader.vue")['default']
  LayoutsLazyImage: typeof import("../../components/layouts/LazyImage.vue")['default']
  LayoutsLazyVideo: typeof import("../../components/layouts/LazyVideo.vue")['default']
  LayoutsLoadingScreen: typeof import("../../components/layouts/LoadingScreen.vue")['default']
  LayoutsMediaOptimizer: typeof import("../../components/layouts/MediaOptimizer.vue")['default']
  LayoutsNavbar: typeof import("../../components/layouts/Navbar.vue")['default']
  SplineBackgroundsDune: typeof import("../../components/spline/Backgrounds/Dune.vue")['default']
  UiAnimatedTestimonials: typeof import("../../components/ui/AnimatedTestimonials.vue")['default']
  UiBackgroundGradientAnimation: typeof import("../../components/ui/BackgroundGradientAnimation.vue")['default']
  UiTooltip: typeof import("../../components/ui/Tooltip.vue")['default']
  UtilsButtonWithArrow: typeof import("../../components/utils/ButtonWithArrow.vue")['default']
  UtilsSocialLinks: typeof import("../../components/utils/SocialLinks.vue")['default']
  UtilsWordpress: typeof import("../../components/utils/Wordpress.vue")['default']
  NuxtWelcome: typeof import("../../node_modules/nuxt/dist/app/components/welcome.vue")['default']
  NuxtLayout: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-layout")['default']
  NuxtErrorBoundary: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']
  ClientOnly: typeof import("../../node_modules/nuxt/dist/app/components/client-only")['default']
  DevOnly: typeof import("../../node_modules/nuxt/dist/app/components/dev-only")['default']
  ServerPlaceholder: typeof import("../../node_modules/nuxt/dist/app/components/server-placeholder")['default']
  NuxtLink: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-link")['default']
  NuxtLoadingIndicator: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']
  NuxtTime: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']
  NuxtRouteAnnouncer: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']
  NuxtImg: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']
  NuxtPicture: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']
  NuxtLinkLocale: typeof import("../../node_modules/@nuxtjs/i18n/dist/runtime/components/NuxtLinkLocale")['default']
  SwitchLocalePathLink: typeof import("../../node_modules/@nuxtjs/i18n/dist/runtime/components/SwitchLocalePathLink")['default']
  NuxtPage: typeof import("../../node_modules/nuxt/dist/pages/runtime/page")['default']
  NoScript: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['NoScript']
  Link: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Link']
  Base: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Base']
  Title: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Title']
  Meta: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Meta']
  Style: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Style']
  Head: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Head']
  Html: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Html']
  Body: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Body']
  NuxtIsland: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-island")['default']
  LazyBusinessProposalContextDiagnostic: LazyComponent<typeof import("../../components/BusinessProposal/ContextDiagnostic.vue")['default']>
  LazyBusinessProposalConversionStrategy: LazyComponent<typeof import("../../components/BusinessProposal/ConversionStrategy.vue")['default']>
  LazyBusinessProposalCreativeSupport: LazyComponent<typeof import("../../components/BusinessProposal/CreativeSupport.vue")['default']>
  LazyBusinessProposalDesignUX: LazyComponent<typeof import("../../components/BusinessProposal/DesignUX.vue")['default']>
  LazyBusinessProposalDevelopmentStages: LazyComponent<typeof import("../../components/BusinessProposal/DevelopmentStages.vue")['default']>
  LazyBusinessProposalExecutiveSummary: LazyComponent<typeof import("../../components/BusinessProposal/ExecutiveSummary.vue")['default']>
  LazyBusinessProposalFinalNote: LazyComponent<typeof import("../../components/BusinessProposal/FinalNote.vue")['default']>
  LazyBusinessProposalFunctionalRequirements: LazyComponent<typeof import("../../components/BusinessProposal/FunctionalRequirements.vue")['default']>
  LazyBusinessProposalGreeting: LazyComponent<typeof import("../../components/BusinessProposal/Greeting.vue")['default']>
  LazyBusinessProposalInvestment: LazyComponent<typeof import("../../components/BusinessProposal/Investment.vue")['default']>
  LazyBusinessProposalNextSteps: LazyComponent<typeof import("../../components/BusinessProposal/NextSteps.vue")['default']>
  LazyBusinessProposalTimeline: LazyComponent<typeof import("../../components/BusinessProposal/Timeline.vue")['default']>
  LazyBusinessProposal: LazyComponent<typeof import("../../components/BusinessProposal/index")['default']>
  LazyLocaleSwitcher: LazyComponent<typeof import("../../components/LocaleSwitcher.vue")['default']>
  LazyVideoModal: LazyComponent<typeof import("../../components/VideoModal.vue")['default']>
  LazyAnimationsPreloaderAnimation: LazyComponent<typeof import("../../components/animations/PreloaderAnimation.vue")['default']>
  LazyHomeBentoGrid: LazyComponent<typeof import("../../components/home/BentoGrid.vue")['default']>
  LazyHomeBookCallSection: LazyComponent<typeof import("../../components/home/BookCallSection.vue")['default']>
  LazyHomeContactSection: LazyComponent<typeof import("../../components/home/ContactSection.vue")['default']>
  LazyHomeContractSection: LazyComponent<typeof import("../../components/home/ContractSection.vue")['default']>
  LazyHomeHero: LazyComponent<typeof import("../../components/home/Hero.vue")['default']>
  LazyHomeInitialVideo: LazyComponent<typeof import("../../components/home/InitialVideo.vue")['default']>
  LazyHomeInitialVideoMobile: LazyComponent<typeof import("../../components/home/InitialVideoMobile.vue")['default']>
  LazyHomeMarqueeStrips: LazyComponent<typeof import("../../components/home/MarqueeStrips.vue")['default']>
  LazyHomeServicesCards: LazyComponent<typeof import("../../components/home/ServicesCards.vue")['default']>
  LazyHomeStudyCases: LazyComponent<typeof import("../../components/home/StudyCases.vue")['default']>
  LazyHomeTechStack: LazyComponent<typeof import("../../components/home/TechStack.vue")['default']>
  LazyHomeUnrepeatableSection: LazyComponent<typeof import("../../components/home/UnrepeatableSection.vue")['default']>
  LazyLayoutsAssetPreloader: LazyComponent<typeof import("../../components/layouts/AssetPreloader.vue")['default']>
  LazyLayoutsContact: LazyComponent<typeof import("../../components/layouts/Contact.vue")['default']>
  LazyLayoutsEmail: LazyComponent<typeof import("../../components/layouts/Email.vue")['default']>
  LazyLayoutsFooter: LazyComponent<typeof import("../../components/layouts/Footer.vue")['default']>
  LazyLayoutsFooterDesktop: LazyComponent<typeof import("../../components/layouts/FooterDesktop.vue")['default']>
  LazyLayoutsFooterMobile: LazyComponent<typeof import("../../components/layouts/FooterMobile.vue")['default']>
  LazyLayoutsImageLoader: LazyComponent<typeof import("../../components/layouts/ImageLoader.vue")['default']>
  LazyLayoutsLazyImage: LazyComponent<typeof import("../../components/layouts/LazyImage.vue")['default']>
  LazyLayoutsLazyVideo: LazyComponent<typeof import("../../components/layouts/LazyVideo.vue")['default']>
  LazyLayoutsLoadingScreen: LazyComponent<typeof import("../../components/layouts/LoadingScreen.vue")['default']>
  LazyLayoutsMediaOptimizer: LazyComponent<typeof import("../../components/layouts/MediaOptimizer.vue")['default']>
  LazyLayoutsNavbar: LazyComponent<typeof import("../../components/layouts/Navbar.vue")['default']>
  LazySplineBackgroundsDune: LazyComponent<typeof import("../../components/spline/Backgrounds/Dune.vue")['default']>
  LazyUiAnimatedTestimonials: LazyComponent<typeof import("../../components/ui/AnimatedTestimonials.vue")['default']>
  LazyUiBackgroundGradientAnimation: LazyComponent<typeof import("../../components/ui/BackgroundGradientAnimation.vue")['default']>
  LazyUiTooltip: LazyComponent<typeof import("../../components/ui/Tooltip.vue")['default']>
  LazyUtilsButtonWithArrow: LazyComponent<typeof import("../../components/utils/ButtonWithArrow.vue")['default']>
  LazyUtilsSocialLinks: LazyComponent<typeof import("../../components/utils/SocialLinks.vue")['default']>
  LazyUtilsWordpress: LazyComponent<typeof import("../../components/utils/Wordpress.vue")['default']>
  LazyNuxtWelcome: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/welcome.vue")['default']>
  LazyNuxtLayout: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-layout")['default']>
  LazyNuxtErrorBoundary: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']>
  LazyClientOnly: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/client-only")['default']>
  LazyDevOnly: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/dev-only")['default']>
  LazyServerPlaceholder: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/server-placeholder")['default']>
  LazyNuxtLink: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-link")['default']>
  LazyNuxtLoadingIndicator: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']>
  LazyNuxtTime: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']>
  LazyNuxtRouteAnnouncer: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']>
  LazyNuxtImg: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']>
  LazyNuxtPicture: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']>
  LazyNuxtLinkLocale: LazyComponent<typeof import("../../node_modules/@nuxtjs/i18n/dist/runtime/components/NuxtLinkLocale")['default']>
  LazySwitchLocalePathLink: LazyComponent<typeof import("../../node_modules/@nuxtjs/i18n/dist/runtime/components/SwitchLocalePathLink")['default']>
  LazyNuxtPage: LazyComponent<typeof import("../../node_modules/nuxt/dist/pages/runtime/page")['default']>
  LazyNoScript: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['NoScript']>
  LazyLink: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Link']>
  LazyBase: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Base']>
  LazyTitle: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Title']>
  LazyMeta: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Meta']>
  LazyStyle: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Style']>
  LazyHead: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Head']>
  LazyHtml: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Html']>
  LazyBody: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Body']>
  LazyNuxtIsland: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-island")['default']>
}

declare module 'vue' {
  export interface GlobalComponents extends _GlobalComponents { }
}

export {}
