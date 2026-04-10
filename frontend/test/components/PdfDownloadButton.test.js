import { mount } from '@vue/test-utils';

global.useProposalStore = jest.fn(() => ({
  currentProposal: {
    uuid: 'test-uuid',
    title: 'Test Proposal',
    client_name: 'Test Client',
    created_at: '2024-01-15T10:00:00Z',
  },
}));

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    blob: () => Promise.resolve(new Blob(['pdf content'], { type: 'application/pdf' })),
  })
);

global.URL.createObjectURL = jest.fn(() => 'blob:test-url');
global.URL.revokeObjectURL = jest.fn();

import PdfDownloadButton from '../../components/BusinessProposal/PdfDownloadButton.vue';

function mountPdfDownloadButton(props = {}) {
  return mount(PdfDownloadButton, { props });
}

describe('PdfDownloadButton', () => {
  it('renders the download button', () => {
    const wrapper = mountPdfDownloadButton();

    expect(wrapper.find('button').exists()).toBe(true);
  });

  it('shows the download icon (not spinner) in idle state', () => {
    const wrapper = mountPdfDownloadButton();

    expect(wrapper.find('.animate-spin').exists()).toBe(false);
  });

  it('has the correct title attribute in idle state', () => {
    const wrapper = mountPdfDownloadButton();

    expect(wrapper.find('button').attributes('title')).toBe('Descargar PDF');
  });

  it('is not disabled in idle state', () => {
    const wrapper = mountPdfDownloadButton();

    expect(wrapper.find('button').attributes('disabled')).toBeUndefined();
  });
});
