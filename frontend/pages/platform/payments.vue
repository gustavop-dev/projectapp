<template>
  <div id="platform-payments">
    <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
      <div>
        <h1 class="text-2xl font-bold text-text-default">
          {{ authStore.isAdmin ? 'Suscripciones' : 'Mi suscripción' }}
        </h1>
        <p class="mt-1 text-sm text-green-light">
          {{ authStore.isAdmin ? 'Suscripciones de hosting de todos los proyectos.' : 'Estado de tu suscripción de hosting.' }}
        </p>
      </div>
      <label
        v-if="authStore.isAdmin"
        class="flex cursor-pointer items-center gap-2 rounded-full border border-border-default px-3 py-1.5 text-xs font-medium text-green-light"
      >
        <input v-model="includeArchived" type="checkbox" class="rounded border-border-default" />
        Mostrar archivados
      </label>
    </div>

    <div v-if="payStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-esmerald dark:border-t-lemon" />
    </div>

    <div v-else-if="payStore.subscriptions.length === 0" class="rounded-3xl border border-dashed border-border-default py-20 text-center" data-enter>
      <p class="text-sm text-green-light">No hay suscripciones de hosting activas.</p>
    </div>

    <template v-else>
      <!-- Subscriptions list -->
      <div class="space-y-6" data-enter>
        <div
          v-for="sub in payStore.subscriptions"
          :key="sub.id"
          class="rounded-2xl border border-border-default bg-surface p-6"
        >
          <!-- Sub header -->
          <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <NuxtLink
                  :to="localePath(`/platform/projects/${sub.project_id}`)"
                  class="text-base font-semibold text-text-default transition hover:text-esmerald/70 dark:text-white dark:hover:text-accent"
                >
                  {{ sub.project_name }}
                </NuxtLink>
                <span v-if="sub.is_archived" class="rounded-full bg-gray-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-text-muted dark:text-text-subtle">
                  Archivada
                </span>
                <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="subStatusClass(sub.status)">
                  {{ sub.status_display }}
                </span>
              </div>
              <p class="mt-1 text-xs text-green-light">Plan {{ sub.plan_display }} · Próximo cobro: {{ formatDate(sub.next_billing_date) }}</p>
            </div>
            <div class="text-right">
              <p class="text-2xl font-bold text-text-brand">${{ formatMoney(sub.billing_amount) }}</p>
              <p class="text-[10px] text-green-light">COP / {{ sub.plan_display.toLowerCase() }}</p>
            </div>
          </div>

          <!-- Plan pricing summary -->
          <div class="mb-4 grid grid-cols-3 gap-3">
            <div class="rounded-xl border border-border-muted p-3">
              <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Base mensual</p>
              <p class="mt-1 text-sm font-semibold text-text-default">${{ formatMoney(sub.base_monthly_amount) }}</p>
            </div>
            <div class="rounded-xl border border-border-muted p-3">
              <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Descuento</p>
              <p class="mt-1 text-sm font-semibold" :class="sub.discount_percent > 0 ? 'text-text-brand' : 'text-green-light'">
                {{ sub.discount_percent > 0 ? `${sub.discount_percent}%` : 'Sin descuento' }}
              </p>
            </div>
            <div class="rounded-xl border border-border-muted p-3">
              <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Estado</p>
              <p v-if="sub.pending_payments === 0" class="mt-1 text-sm font-semibold text-text-brand">Al día</p>
              <p v-else class="mt-1 text-sm font-semibold text-amber-600 dark:text-amber-400">Requiere atención</p>
            </div>
          </div>

          <NuxtLink
            :to="localePath(`/platform/projects/${sub.project_id}/payments`)"
            class="inline-flex items-center gap-1.5 text-xs font-medium text-text-default transition hover:text-esmerald/70 dark:text-accent dark:hover:text-lemon/80"
          >
            Ver suscripción
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          </NuxtLink>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformIncludeArchived } from '~/composables/usePlatformIncludeArchived'
import { usePlatformAuthStore } from '~/stores/platform-auth'

const localePath = useLocalePath()
import { usePlatformPaymentsStore } from '~/stores/platform-payments'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
usePageEntrance('#platform-payments')

const authStore = usePlatformAuthStore()
const payStore = usePlatformPaymentsStore()
const includeArchived = usePlatformIncludeArchived()

function subStatusClass(s) {
  const map = {
    active: 'bg-emerald-500/15 text-text-brand',
    pending: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    suspended: 'bg-red-500/15 text-red-600 dark:text-red-400',
    cancelled: 'bg-gray-500/15 text-text-muted',
  }
  return map[s] || map.pending
}

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).replace(/,/g, '.')
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function loadSubscriptions() {
  await payStore.fetchSubscriptions(authStore.isAdmin && includeArchived.value)
}

onMounted(async () => {
  await loadSubscriptions()
})

watch(includeArchived, () => {
  if (authStore.isAdmin) loadSubscriptions()
})
</script>
