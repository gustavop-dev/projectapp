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

    <section v-if="authStore.isAdmin" class="grid gap-4 md:grid-cols-3" data-enter>
      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Clientes activos</p>
        <p class="mt-4 text-4xl font-bold text-esmerald dark:text-lemon">{{ activeClientsCount }}</p>
      </article>

      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Onboarding pendiente</p>
        <p class="mt-4 text-4xl font-bold text-esmerald dark:text-white">{{ pendingClientsCount }}</p>
      </article>

      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-green-light">Inactivos</p>
        <p class="mt-4 text-4xl font-bold text-esmerald/30 dark:text-white/40">{{ inactiveClientsCount }}</p>
      </article>
    </section>

    <section v-if="authStore.isAdmin" class="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]" data-enter>
      <article class="rounded-3xl border border-esmerald/[0.06] bg-white shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <div class="flex flex-col gap-3 border-b border-esmerald/[0.06] px-6 py-5 dark:border-white/[0.06] sm:flex-row sm:items-center sm:justify-between">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Clientes recientes</h2>
          <NuxtLink
            to="/platform/clients"
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
                  <NuxtLink :to="`/platform/clients/${client.user_id}`" class="font-medium text-esmerald transition hover:text-esmerald/70 dark:text-white dark:hover:text-lemon">
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

      <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <h2 class="text-base font-medium text-esmerald dark:text-white">Próximamente</h2>
        <p class="mt-2 text-sm leading-6 text-green-light">
          Módulos planeados para la plataforma.
        </p>

        <div class="mt-6 space-y-3">
          <div v-for="module in adminModules" :key="module.title" class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
            <p class="text-sm font-medium text-esmerald dark:text-white">{{ module.title }}</p>
            <p class="mt-1 text-xs text-green-light">{{ module.description }}</p>
          </div>
        </div>
      </article>
    </section>

    <section v-else class="space-y-6" data-enter>
      <!-- Client profile card -->
      <div class="grid gap-6 xl:grid-cols-2">
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Tu perfil</h2>
          <div class="mt-6 flex items-center gap-4">
            <div class="flex h-14 w-14 items-center justify-center rounded-full bg-esmerald text-base font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
              {{ authStore.userInitials }}
            </div>
            <div>
              <p class="font-medium text-esmerald dark:text-white">{{ authStore.displayName }}</p>
              <p class="mt-0.5 text-sm text-green-light">{{ authStore.user?.email }}</p>
            </div>
          </div>
          <dl class="mt-6 grid gap-4 sm:grid-cols-2">
            <div class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
              <dt class="text-xs uppercase tracking-[0.16em] text-green-light/60">Empresa</dt>
              <dd class="mt-2 text-sm font-medium text-esmerald dark:text-white">{{ authStore.user?.company_name || '—' }}</dd>
            </div>
            <div class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
              <dt class="text-xs uppercase tracking-[0.16em] text-green-light/60">Teléfono</dt>
              <dd class="mt-2 text-sm font-medium text-esmerald dark:text-white">{{ authStore.user?.phone || '—' }}</dd>
            </div>
          </dl>
        </article>

        <!-- Quick links -->
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Acceso rápido</h2>
          <div class="mt-6 grid gap-3 sm:grid-cols-2">
            <NuxtLink to="/platform/projects" class="group rounded-xl border border-esmerald/[0.06] p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
              <p class="text-sm font-medium text-esmerald dark:text-white">Mis proyectos</p>
              <p class="mt-1 text-xs text-green-light">Estado de avance y módulos.</p>
            </NuxtLink>
            <NuxtLink to="/platform/payments" class="group rounded-xl border border-esmerald/[0.06] p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
              <p class="text-sm font-medium text-esmerald dark:text-white">Mis pagos</p>
              <p class="mt-1 text-xs text-green-light">Suscripciones y facturación.</p>
            </NuxtLink>
            <NuxtLink to="/platform/changes" class="group rounded-xl border border-esmerald/[0.06] p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
              <p class="text-sm font-medium text-esmerald dark:text-white">Solicitudes</p>
              <p class="mt-1 text-xs text-green-light">Cambios y requerimientos.</p>
            </NuxtLink>
            <NuxtLink to="/platform/bugs" class="group rounded-xl border border-esmerald/[0.06] p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:hover:border-white/12">
              <p class="text-sm font-medium text-esmerald dark:text-white">Bugs</p>
              <p class="mt-1 text-xs text-green-light">Reportar y seguir errores.</p>
            </NuxtLink>
          </div>
        </article>
      </div>

      <!-- Client: Subscriptions & Pending Payments -->
      <div v-if="clientSubscriptions.length" class="space-y-4">
        <h2 class="text-base font-medium text-esmerald dark:text-white" data-enter>Hosting y pagos</h2>
        <div
          v-for="sub in clientSubscriptions"
          :key="sub.id"
          class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald"
          data-enter
        >
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div class="flex items-center gap-2">
                <NuxtLink :to="`/platform/projects/${sub.project_id}`" class="text-sm font-semibold text-esmerald transition hover:text-esmerald/70 dark:text-white dark:hover:text-lemon">
                  {{ sub.project_name }}
                </NuxtLink>
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="sub.status === 'active' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'">
                  {{ sub.status_display }}
                </span>
              </div>
              <p class="mt-1 text-xs text-green-light">Plan {{ sub.plan_display }} · Próximo cobro: {{ formatDate(sub.next_billing_date) }}</p>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <p class="text-xl font-bold text-esmerald dark:text-lemon">${{ formatMoney(sub.billing_amount) }}</p>
                <p class="text-[10px] text-green-light">COP</p>
              </div>
              <NuxtLink
                :to="`/platform/projects/${sub.project_id}/payments`"
                class="flex items-center gap-1.5 rounded-xl bg-lemon px-4 py-2.5 text-xs font-semibold text-esmerald-dark transition hover:brightness-105"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                {{ sub.pending_payments > 0 ? 'Pagar' : 'Ver pagos' }}
              </NuxtLink>
            </div>
          </div>
          <!-- Payment method logos -->
          <div class="mt-3 flex items-center gap-3 border-t border-esmerald/[0.04] pt-3 dark:border-white/[0.04]">
            <img src="/images/payments/card.svg" alt="Tarjeta" class="h-5 w-5 opacity-40 dark:invert dark:opacity-30" />
            <img src="/images/payments/pse-seeklogo.png" alt="PSE" class="h-5 w-5 rounded opacity-60" />
            <img src="/images/payments/Nequi.jpeg" alt="Nequi" class="h-5 w-5 rounded opacity-60" />
            <img src="/images/payments/Bancolombia.png" alt="Bancolombia" class="h-5 w-5 rounded-full opacity-60" />
            <span v-if="sub.pending_payments > 0" class="ml-auto rounded-full bg-amber-500/15 px-2.5 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
              {{ sub.pending_payments }} pago{{ sub.pending_payments > 1 ? 's' : '' }} pendiente{{ sub.pending_payments > 1 ? 's' : '' }}
            </span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformClientsStore } from '~/stores/platform-clients'
