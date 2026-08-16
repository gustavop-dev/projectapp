/**
 * Tests for BaseRowLink.
 *
 * Es el enlace primario de una fila de listado: el título que ES la dirección
 * del detalle. Concentra cuatro cosas que por separado se olvidan — el href
 * real, `draggable="false"` (si no, arrastrar por el título arrastra la URL en
 * vez del documento), frenar el burbujeo hacia el atajo de la fila, y estirarse
 * a toda su celda.
 */

import { mount } from '@vue/test-utils';
import BaseRowLink from '../../components/base/BaseRowLink.vue';

const NuxtLinkStub = {
  template: '<a :href="to" v-bind="$attrs"><slot /></a>',
  props: ['to'],
};

function mountLink(props = {}, options = {}) {
  return mount(BaseRowLink, {
    props,
    slots: { default: 'Contrato de Servicios' },
    global: { stubs: { NuxtLink: NuxtLinkStub } },
    ...options,
  });
}

describe('BaseRowLink', () => {
  it('publishes the address as a real link', () => {
    const wrapper = mountLink({ to: '/es-co/panel/documents/1/edit' });

    const link = wrapper.get('a');
    expect(link.attributes('href')).toBe('/es-co/panel/documents/1/edit');
    expect(link.text()).toBe('Contrato de Servicios');
  });

  it('degrades to plain text when the row has no detail to open', () => {
    const wrapper = mountLink({ to: null });

    expect(wrapper.find('a').exists()).toBe(false);
    expect(wrapper.get('span').text()).toBe('Contrato de Servicios');
  });

  it('opts out of the native link drag so the row keeps its own', () => {
    const wrapper = mountLink({ to: '/es-co/panel/documents/1/edit' });

    expect(wrapper.get('a').attributes('draggable')).toBe('false');
  });

  it('keeps the click from reaching the row shortcut behind it', async () => {
    const onRowClick = jest.fn();
    const wrapper = mount(
      {
        components: { BaseRowLink },
        template: '<div @click="onRowClick">'
          + '<span id="cell">Acme</span>'
          + '<BaseRowLink to="/x">Título</BaseRowLink>'
          + '</div>',
        setup: () => ({ onRowClick }),
      },
      { global: { stubs: { NuxtLink: NuxtLinkStub } } },
    );

    await wrapper.get('#cell').trigger('click');
    await wrapper.get('a').trigger('click');

    // El cuerpo de la fila sí llega al atajo; el enlace se lo queda.
    expect(onRowClick).toHaveBeenCalledTimes(1);
  });

  it('covers the whole containing cell only when asked to stretch', () => {
    const plain = mountLink({ to: '/x' });
    const stretched = mountLink({ to: '/x', stretch: true });

    expect(plain.get('a').classes()).not.toContain('after:inset-0');
    expect(stretched.get('a').classes()).toContain('after:absolute');
    expect(stretched.get('a').classes()).toContain('after:inset-0');
  });

  it('does not fake a hit area when there is no address to reach', () => {
    const classes = mountLink({ to: null, stretch: true }).get('span').classes();

    expect(classes).toContain('rounded');
    expect(classes).not.toContain('after:inset-0');
  });
});
