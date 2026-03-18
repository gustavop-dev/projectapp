<template>
  <div id="platform-projects">
    <!-- Header -->
    <div class="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between" data-enter>
      <div>
        <h1 class="text-2xl font-bold text-esmerald dark:text-white sm:text-3xl">
          {{ authStore.isAdmin ? 'Proyectos' : 'Mis proyectos' }}
        </h1>
        <p class="mt-1 text-sm text-green-light">
          {{ authStore.isAdmin ? 'Todos los proyectos de tus clientes.' : 'El estado actual de tus proyectos.' }}
        </p>
      </div>
      <button
        v-if="authStore.isAdmin"
        type="button"
        class="flex items-center gap-2 rounded-xl bg-lemon px-5 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105"
        @click="isCreateModalOpen = true"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        Nuevo proyecto
      </button>
    </div>

    <!-- Status filters (admin) -->
    <div v-if="authStore.isAdmin" class="mb-6 flex flex-wrap gap-2" data-enter>
      <button
        v-for="filter in statusFilters"
        :key="filter.value"
        type="button"
        class="rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-wider transition"
        :class="activeFilter === filter.value
          ? 'bg-esmerald text-white dark:bg-lemon dark:text-esmerald-dark'
          : 'border border-esmerald/10 text-green-light hover:text-esmerald dark:border-white/10 dark:hover:text-white'"
        @click="handleFilterChange(filter.value)"
      >
        {{ filter.label }}
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="projectsStore.isLoading" class="py-20 text-center" data-enter>
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
      <p class="mt-4 text-sm text-green-light">Cargando proyectos...</p>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="projectsStore.projects.length === 0"
      class="rounded-3xl border border-dashed border-esmerald/10 py-20 text-center dark:border-white/10"
      data-enter
    >
      <svg class="mx-auto h-12 w-12 text-green-light/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
      </svg>
      <p class="mt-4 text-sm font-medium text-esmerald dark:text-white">
        {{ authStore.isAdmin ? 'No hay proyectos creados.' : 'Todavía no tienes proyectos asignados.' }}
      </p>
      <p class="mt-1 text-xs text-green-light">
        {{ authStore.isAdmin ? 'Crea el primer proyecto para un cliente.' : 'Tu administrador te asignará proyectos pronto.' }}
      </p>
    </div>

    <!-- Project cards grid -->
    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <NuxtLink
        v-for="project in projectsStore.projects"
        :key="project.id"
        :to="`/platform/projects/${project.id}`"
        class="project-card group relative overflow-hidden rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm transition-all duration-300 hover:border-esmerald/20 hover:shadow-md dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none dark:hover:border-white/15"
        data-enter
      >
        <!-- Status badge -->
        <span
          class="inline-flex rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider"
          :class="statusBadgeClass(project.status)"
        >
          {{ statusLabel(project.status) }}
        </span>

        <!-- Project name -->
        <h3 class="mt-4 text-lg font-semibold text-esmerald transition group-hover:text-esmerald/80 dark:text-white dark:group-hover:text-lemon">
          {{ project.name }}
        </h3>

        <!-- Description (truncated) -->
        <p class="mt-2 line-clamp-2 text-sm leading-relaxed text-green-light">
          {{ project.description || 'Sin descripción.' }}
        </p>

        <!-- Progress bar -->
        <div class="mt-5">
          <div class="mb-1.5 flex items-center justify-between text-xs">
            <span class="font-medium text-green-light/60">Progreso</span>
            <span class="font-bold text-esmerald dark:text-white">{{ project.progress }}%</span>
          </div>
          <div class="h-1.5 overflow-hidden rounded-full bg-esmerald/[0.06] dark:bg-white/[0.06]">
            <div
              class="h-full rounded-full transition-all duration-700 ease-out"
              :class="project.progress === 100 ? 'bg-emerald-500' : 'bg-esmerald dark:bg-lemon'"
              :style="{ width: `${project.progress}%` }"
            />
          </div>
        </div>

        <!-- Meta row -->
        <div class="mt-5 flex items-center justify-between">
          <div v-if="authStore.isAdmin" class="flex items-center gap-2">
            <div class="flex h-6 w-6 items-center justify-center rounded-full bg-esmerald/10 text-[10px] font-bold text-esmerald dark:bg-lemon/15 dark:text-lemon">
              {{ clientInitials(project) }}
            </div>
            <span class="text-xs text-green-light">{{ project.client_company || project.client_name }}</span>
          </div>
          <div v-else />

          <div class="flex items-center gap-1 text-xs text-green-light/60">
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" stroke-width="1.5" /><path d="M16 2v4M8 2v4M3 10h18" stroke-width="1.5" /></svg>
            {{ formatDate(project.estimated_end_date) }}
          </div>
        </div>

        <!-- Hover arrow -->
        <div class="absolute right-5 top-6 translate-x-2 opacity-0 transition-all duration-300 group-hover:translate-x-0 group-hover:opacity-100">
          <svg class="h-5 w-5 text-esmerald dark:text-lemon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
        </div>
      </NuxtLink>
    </div>

    <!-- Create project modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div
          v-if="isCreateModalOpen"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
          @click.self="closeCreateModal"
        >
          <Transition name="modal-content" appear>
            <div
              v-if="isCreateModalOpen"
              class="w-full max-w-lg rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8"
            >
              <div class="mb-6 flex items-center justify-between">
                <h2 class="text-lg font-bold text-esmerald dark:text-white">Nuevo proyecto</h2>
                <button
                  type="button"
                  class="flex h-8 w-8 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
                  @click="closeCreateModal"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <div
                v-if="createError"
                class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400"
              >
                {{ createError }}
              </div>

              <form class="space-y-4" @submit.prevent="handleCreateProject">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Nombre del proyecto <span class="text-red-400">*</span></label>
                  <input
                    v-model="createForm.name"
                    type="text"
                    required
                    placeholder="Ej: Plataforma E-commerce"
                    class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40"
                  />
                </div>

                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea
                    v-model="createForm.description"
                    rows="3"
                    placeholder="Breve descripción del proyecto..."
                    class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40"
                  />
                </div>

                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Cliente <span class="text-red-400">*</span></label>
                  <select
                    v-model="createForm.client_id"
                    required
                    class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
                  >
                    <option value="" disabled>Selecciona un cliente</option>
                    <option
                      v-for="client in clientsForSelect"
                      :key="client.user_id"
                      :value="client.user_id"
                    >
                      {{ client.first_name }} {{ client.last_name }} — {{ client.company_name || client.email }}
                    </option>
                  </select>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Fecha inicio</label>
                    <input
                      v-model="createForm.start_date"
                      type="date"
                      class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
                    />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Entrega estimada</label>
                    <input
                      v-model="createForm.estimated_end_date"
                      type="date"
                      class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
                    />
                  </div>
                </div>

                <div class="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm font-medium text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
                    @click="closeCreateModal"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    :disabled="!canCreate || projectsStore.isUpdating"
                    class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50"
                  >
                    {{ projectsStore.isUpdating ? 'Creando...' : 'Crear proyecto' }}
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
import { computed, onMounted, reactive, ref } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import { usePlatformClientsStore } from '~/stores/platform-clients'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

