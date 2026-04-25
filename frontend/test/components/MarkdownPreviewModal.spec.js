import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import MarkdownPreviewModal from '../../components/panel/documents/MarkdownPreviewModal.vue';

function mountModal(props = {}, slots = {}) {
  return mount(MarkdownPreviewModal, {
    props: { modelValue: true, title: 'Vista previa', ...props },
    slots,
    global: {
      stubs: { Teleport: true, Transition: false },
    },
    attachTo: document.body,
  });
}

describe('MarkdownPreviewModal', () => {
  afterEach(() => {
    document.body.style.overflow = '';
  });

  it('renders slot content when modelValue is true', () => {
    const wrapper = mountModal({ modelValue: true }, { default: '<p data-testid="slot-content">Contenido</p>' });

    expect(wrapper.find('[data-testid="slot-content"]').exists()).toBe(true);
    wrapper.unmount();
  });

  it('does not render modal content when modelValue is false', () => {
    const wrapper = mountModal({ modelValue: false }, { default: '<p data-testid="slot-content">Contenido</p>' });

    expect(wrapper.find('[data-testid="slot-content"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it('close button emits update:modelValue with false', async () => {
    const wrapper = mountModal();

    await wrapper.find('button[aria-label="Cerrar vista previa"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    wrapper.unmount();
  });

  it('backdrop click emits update:modelValue with false', async () => {
    const wrapper = mountModal();

    await wrapper.find('.fixed.inset-0').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    wrapper.unmount();
  });

  it('ESC keydown emits update:modelValue with false after modal opens', async () => {
    const wrapper = mountModal({ modelValue: false });
    await wrapper.setProps({ modelValue: true });
    await nextTick();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    wrapper.unmount();
  });

  it('non-ESC keydown does not emit', async () => {
    const wrapper = mountModal({ modelValue: false });
    await wrapper.setProps({ modelValue: true });
    await nextTick();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    await nextTick();

    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    wrapper.unmount();
  });

  it('displays title prop in modal header', () => {
    const wrapper = mountModal({ title: 'Mi Documento' });

    expect(wrapper.find('h3').text()).toBe('Mi Documento');
    wrapper.unmount();
  });

  it('adds overflow:hidden to document.body when modelValue becomes true', async () => {
    const wrapper = mountModal({ modelValue: false });

    await wrapper.setProps({ modelValue: true });
    await nextTick();

    expect(document.body.style.overflow).toBe('hidden');
    wrapper.unmount();
  });

  it('restores body overflow to empty string when modelValue becomes false', async () => {
    const wrapper = mountModal({ modelValue: true });
    await nextTick();

    await wrapper.setProps({ modelValue: false });
    await nextTick();

    expect(document.body.style.overflow).toBe('');
    wrapper.unmount();
  });

  it('removes keydown listener and restores body overflow on unmount', async () => {
    const wrapper = mountModal({ modelValue: true });
    await nextTick();

    wrapper.unmount();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await nextTick();

    expect(document.body.style.overflow).toBe('');
  });
});
