<template>
  <div id="platform-dashboard" class="space-y-8">
    <section data-enter>
      <h1 class="font-light text-3xl text-esmerald dark:text-white sm:text-4xl">
        {{ welcomeTitle }}
      </h1>
      <p class="mt-3 max-w-2xl text-sm leading-7 text-green-light">
        {{ welcomeDescription }}
      </p>
    </section>

    <section v-if="authStore.isAdmin" class="flex justify-end" data-enter>
      <label class="flex cursor-pointer items-center gap-2 rounded-full border border-esmerald/10 px-3 py-1.5 text-xs font-medium text-green-light dark:border-white/10">
        <input v-model="includeArchived" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
        Mostrar archivados en listas agregadas
      </label>
    </section>

    <section v-if="authStore.isAdmin" class="grid gap-4 sm:grid-cols-2 md:grid-cols-4" data-enter>
      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Clientes activos</p>
        <p class="mt-4 text-4xl font-bold text-esmerald dark:text-lemon">{{ activeClientsCount }}</p>
      </article>

      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Proyectos activos</p>
        <p class="mt-4 text-4xl font-bold text-esmerald dark:text-white">{{ adminActiveProjectsCount }}</p>
      </article>

      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Bugs abiertos</p>
        <p class="mt-4 text-4xl font-bold" :class="adminOpenBugsCount > 0 ? 'text-red-500' : 'text-esmerald dark:text-white'">{{ adminOpenBugsCount }}</p>
      </article>

      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Cambios pendientes</p>
        <p class="mt-4 text-4xl font-bold" :class="adminPendingChangesCount > 0 ? 'text-amber-500' : 'text-esmerald dark:text-white'">{{ adminPendingChangesCount }}</p>
      </article>
    </section>

    <section v-if="authStore.isAdmin" class="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]" data-enter>
      <article class="rounded-3xl border border-esmerald/[0.06] bg-white shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <div class="flex flex-col gap-3 border-b border-esmerald/[0.06] px-6 py-5 dark:border-white/[0.06] sm:flex-row sm:items-center sm:justify-between">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Clientes recientes</h2>
          <NuxtLink
            :to="localePath('/platform/clients')"
            class="rounded-full border border-esmerald/10 px-4 py-2 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
          >
            Ver todos
          </NuxtLink>
        </div>

        <div v-if="platformClientsStore.isLoading" class="px-6 py-12 text-center text-sm text-green-light">
          Cargando...
        </div>

        <div v-else-if="recentClients.length === 0" class="px-6 py-12 text-center text-sm text-green-light">
          Todavía no hay clientes registrados.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead>
              <tr class="border-b border-esmerald/[0.06] text-xs uppercase tracking-[0.16em] text-green-light/60 dark:border-white/[0.06]">
                <th class="px-6 py-3 font-medium">Cliente</th>
                <th class="px-6 py-3 font-medium">Empresa</th>
                <th class="px-6 py-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="client in recentClients" :key="client.user_id" class="border-b border-esmerald/[0.04] last:border-b-0 dark:border-white/[0.03]">
                <td class="px-6 py-4">
                  <NuxtLink :to="localePath(`/platform/clients/${client.user_id}`)" class="font-medium text-esmerald transition hover:text-esmerald/70 dark:text-white dark:hover:text-lemon">
                    {{ client.first_name }} {{ client.last_name }}
                  </NuxtLink>
                  <p class="mt-0.5 text-xs text-green-light/60">{{ client.email }}</p>
                </td>
                <td class="px-6 py-4 text-green-light">{{ client.company_name || '—' }}</td>
                <td class="px-6 py-4">
                  <span class="inline-flex rounded-full px-3 py-1 text-xs font-medium" :class="statusClass(client)">
                    {{ statusLabel(client) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <!-- Activity & Payments summary -->
      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <h2 class="text-base font-medium text-esmerald dark:text-white">Resumen</h2>

        <!-- Stats -->
        <div class="mt-4 grid grid-cols-2 gap-3">
          <div class="rounded-xl border border-esmerald/[0.06] p-3 dark:border-white/[0.06]">
            <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Bugs abiertos</p>
            <p class="mt-1 text-lg font-bold" :class="adminOpenBugsCount > 0 ? 'text-red-500' : 'text-esmerald dark:text-white'">{{ adminOpenBugsCount }}</p>
          </div>
          <div class="rounded-xl border border-esmerald/[0.06] p-3 dark:border-white/[0.06]">
            <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Cambios pendientes</p>
            <p class="mt-1 text-lg font-bold" :class="adminPendingChangesCount > 0 ? 'text-amber-500' : 'text-esmerald dark:text-white'">{{ adminPendingChangesCount }}</p>
          </div>
          <div class="rounded-xl border border-esmerald/[0.06] p-3 dark:border-white/[0.06]">
            <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Entregables</p>
            <p class="mt-1 text-lg font-bold text-esmerald dark:text-white">{{ adminDeliverablesCount }}</p>
          </div>
          <div class="rounded-xl border border-esmerald/[0.06] p-3 dark:border-white/[0.06]">
            <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Proyectos activos</p>
            <p class="mt-1 text-lg font-bold text-esmerald dark:text-lemon">{{ adminActiveProjectsCount }}</p>
          </div>
        </div>

        <!-- Upcoming payments -->
        <div class="mt-5">
          <p class="mb-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Pagos proximos</p>
          <div v-if="adminSubscriptions.length" class="space-y-2">
            <div v-for="sub in adminSubscriptions" :key="sub.id" class="flex items-center justify-between rounded-xl border border-esmerald/[0.06] p-3 dark:border-white/[0.06]">
              <div class="min-w-0 flex-1">
                <p class="truncate text-xs font-medium text-esmerald dark:text-white">{{ sub.project_name }}</p>
                <p class="text-[10px] text-green-light">{{ formatDate(sub.next_billing_date) }}</p>
              </div>
              <div class="flex items-center gap-2">
                <p class="text-xs font-bold text-esmerald dark:text-lemon">${{ formatMoney(sub.billing_amount) }}</p>
                <span v-if="sub.pending_payments > 0" class="h-2 w-2 shrink-0 rounded-full bg-amber-500" title="Pago pendiente" />
              </div>
            </div>
          </div>
          <p v-else class="text-xs text-green-light">Sin suscripciones activas.</p>
        </div>
      </article>
    </section>

    <section v-else class="space-y-6" data-enter>
      <!-- Client: Project status cards -->
      <div class="grid gap-4 sm:grid-cols-3">
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Proyectos activos</p>
          <p class="mt-4 text-4xl font-bold text-esmerald dark:text-lemon">{{ clientActiveProjects.length }}</p>
        </article>
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Bugs abiertos</p>
          <p class="mt-4 text-4xl font-bold" :class="clientOpenBugsCount > 0 ? 'text-red-500' : 'text-esmerald dark:text-white'">{{ clientOpenBugsCount }}</p>
        </article>
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Cambios en curso</p>
          <p class="mt-4 text-4xl font-bold" :class="clientPendingChangesCount > 0 ? 'text-amber-500' : 'text-esmerald dark:text-white'">{{ clientPendingChangesCount }}</p>
        </article>
      </div>

      <!-- Client: Projects overview + Hosting -->
      <div class="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <!-- Projects list -->
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <div class="flex flex-col gap-3 border-b border-esmerald/[0.06] px-6 py-5 dark:border-white/[0.06] sm:flex-row sm:items-center sm:justify-between">
            <h2 class="text-base font-medium text-esmerald dark:text-white">Mis proyectos</h2>
            <NuxtLink
              :to="localePath('/platform/projects')"
              class="rounded-full border border-esmerald/10 px-4 py-2 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
            >
              Ver todos
            </NuxtLink>
          </div>

          <div v-if="projectsStore.isLoading" class="px-6 py-12 text-center text-sm text-green-light">
            Cargando...
          </div>

          <div v-else-if="clientProjects.length === 0" class="px-6 py-12 text-center text-sm text-green-light">
            No tienes proyectos registrados.
          </div>

          <div v-else class="divide-y divide-esmerald/[0.04] dark:divide-white/[0.04]">
            <div v-for="project in clientProjects" :key="project.id" class="flex items-center gap-4 px-6 py-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <NuxtLink :to="localePath(`/platform/projects/${project.id}`)" class="truncate text-sm font-medium text-esmerald transition hover:text-esmerald/70 dark:text-white dark:hover:text-lemon">
                    {{ project.name }}
                  </NuxtLink>
                  <span class="shrink-0 rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="projectStatusClass(project.status)">
                    {{ projectStatusLabel(project.status) }}
                  </span>
                </div>
                <div class="mt-2 flex items-center gap-3">
                  <div class="h-1.5 flex-1 rounded-full bg-esmerald/[0.06] dark:bg-white/[0.06]">
                    <div class="h-full rounded-full bg-esmerald transition-all dark:bg-lemon" :style="{ width: `${project.progress || 0}%` }" />
                  </div>
                  <span class="shrink-0 text-xs font-medium text-green-light">{{ project.progress || 0 }}%</span>
                </div>
              </div>
              <NuxtLink
                :to="localePath(`/platform/projects/${project.id}/board`)"
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
                title="Ver tablero"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="4" y="3" width="4" height="18" rx="1" />
                  <rect x="10" y="3" width="4" height="12" rx="1" />
                  <rect x="16" y="3" width="4" height="15" rx="1" />
                </svg>
              </NuxtLink>
            </div>
          </div>
        </article>

        <!-- Hosting & quick info -->
        <div class="space-y-4">
          <!-- Hosting remaining time -->
          <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
            <h2 class="text-base font-medium text-esmerald dark:text-white">Hosting</h2>
            <div v-if="clientSubscriptions.length" class="mt-4 space-y-4">
              <div v-for="sub in clientSubscriptions" :key="sub.id" class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
                <div class="flex items-center justify-between">
                  <p class="text-sm font-medium text-esmerald dark:text-white">{{ sub.project_name }}</p>
                  <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="sub.status === 'active' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'">
                    {{ sub.status_display }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-green-light">Proximo cobro: {{ formatDate(sub.next_billing_date) }}</p>
                <p v-if="hostingDaysLeft(sub) !== null" class="mt-1 text-xs font-medium" :class="hostingDaysLeft(sub) <= 30 ? 'text-amber-500' : 'text-emerald-500'">
                  {{ hostingDaysLeft(sub) }} dias restantes del periodo actual
                </p>
                <div class="mt-3 flex items-center justify-between">
                  <p class="text-lg font-bold text-esmerald dark:text-lemon">${{ formatMoney(sub.billing_amount) }} <span class="text-[10px] font-normal text-green-light">COP</span></p>
                  <NuxtLink
                    v-if="hostingDaysLeft(sub) !== null && hostingDaysLeft(sub) <= 30"
                    :to="localePath(`/platform/projects/${sub.project_id}/payments`)"
                    class="rounded-lg bg-lemon px-3 py-1.5 text-xs font-semibold text-esmerald-dark transition hover:brightness-105"
                  >
                    Renovar
                  </NuxtLink>
                  <NuxtLink
                    v-else
                    :to="localePath(`/platform/projects/${sub.project_id}/payments`)"
                    class="text-xs font-medium text-esmerald transition hover:text-esmerald/70 dark:text-lemon dark:hover:text-lemon/80"
                  >
                    Ver pagos
                  </NuxtLink>
                </div>
              </div>
            </div>
            <div v-else class="mt-4 rounded-xl border border-dashed border-esmerald/10 p-4 text-center dark:border-white/10">
              <p class="text-xs text-green-light">Sin suscripciones activas</p>
            </div>
          </article>

          <!-- Quick links -->
          <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
            <h2 class="text-base font-medium text-esmerald dark:text-white">Acceso rapido</h2>
            <div class="mt-4 grid gap-2 sm:grid-cols-2">
              <NuxtLink :to="localePath('/platform/changes')" class="rounded-xl border border-esmerald/[0.06] p-3 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
                <p class="text-sm font-medium text-esmerald dark:text-white">Solicitudes</p>
                <p class="mt-0.5 text-[10px] text-green-light">Cambios y requerimientos</p>
              </NuxtLink>
              <NuxtLink :to="localePath('/platform/bugs')" class="rounded-xl border border-esmerald/[0.06] p-3 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
                <p class="text-sm font-medium text-esmerald dark:text-white">Bugs</p>
                <p class="mt-0.5 text-[10px] text-green-light">Reportar y seguir errores</p>
              </NuxtLink>
              <NuxtLink :to="localePath('/platform/deliverables')" class="rounded-xl border border-esmerald/[0.06] p-3 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
                <p class="text-sm font-medium text-esmerald dark:text-white">Entregables</p>
                <p class="mt-0.5 text-[10px] text-green-light">Archivos y versiones</p>
              </NuxtLink>
              <NuxtLink :to="localePath('/platform/payments')" class="rounded-xl border border-esmerald/[0.06] p-3 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
                <p class="text-sm font-medium text-esmerald dark:text-white">Pagos</p>
                <p class="mt-0.5 text-[10px] text-green-light">Suscripciones y facturas</p>
              </NuxtLink>
            </div>
          </article>
        </div>
      </div>

      <!-- Recent deliverables -->
      <article v-if="clientRecentDeliverables.length" class="rounded-3xl border border-esmerald/[0.06] bg-white shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none" data-enter>
        <div class="flex flex-col gap-3 border-b border-esmerald/[0.06] px-6 py-5 dark:border-white/[0.06] sm:flex-row sm:items-center sm:justify-between">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Ultimos entregables</h2>
          <NuxtLink
            :to="localePath('/platform/deliverables')"
            class="rounded-full border border-esmerald/10 px-4 py-2 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
          >
            Ver todos
          </NuxtLink>
        </div>
        <div class="divide-y divide-esmerald/[0.04] dark:divide-white/[0.04]">
          <div v-for="del in clientRecentDeliverables" :key="del.id" class="flex items-center gap-4 px-6 py-4">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-500/10">
              <svg class="h-5 w-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14,2 14,8 20,8" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <p class="truncate text-sm font-medium text-esmerald dark:text-white">{{ del.title }}</p>
              <p class="mt-0.5 text-xs text-green-light">{{ del.project_name }} · {{ formatDate(del.created_at) }}</p>
            </div>
            <span class="shrink-0 rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="deliverableCategoryClass(del.category)">
              {{ deliverableCategoryLabel(del.category) }}
            </span>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformIncludeArchived } from '~/composables/usePlatformIncludeArchived'
import { usePlatformAuthStore } from '~/stores/platform-auth'

const localePath = useLocalePath()
import { usePlatformClientsStore } from '~/stores/platform-clients'
import { usePlatformPaymentsStore } from '~/stores/platform-payments'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import { usePlatformBugReportsStore } from '~/stores/platform-bug-reports'
import { usePlatformChangeRequestsStore } from '~/stores/platform-change-requests'
import { usePlatformDeliverablesStore } from '~/stores/platform-deliverables'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})


