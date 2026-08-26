import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import ProjectStateTransitionModal from '../../components/panel/projects/ProjectStateTransitionModal.vue';
import { useProjectStateStore } from '../../stores/project_states';
import { create_request } from '../../stores/services/request_http';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}));

const PROJECT = {
  id: 9,
  name: 'Kore',
  status_label: 'Activo',
  current_state: {
    id: 2,
    name: 'Activo',
    operational_effect: 'operating',
  },
};

const STATES = [
  {
    id: 2,
    name: 'Activo',
    color: 'emerald',
    operational_effect: 'operating',
    is_active: true,
    merged_into: null,
  },
  {
    id: 4,
    name: 'Suspendido',
    color: 'orange',
    operational_effect: 'suspended',
    is_active: true,
    merged_into: null,
  },
  {
    id: 6,
    name: 'Dado de baja',
    color: 'gray',
    operational_effect: 'decommissioned',
    is_active: true,
    merged_into: null,
  },
];

function mountModal() {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useProjectStateStore();
  store.states = STATES;
  const wrapper = mount(ProjectStateTransitionModal, {
    props: { open: false, project: PROJECT },
    global: {
      plugins: [pinia],
      stubs: {
        BaseModal: {
          props: ['modelValue'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseAlert: { template: '<div><slot /></div>' },
        BaseBadge: { template: '<span><slot /></span>' },
        BaseFormField: { template: '<div><slot /></div>' },
        BaseToggle: {
          props: ['modelValue', 'size'],
          emits: ['update:modelValue'],
          template: '<input type="checkbox" />',
        },
        BaseTextarea: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseButton: {
          props: ['disabled'],
          emits: ['click'],
          template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
  return { wrapper, store };
}

describe('ProjectStateTransitionModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('previews suspension consequences before confirmation', async () => {
    const impact = {
      target_effect: 'suspended',
      impact_token: 'a'.repeat(64),
      effective_at: '2026-08-26T10:00:00+00:00',
      pending_incomes: [],
      future_incomes: [],
      future_payments: [],
      active_hostings: [],
      blockers: [],
    };
    create_request.mockResolvedValueOnce({ data: impact });
    const { wrapper } = mountModal();
    await wrapper.setProps({ open: true });
    await wrapper.get('[data-testid="project-state-target"]').setValue('4');

    await wrapper.get('[data-testid="project-state-preview"]').trigger('click');
    await flushPromises();

    expect(create_request).toHaveBeenCalledWith(
      'projects/9/state-transitions/preview/',
      { state_id: 4 },
    );
    expect(wrapper.get('[data-testid="project-state-impact"]').text())
      .toContain('La deuda ya causada se conserva');
  });

  it('requires a debt decision before decommissioning', async () => {
    const impact = {
      target_effect: 'decommissioned',
      impact_token: 'b'.repeat(64),
      effective_at: '2026-08-26T10:00:00+00:00',
      pending_incomes: [{
        id: 41,
        concept: 'Hosting agosto',
        pending_amount: '120000.00',
      }],
      future_incomes: [],
      future_payments: [],
      active_hostings: [],
      blockers: [],
    };
    create_request
      .mockResolvedValueOnce({ data: impact })
      .mockResolvedValueOnce({
        data: { project: { ...PROJECT, status_label: 'Dado de baja' } },
      });
    const { wrapper } = mountModal();
    await wrapper.setProps({ open: true });
    await wrapper.get('[data-testid="project-state-target"]').setValue('6');
    await wrapper.get('[data-testid="project-state-preview"]').trigger('click');
    await flushPromises();

    const apply = wrapper.get('[data-testid="project-state-apply"]');
    expect(apply.attributes('disabled')).toBeDefined();
    await wrapper.get('[data-testid="project-state-income-41"]')
      .setValue('keep_receivable');
    await wrapper.get('[data-testid="project-state-note"]')
      .setValue('Baja directa confirmada por el cliente.');
    expect(apply.attributes('disabled')).toBeUndefined();

    await apply.trigger('click');
    await flushPromises();

    expect(create_request).toHaveBeenLastCalledWith(
      'projects/9/state-transitions/',
      {
        state_id: 6,
        impact_token: 'b'.repeat(64),
        effective_at: '2026-08-26T10:00:00+00:00',
        note: 'Baja directa confirmada por el cliente.',
        resolutions: [{ income_id: 41, action: 'keep_receivable' }],
      },
    );
    expect(wrapper.emitted('changed')).toHaveLength(1);
  });
});
