import { mount } from '@vue/test-utils'
import TaskCard from '../../components/Tasks/TaskCard.vue'

function baseTask(overrides = {}) {
  return {
    title: 'Fix auth bug',
    description: 'Token expires too soon',
    priority: 'high',
    assignee_name: 'Ana García',
    assignee_email: 'ana@example.com',
    due_date: '2026-05-15',
    is_overdue: false,
    ...overrides,
  }
}

function mountCard(taskOverrides = {}) {
  return mount(TaskCard, { props: { task: baseTask(taskOverrides) } })
}

describe('TaskCard', () => {
  it('renders task title from prop', () => {
    const wrapper = mountCard({ title: 'Deploy to production' })
    expect(wrapper.find('[data-testid="task-card"]').text()).toContain('Deploy to production')
  })

  it('renders description when task.description is provided', () => {
    const wrapper = mountCard({ description: 'Needs review first' })
    expect(wrapper.find('p').exists()).toBe(true)
    expect(wrapper.find('p').text()).toBe('Needs review first')
  })

  it('hides description paragraph when task.description is empty', () => {
    const wrapper = mountCard({ description: '' })
    expect(wrapper.find('p').exists()).toBe(false)
  })

  it('formatDate converts ISO date to locale "Mon D" format', () => {
    const wrapper = mountCard({ due_date: '2026-05-15' })
    expect(wrapper.text()).toContain('May 15')
  })

  it('priorityLabel maps "low" to "Low"', () => {
    const wrapper = mountCard({ priority: 'low' })
    expect(wrapper.find('[data-testid="task-card"]').text()).toContain('Low')
  })

  it('priorityLabel maps "medium" to "Medium"', () => {
    const wrapper = mountCard({ priority: 'medium' })
    expect(wrapper.find('[data-testid="task-card"]').text()).toContain('Medium')
  })

  it('priorityLabel maps "high" to "High"', () => {
    const wrapper = mountCard({ priority: 'high' })
    expect(wrapper.find('[data-testid="task-card"]').text()).toContain('High')
  })

  it('priorityBadgeClass includes gray classes for "low" priority', () => {
    const wrapper = mountCard({ priority: 'low' })
    const badge = wrapper.findAll('span')[0]
    expect(badge.classes()).toContain('bg-gray-100')
  })

  it('priorityBadgeClass includes blue classes for "medium" priority', () => {
    const wrapper = mountCard({ priority: 'medium' })
    const badge = wrapper.findAll('span')[0]
    expect(badge.classes()).toContain('bg-blue-100')
  })

  it('priorityBadgeClass includes red classes for "high" priority', () => {
    const wrapper = mountCard({ priority: 'high' })
    const badge = wrapper.findAll('span')[0]
    expect(badge.classes()).toContain('bg-red-100')
  })

  it('priorityBadgeClass defaults to medium classes for unknown priority', () => {
    const wrapper = mountCard({ priority: 'urgent' })
    const badge = wrapper.findAll('span')[0]
    expect(badge.classes()).toContain('bg-blue-100')
  })

  it('applies overdue date styling when is_overdue is true', () => {
    const wrapper = mountCard({ due_date: '2026-01-01', is_overdue: true })
    const dateSpan = wrapper.findAll('span').find((s) => s.text().includes('Jan'))
    expect(dateSpan.classes()).toContain('text-red-600')
  })

  it('does not apply overdue styling when is_overdue is false', () => {
    const wrapper = mountCard({ due_date: '2026-12-31', is_overdue: false })
    const dateSpan = wrapper.findAll('span').find((s) => s.text().includes('Dec'))
    expect(dateSpan.classes()).not.toContain('text-red-600')
  })

  it('renders assignee name when provided', () => {
    const wrapper = mountCard({ assignee_name: 'Carlos López' })
    expect(wrapper.text()).toContain('Carlos López')
  })

  it('renders "Unassigned" when assignee_name is absent', () => {
    const wrapper = mountCard({ assignee_name: '' })
    expect(wrapper.text()).toContain('Unassigned')
  })

  it('hides due date section when task.due_date is absent', () => {
    const wrapper = mountCard({ due_date: '' })
    expect(wrapper.text()).not.toContain('📅')
  })

  it('data-testid="task-card" is present on the root element', () => {
    const wrapper = mountCard()
    expect(wrapper.find('[data-testid="task-card"]').exists()).toBe(true)
  })
})
