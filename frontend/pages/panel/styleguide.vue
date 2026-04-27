<script setup>
import { ref } from 'vue'
import { useDiagnosticDarkMode } from '~/composables/useDiagnosticDarkMode'

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] })

const { isDark, toggle } = useDiagnosticDarkMode()

// Demo state for components
const sampleText = ref('Texto de ejemplo')
const sampleNumber = ref(42)
const sampleSelect = ref('a')
const sampleTextarea = ref('Una nota corta\ncon dos líneas.')
const toggleA = ref(true)
const toggleB = ref(false)
const checkA = ref(false)
const modalOpen = ref(false)
const fieldError = ref(false)

const segmented = ref('editor')
const filterOpen = ref(false)
const filterCount = ref(2)
const baseTab = ref('a')
const alertVisible = ref(true)
const dropdownLog = ref('')

const tokenSwatches = [
  { group: 'Surface', items: ['bg-surface', 'bg-surface-muted', 'bg-surface-raised'] },
  { group: 'Border', items: ['border-border-default', 'border-border-muted'] },
  { group: 'Text', items: ['text-text-default', 'text-text-muted', 'text-text-subtle', 'text-text-brand'] },
  { group: 'Brand', items: ['bg-primary', 'bg-primary-strong', 'bg-primary-soft', 'bg-accent', 'bg-accent-soft'] },
  { group: 'Form', items: ['bg-input-bg', 'border-input-border', 'text-input-text', 'ring-focus-ring'] },
  {
    group: 'Status',
    items: [
      'bg-success-soft', 'text-success-strong',
      'bg-warning-soft', 'text-warning-strong',
      'bg-danger-soft', 'text-danger-strong',
    ],
  },
]
</script>

