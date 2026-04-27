<template>
  <div id="platform-project-detail">
    <!-- Loading -->
    <div v-if="projectsStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-esmerald dark:border-t-lemon" />
    </div>

    <!-- Not found -->
    <div v-else-if="!project" class="py-20 text-center" data-enter>
      <p class="text-sm text-green-light">Proyecto no encontrado.</p>
      <NuxtLink :to="localePath('/platform/projects')" class="mt-4 inline-block text-sm font-medium text-text-brand">
        ← Volver a proyectos
      </NuxtLink>
    </div>

    <template v-else>
      <!-- Back link + header -->
      <div class="mb-8" data-enter>
        <NuxtLink :to="localePath('/platform/projects')" class="mb-4 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-text-default dark:hover:text-white">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
          Proyectos
        </NuxtLink>

        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold text-text-default sm:text-3xl">{{ project.name }}</h1>
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
          <div v-if="authStore.isAdmin" class="flex shrink-0 flex-wrap gap-2">
            <button
              type="button"
              class="rounded-xl border border-border-default px-4 py-2 text-sm font-medium text-green-light transition hover:text-text-default dark:hover:text-white"
              :disabled="syncLoading"
              @click="runTechnicalSync"
            >
              {{ syncLoading ? 'Sincronizando…' : 'Sync det. técnico' }}
            </button>
            <button
              type="button"
              class="rounded-xl border border-border-default px-4 py-2 text-sm font-medium text-green-light transition hover:text-text-default dark:hover:text-white"
              @click="isEditModalOpen = true"
            >
              Editar
            </button>
          </div>
        </div>
      </div>

      <!-- Stats row -->
      <div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" data-enter>
        <div class="rounded-2xl border border-border-default bg-surface p-5">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Progreso</p>
          <div class="mt-3 flex items-end gap-2">
            <span class="text-3xl font-bold text-text-brand">{{ project.progress }}%</span>
          </div>
          <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-primary/10 dark:bg-white/10">
            <div
              class="progress-bar h-full rounded-full"
              :class="project.progress === 100 ? 'bg-emerald-500' : 'bg-primary dark:bg-accent'"
              :style="{ width: `${project.progress}%` }"
            />
          </div>
        </div>

        <div class="rounded-2xl border border-border-default bg-surface p-5">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Cliente</p>
          <p class="mt-3 text-base font-semibold text-text-default">{{ project.client_company || project.client_name }}</p>
          <p class="mt-0.5 text-xs text-green-light">{{ project.client_email }}</p>
        </div>

        <div class="rounded-2xl border border-border-default bg-surface p-5">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Inicio</p>
          <p class="mt-3 text-base font-semibold text-text-default">{{ formatDate(project.start_date) }}</p>
        </div>

        <div class="rounded-2xl border border-border-default bg-surface p-5">
          <p class="text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Entrega estimada</p>
          <p class="mt-3 text-base font-semibold text-text-default">{{ formatDate(project.estimated_end_date) }}</p>
          <p v-if="daysRemaining !== null" class="mt-0.5 text-xs" :class="daysRemaining <= 7 ? 'text-red-400' : 'text-green-light'">
            {{ daysRemaining > 0 ? `${daysRemaining} días restantes` : daysRemaining === 0 ? 'Hoy' : `${Math.abs(daysRemaining)} días de retraso` }}
          </p>
        </div>
      </div>

      <!-- Payment milestones (admin only) -->
      <div v-if="authStore.isAdmin && project.payment_milestones?.length" class="mb-8 rounded-2xl border border-border-default bg-surface p-5" data-enter>
        <h3 class="mb-3 text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Hitos de pago del desarrollo</h3>
        <div class="flex flex-wrap gap-3">
          <div
            v-for="(milestone, idx) in project.payment_milestones"
            :key="idx"
            class="flex items-center gap-2 rounded-xl border border-border-default bg-surface-muted/40 px-4 py-2.5 dark:bg-primary-strong"
          >
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-esmerald/10 text-[10px] font-bold text-text-default dark:bg-lemon/15 dark:text-accent">{{ idx + 1 }}</span>
            <div>
              <p class="text-xs font-semibold text-text-default">{{ milestone.label }}</p>
              <p v-if="milestone.description" class="text-[11px] text-green-light">{{ milestone.description }}</p>
            </div>
          </div>
        </div>
        <p class="mt-2 text-[10px] text-green-light/50">Estos hitos son de referencia y no se cobran por la plataforma.</p>
      </div>

      <!-- Hosting tiers -->
      <div v-if="project.hosting_tiers?.length" class="mb-8 rounded-2xl border border-border-default bg-surface p-5" data-enter>
        <h3 class="mb-3 text-xs font-medium uppercase tracking-[0.16em] text-green-light/60">Planes de hosting</h3>
        <div class="grid gap-3 sm:grid-cols-3">
          <div
            v-for="tier in project.hosting_tiers"
            :key="tier.frequency"
            class="relative rounded-xl border p-4 text-center"
            :class="tier.badge ? 'border-border-default dark:border-lemon/30' : 'border-border-default'"
          >
            <span v-if="tier.badge" class="absolute -top-2 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-accent px-2 py-0.5 text-[9px] font-bold text-text-default">{{ tier.badge }}</span>
            <p class="text-xs font-bold uppercase tracking-wider text-text-default">{{ tier.label }}</p>
            <p class="mt-2 text-xl font-bold text-text-brand">{{ formatCurrency(tier.billing_amount) }}</p>
            <p class="text-[11px] text-green-light">cada {{ tier.months === 1 ? 'mes' : `${tier.months} meses` }}</p>
            <p v-if="tier.discount_percent" class="mt-1 text-[10px] font-medium text-text-brand">{{ tier.discount_percent }}% descuento</p>
          </div>
        </div>
      </div>

      <!-- Linked proposal badge -->
      <div v-if="project.proposal_title" class="mb-8 flex items-center gap-2 text-xs text-green-light" data-enter>
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
        Propuesta vinculada: <span class="font-medium text-text-default">{{ project.proposal_title }}</span>
      </div>

      <!-- Module cards -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-enter>
        <template v-for="module in projectModules" :key="module.title">
          <NuxtLink
            v-if="module.href"
            :to="module.href"
            class="group rounded-2xl border border-border-default bg-surface p-6 transition hover:border-border-default hover:shadow-md dark:hover:border-white/15"
          >
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl" :class="module.iconBg">
                <SidebarIcon :name="module.icon" class="h-5 w-5" :class="module.iconColor" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-text-default">{{ module.title }}</h3>
                <p class="text-xs text-green-light">{{ module.subtitle }}</p>
              </div>
            </div>
            <p class="mt-4 text-xs leading-relaxed text-green-light/80">{{ module.description }}</p>
            <div class="mt-3 flex items-center gap-1 text-xs font-medium text-text-default opacity-0 transition group-hover:opacity-100 dark:text-accent">
              Abrir <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </div>
          </NuxtLink>
          <div
            v-else
            class="rounded-2xl border border-border-default bg-surface p-6 opacity-50"
          >
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl" :class="module.iconBg">
                <SidebarIcon :name="module.icon" class="h-5 w-5" :class="module.iconColor" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-text-default">{{ module.title }}</h3>
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
              class="w-full max-w-lg rounded-3xl border border-border-default bg-surface p-6 shadow-2xl sm:p-8"
            >
              <div class="mb-6 flex items-center justify-between">
                <h2 class="text-lg font-bold text-text-default">Editar proyecto</h2>
                <button
                  type="button"
                  class="flex h-8 w-8 items-center justify-center rounded-full text-green-light transition hover:bg-surface-muted hover:text-text-default dark:hover:bg-white/10 dark:hover:text-white"
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
                  <input v-model="editForm.name" type="text" class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea v-model="editForm.description" rows="3" class="w-full resize-none rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Estado</label>
                  <select v-model="editForm.status" class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white dark:focus:border-lemon/40">
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
                    <input v-model="editForm.start_date" type="date" class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white dark:focus:border-lemon/40" />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Entrega estimada</label>
                    <input v-model="editForm.estimated_end_date" type="date" class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition focus:border-border-default dark:bg-primary-strong dark:text-white dark:focus:border-lemon/40" />
                  </div>
                </div>
                <div class="flex justify-end gap-3 pt-2">
                  <button type="button" class="rounded-xl border border-border-default px-5 py-2.5 text-sm font-medium text-green-light transition hover:text-text-default dark:hover:text-white" @click="closeEditModal">Cancelar</button>
                  <button type="submit" :disabled="projectsStore.isUpdating" class="rounded-xl bg-accent px-6 py-2.5 text-sm font-semibold text-text-default transition hover:brightness-105 disabled:opacity-50">
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
import { usePlatformApi } from '~/composables/usePlatformApi'
import { buildPlatformListUrl } from '~/composables/useIncludeArchivedQuery'
import { usePlatformIncludeArchived } from '~/composables/usePlatformIncludeArchived'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import SidebarIcon from '~/components/platform/SidebarIcon.vue'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()
const includeArchived = usePlatformIncludeArchived()

