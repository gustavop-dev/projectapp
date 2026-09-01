import { mount } from '@vue/test-utils'
import CatalogSelectionModal from '../../components/AdditionalModules/CatalogSelectionModal.vue'
import BaseCheckbox from '../../components/base/BaseCheckbox.vue'
import BaseFormField from '../../components/base/BaseFormField.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BaseSegmented from '../../components/base/BaseSegmented.vue'
import BaseSelect from '../../components/base/BaseSelect.vue'

global.useI18n = jest.fn(() => ({
  t: (key, params = {}) => `${key}${params.count === undefined ? '' : `:${params.count}`}`,
}))

const category = {
  id: 1,
  is_active: true,
  name_es: 'Comercio',
  name_en: 'Commerce',
}
const moduleItem = {
  id: 7,
  category: 1,
  is_active: true,
  icon: '📅',
  name_es: 'Agenda',
  name_en: 'Scheduling',
}

function mountModal() {
  return mount(CatalogSelectionModal, {
    props: {
      modelValue: false,
      mode: 'pdf',
      categories: [category],
      modules: [moduleItem],
      clients: [{ id: 3, name: 'Acme', company: 'Colombia', email: 'acme@example.com' }],
    },
    global: {
      components: { BaseCheckbox, BaseFormField, BaseInput, BaseSegmented, BaseSelect },
      stubs: {
        BaseAlert: { template: '<div role="alert"><slot /></div>' },
        BaseButton: { template: '<button v-bind="$attrs" type="button"><slot /></button>' },
        BaseModal: {
          props: ['modelValue'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
      },
    },
  })
}

describe('AdditionalModulesCatalogSelectionModal', () => {
  it('autofills the optional PDF recipient from a selected client', async () => {
    const wrapper = mountModal()
    await wrapper.setProps({ modelValue: true })

    await wrapper.get('[data-testid="additional-share-client"]').setValue('3')
    await wrapper.get('[data-testid="additional-selection-submit"]').trigger('click')

    expect(wrapper.emitted('submit')).toEqual([[{
      language: 'es',
      module_ids: [7],
      recipient_label: 'Acme · Colombia',
    }]])
  })

  it('submits English after an explicit language choice', async () => {
    const wrapper = mountModal()
    await wrapper.setProps({ modelValue: true })

    await wrapper.get('[data-testid="additional-selection-language-en"]').trigger('click')
    await wrapper.get('[data-testid="additional-selection-submit"]').trigger('click')

    expect(wrapper.emitted('submit')).toEqual([[{
      language: 'en',
      module_ids: [7],
      recipient_label: '',
    }]])
  })
})
