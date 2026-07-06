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

  it('links aria-labelledby to the titleId prop when provided', async () => {
    const wrapper = mountModal(
      { titleId: 'my-modal-title' },
      { default: '<h3 id="my-modal-title">Título</h3>' },
    )
    await wrapper.vm.$nextTick()
    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog.getAttribute('aria-labelledby')).toBe('my-modal-title')
    wrapper.unmount()
  })

  it('auto-detects a slot heading and links aria-labelledby to it', async () => {
    const wrapper = mountModal({}, { default: '<h3>Editar registro</h3>' })
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const dialog = document.body.querySelector('[role="dialog"]')
    const heading = dialog.querySelector('h3')
    expect(heading.id).toBeTruthy()
    expect(dialog.getAttribute('aria-labelledby')).toBe(heading.id)
    wrapper.unmount()
  })

  it('moves focus to the panel when opened', async () => {
    const wrapper = mountModal()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const panel = document.body.querySelector('[role="dialog"] > div:nth-child(2)')
    expect(document.activeElement).toBe(panel)
    wrapper.unmount()
  })

  it('restores focus to the previously focused element on close', async () => {
    document.body.innerHTML = '<div id="app"></div><button id="opener" type="button">abrir</button>'
    document.getElementById('opener').focus()
    const wrapper = mount(BaseModal, {
      props: { modelValue: false },
      slots: { default: '<p>contenido</p>' },
      attachTo: document.body,
    })
    await wrapper.setProps({ modelValue: true })
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(document.activeElement.id).not.toBe('opener')

    await wrapper.setProps({ modelValue: false })
    expect(document.activeElement.id).toBe('opener')
    wrapper.unmount()
  })

  it('keeps Tab focus inside the panel', async () => {
    const wrapper = mountModal({}, {
      default: '<button id="first" type="button">uno</button><button id="last" type="button">dos</button>',
    })
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    const last = document.getElementById('last')
    last.focus()
    last.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
      cancelable: true,
    }))

    expect(document.activeElement.id).toBe('first')
    wrapper.unmount()
  })
})
