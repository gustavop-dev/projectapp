let pendingScript = null

/** One script per document, with a bounded wait and a recoverable failed load. */
export function loadRecaptcha() {
  if (window.grecaptcha?.render) return Promise.resolve(window.grecaptcha)
  if (pendingScript) return pendingScript

  pendingScript = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    let settled = false
    const finish = (error) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      script.onerror = null
      // A timed-out script may still call its named callback later.
      window.projectappCaptchaReady = () => {}
      if (error) {
        script.remove()
        pendingScript = null
        reject(error)
      } else {
        resolve(window.grecaptcha)
      }
    }
    const timer = setTimeout(() => finish(new Error('captcha_load_timeout')), 10000)
    window.projectappCaptchaReady = () => {
      finish(window.grecaptcha?.render ? null : new Error('captcha_api_unavailable'))
    }
    script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=projectappCaptchaReady'
    script.async = true
    script.defer = true
    script.onerror = () => finish(new Error('captcha_load_failed'))
    document.head.appendChild(script)
  })
  return pendingScript
}
