<script setup>
import { computed, ref, watch } from 'vue'
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue'
import ClientFormFields from '~/components/clients/ClientFormFields.vue'
import { clientFormPayload, emptyClientForm } from '~/utils/billingCode'
import { useProposalClientsStore } from '~/stores/proposal_clients'
import { normalizeName } from '~/utils/clientMatch'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
  /** { profile_id|id, name } — pre-selects the client (orphans panel CTA). */
  seedClient: { type: Object, default: null },
  /** Loaded module rows; the duplicate warning scans the same client's. */
  existingProjects: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'submit', 'change-client'])

const clientsStore = useProposalClientsStore()
const creatingClient = ref(false)
const inlineClientOpen = ref(false)
const inlineClient = ref(emptyClientForm())

const isEdit = computed(() => !!props.record)
const title = computed(() => (isEdit.value ? 'Editar proyecto' : 'Nuevo proyecto'))

const STATUS_OPTIONS = [
  { value: 'active', label: 'Activo' },
  { value: 'paused', label: 'Pausado' },
  { value: 'completed', label: 'Completado' },
]

function defaultForm() {
  return {
    name: '',
    client_profile_id: null,
    client_display_name: '',
    description: '',
    status: 'active',
  }
}

const form = ref(defaultForm())

watch(
  () => [props.open, props.record],
  () => {
    if (!props.open) return
    if (props.record) {
      form.value = {
        name: props.record.name ?? '',
        client_profile_id: props.record.client?.profile_id ?? null,
        client_display_name: props.record.client?.name ?? '',
        description: props.record.description ?? '',
        status: props.record.status ?? 'active',
      }
    } else {
      form.value = defaultForm()
      if (props.seedClient) {
        form.value.client_profile_id = props.seedClient.profile_id
          ?? props.seedClient.id ?? null
        form.value.client_display_name = props.seedClient.name ?? ''
      }
    }
    inlineClientOpen.value = false
  },
  { immediate: true },
)

/**
 * Same-name project for the same client: a signal, not an error — the
 * backend accepts it and the strip never blocks saving. Accent/case-blind
 * comparison so "Vástago" and "vastago" read as the same name.
 */
const duplicate = computed(() => {
  const term = normalizeName(form.value.name)
  if (!term || !form.value.client_profile_id) return null
  return props.existingProjects.find((project) => (
    project.client?.profile_id === form.value.client_profile_id
    && project.id !== props.record?.id
    && normalizeName(project.name) === term
  )) || null
})

const canSubmit = computed(() => Boolean(
  form.value.name.trim() && (isEdit.value || form.value.client_profile_id),
))

const submitBlockReasons = computed(() => [
  !form.value.name.trim() ? 'Escribe el nombre del proyecto.' : '',
  !isEdit.value && !form.value.client_profile_id ? 'Elige o crea el cliente del proyecto.' : '',
].filter(Boolean))

function onClientSelect(client) {
  if (!client) {
    form.value.client_profile_id = null
    form.value.client_display_name = ''
    return
  }
  form.value.client_profile_id = client.id
  form.value.client_display_name = client.name || ''
}

function onCreateNewClient(typedName) {
  inlineClientOpen.value = true
  inlineClient.value = { ...emptyClientForm(), name: typedName || '' }
}

async function createInlineClient() {
  creatingClient.value = true
  const result = await clientsStore.createClient(clientFormPayload(inlineClient.value))
  creatingClient.value = false
  if (result.success && result.data?.id) {
    inlineClientOpen.value = false
    onClientSelect(result.data)
  }
}

