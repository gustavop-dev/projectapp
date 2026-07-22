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
          <p class="text-xs uppercase tracking-wider text-green-light/70">Próximo pago de hosting</p>
          <p class="mt-2 text-2xl font-semibold text-text-default">
            {{ project.next_hosting_payment ? formatCurrency(project.next_hosting_payment.amount) : '—' }}
          </p>
          <p v-if="project.next_hosting_payment?.date" class="text-xs text-green-light/60">
            {{ formatDate(project.next_hosting_payment.date) }}
            <span v-if="project.next_hosting_payment.plan" class="ml-1">· {{ planLabel(project.next_hosting_payment.plan) }}</span>
          </p>
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
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-xl border border-border-default px-3 py-2 text-sm text-text-default transition hover:bg-surface-muted/40"
            @click="openEditModal"
          >
            Editar
          </button>
          <button
            v-if="project.status !== 'archived'"
            type="button"
            :disabled="projectsStore.isUpdating"
            class="rounded-xl border border-amber-500/30 px-3 py-2 text-sm text-amber-700 transition hover:bg-amber-50 disabled:opacity-50 dark:text-amber-400 dark:hover:bg-amber-500/10"
            @click="handleArchive"
          >
            {{ projectsStore.isUpdating ? '…' : 'Archivar' }}
          </button>
          <button
            v-else
            type="button"
            :disabled="projectsStore.isUpdating"
            class="rounded-xl border border-emerald-500/30 px-3 py-2 text-sm text-text-brand transition hover:bg-success-soft disabled:opacity-50"
            @click="handleUnarchive"
          >
            {{ projectsStore.isUpdating ? '…' : 'Reactivar' }}
          </button>
          <button
            type="button"
            :disabled="projectsStore.isUpdating"
            class="rounded-xl border border-red-500/30 px-3 py-2 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-50 dark:hover:bg-red-500/10"
            @click="handleDelete"
          >
            Eliminar
          </button>
        </div>
        <p v-if="actionError" class="mt-3 rounded-xl border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-600 dark:text-red-400">
          {{ actionError }}
        </p>
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

      <!-- Edit project modal -->
      <Teleport to="body">
        <Transition name="modal-overlay">
          <div
            v-if="isEditOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
            @click.self="isEditOpen = false"
          >
            <Transition name="modal-content" appear>
              <div v-if="isEditOpen" class="w-full max-w-md rounded-3xl border border-border-default bg-surface p-6 shadow-2xl sm:p-8">
                <h2 class="mb-5 text-lg font-bold text-text-default">Editar proyecto</h2>
                <form class="space-y-4" @submit.prevent="handleEditSubmit">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Nombre <span class="text-red-400">*</span></label>
                    <input v-model="editForm.name" type="text" required class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white" />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                    <textarea v-model="editForm.description" rows="3" class="w-full resize-none rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white" />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Estado</label>
                    <select v-model="editForm.status" class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none focus:border-border-default dark:bg-primary-strong dark:text-white">
                      <option value="active">Activo</option>
                      <option value="paused">Pausado</option>
                      <option value="completed">Completado</option>
                      <option value="archived">Archivado</option>
                    </select>
                  </div>
                  <p v-if="editError" class="rounded-xl border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ editError }}</p>
                  <div class="flex justify-end gap-3 pt-2">
                    <button type="button" class="rounded-xl border border-border-default px-5 py-2.5 text-sm text-green-light transition hover:text-text-default dark:hover:text-white" @click="isEditOpen = false">Cancelar</button>
                    <button type="submit" :disabled="!editForm.name.trim() || projectsStore.isUpdating" class="rounded-xl bg-accent px-6 py-2.5 text-sm font-semibold text-text-default transition hover:brightness-105 disabled:opacity-50">
                      {{ projectsStore.isUpdating ? 'Guardando…' : 'Guardar cambios' }}
                    </button>
                  </div>
                </form>
              </div>
            </Transition>
          </div>
        </Transition>
      </Teleport>
    </section>
    <div v-else class="px-6 py-12 text-center text-green-light/60">Cargando proyecto…</div>
  </ProjectShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import { formatDate as formatDateUtil } from '~/utils/formatDate'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'
import PhaseList from '~/components/platform/projects/PhaseList.vue'
import PhaseSelectorModal from '~/components/platform/projects/PhaseSelectorModal.vue'

definePageMeta({
  middleware: ['platform-auth'],
  layout: 'platform',
})

const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()
const localePath = useLocalePath()

const project = computed(() => projectsStore.currentProject)
const phases = ref([])
const showAddPhase = ref(false)

const isEditOpen = ref(false)
const editForm = reactive({ name: '', description: '', status: 'active' })
const editError = ref('')
const actionError = ref('')

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
  return formatDateUtil(iso, { fallback: '' })
}

function formatCurrency(value) {
  const n = Number(value || 0)
  if (!n) return '—'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(n)
}

function planLabel(plan) {
  const map = { monthly: 'Mensual', quarterly: 'Trimestral', semiannual: 'Semestral', annual: 'Anual' }
  return map[plan] || plan
}

function openEditModal() {
  editForm.name = project.value?.name || ''
  editForm.description = project.value?.description || ''
  editForm.status = project.value?.status || 'active'
  editError.value = ''
  isEditOpen.value = true
}

async function handleEditSubmit() {
  if (!editForm.name.trim()) return
  editError.value = ''
  const result = await projectsStore.updateProject(project.value.id, { ...editForm })
  if (result.success) {
    isEditOpen.value = false
  } else {
    editError.value = result.message
  }
}

async function handleArchive() {
  if (!project.value) return
  if (!window.confirm(`¿Archivar el proyecto "${project.value.name}"? Podrás reactivarlo después.`)) return
  actionError.value = ''
  const result = await projectsStore.archiveProject(project.value.id)
  if (!result.success) actionError.value = result.message
}

async function handleUnarchive() {
  if (!project.value) return
  actionError.value = ''
  const result = await projectsStore.updateProject(project.value.id, { status: 'active' })
  if (!result.success) actionError.value = result.message
}

async function handleDelete() {
  if (!project.value) return
  const confirm1 = window.confirm(
    `⚠️ ¿Eliminar PERMANENTEMENTE el proyecto "${project.value.name}"?\n\n` +
    'Esto borra todo: fases, requerimientos, bugs, solicitudes, recursos, pagos, accesos.\n' +
    'No se puede deshacer.',
  )
  if (!confirm1) return
  const typed = window.prompt(`Para confirmar, escribe el nombre del proyecto: "${project.value.name}"`)
  if (typed !== project.value.name) {
    if (typed !== null) window.alert('El nombre no coincide. Eliminación cancelada.')
    return
  }
  actionError.value = ''
  const result = await projectsStore.deleteProject(project.value.id)
  if (result.success) {
    await navigateTo(localePath('/platform/projects'))
  } else {
    actionError.value = result.message
  }
}
</script>
