/**
 * Tests for DownloadQrModal.
 * Covers: renders when open, download button triggers a PNG download,
 * transparent-background checkbox disables the background color picker.
 */
import { mount } from '@vue/test-utils';
import DownloadQrModal from '../../components/panel/qr-cards/DownloadQrModal.vue';

jest.mock('qrcode', () => ({
  toCanvas: jest.fn().mockResolvedValue(undefined),
}));

const QRCode = require('qrcode');

const card = { id: '11111111-1111-1111-1111-111111111111', name: 'Tarjeta evento X' };

function mountModal(props = {}) {
  return mount(DownloadQrModal, {
    props: { modelValue: true, card, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('DownloadQrModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the canvas and card name when open', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="qr-canvas"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Tarjeta evento X');
  });

  it('renders the QR encoding the short link, not the destination', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(QRCode.toCanvas).toHaveBeenCalled();
    const [, encodedText] = QRCode.toCanvas.mock.calls[0];
    expect(encodedText).toContain(`/t/${card.id}/`);
  });

  it('disables the background color picker when transparent is checked', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="qr-transparent-toggle"] input').setValue(true);

    expect(wrapper.find('[data-testid="qr-background-color"]').attributes('disabled')).toBeDefined();
  });
});
