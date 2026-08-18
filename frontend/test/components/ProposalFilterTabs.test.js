// Sortable needs a real pointer to do anything, so the drag gesture itself
// belongs to the E2E. Here the stub stands in for it and the test drives the
// two events vuedraggable would emit: the reordered array, then `end`.
// `emits` is declared on purpose — without it the listeners fall through to
// the DOM and every handler fires twice.
jest.mock('vuedraggable', () => ({
  __esModule: true,
  default: {
    name: 'DraggableStub',
    props: ['modelValue'],
    emits: ['update:modelValue', 'start', 'end'],
    template: '<div><template v-for="(element, index) in modelValue || []" :key="element.id ?? index"><slot name="item" :element="element" :index="index" /></template></div>',
  },
}));

// eslint-disable-next-line import/first
import { mount, flushPromises } from '@vue/test-utils';
// eslint-disable-next-line import/first
import ProposalFilterTabs from '../../components/proposals/ProposalFilterTabs.vue';

function mountTabs(props = {}) {
  return mount(ProposalFilterTabs, {
    props: {
      tabs: [
        { id: 'tab-1', name: 'Tab Uno' },
        { id: 'tab-2', name: 'Tab Dos' },
      ],
      activeTabId: 'all',
      isTabLimitReached: false,
      ...props,
    },
  });
}

describe('ProposalFilterTabs', () => {
  it('emits select when the mobile dropdown changes', async () => {
    const wrapper = mountTabs();

    await wrapper.get('select').setValue('tab-2');

    expect(wrapper.emitted('select')).toEqual([['tab-2']]);
  });

  it('opens the create input and emits the trimmed tab name', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-create"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-input"]').setValue('  Nuevo tab  ');
    await wrapper.get('[data-testid="filter-tabs-confirm"]').trigger('click');

    expect(wrapper.emitted('create')).toEqual([['Nuevo tab']]);
    expect(wrapper.find('[data-testid="filter-tabs-input"]').exists()).toBe(false);
  });

  it('disables the create button when the tab limit is reached', () => {
    const wrapper = mountTabs({ isTabLimitReached: true });
    const button = wrapper.get('[data-testid="filter-tabs-create"]');

    expect(button.attributes('disabled')).toBeDefined();
    expect(button.attributes('title')).toBe('Máximo 2 pestañas');
  });

  it('opens the tab menu and closes it from the overlay', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-menu-tab-1"]').trigger('click');
    expect(wrapper.get('[data-testid="filter-tabs-overlay"]').exists()).toBe(true);

    await wrapper.get('[data-testid="filter-tabs-overlay"]').trigger('click');
    expect(wrapper.find('[data-testid="filter-tabs-overlay"]').exists()).toBe(false);
  });

  it('closes the tab menu when the same menu trigger is clicked twice', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-menu-tab-1"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-menu-tab-1"]').trigger('click');

    expect(wrapper.find('[data-testid="filter-tabs-overlay"]').exists()).toBe(false);
  });

  it('starts rename mode from the context menu and emits the new tab name', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-menu-tab-1"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-rename"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="filter-tabs-input"]').setValue('  Renombrada  ');
    await wrapper.get('[data-testid="filter-tabs-confirm"]').trigger('click');

    expect(wrapper.emitted('rename')).toEqual([['tab-1', 'Renombrada']]);
  });

  it('emits delete for the selected tab from the context menu', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-menu-tab-2"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-delete"]').trigger('click');

    expect(wrapper.emitted('delete')).toEqual([['tab-2']]);
    expect(wrapper.find('[data-testid="filter-tabs-overlay"]').exists()).toBe(false);
  });

  it('cancels the inline input on escape', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-create"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-input"]').setValue('Temporal');
    await wrapper.get('[data-testid="filter-tabs-input"]').trigger('keyup.escape');

    expect(wrapper.find('[data-testid="filter-tabs-input"]').exists()).toBe(false);
    expect(wrapper.emitted('create')).toBeUndefined();
  });

  it('ignores confirmation when the trimmed input is empty', async () => {
    const wrapper = mountTabs();

    await wrapper.get('[data-testid="filter-tabs-create"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-input"]').setValue('   ');
    await wrapper.get('[data-testid="filter-tabs-input"]').trigger('keyup.enter');

    expect(wrapper.find('[data-testid="filter-tabs-input"]').exists()).toBe(true);
    expect(wrapper.emitted('create')).toBeUndefined();
    expect(wrapper.emitted('rename')).toBeUndefined();
  });

  it('emits select when a desktop tab button is clicked', async () => {
    const wrapper = mountTabs({ activeTabId: 'tab-1' });

    await wrapper.get('[data-testid="filter-tabs-tab-tab-2"]').trigger('click');

    expect(wrapper.emitted('select')).toEqual([['tab-2']]);
  });
});

