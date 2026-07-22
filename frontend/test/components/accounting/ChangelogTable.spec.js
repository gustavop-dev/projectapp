import { mount } from '@vue/test-utils';
import ChangelogTable from '~/components/accounting/ChangelogTable.vue';

const entries = [
  {
    id: 1,
    entity_type: 'income',
    entity_type_label: 'Ingreso',
    object_id: 10,
    object_repr: 'Página web Acme',
    action: 'updated',
    action_label: 'Actualizado',
    changes: [{ field: 'amount', label: 'Valor', old: '100000', new: '200000' }],
    actor_username: 'gustavo',
    created_at: '2026-06-15T14:30:00-05:00',
  },
  {
    id: 2,
    entity_type: 'expense',
    entity_type_label: 'Gasto',
    object_id: 22,
    object_repr: 'Dominio .com',
    action: 'created',
    action_label: 'Creado',
    changes: [{ field: 'concept', label: 'Concepto', old: null, new: 'Dominio .com' }],
    actor_username: null,
    created_at: '2026-06-16T09:05:00-05:00',
  },
  {
    id: 3,
    entity_type: 'hosting',
    entity_type_label: 'Hosting',
    object_id: 5,
    object_repr: 'Hosting Beta',
    action: 'deleted',
    action_label: 'Eliminado',
    changes: [{ field: 'status', label: 'Estado', old: 'active', new: null }],
    actor_username: 'carlos',
    created_at: '2026-06-17T18:00:00-05:00',
  },
];

function mountTable(props = {}) {
  return mount(ChangelogTable, { props: { entries, ...props } });
}

describe('ChangelogTable', () => {
  it('renders one row per entry with formatted date and actor', () => {
    const wrapper = mountTable();

    const row = wrapper.find('[data-testid="changelog-row-1"]');
    expect(row.exists()).toBe(true);
    expect(row.text()).toContain('Lun, 15 jun 2026, 14:30');
    expect(row.text()).toContain('gustavo');
    expect(row.text()).toContain('Ingreso');
    expect(row.text()).toContain('Página web Acme');
  });

  it('shows "Sistema" when actor_username is missing', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="changelog-row-2"]').text()).toContain('Sistema');
  });

  it('applies action badge tone per action type', () => {
    const wrapper = mountTable();

    const badge = (id) =>
      wrapper.find(`[data-testid="changelog-row-${id}"]`).find('span.rounded-full');
    expect(badge(2).classes()).toContain('bg-success-soft'); // created
    expect(badge(1).classes()).toContain('bg-primary-soft'); // updated
    expect(badge(3).classes()).toContain('bg-danger-soft'); // deleted
  });

  it('toggles the expanded detail row on click', async () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="changelog-detail-1"]').exists()).toBe(false);

    await wrapper.find('[data-testid="changelog-row-1"]').trigger('click');
    expect(wrapper.find('[data-testid="changelog-detail-1"]').exists()).toBe(true);

    await wrapper.find('[data-testid="changelog-row-1"]').trigger('click');
    expect(wrapper.find('[data-testid="changelog-detail-1"]').exists()).toBe(false);
  });

  it('shows old → new diff for updated entries', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="changelog-row-1"]').trigger('click');
    const detail = wrapper.find('[data-testid="changelog-detail-1"]');
    expect(detail.text()).toContain('Valor:');
    expect(detail.text()).toContain('100000 → 200000');
  });

  it('shows only the new value for created entries', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="changelog-row-2"]').trigger('click');
    const detail = wrapper.find('[data-testid="changelog-detail-2"]');
    expect(detail.text()).toContain('Concepto:');
    expect(detail.text()).toContain('Dominio .com');
    expect(detail.text()).not.toContain('→');
  });

  it('shows only the old value for deleted entries', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="changelog-row-3"]').trigger('click');
    const detail = wrapper.find('[data-testid="changelog-detail-3"]');
    expect(detail.text()).toContain('Estado:');
    expect(detail.text()).toContain('active');
    expect(detail.text()).not.toContain('→');
  });

  it('renders the empty state when there are no entries', () => {
    const wrapper = mountTable({ entries: [] });

    expect(wrapper.text()).toContain('Sin registros.');
  });
});
