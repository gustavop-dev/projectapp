import { mount, flushPromises } from '@vue/test-utils';
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

    expect(wrapper.get('[data-testid="filter-tabs-count-tab-1"]').text()).toBe('7');
    expect(wrapper.find('[data-testid="filter-tabs-count-tab-2"]').exists()).toBe(false);
  });

  it('shows a zero count instead of hiding it', () => {
    const wrapper = mountTabs({ counts: { 'tab-1': 0 } });

    expect(wrapper.get('[data-testid="filter-tabs-count-tab-1"]').text()).toBe('0');
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

    expect(wrapper.get('[data-testid="filter-tabs-count-12"]').text()).toBe('3');
  });

  it('badges "Todas" with the unfiltered total when the view sends one', () => {
    const wrapper = mountTabs({ counts: { all: 42 } });

    expect(wrapper.get('[data-testid="filter-tabs-count-all"]').text()).toBe('42');
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

  describe('overflow', () => {
    const manyTabs = Array.from({ length: 5 }, (_, i) => ({
      id: `tab-${i + 1}`, name: `Tab ${i + 1}`,
    }));

    it('renders every tab inline while no limit is set', () => {
      const wrapper = mountTabs({ tabs: manyTabs });

      expect(wrapper.find('[data-testid="filter-tabs-overflow"]').exists()).toBe(false);
      expect(wrapper.find('[data-testid="filter-tabs-tab-tab-5"]').exists()).toBe(true);
    });

    it('moves what does not fit into a "+N" menu', () => {
      const wrapper = mountTabs({ tabs: manyTabs, maxVisible: 3 });

      expect(wrapper.get('[data-testid="filter-tabs-overflow"]').text()).toBe('+2');
      expect(wrapper.find('[data-testid="filter-tabs-tab-tab-3"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="filter-tabs-tab-tab-4"]').exists()).toBe(false);
    });

    it('keeps the selected tab visible even when it belongs to the overflow', () => {
      const wrapper = mountTabs({
        tabs: manyTabs, maxVisible: 3, activeTabId: 'tab-5',
      });

      expect(wrapper.find('[data-testid="filter-tabs-tab-tab-5"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="filter-tabs-tab-tab-3"]').exists()).toBe(false);
      expect(wrapper.get('[data-testid="filter-tabs-overflow"]').text()).toBe('+2');
    });

    it('still lists every tab in the mobile dropdown', () => {
      const wrapper = mountTabs({ tabs: manyTabs, maxVisible: 3 });

      expect(wrapper.get('select').findAll('option')).toHaveLength(6);
    });
  });
});
