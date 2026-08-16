/**
 * Tests for FolderHeader.vue.
 *
 * La cabecera que aparece al ENTRAR a una carpeta: su nombre, de quién es y
 * el botón de editar. Antes el nombre de la carpeta abierta era el último
 * segmento del breadcrumb —un span pelado— y no había dónde pulsar para
 * cambiarle nada estando parado dentro de ella.
 */
import { mount } from '@vue/test-utils';
import FolderHeader from '../../components/panel/documents/FolderHeader.vue';
import BaseButton from '../../components/base/BaseButton.vue';

const folder = {
  id: 5,
  name: 'Kore - Diseño',
  client: 7,
  client_display_name: 'Kore SAS',
  project: 4,
  project_name: 'Kore rediseño',
};

function mountHeader(props = {}) {
  return mount(FolderHeader, {
    props: { folder, ...props },
    global: { components: { BaseButton } },
  });
}

describe('FolderHeader', () => {
  it('names the folder you are standing in', () => {
    const wrapper = mountHeader();

    expect(wrapper.find('[data-testid="folder-header-name"]').text())
      .toBe('Kore - Diseño');
  });

  it('says whose folder it is and for what project', () => {
    const wrapper = mountHeader();

    expect(wrapper.find('[data-testid="folder-header-client"]').text())
      .toContain('Kore SAS');
    expect(wrapper.find('[data-testid="folder-header-project"]').text())
      .toContain('Kore rediseño');
  });

  it('offers editing right there, where the need shows up', async () => {
    const wrapper = mountHeader();

    await wrapper.find('[data-testid="folder-header-edit"]').trigger('click');

    expect(wrapper.emitted('edit')[0][0]).toMatchObject({ id: 5 });
  });

  it('shows an unassigned folder without inventing an owner', () => {
    const wrapper = mountHeader({ folder: { id: 6, name: 'Varios' } });

    expect(wrapper.find('[data-testid="folder-header-client"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="folder-header-project"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="folder-header-name"]').text()).toBe('Varios');
  });

  it('renders nothing when standing outside any folder', () => {
    const wrapper = mountHeader({ folder: null });

    expect(wrapper.find('[data-testid="folder-header"]').exists()).toBe(false);
  });
});
