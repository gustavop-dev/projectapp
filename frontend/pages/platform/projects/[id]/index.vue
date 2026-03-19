<template>
  <div id="platform-project-detail">
    <!-- Loading -->
    <div v-if="projectsStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <!-- Not found -->
    <div v-else-if="!project" class="py-20 text-center" data-enter>
      <p class="text-sm text-green-light">Proyecto no encontrado.</p>
      <NuxtLink to="/platform/projects" class="mt-4 inline-block text-sm font-medium text-esmerald dark:text-lemon">
        ← Volver a proyectos
      </NuxtLink>
    </div>

    <template v-else>
      <!-- Back link + header -->
      <div class="mb-8" data-enter>
        <NuxtLink to="/platform/projects" class="mb-4 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
          Proyectos
        </NuxtLink>

        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold text-esmerald dark:text-white sm:text-3xl">{{ project.name }}</h1>
              <span
                class="inline-flex rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider"
                :class="statusBadgeClass(project.status)"
              >
                {{ statusLabel(project.status) }}
              </span>
            </div>
            <p v-if="project.description" class="mt-2 max-w-2xl text-sm leading-relaxed text-green-light">
              {{ project.description }}
            </p>
          </div>

          <!-- Admin actions -->
          <div v-if="authStore.isAdmin" class="flex shrink-0 gap-2">
            <button
              type="button"
              class="rounded-xl border border-esmerald/10 px-4 py-2 text-sm font-medium text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
              @click="isEditModalOpen = true"
            >
              Editar
            </button>
          </div>
        </div>
      </div>

      <!-- Stats row -->
      <div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" data-enter>
        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Progreso</p>
          <div class="mt-3 flex items-end gap-2">
            <span class="text-3xl font-bold text-esmerald dark:text-lemon">{{ project.progress }}%</span>
          </div>
          <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-esmerald/[0.06] dark:bg-white/[0.06]">
            <div
              class="progress-bar h-full rounded-full"
              :class="project.progress === 100 ? 'bg-emerald-500' : 'bg-esmerald dark:bg-lemon'"
              :style="{ width: `${project.progress}%` }"
            />
          </div>
        </div>

        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Cliente</p>
          <p class="mt-3 text-base font-semibold text-esmerald dark:text-white">{{ project.client_company || project.client_name }}</p>
          <p class="mt-0.5 text-xs text-green-light">{{ project.client_email }}</p>
        </div>

        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Inicio</p>
          <p class="mt-3 text-base font-semibold text-esmerald dark:text-white">{{ formatDate(project.start_date) }}</p>
        </div>

        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Entrega estimada</p>
          <p class="mt-3 text-base font-semibold text-esmerald dark:text-white">{{ formatDate(project.estimated_end_date) }}</p>
          <p v-if="daysRemaining !== null" class="mt-0.5 text-xs" :class="daysRemaining <= 7 ? 'text-red-400' : 'text-green-light'">
            {{ daysRemaining > 0 ? `${daysRemaining} días restantes` : daysRemaining === 0 ? 'Hoy' : `${Math.abs(daysRemaining)} días de retraso` }}
          </p>
        </div>
      </div>

      <!-- Module cards -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-enter>
        <template v-for="module in projectModules" :key="module.title">
          <NuxtLink
            v-if="module.href"
            :to="module.href"
            class="group rounded-2xl border border-esmerald/[0.06] bg-white p-6 transition hover:border-esmerald/20 hover:shadow-md dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/15"
          >
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl" :class="module.iconBg">
                <SidebarIcon :name="module.icon" class="h-5 w-5" :class="module.iconColor" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-esmerald dark:text-white">{{ module.title }}</h3>
                <p class="text-xs text-green-light">{{ module.subtitle }}</p>
              </div>
            </div>
            <p class="mt-4 text-xs leading-relaxed text-green-light/80">{{ module.description }}</p>
            <div class="mt-3 flex items-center gap-1 text-xs font-medium text-esmerald opacity-0 transition group-hover:opacity-100 dark:text-lemon">
              Abrir <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </div>
          </NuxtLink>
          <div
            v-else
            class="rounded-2xl border border-esmerald/[0.06] bg-white p-6 opacity-50 dark:border-white/[0.06] dark:bg-esmerald"
          >
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl" :class="module.iconBg">
                <SidebarIcon :name="module.icon" class="h-5 w-5" :class="module.iconColor" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-esmerald dark:text-white">{{ module.title }}</h3>
                <p class="text-xs text-green-light">{{ module.subtitle }}</p>
              </div>
            </div>
            <p class="mt-4 text-xs leading-relaxed text-green-light/80">{{ module.description }}</p>
            <div class="mt-3">
              <span class="text-[10px] font-semibold uppercase tracking-wider text-green-light/40">Próximamente</span>
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- Edit modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div
          v-if="isEditModalOpen"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
          @click.self="closeEditModal"
        >
          <Transition name="modal-content" appear>
            <div
              v-if="isEditModalOpen"
              class="w-full max-w-lg rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8"
            >
              <div class="mb-6 flex items-center justify-between">
                <h2 class="text-lg font-bold text-esmerald dark:text-white">Editar proyecto</h2>
                <button
                  type="button"
                  class="flex h-8 w-8 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
                  @click="closeEditModal"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <div
                v-if="editError"
                class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400"
              >
                {{ editError }}
              </div>

              <form class="space-y-4" @submit.prevent="handleUpdateProject">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Nombre</label>
                  <input v-model="editForm.name" type="text" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea v-model="editForm.description" rows="3" class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Estado</label>
                  <select v-model="editForm.status" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                    <option value="active">Activo</option>
                    <option value="paused">Pausado</option>
                    <option value="completed">Completado</option>
                    <option value="archived">Archivado</option>
                  </select>
                  <p class="mt-1.5 text-[10px] text-green-light/50">El progreso se calcula automáticamente desde el tablero.</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Inicio</label>
                    <input v-model="editForm.start_date" type="date" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40" />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Entrega estimada</label>
                    <input v-model="editForm.estimated_end_date" type="date" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40" />
                  </div>
                </div>
                <div class="flex justify-end gap-3 pt-2">
                  <button type="button" class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm font-medium text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white" @click="closeEditModal">Cancelar</button>
                  <button type="submit" :disabled="projectsStore.isUpdating" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                    {{ projectsStore.isUpdating ? 'Guardando...' : 'Guardar cambios' }}
                  </button>
                </div>
              </form>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import SidebarIcon from '~/components/platform/SidebarIcon.vue'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

