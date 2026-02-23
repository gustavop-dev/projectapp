/**
 * Nuxt client plugin that listens for Cal.com's "bookingSuccessful" event
 * and fires the Google Ads Book-a-Call conversion only when the user
 * has fully completed the scheduling process.
 *
 * Cal.com is initialized with namespace "discovery-call-projectapp",
 * so events must be listened on Cal.ns["discovery-call-projectapp"].
 */
export default defineNuxtPlugin(() => {
  const CAL_NAMESPACE = 'discovery-call-projectapp'

  const attachListener = () => {
    const calNs = window.Cal?.ns?.[CAL_NAMESPACE]
    if (typeof calNs !== 'function') return false

    calNs('on', {
      action: 'bookingSuccessful',
      callback: () => {
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'conversion', {
            send_to: 'AW-16942315762/DPviCO3Qn_0bEPLx3I4_',
            value: 150000.0,
            currency: 'COP',
          })
        }
      },
    })
    return true
  }

  // Cal.com embed loads async — retry until the namespace is available
  if (!attachListener()) {
    const interval = setInterval(() => {
      if (attachListener()) clearInterval(interval)
    }, 500)
    // Stop trying after 15 seconds
    setTimeout(() => clearInterval(interval), 15000)
  }
})