usePageEntrance('#platform-project-detail')

const isEditModalOpen = ref(false)
const syncLoading = ref(false)
const editError = ref('')
const editForm = reactive({
  name: '',
  description: '',
  status: 'active',
  start_date: '',
  estimated_end_date: '',
})

const project = computed(() => projectsStore.currentProject)


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
    href: localePath(`/platform/projects/${route.params.id}/board`),
  },
  {
    title: 'Solicitudes de cambio',
    subtitle: 'Gestión de cambios',
    description: 'El cliente solicita cambios, el admin evalúa y responde.',
    icon: 'refresh',
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-500',
    href: localePath(`/platform/projects/${route.params.id}/changes`),
  },
  {
    title: 'Reporte de bugs',
    subtitle: 'Seguimiento de errores',
    description: 'Reporta y da seguimiento a errores con severidad y pasos para reproducir.',
    icon: 'bug',
    iconBg: 'bg-red-500/10',
    iconColor: 'text-red-500',
    href: localePath(`/platform/projects/${route.params.id}/bugs`),
  },
  {
    title: 'Entregables',
    subtitle: 'Repositorio de archivos',
    description: 'Diseños, documentos, APKs y accesos organizados por categoría.',
    icon: 'file',
    iconBg: 'bg-purple-500/10',
    iconColor: 'text-purple-500',
    href: localePath(`/platform/projects/${route.params.id}/deliverables`),
  },
  {
    title: 'Collection accounts',
    subtitle: 'Billing documents',
    description: 'View collection accounts and PDFs linked to this project.',
    icon: 'file',
    iconBg: 'bg-emerald-500/10',
    iconColor: 'text-text-brand',
    href: localePath(`/platform/projects/${route.params.id}/collection-accounts`),
  },
  {
    title: 'Modelo de datos',
    subtitle: 'Entidades del proyecto',
    description: 'Visualiza las entidades, campos clave y relaciones del modelo de datos.',
    icon: 'database',
    iconBg: 'bg-indigo-500/10',
    iconColor: 'text-indigo-500',
    href: localePath(`/platform/projects/${route.params.id}/data-model`),
  },
  {
    title: 'Pagos',
    subtitle: 'Hosting y suscripción',
    description: 'Gestiona tu plan de hosting, consulta pagos y selecciona tu forma de pago.',
    icon: 'credit-card',
    iconBg: 'bg-teal-500/10',
    iconColor: 'text-teal-500',
    href: localePath(`/platform/projects/${route.params.id}/payments`),
  },
])

