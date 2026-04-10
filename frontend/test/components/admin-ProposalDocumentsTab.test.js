import { mount } from '@vue/test-utils';

global.useProposalStore = jest.fn(() => ({
  uploadAdditionalDocument: jest.fn().mockResolvedValue({ success: true }),
  deleteAdditionalDocument: jest.fn().mockResolvedValue({ success: true }),
}));

import ProposalDocumentsTab from '../../components/BusinessProposal/admin/ProposalDocumentsTab.vue';

const baseProposal = {
  id: 1,
  uuid: 'abc-123',
  client_name: 'Acme Corp',
  client_email: 'client@acme.com',
};

function mountProposalDocumentsTab(props = {}) {
  return mount(ProposalDocumentsTab, {
    props: {
      proposal: baseProposal,
      documents: [],
      ...props,
    },
    global: {
      stubs: {
        SendDocumentsModal: { template: '<div class="send-modal-stub" />' },
      },
    },
  });
}

describe('ProposalDocumentsTab', () => {
  it('renders contract section', () => {
    const wrapper = mountProposalDocumentsTab();

    expect(wrapper.text()).toContain('Contrato de desarrollo');
  });

  it('shows generate contract button when no contract doc exists', () => {
    const wrapper = mountProposalDocumentsTab({ documents: [] });

    expect(wrapper.text()).toContain('Generar contrato');
  });

  it('renders proposal PDFs section', () => {
    const wrapper = mountProposalDocumentsTab();

    expect(wrapper.text()).toContain('PDFs de la propuesta');
  });

  it('renders the send documents section', () => {
    const wrapper = mountProposalDocumentsTab();

    expect(wrapper.text()).toContain('Enviar documentos al cliente');
  });

  it('emits generateContract when generate button is clicked', async () => {
    const wrapper = mountProposalDocumentsTab({ documents: [] });

    const btn = wrapper.findAll('button').find(b => b.text() === 'Generar contrato');
    await btn.trigger('click');

    expect(wrapper.emitted('generateContract')).toBeTruthy();
  });

  it('shows additional document when provided', () => {
    const docs = [
      {
        id: 10,
        document_type: 'amendment',
        document_type_display: 'Otrosí',
        title: 'Otrosí #1',
        file: '/media/osi.pdf',
        is_generated: false,
      },
    ];

    const wrapper = mountProposalDocumentsTab({ documents: docs });

    expect(wrapper.text()).toContain('Otrosí #1');
  });
});
