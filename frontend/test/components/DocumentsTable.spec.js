/**
 * Tests for DocumentsTable.vue — estado archivado.
 *
 * El scope sólo decide el encabezado de columna; todo lo demás (insignia,
 * fecha, arrastre, restaurar) lo decide `is_archived` de CADA fila, porque con
 * `scope=all` y con la búsqueda global la lista es mixta.
 */

import { mount } from '@vue/test-utils';
import DocumentsTable from '../../components/panel/documents/DocumentsTable.vue';
import BaseButton from '../../components/base/BaseButton.vue';

const BaseTooltipStub = {
  name: 'BaseTooltip',
  props: ['position', 'width', 'minWidth'],
  template: '<div><slot name="trigger" /><slot /></div>',
};

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

const activeFolder = { id: 9, name: 'Contratos 2024', document_count: 4, children_count: 0 };
const archivedFolder = { ...activeFolder, is_archived: true };
// Activa por fuera, con archivados dentro: el estado mixto que deja una
// restauración por cadena.
const mixedFolder = {
  ...activeFolder,
  id: 10,
  name: 'temp',
  archived_document_count: 3,
  archived_children_count: 0,
};

function mountTable(props = {}) {
  return mount(DocumentsTable, {
    props: { documents: [activeDoc], subfolders: [], ...props },
    global: {
      components: { BaseButton, BaseTooltip: BaseTooltipStub },
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
    const wrapper = mountTable({ documents: [archivedDoc], scope: 'archived' });

    expect(wrapper.find('thead').text()).toContain('Archivado');
    expect(wrapper.find('[data-testid="doc-archived-at"]').text()).toContain('2020');
  });

  it('labels the date column neutrally in the mixed scope', () => {
    const wrapper = mountTable({ documents: [activeDoc, archivedDoc], scope: 'all' });

    expect(wrapper.find('thead').text()).toContain('Fecha');
  });

  it('renders the archive age beside the date', () => {
    const wrapper = mountTable({ documents: [archivedDoc], scope: 'archived' });

    expect(wrapper.text()).toMatch(/hace \d+ años?/);
  });

  it('shows the neutral Archivado badge instead of the editorial status', () => {
    const wrapper = mountTable({ documents: [archivedDoc], scope: 'archived' });

    expect(wrapper.text()).toContain('Archivado');
    expect(wrapper.text()).not.toContain('Publicado');
  });

  it('marks only the archived row in a mixed list', () => {
    // Es la mitad de fondo del requisito de búsqueda: un resultado archivado
    // tiene que declararse como tal aunque su vecino esté activo.
    const wrapper = mountTable({ documents: [activeDoc, archivedDoc], scope: 'all' });

    const rows = wrapper.findAll('tbody tr');
    expect(rows[0].find('[data-testid="doc-archived-badge"]').exists()).toBe(false);
    expect(rows[1].find('[data-testid="doc-archived-badge"]').exists()).toBe(true);
    expect(rows[0].text()).toContain('Publicado');
  });

  it('does not make archived document rows draggable', () => {
    const wrapper = mountTable({ documents: [activeDoc, archivedDoc], scope: 'all' });

    const rows = wrapper.findAll('tbody tr');
    // `draggable` es enumerado, no booleano: "false" es la forma de apagarlo.
    expect(rows[0].attributes('draggable')).toBe('true');
    expect(rows[1].attributes('draggable')).toBe('false');
  });

  it('renders a restore action on archived folder rows instead of the navigation chevron', async () => {
    const wrapper = mountTable({
      documents: [], subfolders: [archivedFolder], scope: 'archived',
    });

    const restore = wrapper.find('[data-testid="folder-unarchive"]');
    expect(restore.exists()).toBe(true);

    await restore.trigger('click');
    expect(wrapper.emitted('unarchive-folder')).toEqual([[archivedFolder]]);
  });

  it('lets an archived folder be entered, so its contents are reachable', async () => {
    const wrapper = mountTable({
      documents: [], subfolders: [archivedFolder], scope: 'archived',
    });

    await wrapper.findAll('tbody tr')[0].trigger('click');

    expect(wrapper.emitted('select-folder')).toEqual([[archivedFolder.id]]);
  });

  it('summarises an archived folder with its archived contents', () => {
    const wrapper = mountTable({
      documents: [],
      subfolders: [{ ...archivedFolder, archived_document_count: 4 }],
      scope: 'archived',
    });

    expect(wrapper.text()).toContain('4 documentos');
  });

  it('flags an active folder that still holds archived items', async () => {
    const wrapper = mountTable({ documents: [], subfolders: [mixedFolder] });

    const badge = wrapper.find('[data-testid="folder-archived-badge"]');
    expect(badge.text()).toContain('3');

    await badge.trigger('click');
    expect(wrapper.emitted('view-archived-folder')).toEqual([[mixedFolder]]);
    // @click.stop: entrar a la carpeta en su scope archivado no es lo mismo
    // que entrar en el scope actual.
    expect(wrapper.emitted('select-folder')).toBeUndefined();
  });

  it('lets the page supply the summary so the row can count the whole branch', () => {
    // La página inyecta el conteo del subárbol: entrar a una carpeta y ver sus
    // subcarpetas diciendo «Vacía» es el mismo defecto un clic más adentro.
    const folderSummary = jest.fn(() => '12 documentos · 2 subcarpetas');
    const wrapper = mountTable({ documents: [], subfolders: [activeFolder], folderSummary });

    expect(folderSummary).toHaveBeenCalledWith(activeFolder, 'active');
    expect(wrapper.text()).toContain('12 documentos · 2 subcarpetas');
  });

  it('keeps folder rows navigable in the active scope', async () => {
    const wrapper = mountTable({ documents: [], subfolders: [activeFolder] });

    expect(wrapper.find('[data-testid="folder-unarchive"]').exists()).toBe(false);

    await wrapper.findAll('tbody tr')[0].trigger('click');
    expect(wrapper.emitted('select-folder')).toEqual([[activeFolder.id]]);
  });
});
