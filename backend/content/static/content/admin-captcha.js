/* Django's native login form: no SPA or credentials stored in the browser. */
(() => {
  const root = document.getElementById('login-captcha')
  if (!root) return
  const form = document.getElementById('login-form')
  const submit = form.querySelector('[type="submit"]')
  const status = document.getElementById('captcha-status')
  const retry = document.getElementById('captcha-retry')
  let widget = null
  let valid = false
  let submitting = false
  let timer
  let script

  function message(key) {
    valid = false
    submit.disabled = true
    status.textContent = root.dataset[key]
    retry.hidden = key === 'loading'
  }

  function render() {
    clearTimeout(timer)
    try {
      message('required')
      if (widget !== null) {
        window.grecaptcha.reset(widget)
      } else {
        widget = window.grecaptcha.render('captcha-widget', {
          sitekey: root.dataset.siteKey,
          size: 'compact',
          callback: (token) => {
            valid = Boolean(token)
            submit.disabled = !valid || submitting
            status.textContent = ''
            retry.hidden = true
          },
          'expired-callback': () => message('expired'),
          'error-callback': () => message('unavailable'),
        })
      }
    } catch {
      message('unavailable')
    }
  }

  function load() {
    message('loading')
    clearTimeout(timer)
    if (!root.dataset.siteKey) {
      message('unavailable')
      return
    }
    if (window.grecaptcha?.render) {
      render()
      return
    }
    script?.remove()
    window.projectappAdminCaptchaReady = render
    script = document.createElement('script')
    script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=projectappAdminCaptchaReady'
    script.async = true
    script.defer = true
    script.onerror = () => {
      clearTimeout(timer)
      message('unavailable')
    }
    timer = setTimeout(() => message('unavailable'), 10000)
    document.head.appendChild(script)
  }

  retry.addEventListener('click', load)
  form.addEventListener('submit', (event) => {
    if (!valid || submitting) {
      event.preventDefault()
      return
    }
    submitting = true
    submit.disabled = true
  })
  // A back/forward-cache restore must not revive a consumed token or lock the form.
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      submitting = false
      load()
    }
  })
  load()
})()
