import { mount } from '@vue/test-utils';
import AlertGroupSubItems from '../../components/Panel/AlertGroupSubItems.vue';

const proposals = [
  {
    id: 1,
    title: 'Propuesta Alpha',
    alerts: [
      { alert_type: 'expiring_soon', message: 'Expira en 3 días', icon: '⏰' },
    ],
  },
  {
    id: 2,
    title: 'Propuesta Beta',
    alerts: [],
  },
];

function mountAlertGroupSubItems(props = {}) {
  return mount(AlertGroupSubItems, {
    props: {
      proposals,
      ...props,
    },
  });
}

describe('AlertGroupSubItems', () => {
  it('renders a row for each proposal', () => {
    const wrapper = mountAlertGroupSubItems();

    expect(wrapper.findAll('[class*="cursor-pointer"]').length).toBe(2);
  });

  it('shows proposal titles', () => {
    const wrapper = mountAlertGroupSubItems();

    expect(wrapper.text()).toContain('Propuesta Alpha');
    expect(wrapper.text()).toContain('Propuesta Beta');
  });

  it('shows alert messages for proposals with alerts', () => {
    const wrapper = mountAlertGroupSubItems();

    expect(wrapper.text()).toContain('Expira en 3 días');
  });

  it('emits select with proposalId when a row is clicked', async () => {
    const wrapper = mountAlertGroupSubItems();

    await wrapper.findAll('[class*="cursor-pointer"]')[0].trigger('click');

    expect(wrapper.emitted('select')).toBeTruthy();
    expect(wrapper.emitted('select')[0][0]).toBe(1);
  });
});
