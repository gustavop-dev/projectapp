/**
 * Nuxt client plugin that listens for Cal.com's "bookingSuccessful" event
 * and fires the Google Ads Book-a-Call conversion only when the user
 * has fully completed the scheduling process.
 */
export default defineNuxtPlugin(() => {
  const checkCal = () => {
    if (typeof window.Cal === 'function') {
      window.Cal('on', {
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
    return false
  }

  // Cal.com embed may load async — retry until available
  if (!checkCal()) {
    const interval = setInterval(() => {
      if (checkCal()) clearInterval(interval)
    }, 500)
    // Stop trying after 15 seconds
    setTimeout(() => clearInterval(interval), 15000)
  }
})
