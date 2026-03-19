<template>
  <div id="platform-project-payments">
    <div v-if="payStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="mb-6" data-enter>
        <NuxtLink :to="`/platform/projects/${projectId}`" class="mb-2 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
          {{ projectName }}
        </NuxtLink>
        <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">Pagos</h1>
      </div>

      <!-- No subscription -->
      <div v-if="!sub" class="rounded-3xl border border-dashed border-esmerald/10 py-16 text-center dark:border-white/10" data-enter>
        <p class="text-sm text-green-light">Este proyecto no tiene suscripción de hosting.</p>
      </div>

      <template v-else>
        <!-- Subscription card -->
        <div class="mb-6 rounded-2xl border border-esmerald/[0.06] bg-white p-6 dark:border-white/[0.06] dark:bg-esmerald" data-enter>
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div class="flex items-center gap-2">
                <h2 class="text-lg font-bold text-esmerald dark:text-white">Hosting {{ sub.plan_display }}</h2>
                <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="subStatusClass(sub.status)">{{ sub.status_display }}</span>
              </div>
              <p class="mt-1 text-xs text-green-light">Inicio: {{ formatDate(sub.start_date) }} · Próximo cobro: {{ formatDate(sub.next_billing_date) }}</p>
            </div>
            <div class="text-right">
              <p class="text-3xl font-bold text-esmerald dark:text-lemon">${{ formatMoney(sub.billing_amount) }}</p>
              <p class="text-xs text-green-light">COP / {{ sub.plan_display.toLowerCase() }}</p>
              <p v-if="sub.discount_percent > 0" class="mt-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">{{ sub.discount_percent }}% de descuento</p>
            </div>
          </div>
        </div>

        <!-- Accepted payment methods -->
        <div class="mb-6 rounded-2xl border border-esmerald/[0.06] bg-white px-6 py-4 dark:border-white/[0.06] dark:bg-esmerald" data-enter>
          <p class="mb-3 text-[10px] font-semibold uppercase tracking-wider text-green-light/60">Medios de pago aceptados</p>
          <div class="flex items-center gap-4">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-50 p-1.5 dark:bg-white/[0.06]">
              <img src="/images/payments/card.svg" alt="Tarjeta" class="h-6 w-6 text-green-light dark:invert dark:opacity-70" />
            </div>
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-50 p-1 dark:bg-white/[0.06]">
              <img src="/images/payments/pse-seeklogo.png" alt="PSE" class="h-7 w-7 rounded object-contain" />
            </div>
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-50 p-1 dark:bg-white/[0.06]">
              <img src="/images/payments/Nequi.jpeg" alt="Nequi" class="h-7 w-7 rounded object-contain" />
            </div>
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-50 p-1 dark:bg-white/[0.06]">
              <img src="/images/payments/Bancolombia.png" alt="Bancolombia" class="h-7 w-7 rounded-full object-contain" />
            </div>
            <span class="text-[10px] text-green-light/50">Procesado de forma segura por Wompi</span>
          </div>
        </div>

        <!-- Payments list -->
        <div class="space-y-3" data-enter>
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Historial de pagos</h3>

          <div
            v-for="payment in sortedPayments"
            :key="payment.id"
            class="rounded-2xl border bg-white p-5 transition dark:bg-esmerald"
            :class="paymentBorderClass(payment.status)"
          >
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div class="flex-1">
                <div class="mb-1 flex items-center gap-2">
                  <span class="flex h-8 w-8 items-center justify-center rounded-xl" :class="paymentIconBg(payment.status)">
                    <span class="text-sm">{{ paymentIcon(payment.status) }}</span>
                  </span>
                  <div>
                    <p class="text-sm font-semibold text-esmerald dark:text-white">{{ payment.description || 'Pago hosting' }}</p>
                    <p class="text-[10px] text-green-light/60">
                      {{ formatDate(payment.billing_period_start) }} — {{ formatDate(payment.billing_period_end) }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-4">
                <div class="text-right">
                  <p class="text-lg font-bold text-esmerald dark:text-white">${{ formatMoney(payment.amount) }}</p>
                  <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="paymentStatusClass(payment.status)">
                    {{ paymentStatusLabel(payment.status) }}
                  </span>
                </div>

                <!-- Pay button (client/admin, pending/overdue) -->
                <div v-if="canPay(payment)" class="shrink-0">
                  <button
                    type="button"
                    :disabled="payStore.isUpdating"
                    class="flex items-center gap-2 rounded-xl bg-lemon px-5 py-3 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50"
                    @click="handleOpenPayment(payment)"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                    Pagar ahora
                  </button>
                </div>
              </div>
            </div>

            <!-- Paid confirmation -->
            <div v-if="payment.status === 'paid' && payment.paid_at" class="mt-3 flex items-center gap-2 text-[10px] text-emerald-600 dark:text-emerald-400">
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              Pagado el {{ formatDate(payment.paid_at) }}
            </div>
          </div>

          <div v-if="sortedPayments.length === 0" class="py-8 text-center text-sm text-green-light">
            No hay pagos registrados aún.
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformPaymentsStore } from '~/stores/platform-payments'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
defineI18nRoute(false)
useHead({
  title: 'Pagos — ProjectApp',
  script: [{ src: 'https://checkout.wompi.co/widget.js', async: true }],
})
usePageEntrance('#platform-project-payments')

