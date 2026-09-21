<template>
  <section class="bg-surface border border-border-default rounded-xl shadow-card p-5 space-y-4">
    <h2 class="text-base font-semibold text-text-default">Apariencia</h2>
    <p class="text-sm text-text-subtle">Personaliza el diseño y revisa el resultado en la vista previa. Guarda los cambios para publicarlos.</p>
    <BaseFormRow :cols="2" :gap="4" at="md">
      <BaseFormField v-for="color in colors" :key="color.key" :label="color.label" :for="`lt-${color.key}`" :error="errors[color.key]">
        <div class="flex items-center gap-2">
          <BaseInput :id="`lt-${color.key}`" type="color" :model-value="form[color.key]" class="w-14 shrink-0" @update:model-value="emit('update-field', color.key, $event)" />
          <BaseInput :aria-label="`${color.label} hexadecimal`" :model-value="form[color.key]" maxlength="7" @update:model-value="emit('update-field', color.key, $event)" />
        </div>
      </BaseFormField>
    </BaseFormRow>
    <BaseFormField label="Tipografía" for="lt-font" :error="errors.font_family">
      <BaseSelect id="lt-font" :model-value="form.font_family" :options="fontOptions" @update:model-value="emit('update-field', 'font_family', $event)" />
    </BaseFormField>
    <BaseFormField label="Añadir desde Google Fonts" for="lt-google-font" :error="fontError">
      <div class="flex flex-wrap items-center gap-2">
        <BaseInput id="lt-google-font" v-model="newFont" placeholder="Ejemplo: Playfair Display" class="flex-1 min-w-0" @keydown.enter.prevent="addFont" />
        <BaseButton type="button" variant="secondary" :loading="loadingFont" @click="addFont">Cargar tipografía</BaseButton>
      </div>
    </BaseFormField>
    <p class="text-xs text-text-subtle">Escribe el nombre exacto de la familia en Google Fonts. Requiere conexión; si no carga se usa una fuente del sistema.</p>
    <p v-if="fontSuccess" role="status" class="text-sm text-text-default">{{ fontSuccess }}</p>
    <BaseFormField label="Logo de marca" for="lt-logo" :error="errors.logo">
      <div class="flex flex-wrap items-center gap-3">
        <img v-if="logo" :src="logo" alt="Logo actual" class="h-16 w-32 object-contain rounded border border-border-default" />
        <input id="lt-logo" ref="logoInput" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" @change="selectLogo" />
        <BaseButton type="button" variant="secondary" :loading="busy" @click="logoInput?.click()">{{ logo ? 'Cambiar logo' : 'Subir logo' }}</BaseButton>
        <BaseButton v-if="logo" type="button" variant="danger-ghost" :loading="busy" @click="emit('remove-logo')">Quitar logo</BaseButton>
      </div>
    </BaseFormField>
    <p class="text-xs text-text-subtle">JPG, PNG o WebP, máximo 5 MB. El logo se guarda al subirlo y sustituye la marca ProjectApp cuando la cabecera está visible. La foto de perfil se conserva.</p>
    <BaseButton type="button" variant="ghost" @click="resetTheme">Restablecer colores y tipografía</BaseButton>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { googleFontUrl, isFontFamily, LINKTREE_DEFAULTS } from '~/utils/linktreeTheme';

const props = defineProps({
  form: { type: Object, required: true },
  logo: { type: String, default: '' },
  errors: { type: Object, default: () => ({}) },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(['update-field', 'upload-logo', 'remove-logo']);
const colors = [
  { key: 'background_color', label: 'Fondo' },
  { key: 'accent_color', label: 'Acento y botones' },
  { key: 'text_color', label: 'Texto principal' },
  { key: 'muted_color', label: 'Texto secundario' },
  { key: 'button_text_color', label: 'Texto del botón principal' },
];
const addedFonts = ref([]);
const fontOptions = computed(() => [...new Set([
  'Ubuntu', 'Inter', 'Roboto', 'Montserrat', 'Lato', 'Poppins', 'Playfair Display',
  ...addedFonts.value, props.form.font_family,
].filter(Boolean))]);
const newFont = ref('');
const fontError = ref('');
const fontSuccess = ref('');
const loadingFont = ref(false);
const logoInput = ref(null);

async function addFont() {
  if (loadingFont.value) return;
  const family = newFont.value.trim().replace(/\s+/g, ' ');
  fontError.value = '';
  fontSuccess.value = '';
  if (!isFontFamily(family)) {
    fontError.value = 'Escribe un nombre de familia válido, sin enlaces ni código CSS.';
    return;
  }
  loadingFont.value = true;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(googleFontUrl(family), { signal: controller.signal, credentials: 'omit' });
    if (!response.ok || !(await response.text()).includes('@font-face')) {
      fontError.value = 'No se encontró esa familia en Google Fonts. Verifica el nombre.';
      return;
    }
    addedFonts.value.push(family);
    emit('update-field', 'font_family', family);
    fontSuccess.value = `${family} cargada. Guarda los cambios para publicarla.`;
    newFont.value = '';
  } catch {
    fontError.value = 'No se pudo conectar con Google Fonts. Inténtalo de nuevo.';
  } finally {
    clearTimeout(timeout);
    loadingFont.value = false;
  }
}

function selectLogo(event) {
  const file = event.target.files?.[0];
  if (file && !props.busy) emit('upload-logo', file);
  event.target.value = '';
}

function resetTheme() {
  for (const [key, value] of Object.entries(LINKTREE_DEFAULTS)) emit('update-field', key, value);
  fontSuccess.value = '';
  fontError.value = '';
}
</script>
