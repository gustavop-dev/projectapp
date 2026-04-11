import { mount } from '@vue/test-utils';
import { computed } from 'vue';

// SyncPreviewModal uses `computed` via Nuxt auto-import without explicit import
global.computed = computed;

import SyncPreviewModal from '../../components/BusinessProposal/admin/SyncPreviewModal.vue';

const baseDiff = {
  epics: {
    to_create: [{ epicKey: 'E-1', title: 'Login module' }],
    to_update: [],
    to_delete: [],
  },
  requirements: {
    to_create: [],
    to_update: [],
    to_delete: [],
  },
};

function mountSyncPreviewModal(props = {}) {
  return mount(SyncPreviewModal, {
    props: {
      visible: true,
      projectInfo: { name: 'Web App', client_email: 'client@test.com' },
      deliverableInfo: { title: 'Sprint 1' },
      diff: baseDiff,
      isApplying: false,
      ...props,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('SyncPreviewModal', () => {
  it('renders modal when visible', () => {
    const wrapper = mountSyncPreviewModal();

    expect(wrapper.text()).toContain('Vista previa de sincronización');
  });

  it('shows project name and email', () => {
    const wrapper = mountSyncPreviewModal();

    expect(wrapper.text()).toContain('Web App');
    expect(wrapper.text()).toContain('client@test.com');
  });

  it('shows new items section when diff has to_create items', () => {
    const wrapper = mountSyncPreviewModal();

    expect(wrapper.text()).toContain('Nuevos');
    expect(wrapper.text()).toContain('Login module');
  });

  it('shows empty state when diff has no changes', () => {
    const emptyDiff = {
      epics: { to_create: [], to_update: [], to_delete: [] },
      requirements: { to_create: [], to_update: [], to_delete: [] },
    };

    const wrapper = mountSyncPreviewModal({ diff: emptyDiff });

    expect(wrapper.text()).toContain('Sin cambios estructurales');
  });

  it('emits confirm when confirm button is clicked', async () => {
    const wrapper = mountSyncPreviewModal();

    const confirmBtn = wrapper.findAll('button').find(b => b.text().includes('Confirmar'));
    await confirmBtn.trigger('click');

    expect(wrapper.emitted('confirm')).toBeTruthy();
  });

  it('emits cancel when cancel button is clicked', async () => {
    const wrapper = mountSyncPreviewModal();

    const cancelBtn = wrapper.findAll('button').find(b => b.text() === 'Cancelar');
    await cancelBtn.trigger('click');

    expect(wrapper.emitted('cancel')).toBeTruthy();
  });
});
