import { flushPromises, mount } from '@vue/test-utils';
import ContractTermsDocument from '../../components/BusinessProposal/ContractTermsDocument.vue';

const terms = {
  title: 'Contrato de prestación de servicios',
  preamble_markdown: 'Texto introductorio.',
  clauses: [
    {
      id: 'clause-01',
      number: 1,
      title: 'CLÁUSULA PRIMERA — OBJETO',
      content_markdown: 'Contenido de la cláusula.',
    },
  ],
};

const global = {
  stubs: {
    BaseBadge: { template: '<span><slot /></span>' },
    BaseButton: { template: '<button><slot /></button>' },
    DocumentMarkdownBody: {
      props: ['markdown'],
      template: '<div>{{ markdown }}</div>',
    },
  },
};

describe('ContractTermsDocument', () => {
  it('renders each clause with its stable anchor', () => {
    const wrapper = mount(ContractTermsDocument, { props: { terms }, global });

    expect(wrapper.get('#clause-01').text()).toContain('CLÁUSULA PRIMERA — OBJETO');
  });

  it('renders the masked contract content inside a document surface', () => {
    const wrapper = mount(ContractTermsDocument, { props: { terms }, global });
    const paper = wrapper.get('[data-testid="contract-paper"]');

    expect(paper.attributes('role')).toBe('document');
    expect(paper.attributes('aria-label')).toBe('Contrato de prestación de servicios');
    expect(paper.text()).toContain('Contenido de la cláusula.');
  });

  it('emits ready after clauses mount', async () => {
    const wrapper = mount(ContractTermsDocument, { props: { terms }, global });

    await flushPromises();

    expect(wrapper.emitted('ready')).toHaveLength(1);
  });

  it('emits retry from the unavailable state', async () => {
    const wrapper = mount(ContractTermsDocument, {
      props: { error: 'unavailable' },
      global,
    });

    await wrapper.get('button').trigger('click');

    expect(wrapper.emitted('retry')).toHaveLength(1);
  });
});
