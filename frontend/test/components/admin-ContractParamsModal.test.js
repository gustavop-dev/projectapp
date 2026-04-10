import { mount } from '@vue/test-utils';

global.useProposalStore = jest.fn(() => ({
  fetchCompanySettings: jest.fn().mockResolvedValue({ success: true, data: {} }),
}));

global.useMarkdownPreview = jest.fn(() => ({
  parseMarkdown: jest.fn((val) => val),
}));

jest.mock('dompurify', () => ({ sanitize: jest.fn((val) => val) }));

import ContractParamsModal from '../../components/BusinessProposal/admin/ContractParamsModal.vue';

function mountContractParamsModal(props = {}) {
  return mount(ContractParamsModal, {
    props: {
      visible: true,
      proposal: { client_name: 'Acme Corp', client_email: 'client@acme.com' },
      initialParams: {},
      isEditing: false,
      saving: false,
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

describe('ContractParamsModal', () => {
  it('renders the modal form when visible', () => {
    const wrapper = mountContractParamsModal();

    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('shows "Generar contrato" heading when not editing', () => {
    const wrapper = mountContractParamsModal({ isEditing: false });

    expect(wrapper.text()).toContain('Generar contrato de desarrollo');
  });

  it('shows "Editar contrato" heading when isEditing is true', () => {
    const wrapper = mountContractParamsModal({ isEditing: true });

    expect(wrapper.text()).toContain('Editar contrato de desarrollo');
  });

  it('emits cancel when cancel button is clicked', async () => {
    const wrapper = mountContractParamsModal();

    const cancelBtn = wrapper.findAll('button').find(b => b.text() === 'Cancelar');
    await cancelBtn.trigger('click');

    expect(wrapper.emitted('cancel')).toBeTruthy();
  });

  it('switches to custom contract mode when custom button is clicked', async () => {
    const wrapper = mountContractParamsModal();

    const customBtn = wrapper.findAll('button').find(b => b.text() === 'Contrato personalizado');
    await customBtn.trigger('click');

    expect(wrapper.text()).toContain('Contenido del contrato (Markdown)');
  });

  it('does not render form when visible is false', () => {
    const wrapper = mountContractParamsModal({ visible: false });

    expect(wrapper.find('form').exists()).toBe(false);
  });
});
