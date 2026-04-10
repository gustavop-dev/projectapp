import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

jest.mock('vue3-emoji-picker', () => ({
  __esModule: true,
  default: { name: 'EmojiPicker', template: '<div class="emoji-picker-stub" />' },
}));

jest.mock('vue3-emoji-picker/css', () => {}, { virtual: true });

import EmojiIconField from '../../components/BusinessProposal/admin/EmojiIconField.vue';

function mountField(props = {}) {
  return mount(EmojiIconField, {
    props: { modelValue: '', label: '', ...props },
    global: { stubs: { Teleport: true, EmojiPicker: true } },
  });
}

describe('EmojiIconField', () => {
  it('renders the label when provided', () => {
    const wrapper = mountField({ label: 'Icono de sección' });

    expect(wrapper.text()).toContain('Icono de sección');
  });

  it('renders the input with the current modelValue', () => {
    const wrapper = mountField({ modelValue: '🎨' });

    expect(wrapper.find('input').element.value).toBe('🎨');
  });

  it('emits update:modelValue when the input changes', async () => {
    const wrapper = mountField({ modelValue: '' });

    await wrapper.find('input').setValue('🚀');

    expect(wrapper.emitted('update:modelValue')).toBeTruthy();
    expect(wrapper.emitted('update:modelValue')[0][0]).toBe('🚀');
  });

  it('shows the overlay backdrop when the emoji button is clicked', async () => {
    const wrapper = mountField();

    await wrapper.find('button').trigger('click');
    await nextTick();

    // The v-if="showPicker" overlay div is rendered when picker is open
    const html = wrapper.html();
    expect(html).toContain('z-[9998]');
  });
});
