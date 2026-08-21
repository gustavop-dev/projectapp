import { mount } from '@vue/test-utils';
import ContractTermsOverview from '../../components/BusinessProposal/ContractTermsOverview.vue';

const terms = {
  clauses: [
    { id: 'clause-01', number: 1, title: 'CLÁUSULA PRIMERA — OBJETO' },
    { id: 'clause-02', number: 2, title: 'CLÁUSULA SEGUNDA — PAGOS' },
  ],
};

const global = {
  stubs: {
    BaseBadge: { template: '<span><slot /></span>' },
    BaseAlert: { template: '<div><slot /></div>' },
    BaseButton: { template: '<button><slot /></button>' },
  },
};

describe('ContractTermsOverview', () => {
  it('renders every clause from the global contract', () => {
    const wrapper = mount(ContractTermsOverview, {
      props: { terms },
      global,
    });

    expect(wrapper.text()).toContain('CLÁUSULA PRIMERA — OBJETO');
    expect(wrapper.text()).toContain('CLÁUSULA SEGUNDA — PAGOS');
  });

  it('omits the duplicate draft download action', () => {
    const wrapper = mount(ContractTermsOverview, { props: { terms }, global });

    expect(wrapper.text()).not.toContain('Descargar borrador');
    expect(wrapper.find('[data-testid="contract-draft-download"]').exists()).toBe(false);
  });

  it('emits the selected clause id', async () => {
    const wrapper = mount(ContractTermsOverview, { props: { terms }, global });

    await wrapper.get('[data-testid="contract-clause-link-clause-02"]').trigger('click');

    expect(wrapper.emitted('navigate')).toEqual([['clause-02']]);
  });

  it('renders the loading message while content is pending', () => {
    const wrapper = mount(ContractTermsOverview, {
      props: { loading: true },
      global,
    });

    expect(wrapper.text()).toContain('Preparando el borrador del contrato');
  });

  it('emits retry from the unavailable state', async () => {
    const wrapper = mount(ContractTermsOverview, {
      props: { error: 'unavailable' },
      global,
    });

    await wrapper.get('[data-testid="contract-terms-retry"]').trigger('click');

    expect(wrapper.emitted('retry')).toHaveLength(1);
  });
});