<template>
  <div class="space-y-10">
    <header class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-light text-text-default">Design System — Styleguide</h1>
        <p class="text-sm text-text-muted mt-1">
          Catálogo visual de tokens y componentes base. Úsalo como referencia al construir vistas nuevas y para validar
          dark mode antes de publicar.
        </p>
      </div>
      <BaseButton variant="secondary" size="sm" @click="toggle">
        {{ isDark ? '☀️ Modo claro' : '🌙 Modo oscuro' }}
      </BaseButton>
    </header>

    <!-- Tokens -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">1. Tokens</h2>
      <p class="text-sm text-text-muted">
        Cada chip muestra cómo resuelve el token en el modo activo. Cambia entre claro/oscuro arriba para verificar.
      </p>
      <div v-for="group in tokenSwatches" :key="group.group" class="space-y-2">
        <h3 class="text-xs font-semibold text-text-brand uppercase tracking-wider">{{ group.group }}</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <div
            v-for="cls in group.items"
            :key="cls"
            class="rounded-xl border border-border-muted p-3 bg-surface flex items-center gap-3"
          >
            <span
              class="block w-10 h-10 rounded-lg border border-border-muted"
              :class="cls.startsWith('text-') ? `${cls} flex items-center justify-center font-bold` : cls.startsWith('ring-') ? `ring-2 ${cls}` : cls"
            >
              <template v-if="cls.startsWith('text-')">Aa</template>
            </span>
            <code class="text-xs text-text-muted">{{ cls }}</code>
          </div>
        </div>
      </div>
    </section>

    <!-- Buttons -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">2. BaseButton</h2>
      <BaseCard padding="md">
        <div class="flex flex-wrap items-center gap-3">
          <BaseButton variant="primary">Primary</BaseButton>
          <BaseButton variant="secondary">Secondary</BaseButton>
          <BaseButton variant="ghost">Ghost</BaseButton>
          <BaseButton variant="danger">Danger</BaseButton>
          <BaseButton variant="accent">Accent</BaseButton>
          <BaseButton variant="primary" loading>Loading</BaseButton>
          <BaseButton variant="primary" disabled>Disabled</BaseButton>
        </div>
        <div class="flex flex-wrap items-center gap-3 mt-4">
          <BaseButton size="sm">Small</BaseButton>
          <BaseButton size="md">Medium</BaseButton>
          <BaseButton size="lg">Large</BaseButton>
        </div>
      </BaseCard>
    </section>

    <!-- Badges -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">3. BaseBadge</h2>
      <BaseCard padding="md">
        <div class="flex flex-wrap items-center gap-2">
          <BaseBadge variant="neutral">Neutral</BaseBadge>
          <BaseBadge variant="primary">Primary</BaseBadge>
          <BaseBadge variant="accent">Accent</BaseBadge>
          <BaseBadge variant="success">Success</BaseBadge>
          <BaseBadge variant="warning">Warning</BaseBadge>
          <BaseBadge variant="danger">Danger</BaseBadge>
          <BaseBadge variant="success" size="sm">Small</BaseBadge>
        </div>
      </BaseCard>
    </section>

    <!-- Form controls -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">4. Form controls</h2>
      <BaseCard padding="md">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BaseFormField label="Texto" hint="Hint de ayuda" for="sg-text">
            <BaseInput id="sg-text" v-model="sampleText" placeholder="Escribe algo…" />
          </BaseFormField>
          <BaseFormField label="Número" required for="sg-num">
            <BaseInput id="sg-num" v-model.number="sampleNumber" type="number" min="0" />
          </BaseFormField>
          <BaseFormField
            label="Con error"
            :error="fieldError ? 'Este campo es obligatorio.' : ''"
            for="sg-err"
          >
            <BaseInput id="sg-err" v-model="sampleText" :error="fieldError" />
          </BaseFormField>
          <BaseFormField label="Select" for="sg-sel">
            <BaseSelect
              id="sg-sel"
              v-model="sampleSelect"
              :options="[
                { value: 'a', label: 'Opción A' },
                { value: 'b', label: 'Opción B' },
                { value: 'c', label: 'Opción C' },
              ]"
            />
          </BaseFormField>
          <BaseFormField label="Textarea" hint="Soporta múltiples líneas" class="sm:col-span-2">
            <BaseTextarea v-model="sampleTextarea" :rows="3" />
          </BaseFormField>
          <div class="space-y-3">
            <BaseCheckbox v-model="checkA">Acepto los términos</BaseCheckbox>
            <BaseCheckbox v-model="fieldError">Mostrar estado de error en el campo de arriba</BaseCheckbox>
          </div>
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <BaseToggle v-model="toggleA" aria-label="Activar A" />
              <span class="text-sm text-text-default">Toggle A — {{ toggleA ? 'on' : 'off' }}</span>
            </div>
            <div class="flex items-center gap-3">
              <BaseToggle v-model="toggleB" size="sm" aria-label="Activar B" />
              <span class="text-sm text-text-default">Toggle B (sm) — {{ toggleB ? 'on' : 'off' }}</span>
            </div>
            <div class="flex items-center gap-3">
              <BaseToggle :model-value="false" disabled aria-label="Disabled" />
              <span class="text-sm text-text-muted">Toggle disabled</span>
            </div>
          </div>
        </div>
      </BaseCard>
    </section>

    <!-- Card and surfaces -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">5. BaseCard / Surfaces</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <BaseCard padding="md">
          <h3 class="text-sm font-semibold text-text-default">bg-surface</h3>
          <p class="text-xs text-text-muted mt-1">Tarjeta principal.</p>
        </BaseCard>
        <div class="rounded-xl border border-border-muted p-5 bg-surface-muted">
          <h3 class="text-sm font-semibold text-text-default">bg-surface-muted</h3>
          <p class="text-xs text-text-muted mt-1">Wash de fondo de página.</p>
        </div>
        <div class="rounded-xl border border-border-muted p-5 bg-surface-raised">
          <h3 class="text-sm font-semibold text-text-default">bg-surface-raised</h3>
          <p class="text-xs text-text-muted mt-1">Panel interior elevado.</p>
        </div>
      </div>
    </section>

    <!-- Segmented -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">6. BaseSegmented</h2>
      <BaseCard padding="md">
        <BaseSegmented
          v-model="segmented"
          class="max-w-sm"
          full-width
          :options="[
            { value: 'editor', label: 'Editor' },
            { value: 'json', label: 'JSON' },
            { value: 'preview', label: 'Preview' },
          ]"
        />
        <p class="text-xs text-text-muted mt-3">Selección actual: <code>{{ segmented }}</code></p>
      </BaseCard>
    </section>

    <!-- Tabs -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">7. BaseTabs</h2>
      <BaseCard padding="md">
        <p class="text-xs text-text-muted mb-3">Variant: underline (default)</p>
        <BaseTabs
          v-model="baseTab"
          :tabs="[
            { id: 'a', label: 'General' },
            { id: 'b', label: 'Pendientes', badge: 4 },
            { id: 'c', label: 'Archivado', disabled: true },
          ]"
        />
        <p class="text-xs text-text-muted mb-3">Variant: pill</p>
        <BaseTabs
          v-model="baseTab"
          variant="pill"
          full-width
          :tabs="[
            { id: 'a', label: 'A' },
            { id: 'b', label: 'B' },
            { id: 'c', label: 'C' },
          ]"
        />
      </BaseCard>
    </section>

    <!-- Alert + EmptyState -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">8. BaseAlert / BaseEmptyState</h2>
      <BaseCard padding="md">
        <div class="space-y-3">
          <BaseAlert v-if="alertVisible" variant="info" title="Información" dismissible @dismiss="alertVisible = false">
            Este es un alerta dismissible. Soporta título, body via slot y un dismiss button.
          </BaseAlert>
          <BaseAlert variant="success" title="Listo">Operación completada con éxito.</BaseAlert>
          <BaseAlert variant="warning">Aviso sin título — el body va en el slot default.</BaseAlert>
          <BaseAlert variant="danger" title="Error crítico">Algo salió mal.</BaseAlert>
        </div>
        <div class="mt-6">
          <BaseEmptyState title="Sin propuestas" description="Cuando crees tu primera propuesta aparecerá aquí.">
            <template #actions>
              <BaseButton variant="primary" size="md">Crear propuesta</BaseButton>
              <BaseButton variant="ghost" size="md">Ver demo</BaseButton>
            </template>
          </BaseEmptyState>
        </div>
      </BaseCard>
    </section>

    <!-- Dropdown -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">9. BaseDropdown</h2>
      <BaseCard padding="md">
        <BaseDropdown
          :items="[
            { label: 'Editar', onClick: () => (dropdownLog = 'editar') },
            { label: 'Duplicar', onClick: () => (dropdownLog = 'duplicar') },
            { divider: true },
            { label: 'Archivar', onClick: () => (dropdownLog = 'archivar') },
            { label: 'Eliminar', danger: true, onClick: () => (dropdownLog = 'eliminar') },
          ]"
        >
          <template #trigger>
            <BaseButton variant="secondary" size="md">Acciones ▾</BaseButton>
          </template>
        </BaseDropdown>
        <p class="text-xs text-text-muted mt-3">Última acción: <code>{{ dropdownLog || '—' }}</code></p>
      </BaseCard>
    </section>

    <!-- Existing UI components on tokens -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">10. UI components on tokens</h2>
      <BaseCard padding="md">
        <h3 class="text-sm font-semibold text-text-default mb-3">FilterToggleButton</h3>
        <div class="flex items-center gap-3">
          <UiFilterToggleButton :open="filterOpen" :count="filterCount" @click="filterOpen = !filterOpen" />
          <BaseButton variant="ghost" size="sm" @click="filterCount = (filterCount + 1) % 4">
            Cambiar count ({{ filterCount }})
          </BaseButton>
        </div>
      </BaseCard>
    </section>

    <!-- Modal -->
    <section class="space-y-4">
      <h2 class="text-lg font-semibold text-text-default">11. BaseModal</h2>
      <BaseCard padding="md">
        <div class="flex items-center gap-3">
          <BaseButton variant="primary" @click="modalOpen = true">Abrir modal</BaseButton>
          <span class="text-xs text-text-muted">El modal cierra con backdrop o tecla Esc.</span>
        </div>
      </BaseCard>
      <BaseModal v-model="modalOpen" size="lg">
        <div class="p-6 space-y-4">
          <h3 class="text-lg font-semibold text-text-default">Demo modal</h3>
          <p class="text-sm text-text-muted">
            Renderizado por <code>BaseModal</code> con tokens semánticos. Prueba abrirlo en light y dark.
          </p>
          <BaseFormField label="Campo dentro del modal">
            <BaseInput v-model="sampleText" />
          </BaseFormField>
          <div class="flex justify-end gap-2 pt-3 border-t border-border-muted">
            <BaseButton variant="ghost" @click="modalOpen = false">Cancelar</BaseButton>
            <BaseButton variant="primary" @click="modalOpen = false">Aceptar</BaseButton>
          </div>
        </div>
      </BaseModal>
    </section>
  </div>
</template>
