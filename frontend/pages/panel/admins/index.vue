<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-2xl font-light text-text-default">Administradores</h1>
        <p class="text-sm text-text-subtle mt-1">Gestionar administradores de la plataforma</p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        class="w-fit"
        @click="showCreateModal = true"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Agregar Administrador
      </BaseButton>
    </div>

    <!-- Filters -->
    <div class="flex gap-2 mb-5">
      <button
        v-for="f in filters"
        :key="f.value"
        class="text-xs px-3 py-1.5 rounded-full font-medium transition-colors"
        :class="activeFilter === f.value
          ? 'bg-primary text-white'
          : 'bg-surface-raised text-text-muted hover:bg-border-muted'"
        @click="activeFilter = f.value"
      >
        {{ f.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="adminStore.loading" class="text-center py-16 text-text-subtle text-sm">
      Cargando administradores...
    </div>

    <!-- Empty -->
    <div v-else-if="filteredAdmins.length === 0" class="text-center py-16 text-text-subtle text-sm">
      {{ activeFilter !== 'all' ? 'No hay administradores con este filtro.' : 'No hay administradores aún.' }}
    </div>

    <!-- Admin list -->
    <div v-else class="space-y-3">
      <div
        v-for="admin in filteredAdmins"
        :key="admin.user_id"
        class="bg-surface rounded-xl shadow-sm border border-border-muted px-5 py-4 flex flex-wrap items-center justify-between gap-3"
      >
        <div class="flex items-center gap-4">
          <!-- Avatar -->
          <div class="w-10 h-10 rounded-full bg-primary-soft flex items-center justify-center flex-shrink-0">
            <span class="text-text-brand font-bold text-sm">{{ initials(admin.first_name, admin.last_name) }}</span>
          </div>
          <div>
            <p class="text-sm font-semibold text-text-default">
              {{ admin.first_name }} {{ admin.last_name }}
            </p>
            <p class="text-xs text-text-subtle mt-0.5">{{ admin.email }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <!-- Status pill -->
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="statusClass(admin)"
          >
            {{ statusLabel(admin) }}
          </span>

          <!-- Actions -->
          <button
            v-if="!admin.is_onboarded && admin.is_active"
            class="text-xs px-3 py-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50 font-medium transition-colors"
            :disabled="resendingId === admin.user_id"
            @click="handleResendInvite(admin.user_id)"
          >
            {{ resendingId === admin.user_id ? 'Enviando...' : 'Reenviar invitación' }}
          </button>

          <button
            v-if="admin.is_active"
            class="text-xs px-3 py-1.5 rounded-lg bg-danger-soft text-danger-strong hover:opacity-90 font-medium transition-colors"
            @click="handleDeactivate(admin.user_id)"
          >
            Desactivar
          </button>

          <button
            v-if="!admin.is_active"
            class="text-xs px-3 py-1.5 rounded-lg bg-primary-soft text-text-brand hover:opacity-90 font-medium transition-colors"
            @click="handleReactivate(admin.user_id)"
          >
            Reactivar
          </button>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="closeModal"
      >
        <div role="dialog" aria-modal="true" aria-label="Agregar Administrador" class="bg-surface rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold text-text-default mb-4">Agregar Administrador</h2>
          <p class="text-sm text-text-muted mb-6">
            Se le enviará un email con credenciales temporales para acceder a la plataforma.
          </p>

          <form @submit.prevent="handleCreate">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-text-default mb-1">Email</label>
                <input
                  v-model="form.email"
                  type="email"
                  required
                  class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text rounded-lg text-sm placeholder:text-text-subtle
                         focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                  placeholder="admin@ejemplo.com"
                />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-text-default mb-1">Nombre</label>
                  <input
                    v-model="form.first_name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text rounded-lg text-sm placeholder:text-text-subtle
                           focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                    placeholder="Nombre"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-text-default mb-1">Apellido</label>
                  <input
                    v-model="form.last_name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text rounded-lg text-sm placeholder:text-text-subtle
                           focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                    placeholder="Apellido"
                  />
                </div>
              </div>
            </div>

            <!-- Error message -->
            <p v-if="createError" class="mt-3 text-sm text-danger-strong">{{ createError }}</p>

            <div class="flex justify-end gap-3 mt-6">
              <BaseButton variant="ghost" size="md" type="button" @click="closeModal">
                Cancelar
              </BaseButton>
              <BaseButton
                type="submit"
                variant="primary"
                size="md"
                :loading="creating"
                :disabled="creating"
              >
                {{ creating ? 'Creando...' : 'Crear Administrador' }}
              </BaseButton>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Toast notification -->
    <Teleport to="body">
      <Transition name="toast">
        <div
          v-if="toast"
          class="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium"
          :class="toast.type === 'success'
            ? 'bg-primary text-white'
            : 'bg-danger-strong text-white'"
        >
          {{ toast.message }}
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const { usePanelAdminsStore } = await import('~/stores/panel_admins');
const adminStore = usePanelAdminsStore();

const activeFilter = ref('all');
const showCreateModal = ref(false);
const creating = ref(false);
const createError = ref('');
const resendingId = ref(null);
const toast = ref(null);

const form = ref({ email: '', first_name: '', last_name: '' });

const filters = [
  { label: 'Todos', value: 'all' },
  { label: 'Activos', value: 'active' },
  { label: 'Pendientes', value: 'pending' },
  { label: 'Inactivos', value: 'inactive' },
];

const filteredAdmins = computed(() => {
  if (activeFilter.value === 'all') return adminStore.admins;
  if (activeFilter.value === 'active') return adminStore.activeAdmins;
  if (activeFilter.value === 'pending') return adminStore.pendingAdmins;
  if (activeFilter.value === 'inactive') return adminStore.inactiveAdmins;
  return adminStore.admins;
});

onMounted(() => {
  adminStore.fetchAdmins();
});

function initials(firstName, lastName) {
  return ((firstName?.[0] || '') + (lastName?.[0] || '')).toUpperCase() || '?';
}

function statusLabel(admin) {
  if (!admin.is_active) return 'Inactivo';
  if (!admin.is_onboarded) return 'Pendiente';
  return 'Activo';
}

function statusClass(admin) {
  if (!admin.is_active) return 'bg-surface-raised text-text-muted';
  if (!admin.is_onboarded) return 'bg-warning-soft text-warning-strong';
  return 'bg-primary-soft text-text-brand';
}

function showToast(message, type = 'success') {
  toast.value = { message, type };
  setTimeout(() => { toast.value = null; }, 3000);
}

function closeModal() {
  showCreateModal.value = false;
  form.value = { email: '', first_name: '', last_name: '' };
  createError.value = '';
}

async function handleCreate() {
  creating.value = true;
  createError.value = '';

  const result = await adminStore.createAdmin(form.value);
  creating.value = false;

  if (result.success) {
    closeModal();
    showToast('Administrador creado. Se envió la invitación por email.');
  } else {
    createError.value = result.error;
  }
}

async function handleResendInvite(userId) {
  resendingId.value = userId;
  const result = await adminStore.resendInvite(userId);
  resendingId.value = null;

  if (result.success) {
    showToast('Invitación reenviada.');
  } else {
    showToast(result.error, 'error');
  }
}

async function handleDeactivate(userId) {
  const result = await adminStore.deactivateAdmin(userId);
  if (result.success) {
    showToast('Administrador desactivado.');
  } else {
    showToast(result.error, 'error');
  }
}

async function handleReactivate(userId) {
  const result = await adminStore.reactivateAdmin(userId);
  if (result.success) {
    showToast('Administrador reactivado.');
  } else {
    showToast(result.error, 'error');
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(12px);
}
</style>
