/**
 * Google Ads Conversion Tracking composable.
 * Provides functions to report conversions for:
 * - Form Submission
 * - WhatsApp Click
 * - Book a Call Click
 */
export function useGtagConversions() {
  const trackFormSubmission = (url) => {
    if (typeof window === 'undefined' || typeof window.gtag !== 'function') return
    const callback = () => {
      if (typeof url !== 'undefined') {
        window.open(url, '_self')
      }
    }
    window.gtag('event', 'conversion', {
      send_to: 'AW-16942315762/foFwCMGynP0bEPLx3I4_',
      value: 150000.0,
      currency: 'COP',
      event_callback: callback,
    })
  }

  const trackWhatsAppClick = (url) => {
    if (typeof window === 'undefined' || typeof window.gtag !== 'function') return
    const callback = () => {
      if (typeof url !== 'undefined') {
        window.open(url, '_self')
      }
    }
    window.gtag('event', 'conversion', {
      send_to: 'AW-16942315762/GOn5COrQn_0bEPLx3I4_',
      value: 100000.0,
      currency: 'COP',
      event_callback: callback,
    })
  }

  const trackBookACall = (url) => {
    if (typeof window === 'undefined' || typeof window.gtag !== 'function') return
    const callback = () => {
      if (typeof url !== 'undefined') {
        window.open(url, '_self')
      }
    }
    window.gtag('event', 'conversion', {
      send_to: 'AW-16942315762/DPviCO3Qn_0bEPLx3I4_',
      value: 150000.0,
      currency: 'COP',
      event_callback: callback,
    })
  }

  return {
    trackFormSubmission,
    trackWhatsAppClick,
    trackBookACall,
  }
}
