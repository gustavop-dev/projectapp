import { mount } from '@vue/test-utils'
import HostingActionsModal from '~/components/accounting/HostingActionsModal.vue'

const RECORD = {
  id: 8,
  domain_url: 'acme.co',
  client_name: 'Acme',
  billing_email: 'tesoreria@acme.co',
}

function mountModal(record = RECORD, props = {}) {
  return mount(HostingActionsModal, {
    props: { open: true, record, ...props },
    global: {
      stubs: {
        BaseModal: {
          props: ['modelValue', 'kind'],
          emits: ['close'],
          template: '<div><slot /></div>',
        },
        BaseButton: {
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  })
}

describe('HostingActionsModal', () => {
  it('keeps the five row actions in one touch menu', () => {
    const wrapper = mountModal()

    expect(wrapper.findAll('[data-testid^="hosting-"]')
      .map((node) => node.attributes('data-testid'))).toEqual(expect.arrayContaining([
      'hosting-cycles-8',
      'hosting-send-billing-8',
      'hosting-emails-8',
      'hosting-edit-8',
      'hosting-delete-8',
    ]))
  })

  it('explains why billing is unavailable when the hosting has no email', () => {
    const wrapper = mountModal({ ...RECORD, billing_email: '' })
    const action = wrapper.get('[data-testid="hosting-send-billing-8"]')

    expect(action.attributes('disabled')).toBe('')
    expect(action.text()).toContain('Vincula un cliente con correo')
  })

  it('locks billing while the request is in flight', () => {
    const wrapper = mountModal(RECORD, { billingBusy: true })

    expect(wrapper.get('[data-testid="hosting-send-billing-8"]')
      .attributes('disabled')).toBe('')
  })

  it('emits the selected action with the hosting and closes the menu', async () => {
    const wrapper = mountModal()

    await wrapper.get('[data-testid="hosting-cycles-8"]').trigger('click')

    expect(wrapper.emitted('cycles')[0]).toEqual([RECORD])
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
})
