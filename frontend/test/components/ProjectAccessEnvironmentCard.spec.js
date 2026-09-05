import { flushPromises, mount } from '@vue/test-utils'
import BaseInput from '../../components/base/BaseInput.vue'
import ProjectAccessEnvironmentCard from '../../components/projects/ProjectAccessEnvironmentCard.vue'

global.useI18n = jest.fn(() => ({ t: (key) => key }))

const environment = {
  environment: 'production',
  label: 'Producción',
  site_url: 'https://product.example.test',
  admin_url: 'https://product.example.test/admin/',
  admin_username: 'operator',
  has_password: true,
}

const ConfirmModalStub = {
  props: ['modelValue'],
  emits: ['update:modelValue', 'confirm'],
  template: '<div v-if="modelValue"><button data-testid="confirm-delete" @click="$emit(\'confirm\')">confirm</button></div>',
}

function buildApi() {
  return {
    updateField: jest.fn().mockResolvedValue({ environments: [] }),
    revealPassword: jest.fn().mockResolvedValue({ secret: 'server-only-secret' }),
    deletePassword: jest.fn().mockResolvedValue({ environments: [] }),
  }
}

function mountCard({ api = buildApi(), overrides = {} } = {}) {
  return {
    api,
    wrapper: mount(ProjectAccessEnvironmentCard, {
      props: {
        environment: { ...environment, ...overrides },
        api,
        onUpdated: jest.fn(),
      },
      global: {
        components: { BaseInput },
        stubs: {
          ConfirmModal: ConfirmModalStub,
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    }),
  }
}

describe('ProjectAccessEnvironmentCard', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    })
  })

  it('keeps a stored password masked until reveal is requested', async () => {
    const { api, wrapper } = mountCard()

    expect(wrapper.text()).toContain('••••••••••••')
    expect(wrapper.text()).not.toContain('server-only-secret')

    await wrapper.get('[data-testid="project-access-reveal-password-production"]').trigger('click')
    await flushPromises()

    expect(api.revealPassword).toHaveBeenCalledWith('production')
    expect(wrapper.text()).toContain('server-only-secret')
  })

  it('copies a hidden password without rendering it', async () => {
    const { api, wrapper } = mountCard()

    await wrapper.get('[data-testid="project-access-copy-password-production"]').trigger('click')
    await flushPromises()

    expect(api.revealPassword).toHaveBeenCalledWith('production')
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('server-only-secret')
    expect(wrapper.text()).not.toContain('server-only-secret')
  })

  it('never preloads the existing secret in the password editor', async () => {
    const { wrapper } = mountCard()

    await wrapper.get('[data-testid="project-access-edit-password-production"]').trigger('click')

    expect(wrapper.get('[data-testid="project-access-password-input-production"]').element.value)
      .toBe('')
  })

  it('saves a replacement password through an explicit field request', async () => {
    const { api, wrapper } = mountCard()
    await wrapper.get('[data-testid="project-access-edit-password-production"]').trigger('click')
    await wrapper.get('[data-testid="project-access-password-input-production"]')
      .setValue('replacement-secret')

    await wrapper.get('[data-testid="project-access-save-password-production"]').trigger('click')
    await flushPromises()

    expect(api.updateField).toHaveBeenCalledWith({
      environment: 'production',
      admin_password: 'replacement-secret',
    })
    expect(wrapper.text()).not.toContain('replacement-secret')
  })

  it('rejects an empty replacement password before the request', async () => {
    const { api, wrapper } = mountCard()
    await wrapper.get('[data-testid="project-access-edit-password-production"]').trigger('click')

    await wrapper.get('[data-testid="project-access-save-password-production"]').trigger('click')

    expect(api.updateField).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('projectAccess.errors.passwordRequired')
  })

  it('hides a revealed password without another request', async () => {
    const { api, wrapper } = mountCard()
    const revealButton = wrapper.get('[data-testid="project-access-reveal-password-production"]')

    await revealButton.trigger('click')
    await flushPromises()
    await revealButton.trigger('click')

    expect(api.revealPassword).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('••••••••••••')
    expect(wrapper.text()).not.toContain('server-only-secret')
  })

  it('copies a visible password without revealing it again', async () => {
    const { api, wrapper } = mountCard()

    await wrapper.get('[data-testid="project-access-reveal-password-production"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="project-access-copy-password-production"]').trigger('click')
    await flushPromises()

    expect(api.revealPassword).toHaveBeenCalledTimes(1)
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('server-only-secret')
  })

  it('shows the password field error returned by the API', async () => {
    const api = buildApi()
    api.updateField.mockRejectedValue({
      response: {
        status: 400,
        data: { admin_password: ['Use a longer password.'] },
      },
    })
    const { wrapper } = mountCard({ api })
    await wrapper.get('[data-testid="project-access-edit-password-production"]').trigger('click')
    await wrapper.get('[data-testid="project-access-password-input-production"]')
      .setValue('short')

    await wrapper.get('[data-testid="project-access-save-password-production"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Use a longer password.')
    expect(wrapper.find('[data-testid="project-access-password-input-production"]').exists())
      .toBe(true)
  })

  it('shows an API error when password reveal fails', async () => {
    const api = buildApi()
    api.revealPassword.mockRejectedValue({
      response: { status: 403, data: { detail: 'Reveal denied.' } },
    })
    const { wrapper } = mountCard({ api })

    await wrapper.get('[data-testid="project-access-reveal-password-production"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Reveal denied.')
    expect(wrapper.text()).not.toContain('server-only-secret')
  })

  it('shows an API error when hidden password copy fails', async () => {
    const api = buildApi()
    api.revealPassword.mockRejectedValue({
      response: { status: 403, data: { detail: 'Copy denied.' } },
    })
    const { wrapper } = mountCard({ api })

    await wrapper.get('[data-testid="project-access-copy-password-production"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Copy denied.')
    expect(navigator.clipboard.writeText).not.toHaveBeenCalled()
  })
})
