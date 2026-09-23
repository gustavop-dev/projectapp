let loadRecaptcha

beforeEach(() => {
  jest.useFakeTimers()
  jest.isolateModules(() => {
    loadRecaptcha = require('~/utils/recaptcha').loadRecaptcha
  })
})

afterEach(() => {
  document.head.querySelectorAll('script[src*="recaptcha"]').forEach((script) => script.remove())
  delete window.grecaptcha
  delete window.projectappCaptchaReady
  jest.useRealTimers()
})

// quality: allow-fragile-selector (selects the provider script by its network URL, not application markup)
it('shares one pending provider load across consumers', async () => {
  const first = loadRecaptcha()
  const second = loadRecaptcha()
  window.grecaptcha = { render: jest.fn() }

  window.projectappCaptchaReady()

  expect(await first).toBe(window.grecaptcha)
  expect(await second).toBe(window.grecaptcha)
  expect(document.head.querySelectorAll('script[src*="recaptcha"]')).toHaveLength(1)
})

// quality: allow-fragile-selector (selects the provider script by its network URL, not application markup)
it('bounds the wait for an unresponsive script', async () => {
  const result = loadRecaptcha()
  const assertion = expect(result).rejects.toThrow('captcha_load_timeout')

  jest.advanceTimersByTime(10000)

  await assertion
  expect(document.head.querySelector('script[src*="recaptcha"]')).toBeNull()
})

// quality: allow-fragile-selector (selects the provider script by its network URL, not application markup)
it('allows another load after a network failure', async () => {
  const first = loadRecaptcha()
  const rejection = expect(first).rejects.toThrow('captcha_load_failed')
  document.head.querySelector('script[src*="recaptcha"]').dispatchEvent(new Event('error'))
  await rejection

  const retry = loadRecaptcha()
  window.grecaptcha = { render: jest.fn() }
  window.projectappCaptchaReady()

  expect(await retry).toBe(window.grecaptcha)
})
