/**
 * Tests for DownloadQrModal.
 * Covers: renders when open, download button triggers a PNG download,
 * transparent-background checkbox disables the background color picker,
 * PNG/SVG format selector and SVG export.
 */
import { mount } from '@vue/test-utils';
import DownloadQrModal from '../../components/panel/qr-cards/DownloadQrModal.vue';

jest.mock('qrcode', () => ({
  toCanvas: jest.fn().mockResolvedValue(undefined),
  toString: jest.fn().mockResolvedValue('<svg xmlns="http://www.w3.org/2000/svg"></svg>'),
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
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = jest.fn();
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

    expect(wrapper.find('[data-testid="qr-background-color"]').attributes('disabled')).toBeUndefined();

    await wrapper.find('[data-testid="qr-transparent-toggle"] input').setValue(true);

    expect(wrapper.find('[data-testid="qr-background-color"]').attributes('disabled')).toBe('');
  });

  it('defaults the download button to PNG', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="qr-download-button"]').text()).toBe('Descargar PNG');
  });

  it('switches the download button label to SVG when that format is selected', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="qr-format-svg"]').trigger('click');

    expect(wrapper.find('[data-testid="qr-download-button"]').text()).toBe('Descargar SVG');
  });

  it('exports an SVG string encoding the short link when SVG format is selected and downloaded', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="qr-format-svg"]').trigger('click');
    await wrapper.find('[data-testid="qr-download-button"]').trigger('click');
    await wrapper.vm.$nextTick();

    expect(QRCode.toString).toHaveBeenCalled();
    const [encodedText, options] = QRCode.toString.mock.calls[0];
    expect(encodedText).toContain(`/t/${card.id}/`);
    expect(options.type).toBe('svg');
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('downloads via the canvas without invoking the SVG renderer when PNG format is selected', async () => {
    const wrapper = mountModal();
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="qr-download-button"]').trigger('click');

    expect(wrapper.find('[data-testid="qr-canvas"]').exists()).toBe(true);
    expect(QRCode.toString).not.toHaveBeenCalled();
  });
});
