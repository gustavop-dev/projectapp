import { mount } from '@vue/test-utils';
import ProjectCard from '../../components/panel/projects/ProjectCard.vue';

const PROJECT = {
  id: 12,
  name: 'Proyecto Atlas',
  status: 'active',
  status_label: 'Activo',
  current_state: {
    id: 2,
    name: 'Activo',
    color: 'emerald',
    operational_effect: 'operating',
  },
  created_at: '2026-08-01T10:00:00Z',
  client_name: 'Ana Torres',
  client_company: 'Atlas SAS',
  hostings_count: 2,
  incomes_count: 3,
  unlinked_hostings_count: 1,
  unlinked_incomes_count: 2,
  unlinked_documents_count: 1,
};

function mountCard(props = {}) {
  return mount(ProjectCard, {
    props: { project: PROJECT, ...props },
    global: {
      stubs: {
        NuxtLink: { template: '<a><slot /></a>' },
        BaseBadge: { template: '<span><slot /></span>' },
        ProjectSpaceLink: { template: '<a>Espacio</a>' },
      },
    },
  });
}

describe('ProjectCard', () => {
  it('presents the project identity and operational counts', () => {
    const wrapper = mountCard();

    expect(wrapper.text()).toContain('Proyecto Atlas');
    expect(wrapper.text()).toContain('Ana Torres');
    expect(wrapper.text()).toContain('Atlas SAS');
    expect(wrapper.text()).toContain('Hostings');
    expect(wrapper.text()).toContain('Ingresos');
    expect(wrapper.text()).toContain('4 registros sin proyecto');
    expect(wrapper.get('[data-testid="project-communications-12"]').text())
      .toContain('Comunicaciones');
  });

  it('puts status below an intrinsically contained unbroken project name', () => {
    const wrapper = mountCard({
      project: {
        ...PROJECT,
        name: 'Levantamiento_Fase_4_Multi-Tenant_24082026',
      },
    });
    const title = wrapper.get('h2');
    const status = wrapper.get('[data-testid="project-card-status-12"]');

    expect(title.classes()).toContain('[overflow-wrap:anywhere]');
    expect(title.element.compareDocumentPosition(status.element) & Node.DOCUMENT_POSITION_FOLLOWING)
      .toBeTruthy();
  });

  it('opens the action menu for its project', async () => {
    const wrapper = mountCard();

    await wrapper.get('[data-testid="project-actions-12"]').trigger('click');

    expect(wrapper.emitted('actions')).toEqual([[PROJECT]]);
  });

  it('offers the touch fallback for unlinked records', async () => {
    const wrapper = mountCard();

    await wrapper.get('[data-testid="project-assign-unlinked-12"]').trigger('click');

    expect(wrapper.emitted('assign')).toEqual([[PROJECT]]);
  });

  it('offers lifecycle review when the project needs classification', async () => {
    const project = { ...PROJECT, state_review_required: true };
    const wrapper = mountCard({ project });

    await wrapper.get('[data-testid="project-state-review-12"]').trigger('click');

    expect(wrapper.emitted('change-state')).toEqual([[project]]);
  });

  it('hides assignment for a terminal project', () => {
    const wrapper = mountCard({
      project: {
        ...PROJECT,
        current_state: {
          id: 6,
          name: 'Dado de baja',
          color: 'gray',
          operational_effect: 'decommissioned',
        },
      },
    });

    expect(wrapper.find('[data-testid="project-assign-unlinked-12"]').exists())
      .toBe(false);
  });
});
