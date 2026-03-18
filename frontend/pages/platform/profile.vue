<template>
  <div id="platform-profile">
    <h1 class="mb-1 text-xl font-bold text-esmerald dark:text-white">Mi perfil</h1>
    <p class="mb-8 text-sm text-green-light">Revisa y actualiza tu información personal.</p>

    <!-- Success message -->
    <div
      v-if="successMessage"
      class="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400"
    >
      {{ successMessage }}
    </div>

    <!-- Error message -->
    <div
      v-if="errorMessage"
      class="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400"
    >
      {{ errorMessage }}
    </div>

    <div class="grid gap-6 lg:grid-cols-3">
      <!-- Avatar card -->
      <div class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none">
        <div class="flex flex-col items-center gap-4">
          <div class="relative h-24 w-24 overflow-hidden rounded-full border-2 border-esmerald/10 dark:border-white/10">
            <img
              v-if="avatarUrl"
              :src="avatarUrl"
              alt="Avatar"
              class="h-full w-full object-cover"
            />
            <div v-else class="flex h-full w-full items-center justify-center bg-esmerald text-2xl font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
              {{ authStore.userInitials }}
            </div>
          </div>
          <div class="text-center">
            <p class="text-base font-semibold text-esmerald dark:text-white">{{ authStore.displayName }}</p>
            <p class="text-xs text-green-light">{{ authStore.user?.email }}</p>
            <span
              class="mt-2 inline-block rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider"
              :class="authStore.isAdmin
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400'
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'"
            >
              {{ authStore.isAdmin ? 'Administrador' : 'Cliente' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Profile form -->
      <form
        class="rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:shadow-none lg:col-span-2"
        @submit.prevent="handleUpdate"
      >
        <h2 class="mb-5 text-base font-semibold text-esmerald dark:text-white">Información personal</h2>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Nombre</label>
            <input
              v-model="form.first_name"
              type="text"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Apellido</label>
            <input
              v-model="form.last_name"
              type="text"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Empresa</label>
            <input
              v-model="form.company_name"
              type="text"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Teléfono</label>
            <input
              v-model="form.phone"
              type="tel"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Cédula</label>
            <input
              v-model="form.cedula"
              type="text"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Fecha de nacimiento</label>
            <input
              v-model="form.date_of_birth"
              type="date"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Sexo</label>
            <select
              v-model="form.gender"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            >
              <option value="">Sin especificar</option>
              <option value="male">Masculino</option>
              <option value="female">Femenino</option>
              <option value="other">Otro</option>
              <option value="prefer_not_to_say">Prefiero no decir</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Nivel de educación</label>
            <select
              v-model="form.education_level"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40"
            >
              <option value="">Sin especificar</option>
              <option value="primaria">Primaria</option>
              <option value="secundaria">Secundaria</option>
              <option value="tecnico">Técnico</option>
              <option value="universitario">Universitario</option>
              <option value="posgrado">Posgrado</option>
              <option value="otro">Otro</option>
            </select>
          </div>
        </div>

        <div class="mt-6 flex justify-end">
          <button
            type="submit"
            :disabled="authStore.isLoading"
            class="rounded-xl bg-lemon px-6 py-3 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50"
          >
            {{ authStore.isLoading ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

defineI18nRoute(false)

useHead({
  title: 'Mi perfil — ProjectApp',
})

usePageEntrance('#platform-profile')

const authStore = usePlatformAuthStore()
authStore.hydrate()

const localError = ref('')
const successMessage = ref('')

const form = reactive({
  first_name: '',
  last_name: '',
  company_name: '',
  phone: '',
  cedula: '',
  date_of_birth: '',
  gender: '',
  education_level: '',
})

const errorMessage = computed(() => localError.value || authStore.error)

const avatarUrl = computed(() => authStore.user?.avatar_display_url || '')

onMounted(() => {
  if (authStore.user) {
    form.first_name = authStore.user.first_name || ''
    form.last_name = authStore.user.last_name || ''
    form.company_name = authStore.user.company_name || ''
    form.phone = authStore.user.phone || ''
    form.cedula = authStore.user.cedula || ''
    form.date_of_birth = authStore.user.date_of_birth || ''
    form.gender = authStore.user.gender || ''
    form.education_level = authStore.user.education_level || ''
  }
})

async function handleUpdate() {
  localError.value = ''
  successMessage.value = ''

  const result = await authStore.updateProfile({
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim(),
    company_name: form.company_name.trim(),
    phone: form.phone.trim(),
    cedula: form.cedula.trim(),
    date_of_birth: form.date_of_birth || null,
    gender: form.gender,
    education_level: form.education_level,
  })

  if (!result.success) {
    localError.value = result.message
    return
  }

  successMessage.value = 'Perfil actualizado correctamente.'
  setTimeout(() => { successMessage.value = '' }, 4000)
}
</script>
