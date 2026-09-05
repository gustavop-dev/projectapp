import { flushPromises, mount } from '@vue/test-utils'
import BaseBadge from '../../components/base/BaseBadge.vue'
import BaseEmptyState from '../../components/base/BaseEmptyState.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BaseTextarea from '../../components/base/BaseTextarea.vue'
import BaseToggle from '../../components/base/BaseToggle.vue'
import ProjectAccessNotes from '../../components/projects/ProjectAccessNotes.vue'

global.useI18n = jest.fn(() => ({ t: (key) => key }))

const sensitiveNote = {
  id: 12,
  title: 'Recovery token',
  content: '',
  has_content: true,
  is_sensitive: true,
  updated_by: 'Admin',
}

const regularNote = {
  id: 13,
  title: 'Deployment owner',
  content: 'Operations team',
  has_content: true,
  is_sensitive: false,
  updated_by: 'Admin',
}

const ConfirmModalStub = {
  props: ['modelValue'],
  emits: ['update:modelValue', 'confirm'],
  template: '<div v-if="modelValue"><button data-testid="confirm-delete" @click="$emit(\'confirm\')">confirm</button></div>',
}

function buildApi() {
  return {
    createNote: jest.fn().mockResolvedValue({ notes: [] }),
    updateNote: jest.fn().mockResolvedValue({ notes: [] }),
    deleteNote: jest.fn().mockResolvedValue({ notes: [] }),
    revealNote: jest.fn().mockResolvedValue({ secret: 'recovery-secret' }),
  }
}

function mountNotes({ notes = [sensitiveNote], api = buildApi(), onUpdated = jest.fn() } = {}) {
  return {
    api,
    onUpdated,
    wrapper: mount(ProjectAccessNotes, {
      props: { notes, api, onUpdated },
      global: {
        components: { BaseBadge, BaseEmptyState, BaseInput, BaseTextarea, BaseToggle },
        stubs: {
          BaseAlert: { template: '<div role="alert"><slot /></div>' },
          ConfirmModal: ConfirmModalStub,
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    }),
  }
}

describe('ProjectAccessNotes', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    })
  })

  it('keeps sensitive note content masked until reveal is requested', async () => {
    const { api, wrapper } = mountNotes()

    expect(wrapper.text()).toContain('••••••••••••')
    expect(wrapper.text()).not.toContain('recovery-secret')

    await wrapper.get('[data-testid="project-access-note-reveal-12"]').trigger('click')
    await flushPromises()

    expect(api.revealNote).toHaveBeenCalledWith(12)
    expect(wrapper.text()).toContain('recovery-secret')
  })

  it('copies sensitive content without exposing it in the note body', async () => {
    const { wrapper } = mountNotes()

    await wrapper.get('[data-testid="project-access-note-copy-12"]').trigger('click')
    await flushPromises()

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('recovery-secret')
    expect(wrapper.text()).not.toContain('recovery-secret')
  })

  it('creates a titled note with its sensitivity choice', async () => {
    const { api, onUpdated, wrapper } = mountNotes({ notes: [] })
    await wrapper.get('[data-testid="project-access-add-note"]').trigger('click')
    const form = wrapper.get('[data-testid="project-access-note-create"]')
    await form.get('input').setValue('Deployment owner')
    await form.get('textarea').setValue('Operations team')
    await form.get('[role="switch"]').trigger('click')

    await wrapper.get('[data-testid="project-access-create-note-save"]').trigger('click')
    await flushPromises()

    expect(api.createNote).toHaveBeenCalledWith({
      title: 'Deployment owner',
      content: 'Operations team',
      is_sensitive: true,
    })
    expect(onUpdated).toHaveBeenCalledWith({ notes: [] })
  })

  it('requires both fields before creating a note', async () => {
    const { api, wrapper } = mountNotes({ notes: [] })
    await wrapper.get('[data-testid="project-access-add-note"]').trigger('click')

    await wrapper.get('[data-testid="project-access-create-note-save"]').trigger('click')

    expect(api.createNote).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('projectAccess.errors.noteTitleRequired')
    expect(wrapper.text()).toContain('projectAccess.errors.noteContentRequired')
  })

  it('updates a regular note without requesting its secret', async () => {
    const { api, onUpdated, wrapper } = mountNotes({ notes: [regularNote] })
    await wrapper.get('[data-testid="project-access-note-edit-13"]').trigger('click')
    const note = wrapper.get('[data-testid="project-access-note-13"]')
    await note.get('input').setValue('Release owner')
    await note.get('textarea').setValue('Platform team')

    await wrapper.get('[data-testid="project-access-note-save-13"]').trigger('click')
    await flushPromises()

    expect(api.revealNote).not.toHaveBeenCalled()
    expect(api.updateNote).toHaveBeenCalledWith(13, {
      title: 'Release owner',
      content: 'Platform team',
      is_sensitive: false,
    })
    expect(onUpdated).toHaveBeenCalledWith({ notes: [] })
  })

  it('requires content before updating a note', async () => {
    const { api, wrapper } = mountNotes({ notes: [regularNote] })
    await wrapper.get('[data-testid="project-access-note-edit-13"]').trigger('click')
    await wrapper.get('[data-testid="project-access-note-13"] textarea').setValue('')

    await wrapper.get('[data-testid="project-access-note-save-13"]').trigger('click')

    expect(api.updateNote).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('projectAccess.errors.noteContentRequired')
  })

  it('hides a revealed note without another request', async () => {
    const { api, wrapper } = mountNotes()
    const revealButton = wrapper.get('[data-testid="project-access-note-reveal-12"]')

    await revealButton.trigger('click')
    await flushPromises()
    await revealButton.trigger('click')

    expect(api.revealNote).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('••••••••••••')
    expect(wrapper.text()).not.toContain('recovery-secret')
  })

  it('copies regular note content without requesting a secret', async () => {
    const { api, wrapper } = mountNotes({ notes: [regularNote] })

    await wrapper.get('[data-testid="project-access-note-copy-13"]').trigger('click')
    await flushPromises()

    expect(api.revealNote).not.toHaveBeenCalled()
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Operations team')
  })

  it('loads sensitive content only when editing starts', async () => {
    const { api, wrapper } = mountNotes()

    await wrapper.get('[data-testid="project-access-note-edit-12"]').trigger('click')
    await flushPromises()

    expect(api.revealNote).toHaveBeenCalledWith(12)
    expect(wrapper.get('[data-testid="project-access-note-12"] textarea').element.value)
      .toBe('recovery-secret')
  })

  it('shows note field errors returned by the API', async () => {
    const api = buildApi()
    api.createNote.mockRejectedValue({
      response: {
        status: 400,
        data: {
          title: ['Use a unique title.'],
          content: ['Content is not accepted.'],
        },
      },
    })
    const { wrapper } = mountNotes({ notes: [], api })
    await wrapper.get('[data-testid="project-access-add-note"]').trigger('click')
    const form = wrapper.get('[data-testid="project-access-note-create"]')
    await form.get('input').setValue('Deployment owner')
    await form.get('textarea').setValue('Operations team')

    await wrapper.get('[data-testid="project-access-create-note-save"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Use a unique title.')
    expect(wrapper.text()).toContain('Content is not accepted.')
  })
})
