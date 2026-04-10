import { mount } from '@vue/test-utils';
import WhatsAppFloatingButton from '../../components/BusinessProposal/WhatsAppFloatingButton.vue';

function mountButton(props = {}) {
  return mount(WhatsAppFloatingButton, {
    props: { whatsappLink: 'https://wa.me/123', ...props },
  });
}

describe('WhatsAppFloatingButton', () => {
  it('renders a link with the whatsappLink href', () => {
    const wrapper = mountButton({ whatsappLink: 'https://wa.me/456' });

    expect(wrapper.get('a').attributes('href')).toBe('https://wa.me/456');
  });

  it('renders the SVG icon inside the link', () => {
    const wrapper = mountButton();

    expect(wrapper.find('a svg').exists()).toBe(true);
  });

  it('does not render the link when whatsappLink is empty', () => {
    const wrapper = mountButton({ whatsappLink: '' });

    expect(wrapper.find('a').exists()).toBe(false);
  });
});
