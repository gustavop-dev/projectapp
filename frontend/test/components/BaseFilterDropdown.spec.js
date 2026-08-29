import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

import BaseActionIcon from '../../components/base/BaseActionIcon.vue';
import BaseButton from '../../components/base/BaseButton.vue';
import BaseFilterDropdown from '../../components/base/BaseFilterDropdown.vue';
import BaseInput from '../../components/base/BaseInput.vue';

let outsideHandler = null;
jest.mock('@vueuse/core', () => ({
  onClickOutside: jest.fn((_target, handler) => { outsideHandler = handler; }),
}));

const options = [
  { value: 'draft', label: 'Borrador', count: 3 },
  { value: 'sent', label: 'Enviado', count: 8 },
  { value: 'received', label: 'Recibido', count: 5 },
];

function mountDropdown(props = {}) {
  outsideHandler = null;
  return mount(BaseFilterDropdown, {
    props: {
      label: 'Estado del mensaje',
      options,
      modelValue: [],
      ...props,
    },
    global: {
      components: { BaseActionIcon, BaseButton, BaseInput },
      stubs: { NuxtLink: { template: '<a><slot /></a>' } },
    },
  });
}

describe('BaseFilterDropdown', () => {
  it('shows searchable options with their result counts', async () => {
    const wrapper = mountDropdown();

    await wrapper.get('button').trigger('click');

    expect(wrapper.text()).toContain('Borrador');
    expect(wrapper.text()).toContain('3');
    expect(wrapper.get('input[type="text"]').attributes('aria-label'))
      .toBe('Buscar en Estado del mensaje');
  });

  it('filters options without changing the active selection', async () => {
    const wrapper = mountDropdown({ modelValue: ['sent'] });
    await wrapper.get('button').trigger('click');

    await wrapper.get('input[type="text"]').setValue('reci');

    expect(wrapper.text()).toContain('Recibido');
    expect(wrapper.text()).not.toContain('Borrador');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
  });

  it('clears all selected values from the footer', async () => {
    const wrapper = mountDropdown({ modelValue: ['draft', 'sent'] });
    await wrapper.get('button').trigger('click');

    const clear = wrapper.findAll('button').find((button) => button.text() === 'Limpiar');
    await clear.trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[[]]]);
  });

  it('closes on Escape and on an outside click', async () => {
    const wrapper = mountDropdown();
    await wrapper.get('button').trigger('click');
    await wrapper.get('[role="dialog"]').trigger('keydown', { key: 'Escape' });
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);

    await wrapper.get('button').trigger('click');
    outsideHandler();
    await nextTick();
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
  });
});
