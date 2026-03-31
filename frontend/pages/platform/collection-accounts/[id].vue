<template>
  <div id="platform-collection-account-detail" class="space-y-6">
    <NuxtLink :to="localePath('/platform/collection-accounts')" class="text-sm text-green-light hover:text-esmerald dark:hover:text-white">
      ← Back to list
    </NuxtLink>

    <div v-if="store.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald" />
    </div>

    <div v-else-if="!doc" class="text-sm text-green-light">Not found.</div>

    <template v-else>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-esmerald dark:text-white">{{ doc.title }}</h1>
          <p class="mt-1 font-mono text-sm text-green-light">{{ doc.public_number || 'Draft (no number yet)' }}</p>
          <p class="mt-2 text-sm">
            <span class="rounded-full px-2 py-0.5 text-xs" :class="statusClass">{{ doc.commercial_status }}</span>
            <span v-if="doc.is_overdue" class="ml-2 text-amber-500">Overdue</span>
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-xl border border-esmerald/20 px-4 py-2 text-sm dark:border-white/20"
            @click="download"
          >
            Download PDF
          </button>
          <template v-if="authStore.isAdmin">
            <button
              v-if="doc.commercial_status === 'draft'"
              type="button"
              class="rounded-xl bg-esmerald px-4 py-2 text-sm font-medium text-white dark:bg-lemon dark:text-esmerald-dark"
              :disabled="store.isUpdating"
              @click="doIssue"
            >
              Issue
            </button>
            <button
              v-if="doc.commercial_status === 'issued'"
              type="button"
              class="rounded-xl bg-emerald-600 px-4 py-2 text-sm text-white"
              :disabled="store.isUpdating"
              @click="doPaid"
            >
              Mark paid
            </button>
            <button
              v-if="doc.commercial_status === 'draft' || doc.commercial_status === 'issued'"
              type="button"
              class="rounded-xl border border-red-500/40 px-4 py-2 text-sm text-red-500"
              :disabled="store.isUpdating"
              @click="doCancel"
            >
              Cancel
            </button>
          </template>
        </div>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-green-light">Amounts</h2>
          <p class="mt-2 text-sm text-green-light">Subtotal {{ doc.currency }} {{ doc.subtotal }}</p>
          <p class="text-sm text-green-light">Tax {{ doc.tax_total }}</p>
          <p class="mt-2 text-lg font-bold text-esmerald dark:text-lemon">Total {{ doc.currency }} {{ doc.total }}</p>
        </div>
        <div v-if="doc.collection_account" class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-green-light">Billing</h2>
          <p class="mt-2 text-sm text-esmerald dark:text-white">{{ doc.collection_account.billing_concept || '—' }}</p>
          <p class="mt-1 text-xs text-green-light">{{ doc.collection_account.support_reference }}</p>
        </div>
      </div>

      <div v-if="doc.items?.length" class="rounded-2xl border border-esmerald/[0.06] bg-white dark:border-white/[0.06] dark:bg-esmerald">
        <h2 class="border-b border-esmerald/[0.06] px-5 py-3 text-xs font-semibold uppercase text-green-light dark:border-white/[0.06]">Line items</h2>
        <table class="w-full text-sm">
          <tbody>
            <tr v-for="it in doc.items" :key="it.id" class="border-b border-esmerald/[0.04] dark:border-white/[0.04]">
              <td class="px-5 py-2 text-esmerald dark:text-white">{{ it.description }}</td>
              <td class="px-5 py-2 text-right text-green-light">{{ it.quantity }} × {{ it.unit_price }}</td>
              <td class="px-5 py-2 text-right font-medium">{{ it.line_total }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="authStore.isAdmin && doc.commercial_status === 'draft'" class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
        <h2 class="text-sm font-semibold text-esmerald dark:text-white">Add line items (replaces all)</h2>
        <p class="mt-1 text-xs text-green-light">Submit JSON-like rows: description, unit_price, quantity, line_total optional.</p>
        <textarea
          v-model="itemsJson"
          rows="6"
          class="mt-3 w-full rounded-xl border border-esmerald/10 p-3 font-mono text-xs dark:border-white/10 dark:bg-esmerald-dark dark:text-white"
          placeholder='[{"description":"Service","quantity":1,"unit_price":"100000","discount_amount":"0","tax_amount":"0","line_total":"100000"}]'
        />
        <button
          type="button"
          class="mt-3 rounded-xl bg-esmerald px-4 py-2 text-sm text-white dark:bg-lemon dark:text-esmerald-dark"
          :disabled="store.isUpdating"
          @click="saveItems"
        >
          Save items
        </button>
        <p v-if="itemsError" class="mt-2 text-sm text-red-500">{{ itemsError }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformCollectionAccountsStore } from '~/stores/platform-collection-accounts'

const route = useRoute()
const localePath = useLocalePath()

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

const authStore = usePlatformAuthStore()
const store = usePlatformCollectionAccountsStore()

const itemsJson = ref('[]')
const itemsError = ref('')

const doc = computed(() => store.currentAccount)

const statusClass = computed(() => {
  const s = doc.value?.commercial_status
  if (s === 'paid') return 'bg-emerald-500/15 text-emerald-600'
  if (s === 'issued') return 'bg-blue-500/15 text-blue-500'
  if (s === 'cancelled') return 'bg-gray-500/15 text-gray-500'
  return 'bg-amber-500/15 text-amber-600'
})

async function load() {
  const id = route.params.id
  await store.fetchDetail(id)
}

async function download() {
  if (!doc.value) return
  const name = doc.value.public_number || doc.value.title || 'collection-account'
  await store.downloadPdf(doc.value.id, name)
}

async function doIssue() {
  if (!doc.value) return
  await store.issue(doc.value.id)
}

async function doPaid() {
  if (!doc.value) return
  await store.markPaid(doc.value.id)
}

async function doCancel() {
  if (!doc.value) return
  await store.markCancelled(doc.value.id)
}

async function saveItems() {
  itemsError.value = ''
  if (!doc.value) return
  let items
  try {
    items = JSON.parse(itemsJson.value)
  } catch {
    itemsError.value = 'Invalid JSON'
    return
  }
  if (!Array.isArray(items)) {
    itemsError.value = 'Expected array'
    return
  }
  const res = await store.update(doc.value.id, { items })
  if (!res.success) {
    itemsError.value = typeof res.errors === 'object' ? JSON.stringify(res.errors) : 'Update failed'
  } else {
    itemsJson.value = '[]'
  }
}

onMounted(() => {
  load()
})
</script>
