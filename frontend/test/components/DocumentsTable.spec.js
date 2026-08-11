/**
 * Tests for DocumentsTable.vue — archived mode.
 *
 * El componente no tenía spec: esta es la red de seguridad del modo archivado
 * (columna de fecha, insignia, sin arrastre y restaurar en las filas de carpeta).
 */

import { mount } from '@vue/test-utils';
import DocumentsTable from '../../components/panel/documents/DocumentsTable.vue';
import BaseButton from '../../components/base/BaseButton.vue';

const activeDoc = {
  id: 1,
  title: 'Contrato de Servicios',
  status: 'published',
  created_at: '2026-05-15T10:00:00Z',
  archived_at: null,
  tag_details: [],
};

const archivedDoc = {
  ...activeDoc,
  id: 2,
  title: 'Acta de cierre',
  is_archived: true,
  // Fijo y muy antiguo: la antigüedad se calcula contra la fecha real de
  // ejecución, así que un valor lejano mantiene el aserto estable.
  archived_at: '2020-01-10T10:00:00Z',
};

const archivedFolder = { id: 9, name: 'Contratos 2024', document_count: 4, children_count: 0 };

function mountTable(props = {}) {
  return mount(DocumentsTable, {
    props: { documents: [activeDoc], subfolders: [], ...props },
    global: {
      components: { BaseButton },
      stubs: { NuxtLink: true },
    },
  });
}

describe('DocumentsTable — archived mode', () => {
  it('labels the date column Creado in the active scope', () => {
    const wrapper = mountTable();

    expect(wrapper.find('thead').text()).toContain('Creado');
    expect(wrapper.find('thead').text()).not.toContain('Archivado');
  });

  it('labels the date column Archivado and renders archived_at in the archived scope', () => {
    const wrapper = mountTable({ documents: [archivedDoc], archived: true });

    expect(wrapper.find('thead').text()).toContain('Archivado');
    expect(wrapper.find('[data-testid="doc-archived-at"]').text()).toContain('2020');
  });

  it('renders the archive age beside the date', () => {
    const wrapper = mountTable({ documents: [archivedDoc], archived: true });

    expect(wrapper.text()).toMatch(/hace \d+ años?/);
  });

  it('shows the neutral Archivado badge instead of the editorial status', () => {
    const wrapper = mountTable({ documents: [archivedDoc], archived: true });

    expect(wrapper.text()).toContain('Archivado');
    expect(wrapper.text()).not.toContain('Publicado');
  });

  it('does not make document rows draggable in archived mode', () => {
    const active = mountTable();
    const archived = mountTable({ documents: [archivedDoc], archived: true });

    const activeRow = active.findAll('tbody tr')[0];
    const archivedRow = archived.findAll('tbody tr')[0];

    // `draggable` es enumerado, no booleano: "false" es la forma de apagarlo.
    expect(activeRow.attributes('draggable')).toBe('true');
    expect(archivedRow.attributes('draggable')).toBe('false');
  });

  it('renders a restore action on archived folder rows instead of the navigation chevron', async () => {
    const wrapper = mountTable({
      documents: [], subfolders: [archivedFolder], archived: true,
    });

    const restore = wrapper.find('[data-testid="folder-unarchive"]');
    expect(restore.exists()).toBe(true);

    await restore.trigger('click');
    expect(wrapper.emitted('unarchive-folder')).toEqual([[archivedFolder]]);
  });

  it('keeps folder rows navigable in the active scope', async () => {
    const wrapper = mountTable({ documents: [], subfolders: [archivedFolder] });

    expect(wrapper.find('[data-testid="folder-unarchive"]').exists()).toBe(false);

    await wrapper.findAll('tbody tr')[0].trigger('click');
    expect(wrapper.emitted('select-folder')).toEqual([[archivedFolder.id]]);
  });
});
