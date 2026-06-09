import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import ProjectsTable from '../../components/platform/projects/ProjectsTable.vue'

describe('ProjectsTable', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  const rows = [
    {
      id: 1, name: 'Project A', status: 'active', progress: 40,
      client_name: 'Ada Lovelace', client_email: 'ada@e.co', client_id: 9,
      bugs_open_count: 3, changes_pending_count: 1,
      next_deliverable: null,
      last_activity_at: '2026-05-15T10:00:00Z',
    },
  ]

  it('renders one row per project with the expected columns', () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'admin' } })
    expect(w.text()).toContain('Project A')
    expect(w.text()).toContain('Ada Lovelace')
    expect(w.text()).toContain('40')
    expect(w.text()).toContain('3') // bugs_open_count
  })

  it('emits navigate event on row click with the project id', async () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'admin' } })
    await w.find('[data-testid="project-row-1"]').trigger('click')
    expect(w.emitted('navigate')[0]).toEqual([1])
  })

  it('hides admin-only columns when role is client', () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'client' } })
    expect(w.text()).not.toContain('Ada Lovelace')
  })

  it('renders a mobile card per project that emits navigate on click', async () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'admin' } })
    const card = w.find('[data-testid="project-card-1"]')
    expect(card.exists()).toBe(true)
    await card.trigger('click')
    expect(w.emitted('navigate')[0]).toEqual([1])
  })
})
