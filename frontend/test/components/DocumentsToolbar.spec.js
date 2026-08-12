/**
 * Tests for DocumentsToolbar.vue.
 *
 * Cubre el buscador, el toggle de vista y el filtro de estado — que queda
 * inerte durante la búsqueda porque la búsqueda recorre los dos estados.
 */

import { mount } from '@vue/test-utils';
import DocumentsToolbar from '../../components/panel/documents/DocumentsToolbar.vue';
import BaseSegmented from '../../components/base/BaseSegmented.vue';
import BaseInput from '../../components/base/BaseInput.vue';

function mountToolbar(props = {}) {
  return mount(DocumentsToolbar, {
    props,
    global: { components: { BaseSegmented, BaseInput } },
  });
}

function segmentedByLabel(wrapper, label) {
  return wrapper.findAll('button').find((b) => b.text() === label);
}

describe('DocumentsToolbar', () => {
  it('renders the search input', () => {
    const wrapper = mountToolbar({ search: 'acta' });

    expect(wrapper.find('input[type="search"]').element.value).toBe('acta');
  });

  it('relays what the user types', async () => {
    const wrapper = mountToolbar();

    await wrapper.find('input[type="search"]').setValue('mapeo');

    expect(wrapper.emitted('update:search').at(-1)).toEqual(['mapeo']);
  });

  describe('state filter', () => {
    it('offers the three states', () => {
      const wrapper = mountToolbar();

      const labels = wrapper.find('[data-testid="doc-state-filter"]')
        .findAll('button').map((b) => b.text());
      expect(labels).toEqual(['Todos', 'Solo activos', 'Solo archivados']);
    });

    it('emits the picked state', async () => {
      const wrapper = mountToolbar({ scope: 'active' });

      await segmentedByLabel(wrapper, 'Solo archivados').trigger('click');

      expect(wrapper.emitted('update:scope')).toEqual([['archived']]);
    });

    it('goes inert while a search is running', async () => {
      // La búsqueda ignora el estado: dejar el control operativo sería ofrecer
      // un filtro que no filtra.
      const wrapper = mountToolbar({ scope: 'all', scopeLocked: true });

      await segmentedByLabel(wrapper, 'Solo activos').trigger('click');

      expect(wrapper.emitted('update:scope')).toBeUndefined();
    });
  });

  describe('view mode', () => {
    it('emits the picked view mode', async () => {
      const wrapper = mountToolbar({ viewMode: 'list' });

      await segmentedByLabel(wrapper, 'Galería').trigger('click');

      expect(wrapper.emitted('update:viewMode')).toEqual([['grid']]);
    });
  });
});