function onSubmit() {
  if (!canSubmit.value) return
  const payload = {
    name: form.value.name.trim(),
    description: form.value.description,
    status: form.value.status,
  }
  // The client travels only on create: the panel keeps it immutable and the
  // backend answers 400 if the key even appears on an update.
  if (!isEdit.value) payload.client_profile_id = form.value.client_profile_id
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" kind="form" title-id="project-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="project-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <BaseFormField label="Nombre del proyecto" required>
        <BaseInput
          v-model="form.name"
          data-testid="project-form-name"
          placeholder="Kore, Vástago, Crushme..."
          required
        />
        <!-- Duplicate signal: warn, never block -->
        <div
          v-if="duplicate"
          class="mt-2 flex flex-wrap items-center gap-2 text-xs rounded-lg border border-border-default bg-surface-raised px-3 py-2"
          data-testid="project-form-duplicate-warning"
        >
          <span class="text-text-muted">
            Este cliente ya tiene un proyecto llamado
            <span class="font-medium text-text-default">{{ duplicate.name }}</span>.
            Puedes guardarlo igual si es otro proyecto.
          </span>
        </div>
      </BaseFormField>

      <BaseFormField
        v-if="!isEdit"
        label="Cliente"
        required
        hint="Todo proyecto pertenece a un cliente: es a quien se le cobra."
      >
        <ClientAutocomplete
          v-model="form.client_profile_id"
          :initial-label="form.client_display_name"
          test-id="project-form-client"
          @select="onClientSelect"
          @create-new="onCreateNewClient"
        />
      </BaseFormField>
      <BaseFormField
        v-else
        label="Cliente"
        hint="Cambiarlo es una operación guiada: muestra el impacto sobre hostings, ingresos y cuentas antes de aplicar."
      >
        <div class="flex items-center justify-between gap-2 py-1.5">
          <p class="text-sm text-text-default" data-testid="project-form-client-readonly">
            {{ form.client_display_name || '—' }}
          </p>
          <BaseButton
            type="button"
            variant="ghost"
            size="sm"
            data-testid="project-form-change-client"
            @click="emit('change-client')"
          >
            Cambiar cliente…
          </BaseButton>
        </div>
      </BaseFormField>

      <!-- Inline client creation: same escape hatch as hostings and incomes -->
      <div
        v-if="inlineClientOpen"
        class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-3"
        data-testid="project-form-inline-client"
      >
        <p class="text-sm font-medium text-text-default">Crear cliente nuevo</p>
        <ClientFormFields
          v-model="inlineClient"
          testid-prefix="project-form-inline-client"
          dense
        />
        <div class="flex justify-end gap-2">
          <BaseButton type="button" variant="secondary" size="sm" @click="inlineClientOpen = false">
            Cancelar
          </BaseButton>
          <BaseButton
            type="button"
            variant="primary"
            size="sm"
            :loading="creatingClient"
            data-testid="project-form-inline-client-save"
            @click="createInlineClient"
          >
            {{ creatingClient ? 'Creando...' : 'Crear cliente' }}
          </BaseButton>
        </div>
      </div>

      <!-- PA-38: everything below is optional and can be completed later -->
      <BaseFormRow :cols="2" :gap="4">
        <BaseFormField label="Estado (opcional)">
          <BaseSelect
            v-model="form.status"
            :options="STATUS_OPTIONS"
            data-testid="project-form-status"
          />
        </BaseFormField>
      </BaseFormRow>

      <BaseFormField label="Descripción (opcional)">
        <BaseTextarea
          v-model="form.description"
          :rows="3"
          data-testid="project-form-description"
          placeholder="Qué se entrega, alcance, contexto..."
        />
      </BaseFormField>

      <div class="sticky bottom-0 -mx-6 flex items-center justify-end gap-3 border-t border-border-muted bg-surface px-6 pb-2 pt-4">
        <BaseButton type="button" variant="secondary" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseControlGate
          :reasons="submitBlockReasons"
          label="Guardar proyecto no disponible"
          align="end"
        >
          <template #default="{ describedBy }">
            <BaseButton
              type="submit"
              variant="primary"
              :loading="saving"
              :disabled="Boolean(submitBlockReasons.length)"
              :disabled-reason="submitBlockReasons.join(' ')"
              :aria-describedby="describedBy"
              data-testid="project-form-submit"
            >
              {{ saving ? 'Guardando...' : 'Guardar' }}
            </BaseButton>
          </template>
        </BaseControlGate>
      </div>
    </form>
  </BaseModal>
</template>
