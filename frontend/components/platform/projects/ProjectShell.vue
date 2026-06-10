<template>
  <div class="space-y-4">
    <header class="rounded-3xl border border-border-default bg-surface px-6 py-4 shadow-sm">
      <ProjectBreadcrumb :project-name="project?.name" />
      <div class="mt-2 flex items-center gap-3">
        <h1 class="text-xl font-semibold text-text-default">{{ project?.name || 'Proyecto' }}</h1>
        <span v-if="project" :class="statusChipClass(project.status)">{{ statusLabel(project.status) }}</span>
      </div>
      <p v-if="project" class="mt-1 text-sm text-green-light">
        <template v-if="project.client_name">Cliente: {{ project.client_name }}</template>
        <template v-if="project.start_date"> · Inició: {{ formatDate(project.start_date) }}</template>
        <template v-if="project.next_deliverable"> · Próx. entrega: {{ formatDate(project.next_deliverable.due_date) }}</template>
      </p>
    </header>
    <div class="flex flex-col gap-4 lg:flex-row">
      <ProjectSecondarySidebar :project-id="projectId" />
      <main class="min-w-0 flex-1 rounded-3xl border border-border-default bg-surface px-4 py-6 shadow-sm sm:px-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import ProjectBreadcrumb from '~/components/platform/projects/ProjectBreadcrumb.vue'
import ProjectSecondarySidebar from '~/components/platform/projects/ProjectSecondarySidebar.vue'

const route = useRoute()
const store = usePlatformProjectsStore()

const projectId = computed(() => Number(route.params.id))
const project = computed(() => store.currentProject)

onMounted(() => { if (projectId.value) store.fetchProject(projectId.value) })
watch(projectId, (id) => { if (id) store.fetchProject(id) })

const STATUS_LABELS = { active: 'Activo', paused: 'Pausado', completed: 'Completado', archived: 'Archivado' }
function statusLabel(s) { return STATUS_LABELS[s] || s }
function statusChipClass(s) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    active: 'bg-green-100 text-green-700', paused: 'bg-amber-100 text-amber-700',
    completed: 'bg-sky-100 text-sky-700', archived: 'bg-slate-100 text-slate-600',
  }
  return `${base} ${map[s] || map.archived}`
}
function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>