const route = useRoute()
const authStore = usePlatformAuthStore()
const payStore = usePlatformPaymentsStore()
const projectsStore = usePlatformProjectsStore()

const projectId = computed(() => route.params.id)
const projectName = computed(() => projectsStore.currentProject?.name || 'Proyecto')
const sub = computed(() => payStore.currentSubscription)

const sortedPayments = computed(() => {
  return [...payStore.payments].sort((a, b) => {
    const order = { overdue: 0, pending: 1, processing: 2, failed: 3, paid: 4 }
    return (order[a.status] ?? 5) - (order[b.status] ?? 5)
  })
})

function canPay(payment) {
  return ['pending', 'overdue', 'processing'].includes(payment.status)
}

function subStatusClass(s) {
  const map = {
    active: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    pending: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    suspended: 'bg-red-500/15 text-red-600 dark:text-red-400',
    cancelled: 'bg-gray-500/15 text-gray-500',
  }
  return map[s] || map.pending
}

function paymentBorderClass(s) {
  const map = {
    pending: 'border-amber-500/20 dark:border-amber-500/15',
    overdue: 'border-red-500/20 dark:border-red-500/15',
    paid: 'border-esmerald/[0.06] dark:border-white/[0.06]',
    processing: 'border-blue-500/20 dark:border-blue-500/15',
    failed: 'border-red-500/20 dark:border-red-500/15',
  }
  return map[s] || 'border-esmerald/[0.06] dark:border-white/[0.06]'
}

function paymentIconBg(s) {
  const map = {
    pending: 'bg-amber-500/10', overdue: 'bg-red-500/10',
    paid: 'bg-emerald-500/10', processing: 'bg-blue-500/10', failed: 'bg-red-500/10',
  }
  return map[s] || 'bg-gray-500/10'
}

function paymentIcon(s) {
  const map = { pending: '⏳', overdue: '⚠️', paid: '✅', processing: '🔄', failed: '❌' }
  return map[s] || '💳'
}

function paymentStatusClass(s) {
  const map = {
    pending: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    overdue: 'bg-red-500/15 text-red-600 dark:text-red-400',
    paid: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    processing: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    failed: 'bg-red-500/15 text-red-600 dark:text-red-400',
  }
  return map[s] || map.pending
}

function paymentStatusLabel(s) {
  const map = { pending: 'Pendiente', overdue: 'Vencido', paid: 'Pagado', processing: 'Procesando', failed: 'Fallido' }
  return map[s] || s
}

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('es-CO', { maximumFractionDigits: 0 })
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function handleOpenPayment(payment) {
  const result = await payStore.fetchWidgetData(projectId.value, payment.id)
  if (!result.success) return

  const d = result.data
  if (typeof window !== 'undefined' && window.WidgetCheckout) {
    const checkout = new window.WidgetCheckout({
      currency: d.currency,
      amountInCents: d.amount_in_cents,
      reference: d.reference,
      publicKey: d.public_key,
      redirectUrl: d.redirect_url,
      'signature:integrity': d.integrity_signature,
      customerData: {
        email: d.customer_email,
        fullName: d.customer_full_name,
      },
    })
    checkout.open((result) => {
      const txn = result.transaction
      if (txn && txn.status === 'APPROVED') {
        payStore.fetchProjectSubscription(projectId.value)
      }
    })
  }
}

onMounted(async () => {
  await Promise.all([
    payStore.fetchProjectSubscription(projectId.value),
    projectsStore.currentProject?.id !== Number(projectId.value) ? projectsStore.fetchProject(projectId.value) : Promise.resolve(),
  ])
})
</script>