import { usePlatformPaymentsStore } from '~/stores/platform-payments'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

useHead({
  title: 'Dashboard del portal — ProjectApp',
})

usePageEntrance('#platform-dashboard')

const authStore = usePlatformAuthStore()
const platformClientsStore = usePlatformClientsStore()
const payStore = usePlatformPaymentsStore()
const projectsStore = usePlatformProjectsStore()

authStore.hydrate()

const clientProjects = computed(() => projectsStore.projects || [])
const clientSubscriptions = computed(() => payStore.subscriptions || [])

const adminModules = [
  {
    title: 'Proyectos',
    description: 'Seguimiento de proyectos, estados y próximos entregables.',
  },
  {
    title: 'Pagos',
    description: 'Historial de cobros, próximos vencimientos y comprobantes.',
  },
  {
    title: 'Notificaciones',
    description: 'Alertas centralizadas sobre movimientos importantes del portal.',
  },
]

const clientModules = [
  {
    title: 'Mis proyectos',
    description: 'Estado de avance, hitos y fechas clave de entrega.',
  },
  {
    title: 'Mis solicitudes',
    description: 'Canal para cambios, requerimientos y seguimiento de tickets.',
  },
  {
    title: 'Mis pagos',
    description: 'Resumen de facturación y próximos movimientos financieros.',
  },
]

const welcomeTitle = computed(() => (
  authStore.isAdmin
    ? `Hola ${authStore.displayName}, ya tienes lista la base del portal.`
    : `Hola ${authStore.displayName}, bienvenido a tu portal.`
))

const welcomeDescription = computed(() => (
  authStore.isAdmin
    ? 'Desde aquí podrás invitar clientes, revisar su estado de onboarding y preparar la evolución del resto de módulos de la plataforma.'
    : 'Estamos preparando tu espacio personalizado para que puedas consultar el estado de tus proyectos y tus próximos entregables desde un solo lugar.'
))

const activeClientsCount = computed(() => platformClientsStore.activeClientsCount)
const pendingClientsCount = computed(() => platformClientsStore.pendingClientsCount)
const inactiveClientsCount = computed(() => platformClientsStore.inactiveClientsCount)
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
  return Number(val).toLocaleString('es-CO', { maximumFractionDigits: 0 })
}

onMounted(async () => {
  if (authStore.isAdmin) {
    await platformClientsStore.fetchClients('all')
  } else {
    await Promise.all([
      projectsStore.fetchProjects(),
      payStore.fetchSubscriptions(),
    ])
  }
})
</script>
