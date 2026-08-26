<script setup>
import { computed } from 'vue'
import ProjectSpaceLink from '~/components/panel/projects/ProjectSpaceLink.vue'
import { formatDate } from '~/utils/formatDate'

const props = defineProps({
  project: { type: Object, required: true },
  isSuperuser: { type: Boolean, default: false },
  highlighted: { type: Boolean, default: false },
})

const emit = defineEmits(['actions', 'assign'])

const statusTone = computed(() => ({
  active: 'success',
  paused: 'warning',
  completed: 'info',
  archived: 'neutral',
}[props.project.status] || 'neutral'))

const unlinkedTotal = computed(() => (
  (props.project.unlinked_hostings_count ?? 0)
  + (props.project.unlinked_incomes_count ?? 0)
  + (props.project.unlinked_documents_count ?? 0)
))
</script>

<template>
  <article
    class="flex min-w-0 flex-col rounded-xl border border-border-muted bg-surface p-4 shadow-card"
    :class="highlighted ? 'ring-2 ring-focus-ring/40 bg-primary-soft' : ''"
    :data-testid="`project-card-${project.id}`"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h2 class="break-words text-base font-semibold text-text-default">{{ project.name }}</h2>
        <p class="mt-1 break-words text-sm text-text-muted">{{ project.client_name || 'Sin cliente' }}</p>
        <p v-if="project.client_company" class="break-words text-xs text-text-subtle">
          {{ project.client_company }}
        </p>
      </div>
      <BaseBadge :variant="statusTone" size="sm" class="shrink-0">
        {{ project.status_label }}
      </BaseBadge>
    </div>

    <dl class="mt-4 grid grid-cols-3 gap-2 rounded-lg bg-surface-muted p-3 text-center">
      <div>
        <dt class="text-2xs uppercase tracking-wide text-text-subtle">Creado</dt>
        <dd class="mt-1 text-xs font-medium text-text-default">{{ formatDate(project.created_at) }}</dd>
      </div>
      <div>
        <dt class="text-2xs uppercase tracking-wide text-text-subtle">Hostings</dt>
        <dd class="mt-1 text-sm font-semibold tabular-nums">
          <NuxtLink
            v-if="isSuperuser && project.hostings_count > 0"
            :to="{ path: '/panel/accounting/hostings', query: { project: project.id } }"
            class="text-text-brand hover:underline"
            :data-testid="`project-hostings-link-${project.id}`"
          >
            {{ project.hostings_count }}
          </NuxtLink>
          <span v-else class="text-text-default">{{ project.hostings_count }}</span>
        </dd>
      </div>
      <div>
        <dt class="text-2xs uppercase tracking-wide text-text-subtle">Ingresos</dt>
        <dd class="mt-1 text-sm font-semibold tabular-nums">
          <NuxtLink
            v-if="isSuperuser && project.incomes_count > 0"
            :to="{
              path: '/panel/accounting/incomes',
              query: { accounting_incomeTab: 'all', project: project.id },
            }"
            class="text-text-brand hover:underline"
            :data-testid="`project-incomes-link-${project.id}`"
          >
            {{ project.incomes_count }}
          </NuxtLink>
          <span v-else class="text-text-default">{{ project.incomes_count }}</span>
        </dd>
      </div>
    </dl>

    <BaseButton
      v-if="unlinkedTotal > 0 && project.status !== 'archived'"
      variant="ghost"
      size="sm"
      class="mt-3 w-full justify-start text-warning-strong"
      :data-testid="`project-assign-unlinked-${project.id}`"
      @click="emit('assign', project)"
    >
      {{ unlinkedTotal }} {{ unlinkedTotal === 1 ? 'registro' : 'registros' }} sin proyecto
    </BaseButton>

    <div class="mt-auto flex items-center justify-end gap-2 pt-4">
      <BaseButton
        as="NuxtLink"
        :to="{ path: '/panel/communications', query: { project: project.id } }"
        variant="secondary"
        size="md"
        class="min-h-11"
        :data-testid="`project-communications-${project.id}`"
      >
        Comunicaciones
      </BaseButton>
      <ProjectSpaceLink
        :project-id="project.id"
        :data-testid="`project-space-${project.id}`"
        class="min-h-11 min-w-11"
      />
      <BaseButton
        variant="secondary"
        size="md"
        class="min-h-11"
        :aria-label="`Acciones de ${project.name}`"
        :data-testid="`project-actions-${project.id}`"
        @click="emit('actions', project)"
      >
        Acciones
      </BaseButton>
    </div>
  </article>
</template>
