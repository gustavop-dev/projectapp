import { enableAutoUnmount, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { usePublicDocumentEntrance } from '../../composables/usePublicDocumentEntrance'

enableAutoUnmount(afterEach)

const Document = {
  props: ['sections'],
  setup() {
    const documentRef = ref(null)
    usePublicDocumentEntrance(documentRef)
    return { documentRef }
  },
  template: '<article ref="documentRef"><section v-for="section in sections" :key="section" data-document-enter>{{ section }}</section></article>',
}

describe('public document entrance fallback', () => {
  const originalObserver = global.IntersectionObserver

  afterEach(() => { global.IntersectionObserver = originalObserver })

  it('renders later content when IntersectionObserver is unavailable', async () => {
    global.IntersectionObserver = undefined
    const wrapper = mount(Document, { props: { sections: [] } })

    await wrapper.setProps({ sections: ['Opciones de alianza'] })

    expect(wrapper.text()).toBe('Opciones de alianza')
    expect(wrapper.isVisible()).toBe(true)
  })
})
