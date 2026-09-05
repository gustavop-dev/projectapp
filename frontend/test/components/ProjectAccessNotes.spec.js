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
})