describe('config tab (opt-in)', () => {
  it('is hidden by default', () => {
    const wrapper = mountTabs()
    expect(wrapper.find('[data-testid="filter-tabs-config"]').exists()).toBe(false)
  })

  it('renders and emits config when enabled', async () => {
    const wrapper = mountTabs({ showConfigTab: true })
    const tab = wrapper.find('[data-testid="filter-tabs-config"]')
    expect(tab.exists()).toBe(true)
    await tab.trigger('click')
    expect(wrapper.emitted('config')).toHaveLength(1)
  })

  it('marks the config tab active via configActive', () => {
    const wrapper = mountTabs({ showConfigTab: true, configActive: true })
    expect(
      wrapper.find('[data-testid="filter-tabs-config"]').classes(),
    ).toContain('border-emerald-600')
  })
})

describe('ProposalFilterTabs restorable base', () => {
  const driftedTab = {
    id: 'tab-1',
    name: 'Solo esperados',
    filters: { kind: 'expected' },
    base_filters: { kind: 'expected', paymentStatus: 'pending' },
  };

  it('shows the modified dot only when filters drift from base_filters', () => {
    const wrapper = mountTabs({
      tabs: [
        driftedTab,
        {
          id: 'tab-2',
          name: 'Expanded but equal',
          filters: {
            search: '', kind: 'expected', paymentStatus: 'pending', partner: '',
          },
          base_filters: { kind: 'expected', paymentStatus: 'pending' },
        },
        { id: 'lost', name: 'Builtin', builtin: true },
      ],
    });

    expect(wrapper.find('[data-testid="filter-tabs-modified-tab-1"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-tabs-modified-tab-2"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="filter-tabs-modified-lost"]').exists()).toBe(false);
  });

  it('emits restore from the context menu and closes it', async () => {
    const wrapper = mountTabs({ tabs: [driftedTab] });

    await wrapper.get('[data-testid="filter-tabs-menu-tab-1"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-restore"]').trigger('click');

    expect(wrapper.emitted('restore')).toEqual([['tab-1']]);
    expect(wrapper.find('[data-testid="filter-tabs-restore"]').exists()).toBe(false);
  });

  it('emits rebase from the context menu', async () => {
    const wrapper = mountTabs({ tabs: [driftedTab] });

    await wrapper.get('[data-testid="filter-tabs-menu-tab-1"]').trigger('click');
    await wrapper.get('[data-testid="filter-tabs-rebase"]').trigger('click');

    expect(wrapper.emitted('rebase')).toEqual([['tab-1']]);
  });

  it('hides restore and rebase for a tab without drift', async () => {
    const wrapper = mountTabs({
      tabs: [{
        id: 'tab-3',
        name: 'Al día',
        filters: { kind: 'liquid' },
        base_filters: { kind: 'liquid' },
      }],
    });

    await wrapper.get('[data-testid="filter-tabs-menu-tab-3"]').trigger('click');

    expect(wrapper.find('[data-testid="filter-tabs-rename"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-tabs-restore"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="filter-tabs-rebase"]').exists()).toBe(false);
  });

  it('shows the match count on the tabs that were given one', () => {
    const wrapper = mountTabs({ counts: { 'tab-1': 7 } });

    expect(wrapper.get('[data-testid="filter-tabs-count-tab-1"]').text()).toBe('(7)');
    expect(wrapper.find('[data-testid="filter-tabs-count-tab-2"]').exists()).toBe(false);
  });

  it('shows a zero count instead of hiding it', () => {
    const wrapper = mountTabs({ counts: { 'tab-1': 0 } });

    expect(wrapper.get('[data-testid="filter-tabs-count-tab-1"]').text()).toBe('(0)');
  });

  it('stays badge-free for the views that pass no counts', () => {
    const wrapper = mountTabs();

    expect(wrapper.find('[data-testid="filter-tabs-count-tab-1"]').exists()).toBe(false);
    expect(wrapper.get('select').text()).not.toContain('(');
  });

  it('keys the count by the id so numeric saved-tab ids resolve', () => {
    const wrapper = mountTabs({
      tabs: [{ id: 12, name: 'Guardado' }],
      counts: { 12: 3 },
    });

    expect(wrapper.get('[data-testid="filter-tabs-count-12"]').text()).toBe('(3)');
  });

  it('badges "Todas" with the unfiltered total when the view sends one', () => {
    const wrapper = mountTabs({ counts: { all: 42 } });

    expect(wrapper.get('[data-testid="filter-tabs-count-all"]').text()).toBe('(42)');
  });

  it('says what the count means in the view that is showing it', () => {
    const wrapper = mountTabs({
      counts: { 'tab-1': 1 },
      countTitle: 'Envíos que cumplen este filtro',
    });

    expect(
      wrapper.get('[data-testid="filter-tabs-count-tab-1"]').attributes('title'),
    ).toBe('Envíos que cumplen este filtro');
  });

  it('leaves a hidden tab out of the strip without deleting it', () => {
    const wrapper = mountTabs({
      tabs: [
        { id: 'tab-1', name: 'Tab Uno' },
        { id: 'tab-2', name: 'Tab Dos', is_hidden: true },
      ],
    });

    expect(wrapper.find('[data-testid="filter-tabs-tab-tab-1"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-tabs-tab-tab-2"]').exists()).toBe(false);
  });

  // Ningún filtro predefinido puede quedar inalcanzable. El mecanismo es
  // envolver en varias líneas: nada se manda a un menú ni se recorta, así que
  // el activo tampoco necesita que lo traigan a la vista. jsdom no hace layout
  // —todo boundingClientRect da cero—, así que acá se asserta la clase que
  // decide el mecanismo; que efectivamente no se corte lo prueba el E2E
  // admin-accounting-filter-strip-wrap.spec.js midiendo scrollWidth.
  describe('overflow', () => {
    const manyTabs = Array.from({ length: 12 }, (_, i) => ({
      id: `tab-${i + 1}`, name: `Tab ${i + 1}`,
    }));

    it('renders every tab inline, however many there are', () => {
      const wrapper = mountTabs({ tabs: manyTabs });

      expect(wrapper.findAll('[data-testid^="filter-tabs-tab-"]')).toHaveLength(12);
      expect(wrapper.find('[data-testid="filter-tabs-tab-tab-12"]').exists()).toBe(true);
    });

    it('hides nothing behind a "+N" menu', () => {
      const wrapper = mountTabs({ tabs: manyTabs });

      expect(wrapper.find('[data-testid="filter-tabs-overflow"]').exists()).toBe(false);
    });

    it('wraps the strip onto several lines instead of clipping it', () => {
      const wrapper = mountTabs({ tabs: manyTabs });
      const strip = wrapper.find('.md\\:flex');

      expect(strip.classes()).toEqual(
        expect.arrayContaining(['flex-wrap', 'md:flex']),
      );
      expect(strip.classes()).not.toContain('overflow-x-auto');
    });

    it('keeps the selected tab rendered wherever it falls in the strip', () => {
      const wrapper = mountTabs({ tabs: manyTabs, activeTabId: 'tab-12' });

      expect(wrapper.get('[data-testid="filter-tabs-tab-tab-12"]').classes())
        .toContain('border-emerald-600');
    });

    it('still lists every tab in the mobile dropdown', () => {
      const wrapper = mountTabs({ tabs: manyTabs });

      expect(wrapper.get('select').findAll('option')).toHaveLength(13);
    });
  });
  describe('reordenar la tira', () => {
    const threeTabs = [
      { id: 'lost', name: 'Perdidos', builtin: true },
      { id: 7, name: 'Liquidos' },
      { id: 8, name: 'Gustavo' },
    ];

    function draggable(wrapper) {
      return wrapper.findComponent({ name: 'DraggableStub' });
    }

    /** What vuedraggable does on a drop: rewrite the array, then emit end. */
    async function drop(wrapper, nextOrder) {
      const drag = draggable(wrapper);
      await drag.vm.$emit('start');
      await drag.vm.$emit('update:modelValue', nextOrder);
      await drag.vm.$emit('end');
    }

    it('emite el nuevo orden al soltar', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await drop(wrapper, [threeTabs[1], threeTabs[0], threeTabs[2]]);

      expect(wrapper.emitted('reorder')).toEqual([[[7, 'lost', 8]]]);
    });

    it('no emite nada si el arrastre termina donde empezo', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await drop(wrapper, [...threeTabs]);

      expect(wrapper.emitted('reorder')).toBeUndefined();
    });

    it('arrastrar no aplica el filtro', async () => {
      // Punto 2 de la ficha: mover y seleccionar arrancan igual, y la tira
      // cambia toda la vista. Un arrastre que vuelve a su sitio sigue
      // llegando al navegador como un click sobre el chip.
      const wrapper = mountTabs({ tabs: threeTabs });

      await drop(wrapper, [threeTabs[1], threeTabs[0], threeTabs[2]]);
      await wrapper.get('[data-testid="filter-tabs-tab-7"]').trigger('click');

      expect(wrapper.emitted('select')).toBeUndefined();
    });

    it('vuelve a aceptar clicks cuando el arrastre quedo atras', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await drop(wrapper, [threeTabs[1], threeTabs[0], threeTabs[2]]);
      await new Promise((resolve) => { setTimeout(resolve, 0); });
      await wrapper.get('[data-testid="filter-tabs-tab-7"]').trigger('click');

      expect(wrapper.emitted('select')).toEqual([[7]]);
    });

    it('mueve a la derecha desde el menu del filtro', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await wrapper.get('[data-testid="filter-tabs-menu-7"]').trigger('click');
      await wrapper.get('[data-testid="filter-tabs-move-right-7"]').trigger('click');

      expect(wrapper.emitted('reorder')).toEqual([[['lost', 8, 7]]]);
    });

    it('un builtin tambien se mueve desde su menu', async () => {
      // Punto 4: los de fabrica se reordenan junto a los propios.
      const wrapper = mountTabs({ tabs: threeTabs });

      await wrapper.get('[data-testid="filter-tabs-menu-lost"]').trigger('click');
      await wrapper.get('[data-testid="filter-tabs-move-right-lost"]').trigger('click');

      expect(wrapper.emitted('reorder')).toEqual([[[7, 'lost', 8]]]);
    });

    it('el menu de un builtin no ofrece renombrar ni eliminar', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await wrapper.get('[data-testid="filter-tabs-menu-lost"]').trigger('click');

      expect(wrapper.find('[data-testid="filter-tabs-rename"]').exists()).toBe(false);
      expect(wrapper.find('[data-testid="filter-tabs-delete"]').exists()).toBe(false);
      expect(wrapper.find('[data-testid="filter-tabs-move-left-lost"]').exists()).toBe(true);
    });

    it('deshabilita mover en los extremos', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await wrapper.get('[data-testid="filter-tabs-menu-lost"]').trigger('click');

      // 'lost' es el primero: a la izquierda no hay a dónde ir.
      expect(wrapper.get('[data-testid="filter-tabs-move-left-lost"]').element.disabled)
        .toBe(true);
      expect(wrapper.get('[data-testid="filter-tabs-move-right-lost"]').element.disabled)
        .toBe(false);

      await wrapper.get('[data-testid="filter-tabs-move-left-lost"]').trigger('click');
      expect(wrapper.emitted('reorder')).toBeUndefined();
    });

    it('mueve con Ctrl y las flechas, y anuncia donde quedo', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await wrapper.get('[data-testid="filter-tabs-tab-8"]')
        .trigger('keydown', { key: 'ArrowLeft', ctrlKey: true });

      expect(wrapper.emitted('reorder')).toEqual([[['lost', 8, 7]]]);
      expect(wrapper.get('[data-testid="filter-tabs-live"]').text())
        .toBe('\u00ABGustavo\u00BB movido a la posici\u00F3n 2 de 3');
    });

    it('ignora las flechas sin Ctrl, que son como se recorre la tira', async () => {
      const wrapper = mountTabs({ tabs: threeTabs });

      await wrapper.get('[data-testid="filter-tabs-tab-8"]')
        .trigger('keydown', { key: 'ArrowLeft' });

      expect(wrapper.emitted('reorder')).toBeUndefined();
    });

    it('el orden emitido deja fuera las ocultas, que no se ven', async () => {
      const wrapper = mountTabs({
        tabs: [
          { id: 7, name: 'Liquidos' },
          { id: 9, name: 'Oculta', is_hidden: true },
          { id: 8, name: 'Gustavo' },
        ],
      });

      await wrapper.get('[data-testid="filter-tabs-menu-7"]').trigger('click');
      await wrapper.get('[data-testid="filter-tabs-move-right-7"]').trigger('click');

      expect(wrapper.emitted('reorder')).toEqual([[[8, 7]]]);
    });
  });
});
