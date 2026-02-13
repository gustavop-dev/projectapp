
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


export const BusinessProposalContextDiagnostic: typeof import("../components/BusinessProposal/ContextDiagnostic.vue")['default']
export const BusinessProposalConversionStrategy: typeof import("../components/BusinessProposal/ConversionStrategy.vue")['default']
export const BusinessProposalCreativeSupport: typeof import("../components/BusinessProposal/CreativeSupport.vue")['default']
export const BusinessProposalDesignUX: typeof import("../components/BusinessProposal/DesignUX.vue")['default']
export const BusinessProposalDevelopmentStages: typeof import("../components/BusinessProposal/DevelopmentStages.vue")['default']
export const BusinessProposalExecutiveSummary: typeof import("../components/BusinessProposal/ExecutiveSummary.vue")['default']
export const BusinessProposalFinalNote: typeof import("../components/BusinessProposal/FinalNote.vue")['default']
export const BusinessProposalFunctionalRequirements: typeof import("../components/BusinessProposal/FunctionalRequirements.vue")['default']
export const BusinessProposalGreeting: typeof import("../components/BusinessProposal/Greeting.vue")['default']
export const BusinessProposalInvestment: typeof import("../components/BusinessProposal/Investment.vue")['default']
export const BusinessProposalNextSteps: typeof import("../components/BusinessProposal/NextSteps.vue")['default']
export const BusinessProposalTimeline: typeof import("../components/BusinessProposal/Timeline.vue")['default']
export const BusinessProposal: typeof import("../components/BusinessProposal/index")['default']
export const LocaleSwitcher: typeof import("../components/LocaleSwitcher.vue")['default']
export const VideoModal: typeof import("../components/VideoModal.vue")['default']
export const AnimationsPreloaderAnimation: typeof import("../components/animations/PreloaderAnimation.vue")['default']
export const HomeBentoGrid: typeof import("../components/home/BentoGrid.vue")['default']
export const HomeBookCallSection: typeof import("../components/home/BookCallSection.vue")['default']
export const HomeContactSection: typeof import("../components/home/ContactSection.vue")['default']
export const HomeContractSection: typeof import("../components/home/ContractSection.vue")['default']
export const HomeHero: typeof import("../components/home/Hero.vue")['default']
export const HomeInitialVideo: typeof import("../components/home/InitialVideo.vue")['default']
export const HomeInitialVideoMobile: typeof import("../components/home/InitialVideoMobile.vue")['default']
export const HomeMarqueeStrips: typeof import("../components/home/MarqueeStrips.vue")['default']
export const HomeServicesCards: typeof import("../components/home/ServicesCards.vue")['default']
export const HomeStudyCases: typeof import("../components/home/StudyCases.vue")['default']
export const HomeTechStack: typeof import("../components/home/TechStack.vue")['default']
export const HomeUnrepeatableSection: typeof import("../components/home/UnrepeatableSection.vue")['default']
export const LayoutsAssetPreloader: typeof import("../components/layouts/AssetPreloader.vue")['default']
export const LayoutsContact: typeof import("../components/layouts/Contact.vue")['default']
export const LayoutsEmail: typeof import("../components/layouts/Email.vue")['default']
export const LayoutsFooter: typeof import("../components/layouts/Footer.vue")['default']
export const LayoutsFooterDesktop: typeof import("../components/layouts/FooterDesktop.vue")['default']
export const LayoutsFooterMobile: typeof import("../components/layouts/FooterMobile.vue")['default']
export const LayoutsImageLoader: typeof import("../components/layouts/ImageLoader.vue")['default']
export const LayoutsLazyImage: typeof import("../components/layouts/LazyImage.vue")['default']
export const LayoutsLazyVideo: typeof import("../components/layouts/LazyVideo.vue")['default']
export const LayoutsLoadingScreen: typeof import("../components/layouts/LoadingScreen.vue")['default']
export const LayoutsMediaOptimizer: typeof import("../components/layouts/MediaOptimizer.vue")['default']
export const LayoutsNavbar: typeof import("../components/layouts/Navbar.vue")['default']
export const SplineBackgroundsDune: typeof import("../components/spline/Backgrounds/Dune.vue")['default']
export const UiAnimatedTestimonials: typeof import("../components/ui/AnimatedTestimonials.vue")['default']
export const UiBackgroundGradientAnimation: typeof import("../components/ui/BackgroundGradientAnimation.vue")['default']
export const UiTooltip: typeof import("../components/ui/Tooltip.vue")['default']
export const UtilsButtonWithArrow: typeof import("../components/utils/ButtonWithArrow.vue")['default']
export const UtilsSocialLinks: typeof import("../components/utils/SocialLinks.vue")['default']
export const UtilsWordpress: typeof import("../components/utils/Wordpress.vue")['default']
export const NuxtWelcome: typeof import("../node_modules/nuxt/dist/app/components/welcome.vue")['default']
export const NuxtLayout: typeof import("../node_modules/nuxt/dist/app/components/nuxt-layout")['default']
export const NuxtErrorBoundary: typeof import("../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']
export const ClientOnly: typeof import("../node_modules/nuxt/dist/app/components/client-only")['default']
export const DevOnly: typeof import("../node_modules/nuxt/dist/app/components/dev-only")['default']
export const ServerPlaceholder: typeof import("../node_modules/nuxt/dist/app/components/server-placeholder")['default']
export const NuxtLink: typeof import("../node_modules/nuxt/dist/app/components/nuxt-link")['default']
export const NuxtLoadingIndicator: typeof import("../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']
export const NuxtTime: typeof import("../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']
export const NuxtRouteAnnouncer: typeof import("../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']
export const NuxtImg: typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']
export const NuxtPicture: typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']
export const NuxtLinkLocale: typeof import("../node_modules/@nuxtjs/i18n/dist/runtime/components/NuxtLinkLocale")['default']
export const SwitchLocalePathLink: typeof import("../node_modules/@nuxtjs/i18n/dist/runtime/components/SwitchLocalePathLink")['default']
export const NuxtPage: typeof import("../node_modules/nuxt/dist/pages/runtime/page")['default']
export const NoScript: typeof import("../node_modules/nuxt/dist/head/runtime/components")['NoScript']
export const Link: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Link']
export const Base: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Base']
export const Title: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Title']
export const Meta: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Meta']
export const Style: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Style']
export const Head: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Head']
export const Html: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Html']
export const Body: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Body']
export const NuxtIsland: typeof import("../node_modules/nuxt/dist/app/components/nuxt-island")['default']
export const LazyBusinessProposalContextDiagnostic: LazyComponent<typeof import("../components/BusinessProposal/ContextDiagnostic.vue")['default']>
export const LazyBusinessProposalConversionStrategy: LazyComponent<typeof import("../components/BusinessProposal/ConversionStrategy.vue")['default']>
export const LazyBusinessProposalCreativeSupport: LazyComponent<typeof import("../components/BusinessProposal/CreativeSupport.vue")['default']>
export const LazyBusinessProposalDesignUX: LazyComponent<typeof import("../components/BusinessProposal/DesignUX.vue")['default']>
export const LazyBusinessProposalDevelopmentStages: LazyComponent<typeof import("../components/BusinessProposal/DevelopmentStages.vue")['default']>
export const LazyBusinessProposalExecutiveSummary: LazyComponent<typeof import("../components/BusinessProposal/ExecutiveSummary.vue")['default']>
export const LazyBusinessProposalFinalNote: LazyComponent<typeof import("../components/BusinessProposal/FinalNote.vue")['default']>
export const LazyBusinessProposalFunctionalRequirements: LazyComponent<typeof import("../components/BusinessProposal/FunctionalRequirements.vue")['default']>
export const LazyBusinessProposalGreeting: LazyComponent<typeof import("../components/BusinessProposal/Greeting.vue")['default']>
export const LazyBusinessProposalInvestment: LazyComponent<typeof import("../components/BusinessProposal/Investment.vue")['default']>
export const LazyBusinessProposalNextSteps: LazyComponent<typeof import("../components/BusinessProposal/NextSteps.vue")['default']>
export const LazyBusinessProposalTimeline: LazyComponent<typeof import("../components/BusinessProposal/Timeline.vue")['default']>
export const LazyBusinessProposal: LazyComponent<typeof import("../components/BusinessProposal/index")['default']>
export const LazyLocaleSwitcher: LazyComponent<typeof import("../components/LocaleSwitcher.vue")['default']>
export const LazyVideoModal: LazyComponent<typeof import("../components/VideoModal.vue")['default']>
export const LazyAnimationsPreloaderAnimation: LazyComponent<typeof import("../components/animations/PreloaderAnimation.vue")['default']>
export const LazyHomeBentoGrid: LazyComponent<typeof import("../components/home/BentoGrid.vue")['default']>
export const LazyHomeBookCallSection: LazyComponent<typeof import("../components/home/BookCallSection.vue")['default']>
export const LazyHomeContactSection: LazyComponent<typeof import("../components/home/ContactSection.vue")['default']>
export const LazyHomeContractSection: LazyComponent<typeof import("../components/home/ContractSection.vue")['default']>
export const LazyHomeHero: LazyComponent<typeof import("../components/home/Hero.vue")['default']>
export const LazyHomeInitialVideo: LazyComponent<typeof import("../components/home/InitialVideo.vue")['default']>
export const LazyHomeInitialVideoMobile: LazyComponent<typeof import("../components/home/InitialVideoMobile.vue")['default']>
export const LazyHomeMarqueeStrips: LazyComponent<typeof import("../components/home/MarqueeStrips.vue")['default']>
export const LazyHomeServicesCards: LazyComponent<typeof import("../components/home/ServicesCards.vue")['default']>
export const LazyHomeStudyCases: LazyComponent<typeof import("../components/home/StudyCases.vue")['default']>
export const LazyHomeTechStack: LazyComponent<typeof import("../components/home/TechStack.vue")['default']>
export const LazyHomeUnrepeatableSection: LazyComponent<typeof import("../components/home/UnrepeatableSection.vue")['default']>
export const LazyLayoutsAssetPreloader: LazyComponent<typeof import("../components/layouts/AssetPreloader.vue")['default']>
export const LazyLayoutsContact: LazyComponent<typeof import("../components/layouts/Contact.vue")['default']>
export const LazyLayoutsEmail: LazyComponent<typeof import("../components/layouts/Email.vue")['default']>
export const LazyLayoutsFooter: LazyComponent<typeof import("../components/layouts/Footer.vue")['default']>
export const LazyLayoutsFooterDesktop: LazyComponent<typeof import("../components/layouts/FooterDesktop.vue")['default']>
export const LazyLayoutsFooterMobile: LazyComponent<typeof import("../components/layouts/FooterMobile.vue")['default']>
export const LazyLayoutsImageLoader: LazyComponent<typeof import("../components/layouts/ImageLoader.vue")['default']>
export const LazyLayoutsLazyImage: LazyComponent<typeof import("../components/layouts/LazyImage.vue")['default']>
export const LazyLayoutsLazyVideo: LazyComponent<typeof import("../components/layouts/LazyVideo.vue")['default']>
export const LazyLayoutsLoadingScreen: LazyComponent<typeof import("../components/layouts/LoadingScreen.vue")['default']>
export const LazyLayoutsMediaOptimizer: LazyComponent<typeof import("../components/layouts/MediaOptimizer.vue")['default']>
export const LazyLayoutsNavbar: LazyComponent<typeof import("../components/layouts/Navbar.vue")['default']>
export const LazySplineBackgroundsDune: LazyComponent<typeof import("../components/spline/Backgrounds/Dune.vue")['default']>
export const LazyUiAnimatedTestimonials: LazyComponent<typeof import("../components/ui/AnimatedTestimonials.vue")['default']>
export const LazyUiBackgroundGradientAnimation: LazyComponent<typeof import("../components/ui/BackgroundGradientAnimation.vue")['default']>
export const LazyUiTooltip: LazyComponent<typeof import("../components/ui/Tooltip.vue")['default']>
export const LazyUtilsButtonWithArrow: LazyComponent<typeof import("../components/utils/ButtonWithArrow.vue")['default']>
export const LazyUtilsSocialLinks: LazyComponent<typeof import("../components/utils/SocialLinks.vue")['default']>
export const LazyUtilsWordpress: LazyComponent<typeof import("../components/utils/Wordpress.vue")['default']>
export const LazyNuxtWelcome: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/welcome.vue")['default']>
export const LazyNuxtLayout: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-layout")['default']>
export const LazyNuxtErrorBoundary: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']>
export const LazyClientOnly: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/client-only")['default']>
export const LazyDevOnly: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/dev-only")['default']>
export const LazyServerPlaceholder: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/server-placeholder")['default']>
export const LazyNuxtLink: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-link")['default']>
export const LazyNuxtLoadingIndicator: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']>
export const LazyNuxtTime: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']>
export const LazyNuxtRouteAnnouncer: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']>
export const LazyNuxtImg: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']>
export const LazyNuxtPicture: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']>
export const LazyNuxtLinkLocale: LazyComponent<typeof import("../node_modules/@nuxtjs/i18n/dist/runtime/components/NuxtLinkLocale")['default']>
export const LazySwitchLocalePathLink: LazyComponent<typeof import("../node_modules/@nuxtjs/i18n/dist/runtime/components/SwitchLocalePathLink")['default']>
export const LazyNuxtPage: LazyComponent<typeof import("../node_modules/nuxt/dist/pages/runtime/page")['default']>
export const LazyNoScript: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['NoScript']>
export const LazyLink: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Link']>
export const LazyBase: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Base']>
export const LazyTitle: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Title']>
export const LazyMeta: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Meta']>
export const LazyStyle: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Style']>
export const LazyHead: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Head']>
export const LazyHtml: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Html']>
export const LazyBody: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Body']>
export const LazyNuxtIsland: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-island")['default']>

export const componentNames: string[]
