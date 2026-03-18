<template>
  <div id="platform-client-detail" class="space-y-6">
    <div data-enter>
      <NuxtLink to="/platform/clients" class="inline-flex items-center text-sm font-medium text-green-light transition hover:text-esmerald dark:hover:text-white">
        ← Volver a clientes
      </NuxtLink>
      <h1 class="mt-3 font-light text-3xl text-esmerald dark:text-white">Detalle del cliente</h1>
    </div>

    <div v-if="pageMessage" class="rounded-2xl border px-4 py-3 text-sm" :class="pageMessageVariant === 'success' ? 'border-emerald-500/20 bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300' : 'border-red-500/20 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-200'">
      {{ pageMessage }}
    </div>

    <div v-if="platformClientsStore.isLoading" class="rounded-3xl border border-esmerald/[0.06] bg-white px-6 py-14 text-center text-sm text-green-light shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none" data-enter>
      Cargando cliente...
    </div>

    <div v-else-if="!platformClientsStore.currentClient" class="rounded-3xl border border-esmerald/[0.06] bg-white px-6 py-14 text-center text-sm text-green-light shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none" data-enter>
      No encontramos el cliente solicitado.
    </div>

    <div v-else class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <section class="space-y-6" data-enter>
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <div class="flex items-center gap-4">
            <div class="flex h-14 w-14 items-center justify-center rounded-full bg-esmerald text-base font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
              {{ clientInitials }}
            </div>
            <div>
              <h2 class="text-lg font-medium text-esmerald dark:text-white">{{ form.first_name }} {{ form.last_name }}</h2>
              <p class="mt-0.5 text-sm text-green-light">{{ platformClientsStore.currentClient.email }}</p>
            </div>
          </div>

          <dl class="mt-6 grid gap-3">
            <div class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
              <dt class="text-xs uppercase tracking-[0.16em] text-green-light/60">Empresa</dt>
              <dd class="mt-2 text-sm font-medium text-esmerald dark:text-white">{{ form.company_name || '—' }}</dd>
            </div>
            <div class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
              <dt class="text-xs uppercase tracking-[0.16em] text-green-light/60">Teléfono</dt>
              <dd class="mt-2 text-sm font-medium text-esmerald dark:text-white">{{ form.phone || '—' }}</dd>
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <div class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
                <dt class="text-xs uppercase tracking-[0.16em] text-green-light/60">Estado</dt>
                <dd class="mt-2">
                  <span class="inline-flex rounded-full px-3 py-1 text-xs font-medium" :class="statusClass(platformClientsStore.currentClient)">
                    {{ statusLabel(platformClientsStore.currentClient) }}
                  </span>
                </dd>
              </div>
              <div class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
                <dt class="text-xs uppercase tracking-[0.16em] text-green-light/60">Creado</dt>
                <dd class="mt-2 text-sm font-medium text-esmerald dark:text-white">{{ formatDate(platformClientsStore.currentClient.created_at) }}</dd>
              </div>
            </div>
          </dl>
        </article>

        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Acciones rápidas</h2>
          <div class="mt-5 flex flex-col gap-3">
            <button
              type="button"
              class="rounded-full border border-esmerald/10 px-4 py-3 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white disabled:opacity-50"
              :disabled="platformClientsStore.isUpdating"
              @click="handleResendInvite"
            >
              Reenviar invitación
            </button>

            <button
              v-if="platformClientsStore.currentClient.is_active"
              type="button"
              class="rounded-full border border-red-500/20 px-4 py-3 text-sm text-red-500 transition hover:bg-red-500/10 dark:text-red-300 disabled:opacity-50"
              :disabled="platformClientsStore.isUpdating"
              @click="requestDeactivate"
            >
              Desactivar acceso
            </button>

            <button
              v-else
              type="button"
              class="rounded-full border border-emerald-500/20 px-4 py-3 text-sm text-emerald-600 transition hover:bg-emerald-500/10 dark:text-emerald-400 disabled:opacity-50"
              :disabled="platformClientsStore.isUpdating"
              @click="handleReactivate"
            >
              Reactivar acceso
            </button>
          </div>
        </article>
      </section>

      <section data-enter>
        <article class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
          <h2 class="text-base font-medium text-esmerald dark:text-white">Editar cliente</h2>
          <p class="mt-2 text-sm leading-6 text-green-light">
            Ajusta la información visible para el equipo y el cliente dentro del portal.
          </p>

          <form class="mt-6 grid gap-5 sm:grid-cols-2" @submit.prevent="handleSave">
            <div>
              <label for="client-first-name" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Nombre</label>
              <input id="client-first-name" v-model="form.first_name" type="text" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 dark:focus:border-lemon/40 dark:focus:ring-lemon/20">
            </div>

            <div>
              <label for="client-last-name" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Apellido</label>
              <input id="client-last-name" v-model="form.last_name" type="text" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 dark:focus:border-lemon/40 dark:focus:ring-lemon/20">
            </div>

            <div class="sm:col-span-2">
              <label for="client-email" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Email</label>
              <input id="client-email" :value="platformClientsStore.currentClient.email" type="email" disabled class="w-full rounded-xl border border-esmerald/[0.06] bg-esmerald-light/20 px-4 py-3 text-sm text-green-light outline-none dark:border-white/[0.06] dark:bg-white/[0.03]">
            </div>

            <div>
              <label for="client-company" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Empresa</label>
              <input id="client-company" v-model="form.company_name" type="text" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 dark:focus:border-lemon/40 dark:focus:ring-lemon/20">
            </div>

            <div>
              <label for="client-phone" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Teléfono</label>
              <input id="client-phone" v-model="form.phone" type="text" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 dark:focus:border-lemon/40 dark:focus:ring-lemon/20">
            </div>

            <label class="sm:col-span-2 flex items-center justify-between rounded-xl border border-esmerald/[0.06] px-4 py-4 dark:border-white/[0.06]">
              <div>
                <p class="text-sm font-medium text-esmerald dark:text-white">Cuenta activa</p>
                <p class="mt-1 text-xs text-green-light">Desactiva esta opción si necesitas pausar el acceso del cliente.</p>
              </div>
              <input v-model="form.is_active" type="checkbox" class="h-5 w-5 rounded border-esmerald/10 bg-esmerald-light/40 text-esmerald focus:ring-esmerald/30 dark:border-white/10 dark:bg-esmerald-dark dark:text-lemon dark:focus:ring-lemon/30">
            </label>

            <div class="flex flex-col gap-3 sm:col-span-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                class="rounded-full border border-esmerald/10 px-4 py-3 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
                @click="syncFormFromClient"
              >
                Restablecer
              </button>
              <button
                type="submit"
                class="rounded-full bg-esmerald px-5 py-3 text-sm font-semibold text-white transition hover:bg-esmerald/90 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-lemon dark:text-esmerald-dark dark:hover:bg-lemon/90"
                :disabled="platformClientsStore.isUpdating"
              >
                {{ platformClientsStore.isUpdating ? 'Guardando...' : 'Guardar cambios' }}
              </button>
            </div>
          </form>
        </article>
      </section>
    </div>

    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ConfirmModal from '~/components/ConfirmModal.vue'
