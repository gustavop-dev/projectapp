import { mount } from '@vue/test-utils';
import AlertGroupSubItems from '../../components/Panel/AlertGroupSubItems.vue';
import BaseRowLink from '../../components/base/BaseRowLink.vue';

const NuxtLinkStub = {
  template: '<a :href="to" v-bind="$attrs"><slot /></a>',
  props: ['to'],
};

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

const hrefFor = (id) => `/panel/proposals/${id}/edit`;

function mountAlertGroupSubItems(props = {}) {
  return mount(AlertGroupSubItems, {
    props: {
      proposals,
      hrefFor,
      ...props,
    },
    global: {
      components: { BaseRowLink },
      stubs: { NuxtLink: NuxtLinkStub },
    },
  });
}

describe('AlertGroupSubItems', () => {
  it('renders a row for each proposal', () => {
    const wrapper = mountAlertGroupSubItems();

    expect(wrapper.findAll('[data-testid^="alert-subitem-"]').length).toBe(2);
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

  // La fila no tiene ningún control adentro, así que puede ser el enlace entero
  // y no sólo su título: los cinco gestos funcionan en cualquier punto de ella.
  it('makes each row a real link to its proposal editor', () => {
    const wrapper = mountAlertGroupSubItems();

    const links = wrapper.findAll('a');
    expect(links).toHaveLength(2);
    expect(links[0].attributes('href')).toBe('/panel/proposals/1/edit');
    expect(links[0].text()).toContain('Propuesta Alpha');
    expect(links[1].attributes('href')).toBe('/panel/proposals/2/edit');
  });
});
