import { mount } from '@vue/test-utils';
import { useProposalStore } from '~/stores/proposals';
import ProjectScheduleEditor from '../../components/BusinessProposal/admin/ProjectScheduleEditor.vue';

jest.mock('~/stores/proposals', () => ({
  useProposalStore: jest.fn(),
}));

const proposalStore = {
  currentProposal: null,
  updateProjectStage: jest.fn(),
  completeProjectStage: jest.fn(),
};

const baseProposal = {
  id: 77,
  project_stages: [],
};

function mountEditor(props = {}) {
  return mount(ProjectScheduleEditor, {
    props: {
      proposal: baseProposal,
      ...props,
    },
  });
}

describe('ProjectScheduleEditor', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2026-04-09T12:00:00Z'));
    proposalStore.currentProposal = null;
    proposalStore.updateProjectStage.mockReset();
    proposalStore.completeProjectStage.mockReset();
    useProposalStore.mockReturnValue(proposalStore);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders placeholder stages when the proposal has no project stages', () => {
    const wrapper = mountEditor();

    expect(wrapper.find('[data-testid="stage-card-design"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="stage-card-development"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Sin programar');
  });

  it('falls back to an empty stage list when the source has no project_stages field', () => {
    const wrapper = mountEditor({
      proposal: { id: 77 },
    });

    expect(wrapper.find('[data-testid="stage-card-design"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Sin programar');
  });

  it('reads stage data from the store when currentProposal matches the prop id', () => {
    proposalStore.currentProposal = {
      id: 77,
      project_stages: [
        {
          id: 1,
          stage_key: 'design',
          stage_label: 'Diseño real',
          start_date: '2026-04-01',
          end_date: '2026-04-12',
          completed_at: null,
        },
      ],
    };

    const wrapper = mountEditor({
      proposal: {
        id: 77,
        project_stages: [],
      },
    });

    expect(wrapper.find('[data-testid="stage-start-design"]').element.value).toBe('2026-04-01');
    expect(wrapper.text()).toContain('Etapa de Diseño real');
  });

  it('renders the overdue status badge for a late stage', () => {
    const wrapper = mountEditor({
      proposal: {
        id: 77,
        project_stages: [
          {
            id: 1,
            stage_key: 'design',
            stage_label: 'Diseño',
            start_date: '2026-04-01',
            end_date: '2026-04-05',
            completed_at: null,
          },
        ],
      },
    });

    expect(wrapper.find('[data-testid="stage-status-design"]').text()).toContain('Vencida hace');
  });

  it('falls back to the default label when an existing stage_label is empty', () => {
    const wrapper = mountEditor({
      proposal: {
        id: 77,
        project_stages: [
          {
            id: 1,
            stage_key: 'design',
            stage_label: '',
            start_date: '2026-04-01',
            end_date: '2026-04-12',
            completed_at: null,
          },
        ],
      },
    });

    expect(wrapper.text()).toContain('Etapa de Diseño');
  });

  it('renders the completed badge and disables the inputs for a finished stage', () => {
    const wrapper = mountEditor({
      proposal: {
        id: 77,
        project_stages: [
          {
            id: 1,
            stage_key: 'design',
            stage_label: 'Diseño',
            start_date: '2026-04-01',
            end_date: '2026-04-05',
            completed_at: '2026-04-06T12:00:00Z',
          },
        ],
      },
    });

    expect(wrapper.find('[data-testid="stage-status-design"]').text()).toContain('Completada');
    expect(wrapper.find('[data-testid="stage-start-design"]').attributes('disabled')).toBeDefined();
    expect(wrapper.find('[data-testid="stage-save-design"]').attributes('disabled')).toBeDefined();
    expect(wrapper.find('[data-testid="stage-complete-design"]').exists()).toBe(false);
  });

  it('shows a validation error when saving without both dates', async () => {
    const wrapper = mountEditor();

    await wrapper.find('[data-testid="stage-save-design"]').trigger('click');

    expect(wrapper.find('[data-testid="stage-error-design"]').text()).toContain(
      'Debes especificar fecha de inicio y fecha fin.',
    );
    expect(proposalStore.updateProjectStage).not.toHaveBeenCalled();
  });

  it('shows a validation error when start_date is after end_date', async () => {
    const wrapper = mountEditor();

    await wrapper.find('[data-testid="stage-start-design"]').setValue('2026-04-10');
    await wrapper.find('[data-testid="stage-end-design"]').setValue('2026-04-05');
    await wrapper.find('[data-testid="stage-save-design"]').trigger('click');

    expect(wrapper.find('[data-testid="stage-error-design"]').text()).toContain(
      'La fecha fin debe ser igual o posterior a la fecha de inicio.',
    );
  });

  it('calls updateProjectStage with the selected dates when saving succeeds', async () => {
    proposalStore.updateProjectStage.mockResolvedValueOnce({ success: true });
    const wrapper = mountEditor();

    await wrapper.find('[data-testid="stage-start-design"]').setValue('2026-04-01');
    await wrapper.find('[data-testid="stage-end-design"]').setValue('2026-04-15');
    await wrapper.find('[data-testid="stage-save-design"]').trigger('click');

    expect(proposalStore.updateProjectStage).toHaveBeenCalledWith(
      77,
      'design',
      { start_date: '2026-04-01', end_date: '2026-04-15' },
    );
    expect(wrapper.find('[data-testid="stage-error-design"]').exists()).toBe(false);
  });

  it('shows a fallback error when the save request fails', async () => {
    proposalStore.updateProjectStage.mockResolvedValueOnce({ success: false });
    const wrapper = mountEditor();

    await wrapper.find('[data-testid="stage-start-design"]').setValue('2026-04-01');
    await wrapper.find('[data-testid="stage-end-design"]').setValue('2026-04-15');
    await wrapper.find('[data-testid="stage-save-design"]').trigger('click');

    expect(wrapper.find('[data-testid="stage-error-design"]').text()).toContain(
      'No se pudo guardar. Revisa las fechas e inténtalo de nuevo.',
    );
  });

  it('calls completeProjectStage when marking a stage as completed', async () => {
    proposalStore.completeProjectStage.mockResolvedValueOnce({ success: true });
    const wrapper = mountEditor();

    await wrapper.find('[data-testid="stage-complete-design"]').trigger('click');

    expect(proposalStore.completeProjectStage).toHaveBeenCalledWith(77, 'design');
  });

  it('re-syncs the form when the proposal prop changes', async () => {
    const wrapper = mountEditor();

    await wrapper.setProps({
      proposal: {
        id: 77,
        project_stages: [
          {
            id: 1,
            stage_key: 'design',
            stage_label: 'Diseño',
            start_date: '2026-04-03',
            end_date: '2026-04-16',
            completed_at: null,
          },
        ],
      },
    });

    expect(wrapper.find('[data-testid="stage-start-design"]').element.value).toBe('2026-04-03');
    expect(wrapper.find('[data-testid="stage-end-design"]').element.value).toBe('2026-04-16');
  });
});