function formatCurrency(amount) {
  const num = Number(amount)
  return `$${num.toLocaleString('es-CO')}`
}

function statusBadgeClass(status) {
  const map = {
    active: 'bg-emerald-500/15 text-text-brand',
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

async function runTechnicalSync() {
  if (!project.value) return
  syncLoading.value = true
  try {
    const { get, post } = usePlatformApi()
    const dUrl = buildPlatformListUrl(
      `projects/${project.value.id}/deliverables/`,
      {},
      authStore.isAdmin && includeArchived.value,
    )
    const dres = await get(dUrl)
    const list = dres.data || []
    const anchor = list.find((d) => d.has_business_proposal) || list[0]
    if (!anchor?.id) {
      // eslint-disable-next-line no-alert
      alert('No hay entregable con propuesta para sincronizar.')
      return
    }
    await post(
      `projects/${project.value.id}/deliverables/${anchor.id}/sync-technical-requirements/`,
      {},
    )
    // eslint-disable-next-line no-alert
    alert('Sincronización completada. Revisa entregables y tablero.')
    await projectsStore.fetchProject(project.value.id)
  } catch (e) {
    const msg = e.response?.data?.detail || 'No se pudo sincronizar.'
    // eslint-disable-next-line no-alert
    alert(msg)
  } finally {
    syncLoading.value = false
  }
}

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
