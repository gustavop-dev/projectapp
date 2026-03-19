<template>
  <div id="platform-payments">
    <div class="mb-6" data-enter>
      <h1 class="text-2xl font-bold text-esmerald dark:text-white">
        {{ authStore.isAdmin ? 'Suscripciones' : 'Mi suscripción' }}
      </h1>
      <p class="mt-1 text-sm text-green-light">
        {{ authStore.isAdmin ? 'Suscripciones de hosting de todos los proyectos.' : 'Estado de tu suscripción de hosting.' }}
      </p>
    </div>

    <div v-if="payStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <div v-else-if="payStore.subscriptions.length === 0" class="rounded-3xl border border-dashed border-esmerald/10 py-20 text-center dark:border-white/10" data-enter>
      <p class="text-sm text-green-light">No hay suscripciones de hosting activas.</p>
    </div>

    <template v-else>
      <!-- Subscriptions list -->
      <div class="space-y-6" data-enter>
        <div
          v-for="sub in payStore.subscriptions"
          :key="sub.id"
          class="rounded-2xl border border-esmerald/[0.06] bg-white p-6 dark:border-white/[0.06] dark:bg-esmerald"
        >
          <!-- Sub header -->
          <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div class="flex items-center gap-2">
                <NuxtLink
                  :to="`/platform/projects/${sub.project_id}`"
                  class="text-base font-semibold text-esmerald transition hover:text-esmerald/70 dark:text-white dark:hover:text-lemon"
                >
                  {{ sub.project_name }}
                </NuxtLink>
                <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="subStatusClass(sub.status)">
                  {{ sub.status_display }}
                </span>
              </div>
              <p class="mt-1 text-xs text-green-light">Plan {{ sub.plan_display }} · Próximo cobro: {{ formatDate(sub.next_billing_date) }}</p>
            </div>
            <div class="text-right">
              <p class="text-2xl font-bold text-esmerald dark:text-lemon">${{ formatMoney(sub.billing_amount) }}</p>
              <p class="text-[10px] text-green-light">COP / {{ sub.plan_display.toLowerCase() }}</p>
            </div>
          </div>

          <!-- Plan pricing summary -->
          <div class="mb-4 grid grid-cols-3 gap-3">
            <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
              <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Base mensual</p>
              <p class="mt-1 text-sm font-semibold text-esmerald dark:text-white">${{ formatMoney(sub.base_monthly_amount) }}</p>
            </div>
            <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
              <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Descuento</p>
              <p class="mt-1 text-sm font-semibold" :class="sub.discount_percent > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-green-light'">
                {{ sub.discount_percent > 0 ? `${sub.discount_percent}%` : 'Sin descuento' }}
              </p>
            </div>
            <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
              <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Estado</p>
              <p v-if="sub.pending_payments === 0" class="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">Al día</p>
              <p v-else class="mt-1 text-sm font-semibold text-amber-600 dark:text-amber-400">Requiere atención</p>
            </div>
          </div>

          <NuxtLink
            :to="`/platform/projects/${sub.project_id}/payments`"
            class="inline-flex items-center gap-1.5 text-xs font-medium text-esmerald transition hover:text-esmerald/70 dark:text-lemon dark:hover:text-lemon/80"
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
import { onMounted } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformPaymentsStore } from '~/stores/platform-payments'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
defineI18nRoute(false)
useHead({ title: 'Pagos — ProjectApp' })
usePageEntrance('#platform-payments')

const authStore = usePlatformAuthStore()
const payStore = usePlatformPaymentsStore()

function subStatusClass(s) {
  const map = {
    active: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    pending: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    suspended: 'bg-red-500/15 text-red-600 dark:text-red-400',
    cancelled: 'bg-gray-500/15 text-gray-500',
  }
  return map[s] || map.pending
}

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('es-CO', { maximumFractionDigits: 0 })
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(async () => { await payStore.fetchSubscriptions() })
</script>
