<template>
  <ProjectShell>
    <section v-if="project" class="space-y-8">
      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Progreso</p>
          <p class="mt-2 text-2xl font-semibold text-text-default">{{ project.progress ?? 0 }}%</p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Bugs abiertos</p>
          <p class="mt-2 text-2xl font-semibold" :class="(project.bugs_open_count || 0) > 0 ? 'text-red-600' : 'text-text-default'">
            {{ project.bugs_open_count ?? 0 }}
          </p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Solicitudes pendientes</p>
          <p class="mt-2 text-2xl font-semibold" :class="(project.changes_pending_count || 0) > 0 ? 'text-amber-600' : 'text-text-default'">
            {{ project.changes_pending_count ?? 0 }}
          </p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Próximo entregable</p>
          <p class="mt-2 text-sm text-text-default">{{ project.next_deliverable?.title || '—' }}</p>
          <p v-if="project.next_deliverable?.due_date" class="text-xs text-green-light/60">{{ formatDate(project.next_deliverable.due_date) }}</p>
        </div>
      </div>

      <!-- Phases -->
      <PhaseList
        :project-id="project.id"
        :phases="phases"
        @add-phase="onAddPhase"
        @changed="loadPhases"
      />

      <!-- Actions -->
      <div v-if="authStore.isAdmin" class="rounded-2xl border border-border-default bg-surface p-6">
        <h2 class="text-base font-medium text-text-default">Acciones</h2>
        <p class="mt-1 text-xs text-green-light/60">
          La edición, archivado y eliminación del proyecto viven aquí (no en la tabla).
        </p>
        <div class="mt-3 flex gap-2">
          <button class="rounded-xl border border-border-default px-3 py-2 text-sm" disabled>Editar</button>
          <button class="rounded-xl border border-border-default px-3 py-2 text-sm" disabled>Archivar</button>
          <button class="rounded-xl border border-red-500/30 px-3 py-2 text-sm text-red-600" disabled>Eliminar</button>
        </div>
      </div>

      <PhaseSelectorModal
        v-if="project"
        :visible="showAddPhase"
        mode="add"
        :project-id="project.id"
        :client-id="project.client_id"
        @close="showAddPhase = false"
        @phases-added="onPhasesAdded"
      />
    </section>
    <div v-else class="px-6 py-12 text-center text-green-light/60">Cargando proyecto…</div>
  </ProjectShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'
import PhaseList from '~/components/platform/projects/PhaseList.vue'
import PhaseSelectorModal from '~/components/platform/projects/PhaseSelectorModal.vue'

definePageMeta({
  middleware: ['platform-auth'],
  layout: 'platform',
})

const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()

const project = computed(() => projectsStore.currentProject)
const phases = ref([])
const showAddPhase = ref(false)

async function loadPhases() {
  if (!project.value) return
  phases.value = await projectsStore.loadPhases(project.value.id)
}

onMounted(loadPhases)
watch(() => project.value?.id, loadPhases)

function onAddPhase() { showAddPhase.value = true }
async function onPhasesAdded() {
  await loadPhases()
  showAddPhase.value = false
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>
