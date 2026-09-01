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

function getModalPanel() {
  return document.body.querySelector('[data-modal-kind]')
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
    ['sm', 'panel-portrait:max-w-sm'],
    ['md', 'panel-portrait:max-w-md'],
    ['lg', 'panel-portrait:max-w-2xl'],
    ['xl', 'panel-portrait:max-w-3xl'],
    ['2xl', 'panel-portrait:max-w-4xl'],
    ['5xl', 'panel-portrait:max-w-5xl'],
    ['full', 'panel-portrait:max-w-[min(90vw,1600px)]'],
  ])('maps size=%s to %s', (size, expected) => {
    const wrapper = mountModal({ size })
    const panel = getModalPanel()
    expect(panel.className).toContain('max-w-none')
    expect(panel.className).toContain(expected)
    wrapper.unmount()
  })

  it('lets the panel grow and scroll as a whole by default', () => {
    const wrapper = mountModal()
    const panel = getModalPanel()
    expect(panel.className).toContain('h-dvh')
    expect(panel.className).toContain('panel-portrait:max-h-[90vh]')
    expect(panel.className).toContain('overflow-y-auto')
    expect(panel.className).not.toContain('overflow-hidden')
    wrapper.unmount()
  })

  it('pins the panel to a non-scrolling 90vh column with fullHeight', () => {
    // The slot owns the scroll in this mode (fixed header/footer + panes that
    // scroll on their own); a scrollbar on the panel would nest inside theirs.
    const wrapper = mountModal({ fullHeight: true })
    const panel = getModalPanel()
    expect(panel.className).toContain('h-dvh')
    expect(panel.className).toContain('panel-portrait:h-[90vh]')
    expect(panel.className).toContain('overflow-hidden')
    expect(panel.className).toContain('flex flex-col')
    expect(panel.className).not.toContain('overflow-y-auto')
    wrapper.unmount()
  })

  it('uses the surface token for the modal panel background', () => {
    const wrapper = mountModal()
    const panel = getModalPanel()
    expect(panel.className).toContain('bg-surface')
    wrapper.unmount()
  })

  it('applies a local theme to teleported public content', () => {
    const wrapper = mountModal({ theme: 'dark' })
    const dialog = document.body.querySelector('[role="dialog"]')

    expect(dialog.getAttribute('data-theme')).toBe('dark')
    wrapper.unmount()
  })

  it('uses the semantic modal kind as the width source of truth', () => {
    const wrapper = mountModal({ kind: 'form', size: 'sm' })
    const panel = getModalPanel()
    expect(panel.className).toContain('max-w-none')
    expect(panel.className).toContain('panel-portrait:max-w-2xl')
    expect(panel.className).not.toContain('panel-portrait:max-w-sm')
    expect(panel.getAttribute('data-modal-kind')).toBe('form')
    wrapper.unmount()
  })

  it.each([
    ['confirm', 'panel-portrait:max-w-md'],
    ['form', 'panel-portrait:max-w-2xl'],
    ['form-wide', 'panel-portrait:max-w-5xl'],
    ['wizard', 'panel-portrait:max-w-7xl'],
    ['detail', 'panel-portrait:max-w-5xl'],
    ['workspace', 'panel-portrait:max-w-[min(90vw,100rem)]'],
  ])('maps semantic kind=%s to %s', (kind, expected) => {
    const wrapper = mountModal({ kind })
    const panel = getModalPanel()
    expect(panel.className).toContain(expected)
    expect(panel.getAttribute('data-modal-kind')).toBe(kind)
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
    const panel = getModalPanel()
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
    const panel = getModalPanel()
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