defineI18nRoute(false)

useHead({
  title: 'Proyectos — ProjectApp',
})

usePageEntrance('#platform-projects')

const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()
const clientsStore = usePlatformClientsStore()

const activeFilter = ref('')
const isCreateModalOpen = ref(false)
const createError = ref('')
const createForm = reactive({
  name: '',
  description: '',
  client_id: '',
  start_date: '',
  estimated_end_date: '',
})

const statusFilters = [
  { label: 'Todos', value: '' },
  { label: 'Activos', value: 'active' },
  { label: 'Pausados', value: 'paused' },
  { label: 'Completados', value: 'completed' },
  { label: 'Archivados', value: 'archived' },
]

const clientsForSelect = computed(() =>
  clientsStore.clients.filter((c) => c.is_active && c.is_onboarded),
)

const canCreate = computed(() => Boolean(createForm.name.trim()) && Boolean(createForm.client_id))

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

function clientInitials(project) {
  const name = project.client_name || ''
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('')
}

function formatDate(value) {
  if (!value) return 'Sin fecha'
  return new Date(value).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function handleFilterChange(value) {
  activeFilter.value = value
  projectsStore.fetchProjects(value ? { status: value } : {})
}

function closeCreateModal() {
  isCreateModalOpen.value = false
  createError.value = ''
  createForm.name = ''
  createForm.description = ''
  createForm.client_id = ''
  createForm.start_date = ''
  createForm.estimated_end_date = ''
}

async function handleCreateProject() {
  createError.value = ''

  const payload = {
    name: createForm.name.trim(),
    description: createForm.description.trim(),
    client_id: Number(createForm.client_id),
  }
  if (createForm.start_date) payload.start_date = createForm.start_date
  if (createForm.estimated_end_date) payload.estimated_end_date = createForm.estimated_end_date

  const result = await projectsStore.createProject(payload)
  if (!result.success) {
    createError.value = result.message
    return
  }

  closeCreateModal()
}

onMounted(async () => {
  await projectsStore.fetchProjects()
  if (authStore.isAdmin) {
    await clientsStore.fetchClients('all')
  }
})
</script>

<style scoped>
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
