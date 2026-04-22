import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import ConfirmModal from '../../components/ConfirmModal.vue';

function mountModal(props = {}) {
  return mount(ConfirmModal, {
    props: {
      modelValue: true,
      title: 'Eliminar elemento',
      message: 'Esta acción no se puede deshacer.',
      confirmText: 'Eliminar',
      cancelText: 'Cancelar',
      variant: 'warning',
      ...props,
    },
    global: {
      stubs: {
        Teleport: true,
        Transition: false,
      },
    },
  });
}

describe('ConfirmModal', () => {
  afterEach(() => {
    document.body.style.overflow = '';
  });

  it('renders title, message, and action labels', () => {
    const wrapper = mountModal();

    expect(wrapper.text()).toContain('Eliminar elemento');
    expect(wrapper.text()).toContain('Esta acción no se puede deshacer.');
    expect(wrapper.text()).toContain('Eliminar');
    expect(wrapper.text()).toContain('Cancelar');
  });

  it('emits confirm and closes when the confirm button is clicked', async () => {
    const wrapper = mountModal();

    await wrapper.findAll('button')[1].trigger('click');

    expect(wrapper.emitted('confirm')).toEqual([[]]);
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
  });

  it('emits cancel and closes when the cancel button is clicked', async () => {
    const wrapper = mountModal();

    await wrapper.find('button').trigger('click');

    expect(wrapper.emitted('cancel')).toEqual([[]]);
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
  });

  it('emits cancel when the backdrop is clicked', async () => {
    const wrapper = mountModal();

    await wrapper.get('.fixed.inset-0').trigger('click');

    expect(wrapper.emitted('cancel')).toEqual([[]]);
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
  });

  it('closes on Escape only while the modal is open', async () => {
    const wrapper = mountModal();

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await nextTick();

    expect(wrapper.emitted('cancel')).toEqual([[]]);

    const closedWrapper = mountModal({ modelValue: false });
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await nextTick();

    expect(closedWrapper.emitted('cancel')).toBeUndefined();
  });

  it('locks body scroll while open and restores it when closed or unmounted', async () => {
    const wrapper = mountModal({ modelValue: false });
    await wrapper.setProps({ modelValue: true });
    await nextTick();

    expect(document.body.style.overflow).toBe('hidden');

    await wrapper.setProps({ modelValue: false });
    await nextTick();
    expect(document.body.style.overflow).toBe('');

    await wrapper.setProps({ modelValue: true });
    await nextTick();
    wrapper.unmount();
    expect(document.body.style.overflow).toBe('');
  });

  it('renders the correct variant classes for danger and info', () => {
    const dangerWrapper = mountModal({ variant: 'danger' });
    const infoWrapper = mountModal({ variant: 'info' });

    expect(dangerWrapper.html()).toContain('bg-red-600');
    expect(infoWrapper.html()).toContain('bg-esmerald');
  });

  it('falls back to warning styles when the variant is unknown', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    const wrapper = mountModal({ variant: 'unexpected' });

    expect(wrapper.html()).toContain('bg-lemon/30');
    warnSpy.mockRestore();
  });

  describe('requireTypeText', () => {
    it('renders the type-to-confirm input when requireTypeText is set', () => {
      const wrapper = mountModal({ requireTypeText: 'DELETE' });

      const input = wrapper.find('[data-testid="confirm-type-input"]');
      expect(input.exists()).toBe(true);
    });

    it('disables the confirm button until the typed value matches exactly', async () => {
      const wrapper = mountModal({ requireTypeText: 'DELETE' });

      const confirmBtn = wrapper.find('[data-testid="confirm-modal-confirm"]');
      expect(confirmBtn.attributes('disabled')).toBeDefined();

      const input = wrapper.find('[data-testid="confirm-type-input"]');
      await input.setValue('delete');
      expect(confirmBtn.attributes('disabled')).toBeDefined();

      await input.setValue('DELETE');
      expect(confirmBtn.attributes('disabled')).toBeUndefined();

      await confirmBtn.trigger('click');
      expect(wrapper.emitted('confirm')).toEqual([[]]);
    });

    it('does not emit confirm when clicking while disabled', async () => {
      const wrapper = mountModal({ requireTypeText: 'DELETE' });

      await wrapper.find('[data-testid="confirm-modal-confirm"]').trigger('click');
      expect(wrapper.emitted('confirm')).toBeUndefined();
    });

    it('clears the typed value when the modal reopens', async () => {
      const wrapper = mountModal({ modelValue: false, requireTypeText: 'DELETE' });
      await wrapper.setProps({ modelValue: true });
      await nextTick();

      const input = wrapper.find('[data-testid="confirm-type-input"]');
      await input.setValue('DELETE');
      expect(input.element.value).toBe('DELETE');

      await wrapper.setProps({ modelValue: false });
      await nextTick();
      await wrapper.setProps({ modelValue: true });
      await nextTick();

      expect(wrapper.find('[data-testid="confirm-type-input"]').element.value).toBe('');
    });
  });

  describe('hideCancel', () => {
    it('hides the cancel button when hideCancel is true', () => {
      const wrapper = mountModal({ hideCancel: true });

      const buttons = wrapper.findAll('button').filter((b) => b.text() === 'Cancelar');
      expect(buttons.length).toBe(0);
    });

    it('still shows the confirm button when hideCancel is true', () => {
      const wrapper = mountModal({ hideCancel: true });

      expect(wrapper.find('[data-testid="confirm-modal-confirm"]').exists()).toBe(true);
    });
  });
});
