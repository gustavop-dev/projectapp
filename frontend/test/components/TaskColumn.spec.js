import { mount } from '@vue/test-utils'

jest.mock('vuedraggable', () => ({
  name: 'draggable',
  props: ['modelValue', 'itemKey', 'group', 'ghostClass'],
  emits: ['update:modelValue', 'change'],
  template: '<div data-testid="draggable"></div>',
}))

jest.mock('../../components/Tasks/TaskCard.vue', () => ({
  name: 'TaskCard',
  props: ['task'],
  template: '<div data-testid="task-card">{{ task.title }}</div>',
}))

import TaskColumn from '../../components/Tasks/TaskColumn.vue'

function mountColumn(props = {}) {
  return mount(TaskColumn, {
    props: {
      status: 'todo',
      label: 'Por hacer',
      tasks: [],
      ...props,
    },
  })
}

describe('TaskColumn', () => {
  it('renders the column label prop text', () => {
    const wrapper = mountColumn({ label: 'En progreso' })
    expect(wrapper.text()).toContain('En progreso')
  })

  it('container has data-testid column-todo for status todo', () => {
    const wrapper = mountColumn({ status: 'todo' })
    expect(wrapper.find('[data-testid="column-todo"]').exists()).toBe(true)
  })

  it('container has data-testid column-in_progress for status in_progress', () => {
    const wrapper = mountColumn({ status: 'in_progress', label: 'En progreso' })
    expect(wrapper.find('[data-testid="column-in_progress"]').exists()).toBe(true)
  })

  it('container has data-testid column-blocked for status blocked', () => {
    const wrapper = mountColumn({ status: 'blocked', label: 'Bloqueado' })
    expect(wrapper.find('[data-testid="column-blocked"]').exists()).toBe(true)
  })

  it('container has data-testid column-done for status done', () => {
    const wrapper = mountColumn({ status: 'done', label: 'Hecho' })
    expect(wrapper.find('[data-testid="column-done"]').exists()).toBe(true)
  })

  it('add-task button has correct data-testid for the column status', () => {
    const wrapper = mountColumn({ status: 'todo' })
    expect(wrapper.find('[data-testid="add-task-todo"]').exists()).toBe(true)
  })

  it('clicking add-task button emits add', async () => {
    const wrapper = mountColumn({ status: 'todo' })
    await wrapper.find('[data-testid="add-task-todo"]').trigger('click')
    expect(wrapper.emitted('add')).toBeTruthy()
  })

  it('renders empty state draggable when tasks is empty', () => {
    const wrapper = mountColumn({ tasks: [] })
    expect(wrapper.find('[data-testid="draggable"]').exists()).toBe(true)
  })

  it('renders task count in header', () => {
    const tasks = [
      { id: 1, title: 'A', assignee_name: 'Alice' },
      { id: 2, title: 'B', assignee_name: 'Alice' },
    ]
    const wrapper = mountColumn({ tasks })
    expect(wrapper.text()).toContain('2')
  })

  // ── dotClass computed ──────────────────────────────────────────────────────

  it('dotClass is bg-gray-400 for todo status', () => {
    const wrapper = mountColumn({ status: 'todo' })
    const dot = wrapper.find('span.rounded-full')
    expect(dot.classes()).toContain('bg-gray-400')
  })

  it('dotClass is bg-blue-500 for in_progress status', () => {
    const wrapper = mountColumn({ status: 'in_progress', label: 'En progreso' })
    const dot = wrapper.find('span.rounded-full')
    expect(dot.classes()).toContain('bg-blue-500')
  })

  it('dotClass is bg-red-500 for blocked status', () => {
    const wrapper = mountColumn({ status: 'blocked', label: 'Bloqueado' })
    const dot = wrapper.find('span.rounded-full')
    expect(dot.classes()).toContain('bg-red-500')
  })

  it('dotClass is bg-emerald-500 for done status', () => {
    const wrapper = mountColumn({ status: 'done', label: 'Hecho' })
    const dot = wrapper.find('span.rounded-full')
    expect(dot.classes()).toContain('bg-emerald-500')
  })

  it('dotClass falls back to bg-gray-400 for unknown status', () => {
    const wrapper = mountColumn({ status: 'unknown', label: 'Custom' })
    const dot = wrapper.find('span.rounded-full')
    expect(dot.classes()).toContain('bg-gray-400')
  })

  // ── groupedTasks computed ──────────────────────────────────────────────────

  it('groupedTasks renders assignee group names for assigned tasks', () => {
    const tasks = [
      { id: 1, title: 'Task A', assignee_name: 'Alice' },
      { id: 2, title: 'Task B', assignee_name: 'Bob' },
    ]
    const wrapper = mountColumn({ tasks })
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('Bob')
  })

  it('groupedTasks renders Unassigned group for tasks with null assignee_name', () => {
    const tasks = [{ id: 1, title: 'No owner', assignee_name: null }]
    const wrapper = mountColumn({ tasks })
    expect(wrapper.text()).toContain('Unassigned')
  })

  // ── handleGroupChange / move emit ─────────────────────────────────────────

  it('emits move when draggable emits change with an added event', async () => {
    const tasks = [{ id: 1, title: 'X', assignee_name: 'Alice' }]
    const wrapper = mountColumn({ status: 'in_progress', label: 'En progreso', tasks })
    const draggables = wrapper.findAllComponents({ name: 'draggable' })
    await draggables[0].vm.$emit('change', {
      added: { element: { id: 5 }, newIndex: 0 },
    })
    expect(wrapper.emitted('move')).toBeTruthy()
    expect(wrapper.emitted('move')[0][0]).toMatchObject({ taskId: 5, status: 'in_progress' })
  })

  it('emits move when draggable emits change with a moved event', async () => {
    const tasks = [{ id: 3, title: 'Y', assignee_name: 'Alice' }]
    const wrapper = mountColumn({ status: 'todo', label: 'Por hacer', tasks })
    const draggables = wrapper.findAllComponents({ name: 'draggable' })
    await draggables[0].vm.$emit('change', {
      moved: { element: { id: 3 }, newIndex: 1 },
    })
    expect(wrapper.emitted('move')).toBeTruthy()
    expect(wrapper.emitted('move')[0][0]).toMatchObject({ taskId: 3, status: 'todo' })
  })

  it('does not emit move when draggable emits only a removed event', async () => {
    const tasks = [{ id: 1, title: 'A', assignee_name: 'Alice' }]
    const wrapper = mountColumn({ tasks })
    const draggables = wrapper.findAllComponents({ name: 'draggable' })
    await draggables[0].vm.$emit('change', {
      removed: { element: { id: 1 }, oldIndex: 0 },
    })
    expect(wrapper.emitted('move')).toBeFalsy()
  })
})
