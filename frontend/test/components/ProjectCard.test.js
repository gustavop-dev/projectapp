import { mount } from '@vue/test-utils';
import ProjectCard from '../../components/panel/projects/ProjectCard.vue';

const PROJECT = {
  id: 12,
  name: 'Proyecto Atlas',
  status: 'active',
  status_label: 'Activo',
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
});
