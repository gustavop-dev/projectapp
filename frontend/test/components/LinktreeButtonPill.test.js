/**
 * Tests for LinktreeButtonPill — per-tier rendering, pending state and
 * in-page actions (vcard / install) vs navigation buttons.
 */
import { mount } from '@vue/test-utils';
import LinktreeButtonPill from '../../components/Linktree/LinktreeButtonPill.vue';

const baseButton = {
  id: 1,
  tier: 'primary',
  action: 'linkedin',
  label: 'Conectemos en LinkedIn',
  href: 'https://linkedin.com/in/x',
  resolved_icon: 'linkedin',
  kind: 'url',
  is_pending: false,
  order: 0,
  is_active: true,
};

const factory = (button = {}) =>
  mount(LinktreeButtonPill, { props: { button: { ...baseButton, ...button } } });

describe('LinktreeButtonPill', () => {
  it('renders a url button as an anchor with its href', () => {
    const wrapper = factory();
    const anchor = wrapper.find('a');
    expect(anchor.exists()).toBe(true);
    expect(anchor.attributes('href')).toBe('https://linkedin.com/in/x');
  });

  it('opens external links in a new tab', () => {
    const wrapper = factory();
    expect(wrapper.find('a').attributes('target')).toBe('_blank');
  });

  it('applies the tier modifier class', () => {
    const wrapper = factory({ tier: 'row' });
    expect(wrapper.classes()).toContain('lt-btn--row');
  });

  it('shows the trailing arrow only on row tier', () => {
    const row = factory({ tier: 'row' });
    const primary = factory({ tier: 'primary' });
    expect(row.findAll('svg')).toHaveLength(2);
    expect(primary.findAll('svg')).toHaveLength(1);
  });

  it('renders a vcard button as a native button and emits action on click', async () => {
    const wrapper = factory({ action: 'vcard', kind: 'download-vcard', href: '' });
    const button = wrapper.find('button');
    expect(button.exists()).toBe(true);

    await button.trigger('click');

    expect(wrapper.emitted('action')).toHaveLength(1);
    expect(wrapper.emitted('action')[0][0].action).toBe('vcard');
  });

  it('renders the PENDIENTE tag when the destination is unresolved', () => {
    const wrapper = factory({ href: '', is_pending: true });
    expect(wrapper.text()).toContain('PENDIENTE');
    expect(wrapper.classes()).toContain('lt-btn--pending');
  });

  it('does not emit action when clicking a pending button', async () => {
    const wrapper = factory({ href: '', is_pending: true });

    await wrapper.trigger('click');

    expect(wrapper.emitted('action')).toBeUndefined();
  });
});
