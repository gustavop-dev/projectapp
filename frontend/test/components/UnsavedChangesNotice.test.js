import { mount } from '@vue/test-utils';
import UnsavedChangesNotice from '~/components/panel/UnsavedChangesNotice.vue';

function mountNotice(props = {}) {
  return mount(UnsavedChangesNotice, {
    props: { title: 'Cliente y proyecto sin guardar', ...props },
    global: {
      stubs: {
        BaseAlert: {
          props: ['variant', 'title'],
          template: '<div :data-variant="variant"><p>{{ title }}</p><slot /></div>',
        },
        BaseButton: {
          props: ['variant', 'size', 'disabled', 'loading'],
          // `emits` declarado para que el @click del padre no caiga TAMBIÉN
          // como listener nativo y dispare el handler dos veces.
          emits: ['click'],
          template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
}

describe('UnsavedChangesNotice', () => {
  it('names the unsaved fields in the alert title', () => {
    const wrapper = mountNotice();

    expect(wrapper.text()).toContain('Cliente y proyecto sin guardar');
  });

  it('reads as a warning rather than an invitation', () => {
    const wrapper = mountNotice();

    expect(wrapper.get('[data-variant]').attributes('data-variant')).toBe('warning');
  });

  it('spells out the full list only when one is supplied', () => {
    const withoutDetail = mountNotice();
    expect(withoutDetail.find('[data-testid="unsaved-changes-notice-detail"]').exists()).toBe(false);

    const withDetail = mountNotice({
      title: '4 campos sin guardar',
      detail: 'Título, cliente, proyecto e idioma.',
    });
    expect(withDetail.get('[data-testid="unsaved-changes-notice-detail"]').text())
      .toBe('Título, cliente, proyecto e idioma.');
  });

  it('asks to save and to discard', async () => {
    const wrapper = mountNotice();

    await wrapper.get('[data-testid="unsaved-changes-notice-save"]').trigger('click');
    await wrapper.get('[data-testid="unsaved-changes-notice-discard"]').trigger('click');

    expect(wrapper.emitted('save')).toHaveLength(1);
    expect(wrapper.emitted('discard')).toHaveLength(1);
  });

  // Una cuenta de cobro emitida no se puede guardar: ofrecerlo enseñaría a
  // desconfiar del aviso, porque el backend responde 400.
  it('hides the save action when saving is blocked', () => {
    const wrapper = mountNotice({ canSave: false });

    expect(wrapper.find('[data-testid="unsaved-changes-notice-save"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="unsaved-changes-notice-discard"]').exists()).toBe(true);
  });

  it('blocks discarding while a save is in flight', () => {
    const wrapper = mountNotice({ saving: true });

    expect(wrapper.get('[data-testid="unsaved-changes-notice-discard"]').attributes('disabled'))
      .toBeDefined();
  });

  it('takes a page-specific testid so several notices stay addressable', () => {
    const wrapper = mountNotice({ testid: 'doc-unsaved-notice' });

    expect(wrapper.find('[data-testid="doc-unsaved-notice-save"]').exists()).toBe(true);
  });
});
