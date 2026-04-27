import { mount } from '@vue/test-utils'
import BaseModal from '../../components/base/BaseModal.vue'

// Teleport target — Vue test utils renders the teleport content into the
// component's wrapper unless we attach a body and use `attachTo`.
function mountModal(props = {}, slots = { default: '<p>contenido</p>' }) {
  document.body.innerHTML = '<div id="app"></div>'
  return mount(BaseModal, {
    props: { modelValue: true, ...props },
    slots,
    attachTo: document.body,
  })
}

describe('BaseModal', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('does not render the modal when modelValue is false', () => {
    const wrapper = mountModal({ modelValue: false })
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
    wrapper.unmount()
  })

  it('renders the modal with role=dialog and aria-modal when open', () => {
    const wrapper = mountModal()
    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog).not.toBeNull()
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    expect(dialog.textContent).toContain('contenido')
    wrapper.unmount()
  })

  it.each([
    ['sm', 'max-w-sm'],
    ['md', 'max-w-md'],
    ['lg', 'max-w-2xl'],
    ['xl', 'max-w-3xl'],
    ['2xl', 'max-w-4xl'],
    ['5xl', 'max-w-5xl'],
  ])('maps size=%s to %s', (size, expected) => {
    const wrapper = mountModal({ size })
    const panel = document.body.querySelector('[role="dialog"] > div:nth-child(2)')
    expect(panel.className).toContain(expected)
    wrapper.unmount()
  })

  it('uses the surface token for the modal panel background', () => {
    const wrapper = mountModal()
    const panel = document.body.querySelector('[role="dialog"] > div:nth-child(2)')
    expect(panel.className).toContain('bg-surface')
    wrapper.unmount()
  })

  it('emits update:modelValue=false and close when backdrop is clicked', async () => {
    const wrapper = mountModal()
    const backdrop = document.body.querySelector('[role="dialog"] > div:first-child')
    backdrop.dispatchEvent(new Event('click', { bubbles: true }))
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    expect(wrapper.emitted('close')).toBeTruthy()
    wrapper.unmount()
  })

  it('does NOT close on backdrop click when closeOnBackdrop is false', async () => {
    const wrapper = mountModal({ closeOnBackdrop: false })
    const backdrop = document.body.querySelector('[role="dialog"] > div:first-child')
    backdrop.dispatchEvent(new Event('click', { bubbles: true }))
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    wrapper.unmount()
  })

  it('applies padding=md to the panel when requested', () => {
    const wrapper = mountModal({ padding: 'md' })
    const panel = document.body.querySelector('[role="dialog"] > div:nth-child(2)')
    expect(panel.className).toContain('p-6')
    wrapper.unmount()
  })
})
