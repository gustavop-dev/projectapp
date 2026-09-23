import { flushPromises, mount } from '@vue/test-utils'
import LoginCaptcha from '~/components/auth/LoginCaptcha.vue'
import messages from '~/locales/captcha/es'

let wrapper
let callbacks

beforeEach(() => {
  global.useI18n = () => ({ t: (key) => messages[key.split('.')[1]] })
  window.grecaptcha = {
    render: jest.fn((container, options) => {
      callbacks = options
      const button = document.createElement('button')
      button.type = 'button'
      button.textContent = 'Provider challenge'
      button.addEventListener('click', () => options.callback('verified-token'))
      container.appendChild(button)
      return 0
    }),
    reset: jest.fn(),
  }
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  delete window.grecaptcha
  delete global.useI18n
  document.head.querySelectorAll('script[src*="recaptcha"]').forEach((script) => script.remove())
  jest.restoreAllMocks()
  jest.useRealTimers()
})

async function renderCaptcha(props = {}) {
  wrapper = mount(LoginCaptcha, {
    props: { siteKey: 'public-test-key', ...props },
    global: { stubs: { NuxtLink: true } },
  })
  await flushPromises()
  return wrapper
}

it('emits the solved token from the provider challenge', async () => {
  await renderCaptcha()

  await wrapper.get('button').trigger('click')

  expect(wrapper.emitted('update:token').at(-1)).toEqual(['verified-token'])
  expect(wrapper.find('[role="status"]').exists()).toBe(false)
})

it('invalidates the solved token on expiry', async () => {
  await renderCaptcha()
  await wrapper.get('button').trigger('click')

  callbacks['expired-callback']()
  await flushPromises()

  expect(wrapper.emitted('update:token').at(-1)).toEqual([''])
  expect(wrapper.get('[role="status"]').text()).toBe(messages.expired)
})

it('shows a retry action when the provider reports an error', async () => {
  await renderCaptcha()

  callbacks['error-callback']()
  await flushPromises()

  expect(wrapper.get('[role="status"]').text()).toBe(messages.error)
  expect(wrapper.emitted('update:token').at(-1)).toEqual([''])
  expect(wrapper.text()).toContain(messages.retry)
})

it('resets verification after the parent rejects an attempt', async () => {
  await renderCaptcha()
  await wrapper.get('button').trigger('click')

  await wrapper.setProps({ resetKey: 1 })
  await flushPromises()

  expect(wrapper.emitted('update:token').at(-1)).toEqual([''])
  expect(wrapper.get('[role="status"]').text()).toBe(messages.required)
  expect(window.grecaptcha.reset).toHaveBeenCalledWith(0)
})

it('offers recovery when the site key is missing', async () => {
  await renderCaptcha({ siteKey: '' })

  expect(wrapper.get('[role="status"]').text()).toBe(messages.error)
  expect(wrapper.get('button').text()).toBe(messages.retry)
  expect(wrapper.emitted('update:token').at(-1)).toEqual([''])
})

it('retries the challenge after a provider failure', async () => {
  await renderCaptcha()
  callbacks['error-callback']()
  await flushPromises()

  await wrapper.findAll('button').find((button) => button.text() === messages.retry).trigger('click')
  await flushPromises()

  expect(wrapper.get('[role="status"]').text()).toBe(messages.required)
  expect(window.grecaptcha.reset).toHaveBeenCalledWith(0)
})

it('ignores a token delivered after the component is removed', async () => {
  await renderCaptcha()
  wrapper.unmount()
  const emittedCount = wrapper.emitted('update:token').length

  callbacks.callback('late-token')

  expect(wrapper.emitted('update:token')).toHaveLength(emittedCount)
})

// quality: allow-fragile-selector (the external Google script has no accessible role or app-owned testid)
it('shows recovery when the script fails to load', async () => {
  delete window.grecaptcha
  await renderCaptcha()

  document.head.querySelector('script[src*="recaptcha"]').dispatchEvent(new Event('error'))
  await flushPromises()

  expect(wrapper.get('[role="status"]').text()).toBe(messages.error)
  expect(wrapper.get('button').text()).toBe(messages.retry)
})
