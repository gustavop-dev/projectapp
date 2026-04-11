import { mount } from '@vue/test-utils';

global.useProposalStore = jest.fn(() => ({
  sendDocumentsToClient: jest.fn().mockResolvedValue({ success: true }),
}));

import SendDocumentsModal from '../../components/BusinessProposal/admin/SendDocumentsModal.vue';

const baseProposal = {
  id: 1,
  client_name: 'Test Client',
  client_email: 'client@test.com',
  public_url: 'https://example.com/proposal/abc',
};

function mountSendDocumentsModal(props = {}) {
  return mount(SendDocumentsModal, {
    props: {
      visible: true,
      proposal: baseProposal,
      selectedMainDocs: ['commercial'],
      selectedAdditionalDocs: [],
      ...props,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('SendDocumentsModal', () => {
  it('renders modal content when visible', () => {
    const wrapper = mountSendDocumentsModal();

    expect(wrapper.text()).toContain('Enviar documentos al cliente');
  });

  it('shows recipient email in header', () => {
    const wrapper = mountSendDocumentsModal();

    expect(wrapper.text()).toContain('client@test.com');
  });

  it('renders preview tab by default', () => {
    const wrapper = mountSendDocumentsModal();

    // Preview tab is active by default
    expect(wrapper.text()).toContain('Vista previa');
  });

  it('shows the send button', () => {
    const wrapper = mountSendDocumentsModal();

    const sendBtn = wrapper.findAll('button').find(b => b.text().includes('Enviar documentos'));
    expect(sendBtn).toBeTruthy();
  });

  it('emits cancel when cancel button is clicked', async () => {
    const wrapper = mountSendDocumentsModal();

    const cancelBtn = wrapper.findAll('button').find(b => b.text() === 'Cancelar');
    await cancelBtn.trigger('click');

    expect(wrapper.emitted('cancel')).toBeTruthy();
  });

  it('does not render when visible is false', () => {
    const wrapper = mountSendDocumentsModal({ visible: false });

    expect(wrapper.find('h2').exists()).toBe(false);
  });
});
