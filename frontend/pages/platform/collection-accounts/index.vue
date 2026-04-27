<template>
  <div id="platform-collection-accounts" class="space-y-6">
    <div data-enter>
      <h1 class="text-2xl font-bold text-text-default">
        {{ authStore.isAdmin ? 'Collection accounts' : 'My collection accounts' }}
      </h1>
      <p class="mt-1 text-sm text-green-light">
        {{ authStore.isAdmin ? 'Filter by project or status. Drafts are visible to admins only.' : 'Documents issued to your company.' }}
      </p>
    </div>

    <div v-if="authStore.isAdmin" class="flex flex-wrap gap-3 rounded-2xl border border-border-default bg-surface p-4" data-enter>
      <input
        v-model.number="filters.project_id"
        type="number"
        placeholder="Project ID"
        class="rounded-xl border border-border-default bg-surface px-3 py-2 text-sm dark:bg-primary-strong dark:text-white"
      />
      <select
        v-model="filters.commercial_status"
        class="rounded-xl border border-border-default bg-surface px-3 py-2 text-sm dark:bg-primary-strong dark:text-white"
      >
        <option value="">All statuses</option>
        <option value="draft">draft</option>
        <option value="issued">issued</option>
        <option value="paid">paid</option>
        <option value="cancelled">cancelled</option>
      </select>
      <button
        type="button"
        class="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white dark:bg-accent dark:text-text-default"
        @click="applyFilters"
      >
        Apply filters
      </button>
      <button
        type="button"
        class="rounded-xl border border-border-default px-4 py-2 text-sm text-text-brand"
        @click="showCreate = true"
      >
        New collection account
      </button>
    </div>

    <div v-if="store.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-esmerald dark:border-t-lemon" />
    </div>

    <div v-else-if="store.accounts.length === 0" class="rounded-2xl border border-dashed border-border-default py-16 text-center text-sm text-green-light">
      No collection accounts yet.
    </div>

    <div v-else class="overflow-x-auto rounded-2xl border border-border-default bg-surface">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-border-default text-xs uppercase text-green-light">
            <th class="px-4 py-3">Number</th>
            <th class="px-4 py-3">Title</th>
            <th class="px-4 py-3">Status</th>
            <th class="px-4 py-3">Total</th>
            <th class="px-4 py-3">Due</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in store.accounts"
            :key="row.id"
            class="border-b border-border-muted last:border-0"
          >
            <td class="px-4 py-3 font-mono text-xs text-green-light">{{ row.public_number || '—' }}</td>
            <td class="px-4 py-3 font-medium text-text-default">{{ row.title }}</td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-0.5 text-xs" :class="statusClass(row)">{{ row.commercial_status }}</span>
              <span v-if="row.is_overdue" class="ml-1 text-xs text-amber-500">overdue</span>
            </td>
            <td class="px-4 py-3">{{ row.currency }} {{ formatMoney(row.total) }}</td>
            <td class="px-4 py-3 text-green-light">{{ row.due_date || '—' }}</td>
            <td class="px-4 py-3 text-right">
              <NuxtLink
                :to="localePath(`/platform/collection-accounts/${row.id}`)"
                class="text-sm font-medium text-text-brand"
              >
                Open
              </NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal (admin) -->
    <div
      v-if="showCreate && authStore.isAdmin"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      @click.self="showCreate = false"
    >
      <div class="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-surface p-6 dark:bg-primary-strong">
        <h2 class="text-lg font-semibold text-text-default">New collection account</h2>
        <form class="mt-4 space-y-3" @submit.prevent="submitCreate">
          <div>
            <label class="block text-xs text-green-light">Title</label>
            <input v-model="createForm.title" required class="mt-1 w-full rounded-xl border border-border-default px-3 py-2 text-sm dark:text-white" />
          </div>
          <div>
            <label class="block text-xs text-green-light">Project ID</label>
            <input v-model.number="createForm.project_id" type="number" class="mt-1 w-full rounded-xl border border-border-default px-3 py-2 text-sm dark:text-white" />
          </div>
          <div>
            <label class="block text-xs text-green-light">Client user ID (optional if project set)</label>
            <input v-model.number="createForm.client_user_id" type="number" class="mt-1 w-full rounded-xl border border-border-default px-3 py-2 text-sm dark:text-white" />
          </div>
          <div>
            <label class="block text-xs text-green-light">Payment term days</label>
            <input v-model.number="createForm.payment_term_days" type="number" min="0" class="mt-1 w-full rounded-xl border border-border-default px-3 py-2 text-sm dark:text-white" />
          </div>
          <p v-if="createError" class="text-sm text-red-500">{{ createError }}</p>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="flex-1 rounded-xl bg-primary py-2 text-sm font-medium text-white dark:bg-accent dark:text-text-default" :disabled="store.isUpdating">
              Create
            </button>
            <button type="button" class="rounded-xl border px-4 py-2 text-sm" @click="showCreate = false">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformCollectionAccountsStore } from '~/stores/platform-collection-accounts'

const localePath = useLocalePath()

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

const authStore = usePlatformAuthStore()
const store = usePlatformCollectionAccountsStore()

const filters = reactive({
  project_id: null,
  commercial_status: '',
})

const showCreate = ref(false)
const createError = ref('')
const createForm = reactive({
  title: '',
  project_id: null,
  client_user_id: null,
  payment_term_days: 30,
})

function formatMoney(v) {
  if (v == null) return '0'
  return Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function statusClass(row) {
  const s = row.commercial_status
  if (s === 'paid') return 'bg-emerald-500/15 text-text-brand'
  if (s === 'issued') return 'bg-blue-500/15 text-blue-500'
  if (s === 'cancelled') return 'bg-gray-500/15 text-text-muted'
  return 'bg-amber-500/15 text-amber-600'
}

async function load() {
  const params = {}
  if (authStore.isAdmin) {
    if (filters.project_id) params.project_id = filters.project_id
    if (filters.commercial_status) params.commercial_status = filters.commercial_status
  }
  await store.fetchList(params)
}

function applyFilters() {
  load()
}

async function submitCreate() {
  createError.value = ''
  const payload = {
    title: createForm.title.trim(),
    payment_term_type: 'days_after_issue',
    payment_term_days: createForm.payment_term_days || 0,
  }
  if (createForm.project_id) payload.project_id = createForm.project_id
  if (createForm.client_user_id) payload.client_user_id = createForm.client_user_id
  const res = await store.create(payload)
  if (res.success && res.data?.id) {
    showCreate.value = false
    await navigateTo(localePath(`/platform/collection-accounts/${res.data.id}`))
  } else {
    createError.value =
      typeof res.errors === 'object'
        ? JSON.stringify(res.errors)
        : store.error || 'Create failed'
  }
}

onMounted(() => {
  load()
})
</script>
