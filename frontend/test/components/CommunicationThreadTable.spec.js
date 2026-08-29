import { mount } from '@vue/test-utils';

import CommunicationThreadTable from '~/components/communications/CommunicationThreadTable.vue';

const BaseRowLinkStub = {
  props: ['to', 'stretch'],
  template: '<a :href="to"><slot /></a>',
};

const BaseBadgeStub = {
  template: '<span data-badge><slot /></span>',
};

const BaseResponsiveTableStub = {
  props: ['columns', 'rows'],
  template: `
    <div data-testid="desktop-thread-table">
      <slot v-if="rows.length" name="cell-title" :row="rows[0]" />
    </div>
  `,
};

const longMessage = `Confirmamos   que el alcance incluye la revisión de accesibilidad,
  las pruebas de aceptación y el acompañamiento de salida para todo el equipo responsable,
  con una secuencia adicional que no debe aparecer completa en el listado.`;

function thread(overrides = {}) {
  return {
    id: 41,
    title: 'Aprobación de alcance',
    status: 'open',
    client_name: 'Ana Proyecto',
    project_name: 'Portal de clientes',
    messages_count: 2,
    draft_count: 1,
    channels: ['email', 'whatsapp'],
    latest_message: {
      direction: 'incoming',
      content: longMessage,
    },
    last_activity_at: '2026-08-24T15:10:00Z',
    ...overrides,
  };
}

function mountList(props = {}) {
  return mount(CommunicationThreadTable, {
    props: {
      threads: [thread()],
      hrefFor: (row) => `/panel/communications?thread=${row.id}`,
      compact: true,
      ...props,
    },
    global: {
      stubs: {
        BaseBadge: BaseBadgeStub,
        BaseResponsiveTable: BaseResponsiveTableStub,
        BaseRowLink: BaseRowLinkStub,
      },
    },
  });
}

describe('CommunicationThreadTable', () => {
  it('renders thread identity metadata in a compact card', () => {
    const wrapper = mountList();
    const card = wrapper.get('[data-testid="communication-thread-row-41"]');

    expect(card.text()).toContain('Aprobación de alcance');
    expect(card.text()).toContain('Ana Proyecto · Portal de clientes');
    expect(card.text()).toContain('Abierto');
    expect(card.text()).toContain('Correo');
    expect(card.text()).toContain('WhatsApp');
    expect(card.text()).toContain('2 mensajes');
    expect(card.text()).toContain('1 borrador');
    expect(card.text()).toContain('24 ago');
  });

  it('shortens the compact message preview to one normalized line', () => {
    const wrapper = mountList();
    const excerpt = wrapper.get('[data-testid="communication-thread-excerpt-41"]');
    const excerptContent = excerpt.text().replace(/^Cliente:\s*/, '');

    expect(excerpt.text()).toMatch(/^Cliente:/);
    expect(excerptContent).not.toMatch(/\s{2,}/);
    expect(excerptContent).toHaveLength(120);
    expect(excerptContent.endsWith('…')).toBe(true);
    expect(excerpt.classes()).toContain('truncate');
    expect(excerpt.attributes('title')).toBeUndefined();
  });

  it('omits the preview when the thread has no messages', () => {
    const wrapper = mountList({ threads: [thread({ latest_message: null })] });

    expect(wrapper.find('[data-testid="communication-thread-excerpt-41"]').exists()).toBe(false);
  });

  it('removes the redundant compact card label', () => {
    const wrapper = mountList();

    expect(wrapper.text()).not.toContain('Hilo');
  });

  it('keeps compact content inside the list width', () => {
    const wrapper = mountList();

    expect(wrapper.get('[data-testid="communication-thread-list"]').classes())
      .toContain('overflow-x-hidden');
    expect(wrapper.get('[data-testid="communication-thread-row-41"]').classes())
      .toContain('overflow-hidden');
  });

  it('labels the desktop identity column as Asunto', () => {
    const wrapper = mountList({ compact: false });
    const table = wrapper.getComponent(BaseResponsiveTableStub);

    expect(table.props('columns').find((column) => column.key === 'title').label).toBe('Asunto');
  });

  it('opens the thread from the compact card surface', async () => {
    const wrapper = mountList();

    await wrapper.get('[data-testid="communication-thread-row-41"]').trigger('click');

    expect(wrapper.emitted('open')).toHaveLength(1);
    expect(wrapper.emitted('open')[0][0]).toMatchObject({ id: 41 });
  });
});
