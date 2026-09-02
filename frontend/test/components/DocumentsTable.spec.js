/**
 * Tests for DocumentsTable.vue — estado archivado.
 *
 * El scope sólo decide el encabezado de columna; todo lo demás (insignia,
 * fecha, arrastre, restaurar) lo decide `is_archived` de CADA fila, porque con
 * `scope=all` y con la búsqueda global la lista es mixta.
 */

import { mount } from '@vue/test-utils';
import DocumentsTable from '../../components/panel/documents/DocumentsTable.vue';
import BaseActionIcon from '../../components/base/BaseActionIcon.vue';
import BaseRowLink from '../../components/base/BaseRowLink.vue';

const BaseTooltipStub = {
  name: 'BaseTooltip',
  props: ['text', 'position', 'width', 'minWidth'],
  template: '<div :data-tooltip="text"><slot name="trigger" /><slot /></div>',
};

const BaseBadgeStub = {
  name: 'BaseBadge',
  props: ['variant', 'size'],
  template: '<span><slot /></span>',
};

// Preserva el href: el contrato de la fila es justamente que el título tenga
// dirección, y el auto-stub de NuxtLink no renderiza ninguna.
const NuxtLinkStub = {
  template: '<a :href="to" v-bind="$attrs"><slot /></a>',
  props: ['to'],
};

const editToFor = (doc) => `/panel/documents/${doc.id}/edit`;

const activeDoc = {
  id: 1,
  title: 'Contrato de Servicios',
  created_at: '2026-05-15T10:00:00Z',
  archived_at: null,
  active_states: [{
    id: 21,
    duration_seconds: 86400,
    state: {
      id: 1,
      name: 'Enviado',
      color: 'blue',
      system_key: 'sent',
      group_mode: 'exclusive',
      group_order: 0,
      order: 1,
    },
  }],
};

const longNamedDoc = {
  ...activeDoc,
  id: 3,
  title: 'Levantamiento_Fase_4_Multi-Tenant_24082026',
  folder_name: 'Respuesta_Etapa_3_Inventario',
  client_display_name: 'guia_apuntar_dominio_ux_26082026',
  project_name: 'Proyecto_Multi-Tenant_Implementacion_24082026',
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
      // BaseRowLink va registrado a mano: en Jest no hay auto-import de Nuxt.
      components: {
        BaseBadge: BaseBadgeStub,
        BaseTooltip: BaseTooltipStub,
        BaseRowLink,
      },
      stubs: { NuxtLink: NuxtLinkStub },
    },
  });
}

