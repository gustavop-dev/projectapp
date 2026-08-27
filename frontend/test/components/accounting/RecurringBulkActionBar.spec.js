import { flushPromises, mount } from '@vue/test-utils';

import RecurringBulkActionBar from '~/components/accounting/RecurringBulkActionBar.vue';

const BaseBulkActionBarStub = {
  props: [
    'selectedCount', 'outsideCount', 'filteredCount', 'allFilteredSelected',
    'actions', 'busy', 'testidPrefix',
  ],
  emits: ['select-all', 'clear'],
  template: `
    <div v-if="selectedCount" data-testid="bulk-stub">
      <button type="button" data-testid="select-all" @click="$emit('select-all')">Todos</button>
      <button
        v-for="item in actions.filter((entry) => !entry.divider)"
        :key="item.action"
        type="button"
        :data-testid="\`bulk-action-\${item.action}\`"
        @click="item.onClick()"
      >{{ item.label }}</button>
    </div>
  `,
};

const ConfirmModalStub = {
  props: [
    'modelValue', 'title', 'message', 'confirmText', 'cancelText', 'variant', 'size',
  ],
  emits: ['update:modelValue', 'confirm', 'cancel'],
  template: `
    <div v-if="modelValue" data-testid="confirm-stub">
      <h2>{{ title }}</h2>
      <p>{{ message }}</p>
      <slot />
      <button type="button" data-testid="confirm" @click="$emit('confirm')">{{ confirmText }}</button>
    </div>
  `,
};

const ROWS = [
  { id: 1, name: 'Figma' },
  { id: 2, name: 'Cloudflare' },
  { id: 3, name: 'Google Workspace' },
];

function mountBar(props = {}) {
  return mount(RecurringBulkActionBar, {
    props: {
      rows: ROWS,
      selected: [1, 3],
      filteredIds: [1, 2],
      busy: false,
      ...props,
    },
    global: {
      stubs: {
        BaseBulkActionBar: BaseBulkActionBarStub,
        ConfirmModal: ConfirmModalStub,
      },
    },
  });
}

describe('RecurringBulkActionBar', () => {
  it('confirms the complete selection by name', async () => {
    const wrapper = mountBar();

    await wrapper.get('[data-testid="bulk-action-archive"]').trigger('click');

    expect(wrapper.get('[data-testid="confirm-stub"]').text()).toContain('Figma');
    expect(wrapper.get('[data-testid="confirm-stub"]').text()).toContain('Google Workspace');
  });

  it('submits one atomic lifecycle request', async () => {
    const wrapper = mountBar();
    await wrapper.get('[data-testid="bulk-action-deactivate"]').trigger('click');

    await wrapper.get('[data-testid="confirm"]').trigger('click');
    await flushPromises();

    expect(wrapper.emitted('submit')[0][0]).toEqual({
      ids: [1, 3],
      action: 'deactivate',
    });
  });

  it('extends the selection to every filtered payment', async () => {
    const wrapper = mountBar();

    await wrapper.get('[data-testid="select-all"]').trigger('click');

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([1, 3, 2]);
  });
});