usePageEntrance('#platform-dashboard')

const authStore = usePlatformAuthStore()
const platformClientsStore = usePlatformClientsStore()
const payStore = usePlatformPaymentsStore()
const projectsStore = usePlatformProjectsStore()
const bugStore = usePlatformBugReportsStore()
const changeStore = usePlatformChangeRequestsStore()
const deliverablesStore = usePlatformDeliverablesStore()
const includeArchived = usePlatformIncludeArchived()

authStore.hydrate()

const clientProjects = computed(() => projectsStore.projects || [])
const clientSubscriptions = computed(() => payStore.subscriptions || [])
const clientActiveProjects = computed(() => clientProjects.value.filter((p) => p.status === 'active'))
const clientOpenBugsCount = computed(() => bugStore.bugReports.filter((b) => b.status !== 'resolved').length)
const clientPendingChangesCount = computed(() => changeStore.changeRequests.filter((cr) => ['pending', 'evaluating'].includes(cr.status)).length)
const clientRecentDeliverables = computed(() => (deliverablesStore.deliverables || []).slice(0, 5))

const adminOpenBugsCount = computed(() => bugStore.bugReports.filter((b) => b.status !== 'resolved').length)
const adminPendingChangesCount = computed(() => changeStore.changeRequests.filter((cr) => ['pending', 'evaluating'].includes(cr.status)).length)
const adminDeliverablesCount = computed(() => (deliverablesStore.deliverables || []).length)
const adminActiveProjectsCount = computed(() => (projectsStore.projects || []).filter((p) => p.status === 'active').length)
const adminSubscriptions = computed(() => (payStore.subscriptions || []).slice(0, 5))

