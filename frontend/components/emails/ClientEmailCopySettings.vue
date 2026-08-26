<template>
  <div class="border-t border-border-muted pt-6" data-testid="client-email-copy-settings">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <div class="flex items-center gap-2">
          <h4 class="text-sm font-semibold text-text-default">Copias de todos los correos</h4>
          <span class="rounded bg-primary-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-text-brand">
            BCC
          </span>
        </div>
        <p class="mt-1 max-w-2xl text-xs text-text-muted">
          Cada salida registrada se copia de forma oculta. Esta lista es independiente de los destinatarios de avisos internos.
        </p>
      </div>
    </div>

    <div class="mt-4 rounded-lg border border-warning-strong/30 bg-warning-soft px-3 py-2 text-xs text-warning-strong">
      Cada destinatario activo añade hasta un envío BCC por correo. Con un destinatario y todas las familias, el volumen SMTP y el volumen de esa bandeja pueden duplicarse.
    </div>

    <div class="mt-3 rounded-lg border border-danger-strong/30 bg-danger-soft px-3 py-2 text-xs text-danger-strong" data-testid="email-copy-security-warning">
      La familia Seguridad copia y conserva el contenido completo de códigos de verificación (OTP), enlaces de recuperación e invitaciones con contraseña temporal. Toda persona administradora puede consultar este historial.
    </div>

    <p v-if="store.isLoadingCopyRecipients" class="py-5 text-center text-xs text-text-subtle">
      Cargando destinatarios...
    </p>

    <template v-else>
      <form class="mt-5 space-y-3 rounded-lg border border-border-muted bg-surface-muted p-3" @submit.prevent="addRecipient">
        <BaseFormField label="Nuevo destinatario" for="client-copy-email">
          <BaseInput
            id="client-copy-email"
            v-model="newEmail"
            type="email"
            placeholder="nombre@empresa.com"
            data-testid="client-copy-email"
          />
        </BaseFormField>
        <FamilyPicker v-model="newFamilies" :options="store.copyFamilies" test-prefix="client-copy-new" />
        <div class="flex items-center justify-end">
          <BaseButton
            type="submit"
            size="sm"
            :disabled="!newEmail.trim() || !newFamilies.length || store.isSavingCopyRecipient"
            data-testid="client-copy-add"
          >
            Agregar destinatario
          </BaseButton>
        </div>
      </form>

      <p v-if="!store.copyRecipients.length" class="py-6 text-center text-xs text-text-subtle">
        No hay destinatarios configurados. Los correos siguen saliendo a sus destinatarios principales sin copia interna.
      </p>

      <div v-else class="mt-4 space-y-3">
        <article
          v-for="recipient in store.copyRecipients"
          :key="recipient.id"
          class="rounded-lg border border-border-muted p-3"
          :data-testid="`client-copy-row-${recipient.id}`"
        >
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div class="min-w-0">
              <p class="break-all text-sm font-medium text-text-default">{{ recipient.email }}</p>
              <p class="mt-0.5 text-[11px]" :class="recipient.is_active ? 'text-success-strong' : 'text-text-subtle'">
                {{ recipient.is_active ? 'Activo' : 'Pausado' }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <BaseButton
                variant="secondary"
                size="sm"
                :disabled="store.isSavingCopyRecipient"
                :data-testid="`client-copy-toggle-${recipient.id}`"
                @click="toggleRecipient(recipient)"
              >
                {{ recipient.is_active ? 'Pausar' : 'Activar' }}
              </BaseButton>
              <BaseButton
                variant="danger-ghost"
                size="sm"
                :disabled="store.isSavingCopyRecipient"
                :data-testid="`client-copy-delete-${recipient.id}`"
                @click="removeRecipient(recipient)"
              >
                Eliminar
              </BaseButton>
            </div>
          </div>

          <div class="mt-3">
            <FamilyPicker
              v-model="draftFamilies[recipient.id]"
              :options="store.copyFamilies"
              :test-prefix="`client-copy-${recipient.id}`"
            />
            <div class="mt-2 flex justify-end">
              <BaseButton
                variant="secondary"
                size="sm"
                :disabled="!canSaveFamilies(recipient) || store.isSavingCopyRecipient"
                :data-testid="`client-copy-save-${recipient.id}`"
                @click="saveFamilies(recipient)"
              >
                Guardar familias
              </BaseButton>
            </div>
          </div>
        </article>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import FamilyPicker from '~/components/emails/FamilyPicker.vue';
import { useEmailStore } from '~/stores/emails';
import { usePanelNotify } from '~/composables/usePanelNotify';

const store = useEmailStore();
const notify = usePanelNotify();
const newEmail = ref('');
const newFamilies = ref([]);
const draftFamilies = reactive({});

function hydrateDrafts() {
  for (const recipient of store.copyRecipients) {
    draftFamilies[recipient.id] = [...(recipient.families || [])];
  }
  if (!newFamilies.value.length) {
    newFamilies.value = store.copyFamilies.map(option => option.value);
  }
}

function errorDetail(error) {
  if (!error) return 'Intenta de nuevo.';
  if (typeof error === 'string') return error;
  const first = Object.values(error).flat()[0];
  return typeof first === 'string' ? first : 'Intenta de nuevo.';
}

async function addRecipient() {
  const result = await store.createCopyRecipient({
    email: newEmail.value.trim(),
    is_active: true,
    families: [...newFamilies.value],
  });
  if (!result.success) {
    notify.error({ title: 'No se pudo agregar', detail: errorDetail(result.error) });
    return;
  }
  newEmail.value = '';
  newFamilies.value = store.copyFamilies.map(option => option.value);
  hydrateDrafts();
  notify.success({ title: 'Destinatario agregado' });
}

async function toggleRecipient(recipient) {
  const result = await store.updateCopyRecipient(recipient.id, {
    is_active: !recipient.is_active,
  });
  if (!result.success) {
    notify.error({ title: 'No se pudo actualizar', detail: errorDetail(result.error) });
    return;
  }
  hydrateDrafts();
}

function canSaveFamilies(recipient) {
  const families = draftFamilies[recipient.id] || [];
  if (recipient.is_active && !families.length) return false;
  return JSON.stringify(families) !== JSON.stringify(recipient.families || []);
}

async function saveFamilies(recipient) {
  const result = await store.updateCopyRecipient(recipient.id, {
    families: [...(draftFamilies[recipient.id] || [])],
  });
  if (!result.success) {
    notify.error({ title: 'No se pudieron guardar las familias', detail: errorDetail(result.error) });
    return;
  }
  hydrateDrafts();
  notify.success({ title: 'Familias actualizadas' });
}

async function removeRecipient(recipient) {
  const result = await store.deleteCopyRecipient(recipient.id);
  if (!result.success) {
    notify.error({ title: 'No se pudo eliminar', detail: errorDetail(result.error) });
    return;
  }
  delete draftFamilies[recipient.id];
  notify.success({ title: 'Destinatario eliminado' });
}

watch(() => store.copyRecipients, hydrateDrafts, { deep: true });

onMounted(async () => {
  const result = await store.fetchCopyRecipients();
  if (!result.success) {
    notify.error({
      title: 'No se pudieron cargar las copias internas',
      detail: errorDetail(result.error),
    });
  }
  hydrateDrafts();
});
</script>