import { useConfirmModal } from '~/composables/useConfirmModal'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformClientsStore } from '~/stores/platform-clients'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
  platformRole: 'admin',
})

defineI18nRoute(false)

useHead({
  title: 'Detalle de cliente — ProjectApp',
})

usePageEntrance('#platform-client-detail')

const route = useRoute()
const platformClientsStore = usePlatformClientsStore()
const pageMessage = ref('')
const pageMessageVariant = ref('success')
const form = reactive({
  first_name: '',
  last_name: '',
  company_name: '',
  phone: '',
  is_active: true,
})

const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal()

const clientId = computed(() => Number(route.params.id))
const clientInitials = computed(() => `${form.first_name || ''} ${form.last_name || ''}`
  .trim()
  .split(/\s+/)
  .slice(0, 2)
  .map((part) => part[0]?.toUpperCase() || '')
  .join('') || 'PA')

function statusLabel(client) {
  if (!client?.is_active) return 'Inactivo'
  if (!client?.is_onboarded) return 'Pendiente'
  return 'Activo'
}

function statusClass(client) {
  if (!client?.is_active) return 'bg-white/10 text-green-light/60'
  if (!client?.is_onboarded) return 'bg-amber-100 text-amber-700 dark:bg-lemon/10 dark:text-lemon'
  return 'bg-emerald-500/15 text-emerald-400'
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function syncFormFromClient() {
  const client = platformClientsStore.currentClient
  if (!client) return

  form.first_name = client.first_name || ''
  form.last_name = client.last_name || ''
  form.company_name = client.company_name || ''
  form.phone = client.phone || ''
  form.is_active = Boolean(client.is_active)
}

async function loadClient() {
  pageMessage.value = ''
  const result = await platformClientsStore.fetchClient(clientId.value)
  if (result.success) {
    syncFormFromClient()
  }
}

async function handleSave() {
  pageMessage.value = ''

  if (!form.first_name.trim() || !form.last_name.trim()) {
    pageMessageVariant.value = 'error'
    pageMessage.value = 'Completa nombre y apellido del cliente.'
    return
  }

  const result = await platformClientsStore.updateClient(clientId.value, {
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim(),
    company_name: form.company_name.trim(),
    phone: form.phone.trim(),
    is_active: form.is_active,
  })

  pageMessageVariant.value = result.success ? 'success' : 'error'
  pageMessage.value = result.success
    ? 'Cliente actualizado correctamente.'
    : result.message

  if (result.success) {
    syncFormFromClient()
  }
}

async function handleResendInvite() {
  pageMessage.value = ''
  const result = await platformClientsStore.resendInvite(clientId.value)
  pageMessageVariant.value = result.success ? 'success' : 'error'
  pageMessage.value = result.success ? result.message : result.message
  await loadClient()
}

async function handleReactivate() {
  pageMessage.value = ''
  const result = await platformClientsStore.updateClient(clientId.value, { is_active: true })
  pageMessageVariant.value = result.success ? 'success' : 'error'
  pageMessage.value = result.success
    ? 'Cliente reactivado correctamente.'
    : result.message

  await loadClient()
}

function requestDeactivate() {
  requestConfirm({
    title: 'Desactivar acceso',
    message: 'El cliente dejará de poder entrar al portal hasta que se reactive su cuenta.',
    confirmText: 'Desactivar',
    variant: 'danger',
    onConfirm: async () => {
      const result = await platformClientsStore.deactivateClient(clientId.value)
      pageMessageVariant.value = result.success ? 'success' : 'error'
      pageMessage.value = result.success
        ? 'Cliente desactivado correctamente.'
        : result.message

      await loadClient()
    },
  })
}

watch(() => route.params.id, async () => {
  await loadClient()
})

onMounted(async () => {
  await loadClient()
})
</script>