const welcomeTitle = computed(() => (
  authStore.isAdmin
    ? `Hola ${authStore.displayName}`
    : `Hola ${authStore.displayName}, bienvenido a tu portal.`
))

const welcomeDescription = computed(() => (
  authStore.isAdmin
    ? 'Vista general de clientes, proyectos y actividad reciente en la plataforma.'
    : 'Consulta el estado de tus proyectos, entregables y proximos pagos desde un solo lugar.'
))

const activeClientsCount = computed(() => platformClientsStore.activeClientsCount)
const recentClients = computed(() => platformClientsStore.recentClients)

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function statusLabel(client) {
  if (!client.is_active) return 'Inactivo'
  if (!client.is_onboarded) return 'Pendiente'
  return 'Activo'
}

function statusClass(client) {
  if (!client.is_active) return 'bg-white/10 text-green-light/60'
  if (!client.is_onboarded) return 'bg-amber-100 text-amber-700 dark:bg-lemon/10 dark:text-lemon'
  return 'bg-emerald-500/15 text-emerald-400'
}

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).replace(/,/g, '.')
}

function projectStatusLabel(status) {
  const map = { active: 'Activo', paused: 'Pausado', completed: 'Completado', archived: 'Archivado' }
  return map[status] || status
}

function projectStatusClass(status) {
  const map = {
    active: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    paused: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    completed: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    archived: 'bg-white/10 text-green-light/60',
  }
  return map[status] || 'bg-white/10 text-green-light/60'
}