describe('DocumentsTable — archived mode', () => {
  it('orders headers by document-list business priority', () => {
    const wrapper = mountTable();

    const labels = wrapper.findAll('thead th')
      .map((header) => header.text().replace(/\s+/g, ' ').trim());

    expect(labels).toEqual([
      '', 'Título', 'Estados', 'Creado', 'Cliente', 'Proyecto',
    ]);
    expect(wrapper.get('[data-testid="documents-column-actions"]').attributes('aria-label'))
      .toBe('Acciones');
  });

  it('orders document cells by document-list business priority', () => {
    const wrapper = mountTable();

    const cells = wrapper.get('[data-testid="document-row-1"]').findAll('td');

    const actionsButton = cells[0].get('[aria-label="Acciones de Contrato de Servicios"]');
    expect(actionsButton.attributes('title')).toBeUndefined();
    expect(cells[1].text()).toContain('Contrato de Servicios');
    expect(cells[2].text()).toContain('Enviado');
    expect(cells[3].text()).toContain('2026');
    expect(cells[4].text()).toBe('—');
    expect(cells[5].text()).toBe('—');
  });

  it('labels the date column Creado in the active scope', () => {
    const wrapper = mountTable();

    expect(wrapper.find('thead').text()).toContain('Creado');
    expect(wrapper.find('thead').text()).not.toContain('Archivado');
  });

  it('exposes the recent date order from the column header', () => {
    const wrapper = mountTable();
    const header = wrapper.get('[data-testid="documents-column-date"]');
    const button = wrapper.get('[data-testid="documents-date-sort"]');

    expect(header.attributes('aria-sort')).toBe('descending');
    expect(button.attributes('aria-label')).toContain('más nuevos primero');
    expect(button.findComponent(BaseActionIcon).props('action')).toBe('sort-descending');
  });

  it('requests the oldest order from the date header', async () => {
    const wrapper = mountTable();

    await wrapper.get('[data-testid="documents-date-sort"]').trigger('click');

    expect(wrapper.emitted('sort-date')).toEqual([['oldest']]);
  });

  it('requests the recent order from an ascending date header', async () => {
    const wrapper = mountTable({ dateOrder: 'oldest' });
    const header = wrapper.get('[data-testid="documents-column-date"]');
    const button = wrapper.get('[data-testid="documents-date-sort"]');

    expect(header.attributes('aria-sort')).toBe('ascending');
    expect(button.findComponent(BaseActionIcon).props('action')).toBe('sort-ascending');
    await button.trigger('click');
    expect(wrapper.emitted('sort-date')).toEqual([['recent']]);
  });

  it('labels the date column Archivado and renders archived_at in the archived scope', () => {
    const wrapper = mountTable({ documents: [archivedDoc], scope: 'archived' });

    expect(wrapper.find('thead').text()).toContain('Archivado');
    expect(wrapper.find('[data-testid="doc-archived-at"]').text()).toContain('2020');
  });

  it('falls back to created_at when an archived row has no archive timestamp', () => {
    const wrapper = mountTable({
      documents: [{ ...archivedDoc, archived_at: null, created_at: '2019-06-02T12:00:00Z' }],
      scope: 'archived',
    });

    expect(wrapper.get('[data-testid="doc-archived-at"]').text()).toContain('2019');
  });

  it('labels the date column neutrally in the mixed scope', () => {
    const wrapper = mountTable({ documents: [activeDoc, archivedDoc], scope: 'all' });

    expect(wrapper.find('thead').text()).toContain('Fecha');
  });

  it('renders the archive age beside the date', () => {
    const wrapper = mountTable({ documents: [archivedDoc], scope: 'archived' });

    expect(wrapper.text()).toMatch(/hace \d+ años?/);
  });

  it('shows the neutral Archivado badge instead of workflow states', () => {
    const wrapper = mountTable({ documents: [archivedDoc], scope: 'archived' });

    expect(wrapper.text()).toContain('Archivado');
    expect(wrapper.text()).not.toContain('Enviado');
  });

  it('renders the derived commercial state instead of workflow episodes', () => {
    const wrapper = mountTable({
      documents: [{
        ...activeDoc,
        display_state: { key: 'paid', label: 'Pagada', variant: 'success' },
      }],
    });

    const badge = wrapper.get('[data-testid="doc-derived-state-1"]');
    expect(badge.text()).toBe('Pagada');
    expect(wrapper.get('[data-testid="doc-states-cell-1"]').text()).not.toContain('Enviado');
  });

  it('marks only the archived row in a mixed list', () => {
    // Es la mitad de fondo del requisito de búsqueda: un resultado archivado
    // tiene que declararse como tal aunque su vecino esté activo.
    const wrapper = mountTable({ documents: [activeDoc, archivedDoc], scope: 'all' });

    const rows = wrapper.findAll('tbody tr');
    expect(rows[0].find('[data-testid="doc-archived-badge"]').exists()).toBe(false);
    expect(rows[1].find('[data-testid="doc-archived-badge"]').exists()).toBe(true);
    expect(rows[0].text()).toContain('Enviado');
  });

  it('does not make archived document rows draggable', () => {
    const wrapper = mountTable({ documents: [activeDoc, archivedDoc], scope: 'all' });

    const rows = wrapper.findAll('tbody tr');
    // `draggable` es enumerado, no booleano: "false" es la forma de apagarlo.
    expect(rows[0].attributes('draggable')).toBe('true');
    expect(rows[1].attributes('draggable')).toBe('false');
  });

  it('does not make generated snapshots draggable', () => {
    const wrapper = mountTable({
      documents: [{ ...activeDoc, is_generated_snapshot: true }],
    });

    expect(wrapper.get('[data-testid="document-row-1"]').attributes('draggable')).toBe('false');
  });

  it('does not make issued collection accounts draggable', () => {
    const wrapper = mountTable({
      documents: [{
        ...activeDoc,
        document_type_code: 'collection_account',
        commercial_status: 'issued',
      }],
    });

    expect(wrapper.get('[data-testid="document-row-1"]').attributes('draggable')).toBe('false');
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

describe('DocumentsTable — asociación cliente/proyecto', () => {
  it('renders the linked client and project in their own columns', () => {
    const wrapper = mountTable({
      documents: [{
        ...activeDoc,
        client: 4,
        client_display_name: 'Kore SAS',
        project: 11,
        project_name: 'Kore - Diseño',
      }],
    });

    expect(wrapper.find('thead').text()).toContain('Cliente');
    expect(wrapper.find('thead').text()).toContain('Proyecto');
    expect(wrapper.find('[data-testid="doc-client-cell-1"]').text()).toBe('Kore SAS');
    expect(wrapper.find('[data-testid="doc-project-cell-1"]').text()).toBe('Kore - Diseño');
  });

  it('falls back to the free-text name in italics when nothing is linked', () => {
    const wrapper = mountTable({
      documents: [{ ...activeDoc, client_name: 'ACME Corp' }],
    });

    const cell = wrapper.find('[data-testid="doc-client-cell-1"]');
    expect(cell.text()).toBe('ACME Corp');
    expect(cell.find('span').classes()).toContain('italic');
  });

  it('shows dashes when the document has no association at all', () => {
    const wrapper = mountTable({ documents: [{ ...activeDoc }] });

    expect(wrapper.find('[data-testid="doc-client-cell-1"]').text()).toBe('—');
    expect(wrapper.find('[data-testid="doc-project-cell-1"]').text()).toBe('—');
  });
});

describe('DocumentsTable — fila navegable', () => {
  it('publishes the editor address on the title, not just on the row handler', () => {
    const wrapper = mountTable({ editToFor });

    const link = wrapper.get('[data-testid="document-open-1"]');
    expect(link.attributes('href')).toBe('/panel/documents/1/edit');
    expect(link.text()).toBe('Contrato de Servicios');
  });

  it('forwards the click so the page can tell a plain open from a new tab', async () => {
    const wrapper = mountTable({ editToFor });

    await wrapper.get('[data-testid="doc-client-cell-1"]').trigger('click');

    const [doc, event] = wrapper.emitted('open')[0];
    expect(doc.id).toBe(1);
    expect(event).toBeInstanceOf(MouseEvent);
  });

  it('forwards a wheel click too, which is a different event entirely', async () => {
    const wrapper = mountTable({ editToFor });

    await wrapper.get('[data-testid="doc-client-cell-1"]').trigger('auxclick', { button: 1 });

    expect(wrapper.emitted('open')).toHaveLength(1);
    expect(wrapper.emitted('open')[0][1].button).toBe(1);
  });

  it('opens actions without forwarding the row navigation', async () => {
    const wrapper = mountTable({ editToFor });

    await wrapper.get('[aria-label="Acciones de Contrato de Servicios"]').trigger('click');
    await wrapper.get('[data-testid="doc-actions-cell-1"]')
      .trigger('auxclick', { button: 1 });

    expect(wrapper.emitted('action')).toEqual([[activeDoc]]);
    expect(wrapper.emitted('open')).toBeUndefined();
  });

  it('lets the title link navigate on its own instead of opening twice', async () => {
    const wrapper = mountTable({ editToFor });

    await wrapper.get('[data-testid="doc-client-cell-1"]').trigger('click');
    await wrapper.get('[data-testid="document-open-1"]').trigger('click');

    expect(wrapper.emitted('open')).toHaveLength(1);
  });

  it('opts the title out of the native link drag so the row keeps its own', () => {
    const wrapper = mountTable({ editToFor });

    expect(wrapper.get('[data-testid="document-open-1"]').attributes('draggable')).toBe('false');
    expect(wrapper.findAll('tbody tr')[0].attributes('draggable')).toBe('true');
  });
});

describe('DocumentsTable — fila de carpeta', () => {
  const folderToFor = (sub) => `/panel/documents?folder=${sub.id}`;

  it('does not make system-managed folders draggable', () => {
    const wrapper = mountTable({
      subfolders: [{ ...activeFolder, is_system_managed: true }],
    });

    expect(wrapper.findAll('tbody tr')[0].attributes('draggable')).toBe('false');
  });

  it('publishes the folder address on its name', () => {
    const wrapper = mountTable({ documents: [], subfolders: [activeFolder], folderToFor });

    const link = wrapper.get('[data-testid="folder-open-9"]');
    expect(link.attributes('href')).toBe('/panel/documents?folder=9');
    expect(link.text()).toBe('Contratos 2024');
  });

  it('keeps the plain click for the page, which owns how a folder is entered', async () => {
    const wrapper = mountTable({ documents: [], subfolders: [activeFolder], folderToFor });

    await wrapper.get('[data-testid="folder-open-9"]').trigger('click');

    // La página entra por el store — y en plena búsqueda hace algo distinto —,
    // así que el enlace cede el clic simple en vez de navegar por su cuenta.
    expect(wrapper.emitted('select-folder')).toEqual([[activeFolder.id]]);
  });

  it('hands a ctrl+click to the browser instead of entering the folder', async () => {
    const wrapper = mountTable({ documents: [], subfolders: [activeFolder], folderToFor });

    await wrapper.get('[data-testid="folder-open-9"]').trigger('click', { ctrlKey: true });

    expect(wrapper.emitted('select-folder')).toBeUndefined();
  });

  it('does not fake an address when the page says there is none', async () => {
    const wrapper = mountTable({ documents: [], subfolders: [activeFolder] });

    expect(wrapper.find('a').exists()).toBe(false);
    // La fila sigue entrando a la carpeta: lo que falta es la dirección.
    await wrapper.findAll('tbody tr')[0].trigger('click');
    expect(wrapper.emitted('select-folder')).toEqual([[activeFolder.id]]);
  });
});

describe('DocumentsTable — title column', () => {
  beforeEach(() => {
    window.localStorage.clear();
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 1440 });
  });

  it('truncates the title to one contained line before disclosure', () => {
    const wrapper = mountTable({ editToFor });

    expect(wrapper.get('[data-testid="document-open-1"]').classes()).toContain('truncate');
  });

  it('gives an unbroken title the intrinsic-safe truncation contract', () => {
    const wrapper = mountTable({ documents: [longNamedDoc], editToFor });
    const title = wrapper.get('[data-testid="document-open-3"]');

    expect(title.classes()).toEqual(expect.arrayContaining([
      'w-full', 'min-w-0', 'max-w-full', 'truncate',
    ]));
  });

  it('renders the folder below the title in a contained metadata row', () => {
    const wrapper = mountTable({ documents: [longNamedDoc], editToFor });
    const title = wrapper.get('[data-testid="document-open-3"]');
    const metadata = wrapper.get('[data-testid="document-title-meta-3"]');
    const folder = wrapper.get('[data-testid="document-folder-badge-3"]');

    expect(title.element.compareDocumentPosition(metadata.element) & Node.DOCUMENT_POSITION_FOLLOWING)
      .toBeTruthy();
    expect(metadata.classes()).toEqual(expect.arrayContaining(['flex-wrap', 'max-w-full']));
    expect(folder.classes()).toContain('[overflow-wrap:anywhere]');
  });

  it('does not reserve a desktop metadata line without a folder', () => {
    const wrapper = mountTable({ documents: [activeDoc], editToFor });

    expect(wrapper.get('[data-testid="document-title-meta-1"]').classes())
      .toContain('panel-desktop:hidden');
  });

  it('publishes the title resize separator', () => {
    const wrapper = mountTable({ editToFor });

    const handle = wrapper.get('[data-testid="documents-title-resize-handle"]');
    expect(handle.attributes('role')).toBe('separator');
    expect(handle.attributes('aria-valuenow')).toBe('320');
    expect(handle.attributes('aria-valuemax')).toBe('520');
    expect(handle.attributes('title')).toBe('Ajustar el ancho de la columna Título');
  });

  it('keeps the workflow states column fixed', () => {
    const wrapper = mountTable({ editToFor });

    expect(wrapper.get('[data-testid="documents-column-states"]').element.style.width)
      .toBe('224px');
  });

  it('keeps the actions column fixed', () => {
    const wrapper = mountTable({ editToFor });

    expect(wrapper.get('[data-testid="documents-column-actions"]').element.style.width)
      .toBe('56px');
  });

  it('persists a keyboard title resize', async () => {
    const wrapper = mountTable({ editToFor });

    await wrapper.get('[data-testid="documents-title-resize-handle"]')
      .trigger('keydown', { key: 'ArrowRight' });

    expect(window.localStorage.getItem('projectapp-table-widths:documents-list'))
      .toBe('{"title":336}');
  });

  it('forgets the title width on reset', async () => {
    window.localStorage.setItem(
      'projectapp-table-widths:documents-list',
      '{"title":400}',
    );
    const wrapper = mountTable({ editToFor });

    const handle = wrapper.get('[data-testid="documents-title-resize-handle"]');
    await handle.trigger('dblclick');

    expect(handle.attributes('aria-valuenow')).toBe('320');
    expect(window.localStorage.getItem('projectapp-table-widths:documents-list')).toBeNull();
  });

  it('opens the thread from its badge without opening the document', async () => {
    const threadedDoc = {
      ...activeDoc,
      thread_summary: { id: 3, title: 'Historia del contrato', document_count: 4 },
    };
    const wrapper = mountTable({ documents: [threadedDoc], editToFor });

    const badge = wrapper.get('[data-testid="document-thread-open-1"]');
    expect(badge.text()).toContain('Hilo · 4');

    await badge.trigger('click');

    // Falla si el badge deja de ser puerta al hilo o arrastra la apertura del documento.
    expect(wrapper.emitted('thread')[0]).toEqual([threadedDoc]);
    expect(wrapper.emitted('open')).toBeFalsy();
  });
});