const route = useRoute()
const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()

usePageEntrance('#platform-project-detail')

const isEditModalOpen = ref(false)
const editError = ref('')
const editForm = reactive({
  name: '',
  description: '',
  status: 'active',
  start_date: '',
  estimated_end_date: '',
})

const project = computed(() => projectsStore.currentProject)

useHead({
  title: computed(() => project.value ? `${project.value.name} — ProjectApp` : 'Proyecto — ProjectApp'),
})

const daysRemaining = computed(() => {
  if (!project.value?.estimated_end_date) return null
  const end = new Date(project.value.estimated_end_date)
  const now = new Date()
  return Math.ceil((end - now) / (1000 * 60 * 60 * 24))
})

const projectModules = computed(() => [
  {
    title: 'Tablero',
    subtitle: 'Kanban de requerimientos',
    description: 'Visualiza el estado de cada requerimiento del proyecto en un tablero tipo Kanban.',
    icon: 'board',
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-500',
    href: `/platform/projects/${route.params.id}/board`,
  },
  {
    title: 'Solicitudes de cambio',
    subtitle: 'Gestión de cambios',
    description: 'El cliente solicita cambios, el admin evalúa y responde.',
    icon: 'refresh',
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-500',
  },
  {
    title: 'Reporte de bugs',
    subtitle: 'Seguimiento de errores',
    description: 'Reporta y da seguimiento a errores con severidad y pasos para reproducir.',
    icon: 'bug',
    iconBg: 'bg-red-500/10',
    iconColor: 'text-red-500',
  },
  {
    title: 'Entregables',
    subtitle: 'Repositorio de archivos',
    description: 'Diseños, documentos, APKs y accesos organizados por categoría.',
    icon: 'file',
    iconBg: 'bg-purple-500/10',
    iconColor: 'text-purple-500',
  },
])

function statusBadgeClass(status) {
  const map = {
    active: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    paused: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    completed: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    archived: 'bg-white/10 text-green-light/60',
  }
  return map[status] || map.active
}

function statusLabel(status) {
  const map = { active: 'Activo', paused: 'Pausado', completed: 'Completado', archived: 'Archivado' }
  return map[status] || status
}

function formatDate(value) {
  if (!value) return 'Sin definir'
  return new Date(value).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function openEditModal() {
  if (!project.value) return
  editForm.name = project.value.name
  editForm.description = project.value.description
  editForm.status = project.value.status
  editForm.start_date = project.value.start_date || ''
  editForm.estimated_end_date = project.value.estimated_end_date || ''
  editError.value = ''
  isEditModalOpen.value = true
}

function closeEditModal() {
  isEditModalOpen.value = false
  editError.value = ''
}

async function handleUpdateProject() {
  editError.value = ''
  const payload = {}
  if (editForm.name.trim()) payload.name = editForm.name.trim()
  if (editForm.description !== undefined) payload.description = editForm.description.trim()
  if (editForm.status) payload.status = editForm.status
  payload.start_date = editForm.start_date || null
  payload.estimated_end_date = editForm.estimated_end_date || null

  const result = await projectsStore.updateProject(project.value.id, payload)
  if (!result.success) {
    editError.value = result.message
    return
  }
  closeEditModal()
}

watch(isEditModalOpen, (val) => {
  if (val) openEditModal()
})

onMounted(async () => {
  const projectId = route.params.id
  await projectsStore.fetchProject(projectId)
})
</script>

<style scoped>
.progress-bar {
  transition: width 1s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-overlay-enter-active,
.modal-overlay-leave-active {
  transition: opacity 0.25s ease;
}
.modal-overlay-enter-from,
.modal-overlay-leave-to {
  opacity: 0;
}
.modal-content-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-content-leave-active {
  transition: all 0.2s ease-in;
}
.modal-content-enter-from {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
}
.modal-content-leave-to {
  opacity: 0;
  transform: scale(0.97);
}
</style>
