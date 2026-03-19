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
        <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">Suscripción</h1>
      </div>

      <!-- No subscription -->
      <div v-if="!sub" class="rounded-3xl border border-dashed border-esmerald/10 py-16 text-center dark:border-white/10" data-enter>
        <p class="text-sm text-green-light">Este proyecto no tiene suscripción de hosting.</p>
      </div>

      <template v-else>
        <!-- Subscription summary card -->
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

        <!-- Current billing period -->
        <div class="mb-6" data-enter>
          <!-- Up to date — no action needed -->
          <div v-if="payStore.subscriptionUpToDate" class="rounded-2xl border border-emerald-500/20 bg-emerald-50/50 p-6 dark:border-emerald-500/15 dark:bg-emerald-900/10">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10">
                <svg class="h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </span>
              <div>
                <p class="text-sm font-semibold text-emerald-700 dark:text-emerald-400">Suscripción al día</p>
                <p class="text-xs text-emerald-600/70 dark:text-emerald-400/60">Tu suscripción se renueva automáticamente. Próximo cobro: {{ formatDate(sub.next_billing_date) }}</p>
              </div>
            </div>
          </div>

          <!-- Current period needs attention -->
          <div v-else-if="currentPayment" class="rounded-2xl border bg-white p-6 dark:bg-esmerald" :class="currentPeriodBorderClass">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div class="flex items-start gap-3">
                <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="paymentIconBg(currentPayment.status)">
                  <span class="text-base">{{ paymentIcon(currentPayment.status) }}</span>
                </span>
                <div>
                  <p class="text-sm font-semibold text-esmerald dark:text-white">Período actual</p>
                  <p class="mt-0.5 text-xs text-green-light">
                    {{ formatDate(currentPayment.billing_period_start) }} — {{ formatDate(currentPayment.billing_period_end) }}
                  </p>
                  <span class="mt-1.5 inline-block rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="paymentStatusClass(currentPayment.status)">
                    {{ paymentStatusLabel(currentPayment.status) }}
                  </span>
                  <p v-if="currentPayment.status === 'failed'" class="mt-1.5 text-xs text-red-500 dark:text-red-400">
                    El cobro automático falló. Puedes renovar manualmente.
                  </p>
                  <p v-else-if="currentPayment.status === 'overdue'" class="mt-1.5 text-xs text-red-500 dark:text-red-400">
                    Este cobro está vencido. Renueva para mantener tu servicio activo.
                  </p>
                  <p v-else-if="currentPayment.status === 'processing'" class="mt-1.5 text-xs text-blue-500 dark:text-blue-400">
                    Tu pago está siendo procesado.
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-4">
                <div class="text-right">
                  <p class="text-2xl font-bold text-esmerald dark:text-white">${{ formatMoney(currentPayment.amount) }}</p>
                </div>

                <div v-if="canPay(currentPayment)" class="shrink-0">
                  <button
                    type="button"
                    :disabled="payStore.isUpdating"
                    class="flex items-center gap-2 rounded-xl bg-lemon px-5 py-3 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50"
                    @click="openCheckout(currentPayment)"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                    {{ currentPayment.status === 'failed' || currentPayment.status === 'overdue' ? 'Renovar' : 'Pagar ahora' }}
                  </button>
                </div>
              </div>
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

        <!-- Payment history (collapsible) -->
        <div v-if="payStore.pastPayments.length > 0" data-enter>
          <button
            type="button"
            class="mb-3 flex w-full items-center gap-2 text-xs font-semibold uppercase tracking-wider text-green-light/60 transition hover:text-green-light"
            @click="showHistory = !showHistory"
          >
            <svg class="h-3.5 w-3.5 transition-transform" :class="showHistory ? 'rotate-90' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            Historial de pagos ({{ payStore.pastPayments.length }})
          </button>

          <transition name="slide">
            <div v-show="showHistory" class="space-y-2">
              <div
                v-for="payment in payStore.pastPayments"
                :key="payment.id"
                class="rounded-xl border border-esmerald/[0.04] bg-white px-5 py-3.5 dark:border-white/[0.04] dark:bg-esmerald"
              >
                <div class="flex items-center justify-between gap-4">
                  <div class="flex items-center gap-2.5">
                    <span class="flex h-7 w-7 items-center justify-center rounded-lg" :class="paymentIconBg(payment.status)">
                      <span class="text-xs">{{ paymentIcon(payment.status) }}</span>
                    </span>
                    <div>
                      <p class="text-xs font-medium text-esmerald dark:text-white">
                        {{ formatDate(payment.billing_period_start) }} — {{ formatDate(payment.billing_period_end) }}
                      </p>
                      <div v-if="payment.status === 'paid' && payment.paid_at" class="mt-0.5 text-[10px] text-emerald-600/70 dark:text-emerald-400/60">
                        Pagado el {{ formatDate(payment.paid_at) }}
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <p class="text-sm font-semibold text-esmerald dark:text-white">${{ formatMoney(payment.amount) }}</p>
                    <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="paymentStatusClass(payment.status)">
                      {{ paymentStatusLabel(payment.status) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </transition>
        </div>

        <div v-else-if="payStore.payments.length === 0" class="py-8 text-center text-sm text-green-light" data-enter>
          No hay pagos registrados aún.
        </div>
      </template>
    </template>

    <!-- Checkout modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div v-if="checkoutPayment" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="closeCheckout">
          <Transition name="modal-content" appear>
            <div v-if="checkoutPayment" class="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <!-- Header -->
              <div class="mb-5 flex items-center justify-between">
                <div>
                  <h2 class="text-lg font-bold text-esmerald dark:text-white">Pagar suscripción</h2>
                  <p class="mt-0.5 text-xs text-green-light">${{ formatMoney(checkoutPayment.amount) }} COP</p>
                </div>
                <button type="button" class="flex h-8 w-8 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white" @click="closeCheckout">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <!-- Payment method selector -->
              <div class="mb-5 grid grid-cols-4 gap-2">
                <button
                  v-for="m in paymentMethods" :key="m.key" type="button"
                  class="flex flex-col items-center gap-1.5 rounded-xl border p-3 transition"
                  :class="selectedMethod === m.key
                    ? 'border-esmerald bg-esmerald-light/40 dark:border-lemon dark:bg-lemon/10'
                    : 'border-esmerald/10 hover:border-esmerald/20 dark:border-white/10 dark:hover:border-white/20'"
                  @click="selectedMethod = m.key"
                >
                  <img :src="m.logo" :alt="m.label" class="h-8 w-8 rounded object-contain" :class="m.logoClass" />
                  <span class="text-[9px] font-medium text-esmerald dark:text-white">{{ m.label }}</span>
                </button>
              </div>

              <!-- Card form -->
              <form v-if="selectedMethod === 'card'" class="space-y-3" @submit.prevent="handleCardPay">
                <div>
                  <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Número de tarjeta</label>
                  <input :value="cardForm.card_number" type="text" inputmode="numeric" maxlength="19" placeholder="4242 4242 4242 4242" required autocomplete="cc-number" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 font-mono text-sm tracking-wider text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" @input="formatCardNumber" />
                </div>
                <div>
                  <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Titular de la tarjeta</label>
                  <input v-model="cardForm.card_holder" type="text" placeholder="Nombre como aparece en la tarjeta" required minlength="5" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div class="grid grid-cols-3 gap-3">
                  <div>
                    <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Mes</label>
                    <input v-model="cardForm.exp_month" type="text" inputmode="numeric" maxlength="2" placeholder="MM" required class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-3 text-center text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                  <div>
                    <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Año</label>
                    <input v-model="cardForm.exp_year" type="text" inputmode="numeric" maxlength="2" placeholder="AA" required class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-3 text-center text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                  <div>
                    <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">CVC</label>
                    <input v-model="cardForm.cvc" type="text" inputmode="numeric" maxlength="4" placeholder="123" required class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-3 text-center text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                </div>

                <div v-if="checkoutError" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400">
                  {{ checkoutError }}
                </div>

                <button type="submit" :disabled="payStore.isUpdating" class="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-lemon px-5 py-3.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                  <svg v-if="payStore.isUpdating" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                  <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                  {{ payStore.isUpdating ? 'Procesando...' : `Pagar $${formatMoney(checkoutPayment.amount)} COP` }}
                </button>

                <p class="text-center text-[10px] text-green-light/50">Pago a 1 cuota · Procesado de forma segura por Wompi</p>
              </form>

              <!-- PSE / Nequi / Bancolombia — uses Wompi widget -->
              <div v-else class="space-y-3">
                <div class="rounded-xl border border-esmerald/[0.06] bg-esmerald-light/20 p-4 text-center dark:border-white/[0.06] dark:bg-white/[0.02]">
                  <p class="text-sm font-medium text-esmerald dark:text-white">{{ selectedMethodLabel }}</p>
                  <p class="mt-1 text-xs text-green-light">Se abrirá la pasarela de pago segura para completar tu transacción.</p>
                </div>

                <button type="button" :disabled="payStore.isUpdating" class="flex w-full items-center justify-center gap-2 rounded-xl bg-lemon px-5 py-3.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50" @click="handleWidgetPay">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                  Continuar con {{ selectedMethodLabel }}
                </button>
              </div>

              <!-- Security footer -->
              <div class="mt-4 flex items-center justify-center gap-2">
                <svg class="h-3.5 w-3.5 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                <span class="text-[10px] text-green-light/40">Conexión segura · SSL 256-bit · ProjectApp</span>
              </div>
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
const currentPayment = computed(() => payStore.currentPeriodPayment)
const showHistory = ref(false)

const checkoutPayment = ref(null)
const selectedMethod = ref('card')
const checkoutError = ref('')
const cardForm = reactive({
  card_number: '', card_holder: '', exp_month: '', exp_year: '', cvc: '',
})

const paymentMethods = [
  { key: 'card', label: 'Tarjeta', logo: '/images/payments/card.svg', logoClass: 'dark:invert dark:opacity-70' },
  { key: 'pse', label: 'PSE', logo: '/images/payments/pse-seeklogo.png', logoClass: '' },
  { key: 'nequi', label: 'Nequi', logo: '/images/payments/Nequi.jpeg', logoClass: '' },
  { key: 'bancolombia', label: 'Bancolombia', logo: '/images/payments/Bancolombia.png', logoClass: 'rounded-full' },
]

const selectedMethodLabel = computed(() => {
  const m = paymentMethods.find((pm) => pm.key === selectedMethod.value)
  return m?.label || ''
})

const currentPeriodBorderClass = computed(() => {
  if (!currentPayment.value) return 'border-esmerald/[0.06] dark:border-white/[0.06]'
  return paymentBorderClass(currentPayment.value.status)
})

function canPay(payment) {
  return ['pending', 'overdue', 'failed'].includes(payment.status)
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
  return Number(val).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).replace(/,/g, '.')
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCardNumber(event) {
  const raw = event.target.value.replace(/\D/g, '').slice(0, 16)
  const formatted = raw.replace(/(.{4})/g, '$1 ').trim()
  cardForm.card_number = formatted
  event.target.value = formatted
}

function openCheckout(payment) {
  checkoutPayment.value = payment
  selectedMethod.value = 'card'
  checkoutError.value = ''
  cardForm.card_number = ''
  cardForm.card_holder = ''
  cardForm.exp_month = ''
  cardForm.exp_year = ''
  cardForm.cvc = ''
}

function closeCheckout() {
  checkoutPayment.value = null
  checkoutError.value = ''
}

async function handleCardPay() {
  if (!checkoutPayment.value) return
  checkoutError.value = ''

  const result = await payStore.payWithCard(projectId.value, checkoutPayment.value.id, {
    card_number: cardForm.card_number.replace(/\s/g, ''),
    exp_month: cardForm.exp_month,
    exp_year: cardForm.exp_year,
    cvc: cardForm.cvc,
    card_holder: cardForm.card_holder,
  })

  if (!result.success) {
    checkoutError.value = result.message
    return
  }

  if (result.data.transaction_status === 'APPROVED' || result.data.transaction_status === 'PENDING') {
    closeCheckout()
    await payStore.fetchProjectSubscription(projectId.value)
  } else {
    checkoutError.value = `Transacción ${result.data.transaction_status}. Intenta con otro método de pago.`
  }
}

async function handleWidgetPay() {
  if (!checkoutPayment.value) return

  const result = await payStore.fetchWidgetData(projectId.value, checkoutPayment.value.id)
  if (!result.success) return

  const d = result.data
  if (typeof window === 'undefined' || !window.WidgetCheckout) return

  const widgetConfig = {
    currency: d.currency,
    amountInCents: d.amount_in_cents,
    reference: d.reference,
    publicKey: d.public_key,
    'signature:integrity': d.integrity_signature,
    customerData: { email: d.customer_email, fullName: d.customer_full_name },
  }
  if (d.redirect_url) widgetConfig.redirectUrl = d.redirect_url

  const paymentId = checkoutPayment.value.id
  closeCheckout()

  const checkout = new window.WidgetCheckout(widgetConfig)
  checkout.open(async (widgetResult) => {
    const txn = widgetResult.transaction
    if (txn && txn.id) {
      await payStore.verifyTransaction(projectId.value, paymentId, txn.id)
    }
    await payStore.fetchProjectSubscription(projectId.value)
  })
}

onMounted(async () => {
  await Promise.all([
    payStore.fetchProjectSubscription(projectId.value),
    projectsStore.currentProject?.id !== Number(projectId.value) ? projectsStore.fetchProject(projectId.value) : Promise.resolve(),
  ])
})
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 1000px;
}
</style>