function hostingDaysLeft(sub) {
  if (!sub.next_billing_date) return null
  const now = new Date()
  const next = new Date(sub.next_billing_date)
  const diff = Math.ceil((next - now) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 0
}

function deliverableCategoryLabel(cat) {
  const map = { designs: 'Diseno', documents: 'Documento', credentials: 'Credenciales', apks: 'APK', other: 'Otro' }
  return map[cat] || cat
}

function deliverableCategoryClass(cat) {
  const map = {
    designs: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    documents: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    credentials: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    apks: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    other: 'bg-gray-500/15 text-gray-600 dark:text-gray-400',
  }
  return map[cat] || 'bg-gray-500/15 text-gray-600 dark:text-gray-400'
}

async function loadAggregatedLists() {
  const a = authStore.isAdmin && includeArchived.value
  await Promise.all([
    payStore.fetchSubscriptions(a),
    bugStore.fetchAllBugReports(null, a),
    changeStore.fetchAllChangeRequests(null, a),
    deliverablesStore.fetchAllDeliverables(null, a),
  ])
}

onMounted(async () => {
  if (authStore.isAdmin) {
    await Promise.all([
      platformClientsStore.fetchClients('all'),
      projectsStore.fetchProjects(),
      loadAggregatedLists(),
    ])
  } else {
    await Promise.all([
      projectsStore.fetchProjects(),
      payStore.fetchSubscriptions(),
      bugStore.fetchAllBugReports(),
      changeStore.fetchAllChangeRequests(),
      deliverablesStore.fetchAllDeliverables(),
    ])
  }
})

watch(includeArchived, () => {
  if (authStore.isAdmin) loadAggregatedLists()
})
</script>
