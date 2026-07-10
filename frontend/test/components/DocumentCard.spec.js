import { mount, flushPromises } from '@vue/test-utils'
import DocumentCard from '../../components/panel/documents/DocumentCard.vue'

const NuxtLink = {
  name: 'NuxtLink',
  props: ['to'],
  template: '<a :href="typeof to === \'string\' ? to : \'#\'"><slot /></a>',
}

const BaseTooltip = {
  name: 'BaseTooltip',
  props: ['text'],
  template: '<span :data-tooltip="text"><slot /></span>',
}

const baseDocument = {
  id: 7,
  title: 'Contrato de Servicios',
  status: 'published',
  client_name: 'ACME Corp',
  created_at: '2026-03-01T10:00:00Z',
  content_excerpt: '# Contrato\n\nAlcance con **términos**.',
  tag_details: [
    { id: 1, name: 'Legal', color: 'blue' },
    { id: 2, name: 'Cliente', color: 'green' },
    { id: 3, name: 'Interno', color: 'red' },
  ],
}

async function mountCard(props = {}) {
  const wrapper = mount(DocumentCard, {
    props: { document: baseDocument, editTo: '/panel/documents/7/edit', ...props },
    global: { components: { NuxtLink, BaseTooltip } },
  })
  await flushPromises() // DOMPurify dynamic import inside DocumentMarkdownBody
  return wrapper
}

describe('DocumentCard', () => {
  it('renders title, status, meta and mini-preview', async () => {
    const wrapper = await mountCard()

    expect(wrapper.text()).toContain('Contrato de Servicios')
    expect(wrapper.text()).toContain('Publicado')
    expect(wrapper.text()).toContain('ACME Corp')
    expect(wrapper.html()).toContain('markdown-preview--mini')
    expect(wrapper.text()).toContain('Alcance con')
  })

  it('renders the title as a link to the edit page', async () => {
    const wrapper = await mountCard()
    const link = wrapper.find('a[href="/panel/documents/7/edit"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Contrato de Servicios')
  })

  it('shows at most two tag chips plus a +N tooltip with the rest', async () => {
    const wrapper = await mountCard()

    expect(wrapper.text()).toContain('Legal')
    expect(wrapper.text()).toContain('Cliente')
    expect(wrapper.text()).not.toContain('Interno')
    expect(wrapper.text()).toContain('+1')
    expect(wrapper.find('[data-tooltip="Interno"]').exists()).toBe(true)
  })

  it('emits open on card click and action on the kebab', async () => {
    const wrapper = await mountCard()

    await wrapper.trigger('click')
    expect(wrapper.emitted('open')).toHaveLength(1)

    await wrapper.find('button[title="Acciones"]').trigger('click')
    expect(wrapper.emitted('action')).toHaveLength(1)
    // The kebab click must not also open the card.
    expect(wrapper.emitted('open')).toHaveLength(1)
  })

  it('exposes an accessible name for the kebab', async () => {
    const wrapper = await mountCard()
    const kebab = wrapper.find('button[title="Acciones"]')
    expect(kebab.attributes('aria-label')).toBe('Acciones de Contrato de Servicios')
  })

  it('emits dragstart/dragend and dims while dragging', async () => {
    const wrapper = await mountCard({ dragging: true })

    expect(wrapper.classes()).toContain('opacity-50')
    await wrapper.trigger('dragstart')
    await wrapper.trigger('dragend')
    expect(wrapper.emitted('dragstart')).toHaveLength(1)
    expect(wrapper.emitted('dragend')).toHaveLength(1)
  })

  it('shows a placeholder when there is no excerpt', async () => {
    const wrapper = await mountCard({
      document: { ...baseDocument, content_excerpt: '', tag_details: [] },
    })
    expect(wrapper.html()).not.toContain('markdown-preview--mini')
    expect(wrapper.text()).toContain('—')
  })
})
