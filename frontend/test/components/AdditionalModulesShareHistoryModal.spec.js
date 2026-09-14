import { mount } from '@vue/test-utils'

import BaseToggle from '../../components/base/BaseToggle.vue'
import ShareHistoryModal from '../../components/AdditionalModules/ShareHistoryModal.vue'

global.useI18n = jest.fn(() => ({
  t: (key, params = {}) => `${key}${params.label ? `:${params.label}` : ''}`,
  locale: { value: 'es-co' },
}))

const link = (overrides = {}) => ({
  uuid: '11111111-1111-4111-8111-111111111111',
  recipient_label: 'Cliente Acme',
  client_name: '',
  language: 'es',
  is_active: true,
  show_explainer_video: true,
  view_count: 0,
  selected_modules: [{ id: 7, name_es: 'Agenda', name_en: 'Scheduling' }],
  public_path: '/es-co/additional-modules/share/11111111-1111-4111-8111-111111111111',
  created_at: '2026-09-14T10:00:00Z',
  first_viewed_at: null,
  last_viewed_at: null,
  ...overrides,
})

const hiddenVideoLink = link({
  uuid: '22222222-2222-4222-8222-222222222222',
  recipient_label: 'Cliente Beta',
  show_explainer_video: false,
})

function mountHistory(props = {}) {
  return mount(ShareHistoryModal, {
    props: { modelValue: true, links: [link(), hiddenVideoLink], ...props },
    global: {
      components: { BaseToggle },
      stubs: {
        BaseModal: { props: ['modelValue'], template: '<div v-if="modelValue"><slot /></div>' },
        BaseAlert: { template: '<div role="status"><slot /></div>' },
        BaseBadge: { template: '<span><slot /></span>' },
        BaseEmptyState: { props: ['title'], template: '<p>{{ title }}</p>' },
        NuxtLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

const toggleOf = (wrapper, uuid) => wrapper.get(`[data-testid="additional-share-history-video-toggle-${uuid}"]`)

describe('AdditionalModulesShareHistoryModal explainer video', () => {
  it('shows each link with its own video switch state', () => {
    const wrapper = mountHistory()

    expect(toggleOf(wrapper, link().uuid).attributes('aria-checked')).toBe('true')
    expect(toggleOf(wrapper, hiddenVideoLink.uuid).attributes('aria-checked')).toBe('false')
    expect(toggleOf(wrapper, link().uuid).attributes('aria-label'))
      .toBe('additionalModules.shareVideoToggleAria:Cliente Acme')
  })

  it('asks to hide the video for that link only', async () => {
    const wrapper = mountHistory()

    await toggleOf(wrapper, link().uuid).trigger('click')

    expect(wrapper.emitted('video')).toEqual([[{ link: link(), value: false }]])
  })

  it('explains that no link shows the video while the catalog hides it', () => {
    const visible = mountHistory()
    const hidden = mountHistory({ catalogVideoVisible: false })

    expect(visible.find('[data-testid="additional-share-history-video-catalog-off"]').exists()).toBe(false)
    expect(hidden.get('[data-testid="additional-share-history-video-catalog-off"]').text())
      .toContain('additionalModules.shareVideoCatalogOff')
  })
})
