<template>
  <div>
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
    <DiagnosticActionsModal
      :visible="showActionsModal"
      :diagnostic="store.current || {}"
      @close="showActionsModal = false"
      @send="onSendInitial"
      @resend="onSendInitial"
      @analyze="onMarkAnalysis"
      @send-final="onSendFinal"
      @delete="onDelete"
    />

    <div v-if="store.isLoading && !store.current" class="py-16 text-center text-text-subtle text-sm">
      Cargando…
    </div>

    <div v-else-if="!store.current" class="py-16 text-center text-rose-600 dark:text-rose-400 text-sm">
      No se encontró el diagnóstico.
    </div>

    <template v-else>
      <div class="mb-8">
        <NuxtLink
          :to="localePath('/panel/diagnostics')"
          class="text-sm text-text-muted hover:text-text-default transition-colors"
        >
          ← Volver a diagnósticos
        </NuxtLink>
      </div>

      <!-- Sticky header: title + investment + status -->
      <div
        class="sticky top-0 z-30 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-3 mb-6
               bg-surface/80 backdrop-blur-md
               border-b border-border-muted transition-all"
      >
        <div class="flex flex-wrap items-center gap-2 sm:gap-3">
          <h1 class="text-lg sm:text-xl font-light text-text-default truncate">
            {{ store.current.title }}
          </h1>
          <span
            v-if="store.current.investment_amount > 0"
            class="text-sm sm:text-base font-light text-text-subtle whitespace-nowrap"
          >
            ({{ formatInvestment(store.current.investment_amount, store.current.currency) }})
          </span>
          <DiagnosticStatusBadge :status="store.current.status" />
        </div>
      </div>

      <!-- Tabs -->
      <BaseTabs :tabs="tabs" v-model="activeTab" />

      <!-- General -->
      <section v-if="activeTab === 'general'">
        <TabSplitLayout ratio="3:2">
          <template #aside>
        <!-- Editable slug (URL personalizada) -->
        <div class="bg-surface border border-border-muted rounded-xl p-4 sm:p-5 mb-4">
          <label class="text-xs font-medium text-text-muted uppercase tracking-wider" for="diagnostic-slug-input">
            URL personalizada
          </label>
          <div class="mt-2 flex flex-wrap items-stretch gap-2">
            <div class="flex-1 min-w-[260px] flex items-stretch rounded-lg border border-input-border bg-surface-raised focus-within:border-focus-ring focus-within:ring-1 focus-within:ring-focus-ring/30">
              <span class="px-3 flex items-center text-xs text-text-subtle border-r border-input-border select-none">/diagnostic/</span>
              <input
                id="diagnostic-slug-input"
                v-model="slugDraft"
                type="text"
                data-testid="diagnostic-slug-input"
                class="flex-1 bg-transparent px-3 py-2 text-sm text-text-default placeholder:text-text-subtle focus:outline-none font-mono"
                placeholder="maria-lopez"
                maxlength="120"
                @keydown.enter.prevent="saveSlug"
              />
            </div>
            <BaseButton
              variant="primary"
              size="sm"
              :disabled="slugSaving || slugDraft === (store.current?.slug || '')"
              @click="saveSlug"
            >
              {{ slugSaving ? 'Guardando…' : (slugSaved ? 'Guardado' : 'Guardar') }}
            </BaseButton>
            <BaseButton
              variant="secondary"
              size="sm"
              title="Regenerar desde el nombre del cliente"
              @click="regenerateSlugFromName"
            >
              Regenerar
            </BaseButton>
          </div>
          <p v-if="slugError" class="text-xs text-danger-strong mt-2">{{ slugError }}</p>
          <p v-else class="text-xs text-text-subtle mt-2">
            Solo minúsculas, números y guiones. El cliente verá esta URL en el enlace.
          </p>
        </div>

        <!-- Read-only info grid -->
        <div class="bg-surface-raised rounded-xl p-4 sm:p-5 mb-6 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-text-subtle text-xs">ID</span>
            <p class="text-text-muted font-mono text-xs mt-0.5">#{{ store.current.id }}</p>
          </div>

          <div v-if="store.current.public_url">
            <div class="flex items-center gap-1">
              <span class="text-text-subtle text-xs">URL pública</span>
              <button
                type="button"
                :title="urlCopied ? 'Copiado!' : 'Copiar URL'"
                class="text-text-subtle hover:text-text-brand transition-colors"
                @click="copyPublicUrl"
              >
                <DocumentDuplicateIcon v-if="!urlCopied" class="w-3.5 h-3.5" />
                <CheckIcon v-else class="w-3.5 h-3.5 text-success-strong" />
              </button>
            </div>
            <p class="mt-0.5">
              <a :href="store.current.public_url" target="_blank" rel="noopener noreferrer" class="text-text-brand hover:underline text-xs break-all">
                {{ store.current.public_url }}
              </a>
            </p>
          </div>

          <div>
            <span class="text-text-subtle text-xs">Vistas</span>
            <p class="text-text-muted mt-0.5">
              <span class="font-medium">{{ store.current.view_count }}</span>
              <span v-if="store.current.last_viewed_at" class="text-text-subtle text-xs ml-1">· última {{ formatDate(store.current.last_viewed_at) }}</span>
              <span v-else class="text-text-subtle text-xs ml-1">· sin vistas</span>
            </p>
          </div>
          <div>
            <span class="text-text-subtle text-xs">Creado</span>
            <p class="text-text-muted mt-0.5 text-xs">{{ formatDate(store.current.created_at) }}</p>
          </div>
          <div v-if="store.current.initial_sent_at">
            <span class="text-text-subtle text-xs">Envío inicial</span>
            <p class="text-text-muted mt-0.5 text-xs">{{ formatDate(store.current.initial_sent_at) }}</p>
          </div>
          <div v-if="store.current.final_sent_at">
            <span class="text-text-subtle text-xs">Envío final</span>
            <p class="text-text-muted mt-0.5 text-xs">{{ formatDate(store.current.final_sent_at) }}</p>
          </div>
          <div v-if="store.current.responded_at">
            <span class="text-text-subtle text-xs">Respondido</span>
            <p class="text-text-muted mt-0.5 text-xs">{{ formatDate(store.current.responded_at) }}</p>
          </div>
        </div>

          </template>

          <template #main>
        <!-- Editable form -->
        <form class="bg-surface rounded-xl shadow-sm border border-border-muted" @submit.prevent="handleUpdate">
          <div class="p-4 sm:p-8 space-y-6">
            <BaseFormField label="Título">
              <BaseInput v-model="form.title" type="text" required data-testid="diagnostic-edit-title" />
            </BaseFormField>

            <!-- Client picker (autocomplete + snapshot fields) -->
            <div class="space-y-4 border border-border-muted rounded-xl p-4 bg-surface-raised">
              <div>
                <label class="block text-sm font-medium text-text-default mb-1">Cliente</label>
                <ClientAutocomplete
                  v-model="form.client_id"
                  :initial-label="form.client_label"
                  test-id="diagnostic-edit-client-autocomplete"
                  placeholder="Buscar cliente por nombre, email o empresa…"
                  @select="onClientSelected"
                />
                <p class="text-xs text-text-subtle mt-1">
                  Busca y selecciona un cliente existente. Si no tiene email real, las automatizaciones de correo quedarán pausadas.
                </p>
              </div>

              <!-- Placeholder warning badge -->
              <div
                v-if="store.current?.client?.is_email_placeholder"
                class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-100 dark:border-amber-500/20"
              >
                <span class="text-amber-700 dark:text-amber-300 text-xs font-medium">
                  📧 Email pendiente — las automatizaciones de correo están pausadas para este cliente.
                </span>
              </div>

              <!-- Snapshot fields -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <BaseFormField label="Nombre snapshot" size="sm">
                  <BaseInput v-model="form.client_name" type="text" size="sm" data-testid="diagnostic-edit-client-name" />
                </BaseFormField>
                <BaseFormField label="Email snapshot" size="sm">
                  <BaseInput v-model="form.client_email" type="email" size="sm" data-testid="diagnostic-edit-client-email" />
                </BaseFormField>
                <BaseFormField label="Teléfono / WhatsApp" size="sm">
                  <BaseInput v-model="form.client_phone" type="tel" size="sm" placeholder="+57 300 123 4567" data-testid="diagnostic-edit-client-phone" />
                </BaseFormField>
                <BaseFormField label="Empresa" size="sm">
                  <BaseInput v-model="form.client_company" type="text" size="sm" placeholder="Acme Inc." data-testid="diagnostic-edit-client-company" />
                </BaseFormField>
              </div>

              <!-- Propagate-to-profile checkbox -->
              <BaseCheckbox v-model="form.propagate_client_updates" data-testid="diagnostic-edit-client-propagate">
                Actualizar el perfil del cliente con estos cambios (también se reflejarán en sus otras propuestas y diagnósticos).
              </BaseCheckbox>
            </div>

            <BaseFormField label="Idioma" hint="Solo afecta los títulos por defecto al crear. Cambiar aquí no regenera las secciones existentes.">
              <BaseSelect
                v-model="form.language"
                :options="[{ value: 'es', label: 'Español' }, { value: 'en', label: 'English' }]"
              />
            </BaseFormField>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <BaseFormField label="Inversión total">
                <BaseInput
                  v-model.number="form.investment_amount"
                  type="number"
                  min="0"
                  step="0.01"
                  data-testid="diagnostic-edit-investment"
                />
              </BaseFormField>
              <BaseFormField label="Moneda">
                <BaseSelect
                  v-model="form.currency"
                  :options="[{ value: 'COP', label: 'COP' }, { value: 'USD', label: 'USD' }]"
                />
              </BaseFormField>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <BaseFormField label="% pago inicial">
                <div class="flex items-center gap-2">
                  <BaseInput v-model.number="form.payment_initial_pct" type="number" min="0" max="100" step="1" />
                  <span class="text-sm text-text-muted">%</span>
                </div>
              </BaseFormField>
              <BaseFormField label="% pago final" hint="Calculado automáticamente como 100 − % pago inicial.">
                <div class="flex items-center gap-2">
                  <BaseInput v-model.number="form.payment_final_pct" type="number" min="0" max="100" step="1" disabled />
                  <span class="text-sm text-text-muted">%</span>
                </div>
              </BaseFormField>
            </div>

            <BaseFormField label="Duración (texto)">
              <BaseInput v-model="form.duration_label" type="text" placeholder="Ej: 1 semana" />
            </BaseFormField>
          </div>

          <!-- Sticky action bar -->
          <div class="sticky bottom-0 rounded-b-xl bg-surface/95 backdrop-blur-sm border-t border-border-muted px-4 sm:px-5 py-3 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-20">
            <div class="flex flex-wrap items-center gap-2 sm:gap-3 pr-14 sm:pr-0">
              <BaseButton
                type="submit"
                variant="primary"
                size="md"
                :loading="store.isUpdating"
                :disabled="store.isUpdating"
                data-testid="diagnostic-edit-submit"
              >
                {{ store.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
              </BaseButton>

              <BaseButton
                variant="secondary"
                size="md"
                data-testid="diagnostic-actions-menu"
                aria-label="Acciones del diagnóstico"
                title="Más acciones"
                class="!w-10 !h-10 !p-0"
                @click="showActionsModal = true"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                  <path fill-rule="evenodd" d="M14.615 1.595a.75.75 0 0 1 .359.852L12.982 9.75h7.268a.75.75 0 0 1 .548 1.262l-10.5 11.25a.75.75 0 0 1-1.272-.71l1.992-7.302H3.818a.75.75 0 0 1-.548-1.262l10.5-11.25a.75.75 0 0 1 .845-.143Z" clip-rule="evenodd" />
                </svg>
              </BaseButton>

              <button
                v-if="nextAction"
                type="button"
                :disabled="store.isUpdating"
                :data-testid="'diagnostic-next-action-' + nextAction.key"
                :class="['px-4 sm:px-5 py-2 rounded-xl font-medium text-sm transition-all shadow-sm active:scale-[0.98] disabled:opacity-50 ml-auto', nextAction.colorClass]"
                @click="handleNextAction"
              >
                {{ nextAction.label }}
              </button>
            </div>
          </div>
        </form>
          </template>
        </TabSplitLayout>
      </section>

      <!-- Correos -->
      <div v-if="activeTab === 'emails'">
        <DiagnosticEmailsTab :diagnostic="store.current" />
      </div>

      <!-- Documentos (adjuntos) -->
      <div v-if="activeTab === 'documents'" class="max-w-7xl mx-auto">
        <DiagnosticDocumentsTab :diagnostic="store.current" />
      </div>

      <!-- Secciones (JSON-driven content) -->
      <section v-if="activeTab === 'sections'" class="max-w-7xl mx-auto">
        <div v-if="orderedSections.length" class="mb-4 bg-surface rounded-xl shadow-sm border border-border-muted px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold text-text-muted uppercase tracking-wider">Completitud de secciones</span>
            <span class="text-sm font-bold" :class="sectionCompletenessColor.text">
              {{ sectionCompleteness }}%
            </span>
          </div>
          <div class="w-full h-2 bg-surface-raised rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="sectionCompletenessColor.bar"
              :style="{ width: sectionCompleteness + '%' }"
            />
          </div>
          <p class="text-[11px] text-text-subtle mt-1.5">
            {{ sectionsWithContent }}/{{ enabledSectionsCount }} secciones habilitadas tienen contenido.
          </p>
        </div>
        <div class="text-xs text-text-muted mb-3">
          Cada tarjeta representa una sección visible para el cliente. Los cambios se guardan
          automáticamente al perder foco.
        </div>
        <div class="space-y-3">
          <DiagnosticSectionEditor
            v-for="section in orderedSections"
            :key="section.id"
            :section="section"
            :is-saving="sectionSavingId === section.id"
            :last-saved-at="sectionLastSaved[section.id]"
            @update:content="(json) => onSectionContentChange(section, json)"
            @update:section="(meta) => onSectionMetaChange(section, meta)"
            @reset="() => onSectionReset(section)"
          />
        </div>
      </section>

      <!-- Prompt -->
      <section v-if="activeTab === 'prompt'" class="max-w-7xl mx-auto">
        <DiagnosticPromptPanel />
      </section>

      <!-- JSON (export + import) -->
      <section v-if="activeTab === 'json'" class="max-w-screen-2xl mx-auto">
        <!-- Summary metrics -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4">
            <p class="text-xs font-medium text-text-subtle dark:text-green-light/40 uppercase tracking-wide">Secciones</p>
            <p class="mt-1.5 text-2xl font-light text-text-default tabular-nums">{{ jsonSummary.total }}</p>
            <p class="text-xs text-text-muted mt-0.5">
              {{ jsonSummary.enabled }} habilitadas · {{ jsonSummary.enabledPct }}%
            </p>
          </div>
          <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4">
            <p class="text-xs font-medium text-text-subtle dark:text-green-light/40 uppercase tracking-wide">Progreso</p>
            <p class="mt-1.5 text-2xl font-light text-text-default tabular-nums">{{ jsonSummary.progressPct }}%</p>
            <div class="mt-2 h-1.5 rounded-full bg-surface-raised overflow-hidden">
              <div
                class="h-full bg-primary transition-all"
                :style="{ width: `${jsonSummary.progressPct}%` }"
              />
            </div>
            <p class="text-xs text-text-muted mt-1.5">
              {{ jsonSummary.completed }}/{{ jsonSummary.enabled }} con contenido
            </p>
          </div>
          <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4">
            <p class="text-xs font-medium text-text-subtle dark:text-green-light/40 uppercase tracking-wide">Tamaño JSON</p>
            <p class="mt-1.5 text-2xl font-light text-text-default tabular-nums">{{ jsonSummary.sizeLabel }}</p>
            <p class="text-xs text-text-muted mt-0.5">Metadata + secciones</p>
          </div>
          <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4">
            <p class="text-xs font-medium text-text-subtle dark:text-green-light/40 uppercase tracking-wide">Última actualización</p>
            <p
              class="mt-1.5 text-sm font-medium text-text-default"
              :title="jsonSummary.updatedAt || ''"
            >
              <span v-if="jsonSummary.updatedAt">{{ formatDate(jsonSummary.updatedAt) }}</span>
              <span v-else class="text-text-subtle dark:text-green-light/40">—</span>
            </p>
            <p class="text-xs text-text-muted mt-0.5">Al guardar cambios</p>
          </div>
        </div>

        <TabSplitLayout>
          <template #main>
        <!-- Current JSON (read-only) -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h3 class="text-sm font-medium text-text-default">JSON del diagnóstico</h3>
              <p class="text-xs text-text-subtle dark:text-green-light/40 mt-0.5">Representación JSON completa — se actualiza al guardar cambios en otras pestañas.</p>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-muted bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="refreshExportJson"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Actualizar
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-muted bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="copyExportJson"
              >
                <DocumentDuplicateIcon class="w-3.5 h-3.5" />
                {{ jsonCopied ? '¡Copiado!' : 'Copiar' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-muted bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="downloadExportJson"
              >
                <ArrowDownTrayIcon class="w-3.5 h-3.5" />
                Descargar
              </button>
            </div>
          </div>
          <textarea
            :value="exportJsonString"
            readonly
            rows="18"
            class="bg-input-bg w-full px-4 py-3 border border-border-default rounded-xl text-xs font-mono leading-relaxed
                   text-text-default outline-none resize-y cursor-text select-all"
          />
        </div>

          </template>

          <template #aside>
        <!-- Import JSON -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
          <h3 class="text-sm font-medium text-text-default mb-1">Importar JSON</h3>
          <p class="text-xs text-text-subtle mb-4">Pega o sube un JSON para reemplazar el contenido del diagnóstico (metadata + secciones).</p>

          <div class="flex items-center gap-3 mb-3">
            <label
              class="inline-flex items-center gap-2 px-3 py-1.5 border border-border-default dark:border-white/[0.08] rounded-lg text-xs
                     text-text-default hover:bg-surface-raised cursor-pointer transition-colors"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Subir .json
              <input type="file" accept=".json" class="hidden" @change="handleJsonFileUpload" />
            </label>
            <span v-if="jsonImportFileName" class="text-xs text-text-muted">{{ jsonImportFileName }}</span>
          </div>

          <textarea
            v-model="jsonImportRaw"
            rows="10"
            placeholder="Pega aquí el JSON completo del diagnóstico..."
            class="bg-input-bg w-full px-4 py-3 border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 rounded-xl text-xs font-mono leading-relaxed
                   focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y"
            @input="parseImportJson"
          />

          <div v-if="jsonImportError" class="mt-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
            {{ jsonImportError }}
          </div>

          <div v-if="jsonImportParsed && !jsonImportError" class="mt-3 bg-primary-soft border border-emerald-200 dark:border-emerald-700/30 rounded-lg px-4 py-3">
            <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <span><span class="text-text-muted">Cliente:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.clientName }}</span></span>
              <span><span class="text-text-muted">Secciones:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.sectionCount }}</span></span>
              <span v-if="jsonImportPreview.investment"><span class="text-text-muted">Inversión:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.investment }}</span></span>
            </div>
          </div>

          <div v-if="jsonImportParsed && !jsonImportError" class="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              :disabled="store.isUpdating"
              class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
                     hover:bg-primary-strong transition-all shadow-sm shadow-emerald-100 hover:shadow-md hover:shadow-emerald-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-wait"
              @click="handleApplyImportJson"
            >
              <svg v-if="store.isUpdating" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ store.isUpdating ? 'Aplicando...' : 'Aplicar JSON' }}
            </button>
            <p class="text-xs text-text-subtle dark:text-green-light/40">Esto reemplazará la metadata y todas las secciones del diagnóstico.</p>
          </div>

          <div v-if="jsonImportMsg" class="mt-3 text-sm px-4 py-3 rounded-xl" :class="jsonImportMsg.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'">
            {{ jsonImportMsg.text }}
          </div>
        </div>
          </template>
        </TabSplitLayout>
      </section>

      <!-- Actividad -->
      <div v-if="activeTab === 'activity'" class="max-w-5xl mx-auto">
        <DiagnosticActivityTab
          :diagnostic="store.current"
          @log="onLogActivity"
        />
      </div>

      <!-- Analytics -->
      <div v-if="activeTab === 'analytics'" class="max-w-screen-2xl mx-auto">
        <DiagnosticAnalytics
          :diagnostic-id="id"
          :loader="() => store.fetchAnalytics(id)"
        />
      </div>
    </template>

    <PanelToast />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, onUnmounted } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticSectionEditor from '~/components/WebAppDiagnostic/admin/DiagnosticSectionEditor.vue';
import DiagnosticPromptPanel from '~/components/WebAppDiagnostic/admin/DiagnosticPromptPanel.vue';
import DiagnosticActivityTab from '~/components/WebAppDiagnostic/admin/DiagnosticActivityTab.vue';
import DiagnosticAnalytics from '~/components/WebAppDiagnostic/admin/DiagnosticAnalytics.vue';
import DiagnosticEmailsTab from '~/components/WebAppDiagnostic/DiagnosticEmailsTab.vue';
import DiagnosticDocumentsTab from '~/components/WebAppDiagnostic/DiagnosticDocumentsTab.vue';
import DiagnosticActionsModal from '~/components/WebAppDiagnostic/DiagnosticActionsModal.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import PanelToast from '~/components/panel/PanelToast.vue';
import TabSplitLayout from '~/components/panel/TabSplitLayout.vue';
import { DocumentDuplicateIcon, CheckIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelToast } from '~/composables/usePanelToast';
import { getDiagnosticNextAction } from '~/utils/diagnosticNextAction';
import { toSlug } from '~/utils/slugify';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const store = useDiagnosticsStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();
const panelToast = usePanelToast();

const moneyFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const dateTimeFormatter = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

function formatMoney(amount) {
  const n = Number(amount);
  if (Number.isNaN(n)) return amount;
  return moneyFormatter.format(n);
}
function formatInvestment(value, currency = 'COP') {
  if (!value) return '';
  const num = Number(value);
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' ' + currency;
}
function formatDate(iso) {
  if (!iso) return '';
  return dateTimeFormatter.format(new Date(iso));
}

const id = computed(() => Number(route.params.id));
const status = computed(() => store.current?.status);

const hasEmailsTab = computed(() =>
  [DIAGNOSTIC_STATUS.SENT, DIAGNOSTIC_STATUS.VIEWED, DIAGNOSTIC_STATUS.NEGOTIATING,
   DIAGNOSTIC_STATUS.ACCEPTED, DIAGNOSTIC_STATUS.REJECTED, DIAGNOSTIC_STATUS.FINISHED]
    .includes(status.value),
);
const hasDocumentsTab = computed(() =>
  [DIAGNOSTIC_STATUS.NEGOTIATING, DIAGNOSTIC_STATUS.ACCEPTED,
   DIAGNOSTIC_STATUS.REJECTED, DIAGNOSTIC_STATUS.FINISHED]
    .includes(status.value),
);

const tabs = computed(() => {
  const base = [{ id: 'general', label: 'General' }];
  if (hasEmailsTab.value)    base.push({ id: 'emails',    label: 'Correos' });
  if (hasDocumentsTab.value) base.push({ id: 'documents', label: 'Documentos' });
  base.push(
    { id: 'sections',  label: 'Secciones' },
    { id: 'prompt',    label: 'Prompt Diagnostic' },
    { id: 'json',      label: 'JSON' },
    { id: 'activity',  label: 'Actividad' },
    { id: 'analytics', label: 'Analytics' },
  );
  return base;
});
const tabIds = computed(() => tabs.value.map((t) => t.id));

const LEGACY_TAB_REDIRECTS = { pricing: 'general', radiography: 'sections', technical: 'sections', plantillas: 'json', summary: 'general' };
const initialQueryTab = route.query.tab;

// Apply legacy redirects eagerly; accept any string for now so a bookmarked tab
// like `?tab=emails` is not prematurely dropped while `store.current` is still loading.
const activeTab = ref(LEGACY_TAB_REDIRECTS[initialQueryTab] || initialQueryTab || 'general');

watch(activeTab, (tab) => {
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } });
  }
});

// Once the diagnostic is loaded, drop the active tab back to General if it isn't allowed
// for the current status (fixes the ?tab=emails-on-draft case too).
watch([tabIds, () => store.current], ([ids, current]) => {
  if (current && !ids.includes(activeTab.value)) {
    activeTab.value = 'general';
  }
});

// Honor legacy tab ids if the route changes during the session (link clicks, browser back).
watch(() => route.query.tab, (raw) => {
  if (raw && LEGACY_TAB_REDIRECTS[raw] && activeTab.value !== LEGACY_TAB_REDIRECTS[raw]) {
    activeTab.value = LEGACY_TAB_REDIRECTS[raw];
  }
});

const slugDraft = ref('');
const slugError = ref('');
const slugSaving = ref(false);
const slugSaved = ref(false);
let slugSavedTimer = null;
const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

watch(
  () => store.current?.slug,
  (value) => { slugDraft.value = value || ''; },
  { immediate: true },
);

function regenerateSlugFromName() {
  slugDraft.value = toSlug(store.current?.client_name, { fallback: 'diagnostico' });
  slugError.value = '';
}

async function saveSlug() {
  const value = (slugDraft.value || '').trim();
  slugError.value = '';
  slugSaved.value = false;
  if (value === (store.current?.slug || '')) return;
  if (value && !slugRegex.test(value)) {
    slugError.value = 'Solo minúsculas, números y guiones (sin espacios ni acentos).';
    return;
  }
  if (value.length > 120) {
    slugError.value = 'La URL personalizada no puede superar 120 caracteres.';
    return;
  }
  slugSaving.value = true;
  try {
    const result = await store.update(id.value, { slug: value });
    if (result?.success) {
      slugDraft.value = store.current?.slug || value;
      slugSaved.value = true;
      if (slugSavedTimer) clearTimeout(slugSavedTimer);
      slugSavedTimer = setTimeout(() => { slugSaved.value = false; }, 2000);
    } else {
      const errors = result?.errors || {};
      slugError.value = errors.slug?.[0] || result?.error || 'No se pudo guardar la URL.';
    }
  } finally {
    slugSaving.value = false;
  }
}

// ── Public URL copy ───────────────────────────────────────────────────
const urlCopied = ref(false);
let urlCopiedTimer = null;
async function copyPublicUrl() {
  if (!store.current?.public_url) return;
  try {
    await navigator.clipboard.writeText(store.current.public_url);
    urlCopied.value = true;
    if (urlCopiedTimer) clearTimeout(urlCopiedTimer);
    urlCopiedTimer = setTimeout(() => { urlCopied.value = false; }, 1500);
  } catch (_) { /* ignore */ }
}

// ── General editable form (title/client/language/pricing/size) ────────
const form = reactive({
  title: '',
  client_id: null,
  client_label: '',
  client_name: '',
  client_email: '',
  client_phone: '',
  client_company: '',
  propagate_client_updates: false,
  language: 'es',
  investment_amount: '',
  currency: 'COP',
  payment_initial_pct: null,
  payment_final_pct: null,
  duration_label: '',
});

const showActionsModal = ref(false);

function onClientSelected(client) {
  if (!client) return;
  form.client_id = client.id;
  form.client_label = client.name || form.client_label;
  form.client_name = client.name || form.client_name;
  form.client_email = client.is_email_placeholder ? '' : (client.email || '');
  form.client_phone = client.phone || form.client_phone;
  form.client_company = client.company || form.client_company;
}

function pctOrNull(v) {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

watch(() => form.payment_initial_pct, (v) => {
  const n = pctOrNull(v);
  if (n === null) {
    form.payment_final_pct = null;
    return;
  }
  const clamped = Math.max(0, Math.min(100, n));
  form.payment_final_pct = 100 - clamped;
});

function syncFormGeneral() {
  if (!store.current) return;
  const c = store.current;
  const pt = c.payment_terms || {};
  form.title = c.title || '';
  form.client_id = c.client?.id || null;
  form.client_label = c.client?.name || '';
  form.client_name = c.client_name || c.client?.name || '';
  form.client_email = c.client_email || (c.client?.is_email_placeholder ? '' : c.client?.email) || '';
  form.client_phone = c.client_phone || '';
  form.client_company = c.client_company || c.client?.company || '';
  form.propagate_client_updates = false;
  form.language = c.language || 'es';
  form.investment_amount = c.investment_amount ?? '';
  form.currency = c.currency || 'COP';
  form.payment_initial_pct = pt.initial_pct ?? null;
  form.payment_final_pct = pt.final_pct ?? null;
  form.duration_label = c.duration_label || '';
}

async function handleUpdate() {
  const payload = {
    title: form.title,
    language: form.language,
    investment_amount: form.investment_amount === '' ? null : form.investment_amount,
    currency: form.currency,
    payment_terms: {
      initial_pct: pctOrNull(form.payment_initial_pct),
      final_pct: pctOrNull(form.payment_final_pct),
    },
    duration_label: form.duration_label,
    client_name: form.client_name,
    client_email: form.client_email,
    client_phone: form.client_phone,
    client_company: form.client_company,
    propagate_client_updates: form.propagate_client_updates,
  };
  if (form.client_id && form.client_id !== store.current?.client?.id) {
    payload.client_id = form.client_id;
  }
  const result = await store.update(id.value, payload);
  showToast(
    result.success ? 'Diagnóstico actualizado.' : (result.error || 'Error al actualizar.'),
    result.success ? 'success' : 'error',
  );
}

function showToast(message, type) {
  panelToast.showToast({ type, text: message });
}

watch(() => store.current?.id, syncFormGeneral, { immediate: true });

// ── Next action (sticky bar) ──────────────────────────────────────────
const nextAction = computed(() => getDiagnosticNextAction(store.current));

function handleNextAction() {
  const a = nextAction.value;
  if (!a) return;
  if (a.key === 'send') return onSendInitial();
  if (a.key === 'analyze') return onMarkAnalysis();
  if (a.key === 'send-final') return onSendFinal();
}

// ── Sections tab ──────────────────────────────────────────────────────
const orderedSections = computed(() => {
  const list = store.current?.sections || [];
  return [...list].sort((a, b) => a.order - b.order);
});

function sectionHasContent(section) {
  const content = section?.content_json;
  if (!content || typeof content !== 'object') return false;
  const hasValue = (v) => {
    if (v == null) return false;
    if (typeof v === 'string') return v.trim().length > 0;
    if (typeof v === 'number') return v !== 0;
    if (Array.isArray(v)) return v.some(hasValue);
    if (typeof v === 'object') return Object.values(v).some(hasValue);
    return Boolean(v);
  };
  for (const [key, value] of Object.entries(content)) {
    if (key === 'index' || key === 'title') continue;
    if (hasValue(value)) return true;
  }
  return false;
}

const enabledSectionsCount = computed(
  () => orderedSections.value.filter((s) => s.is_enabled).length,
);
const sectionsWithContent = computed(
  () => orderedSections.value.filter((s) => s.is_enabled && sectionHasContent(s)).length,
);
const sectionCompleteness = computed(() =>
  enabledSectionsCount.value
    ? Math.round((sectionsWithContent.value / enabledSectionsCount.value) * 100)
    : 0,
);
const sectionCompletenessColor = computed(() => {
  const pct = sectionCompleteness.value;
  if (pct >= 80) return { text: 'text-text-brand', bar: 'bg-primary' };
  if (pct >= 50) return { text: 'text-amber-600', bar: 'bg-amber-500' };
  return { text: 'text-red-500', bar: 'bg-red-400' };
});

const sectionSavingId = ref(null);
const sectionLastSaved = reactive({});
const sectionTimers = new Map();

function scheduleSectionUpdate(sectionId, payload, delay = 600) {
  const existing = sectionTimers.get(sectionId);
  if (existing) clearTimeout(existing);
  sectionTimers.set(sectionId, setTimeout(async () => {
    sectionTimers.delete(sectionId);
    sectionSavingId.value = sectionId;
    try {
      const res = await store.updateSection(id.value, sectionId, payload);
      if (res.success) {
        sectionLastSaved[sectionId] = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
      } else {
        showToast(res.error || 'Error al guardar la sección.', 'error');
      }
    } finally {
      sectionSavingId.value = null;
    }
  }, delay));
}

function onSectionContentChange(section, contentJson) {
  scheduleSectionUpdate(section.id, { content_json: contentJson });
}
function onSectionMetaChange(section, meta) {
  scheduleSectionUpdate(section.id, meta, 300);
}
async function onSectionReset(section) {
  requestConfirm({
    title: 'Restaurar sección',
    message: `¿Restaurar «${section.title}» al contenido por defecto? Se perderán las ediciones actuales.`,
    variant: 'warning',
    confirmText: 'Restaurar',
    onConfirm: async () => {
      const r = await store.resetSection(id.value, section.id);
      showToast(r?.success ? 'Sección restaurada.' : (r?.error || 'Error.'), r?.success ? 'success' : 'error');
    },
  });
}

onBeforeUnmount(() => {
  sectionTimers.forEach((t) => clearTimeout(t));
  sectionTimers.clear();
});

// ── JSON tab (export + import) ────────────────────────────────────────
const METADATA_KEYS = [
  'title', 'language', 'investment_amount', 'currency', 'payment_terms',
  'duration_label', 'size_category', 'radiography',
];

function buildDiagnosticExport() {
  const d = store.current;
  if (!d) return null;
  const metadata = {};
  for (const k of METADATA_KEYS) {
    if (d[k] !== undefined) metadata[k] = d[k];
  }
  if (d.client) {
    metadata.client = {
      id: d.client.id,
      name: d.client.name,
      email: d.client.email,
      company: d.client.company,
    };
  }
  const sections = [...(d.sections || [])]
    .sort((a, b) => a.order - b.order)
    .map((s) => ({
      id: s.id,
      section_type: s.section_type,
      title: s.title,
      order: s.order,
      is_enabled: s.is_enabled,
      visibility: s.visibility,
      content_json: s.content_json,
    }));
  return { metadata, sections };
}

// Lazy: only evaluated when the JSON tab is rendered (and by copy/download handlers).
const exportJsonString = computed(() => {
  const payload = buildDiagnosticExport();
  return payload ? JSON.stringify(payload, null, 2) : '';
});

const jsonSummary = computed(() => {
  const sections = store.current?.sections || [];
  const total = sections.length;
  const enabled = sections.filter((s) => s.is_enabled).length;
  const completed = sections.filter((s) => s.is_enabled && sectionHasContent(s)).length;
  const enabledPct = total ? Math.round((enabled / total) * 100) : 0;
  const progressPct = enabled ? Math.round((completed / enabled) * 100) : 0;
  const bytes = new TextEncoder().encode(exportJsonString.value).length;
  const sizeKb = bytes / 1024;
  const sizeLabel = sizeKb >= 10
    ? `${sizeKb.toFixed(0)} KB`
    : `${sizeKb.toFixed(1)} KB`;
  return {
    total,
    enabled,
    enabledPct,
    completed,
    progressPct,
    sizeLabel,
    updatedAt: store.current?.updated_at || null,
  };
});

const jsonCopied = ref(false);
let jsonCopiedTimer = null;

async function refreshExportJson() {
  // Pull a fresh copy from the server; store mutation re-renders the computed.
  await store.fetchDetail(id.value);
}

async function copyExportJson() {
  try {
    await navigator.clipboard.writeText(exportJsonString.value);
    jsonCopied.value = true;
    if (jsonCopiedTimer) clearTimeout(jsonCopiedTimer);
    jsonCopiedTimer = setTimeout(() => { jsonCopied.value = false; }, 1500);
  } catch (_) { /* ignore */ }
}

function downloadExportJson() {
  const text = exportJsonString.value;
  if (!text) return;
  const slug = (store.current?.title || `diagnostic-${id.value}`)
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'diagnostic';
  const blob = new Blob([text], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${slug}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const jsonImportRaw = ref('');
const jsonImportParsed = ref(null);
const jsonImportError = ref('');
const jsonImportFileName = ref('');
const jsonImportMsg = ref(null);

const jsonImportPreview = computed(() => {
  const p = jsonImportParsed.value;
  if (!p) return {};
  const meta = p.metadata || {};
  const client = meta.client || {};
  const amount = meta.investment_amount;
  const currency = meta.currency || '';
  return {
    clientName: client.name || '—',
    sectionCount: Array.isArray(p.sections) ? p.sections.length : 0,
    investment: amount ? `${formatMoney(amount)} ${currency}`.trim() : '',
  };
});

function parseImportJson() {
  jsonImportMsg.value = null;
  const raw = jsonImportRaw.value.trim();
  if (!raw) {
    jsonImportParsed.value = null;
    jsonImportError.value = '';
    return;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('El JSON raíz debe ser un objeto con `metadata` y `sections`.');
    }
    if (!Array.isArray(parsed.sections)) {
      throw new Error('`sections` debe ser un array.');
    }
    jsonImportParsed.value = parsed;
    jsonImportError.value = '';
  } catch (err) {
    jsonImportParsed.value = null;
    jsonImportError.value = `JSON inválido: ${err.message}`;
  }
}

function handleJsonFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  jsonImportFileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    jsonImportRaw.value = String(e.target?.result || '');
    parseImportJson();
  };
  reader.readAsText(file);
  event.target.value = '';
}

async function handleApplyImportJson() {
  if (!jsonImportParsed.value) return;
  jsonImportMsg.value = null;
  const { metadata = {}, sections = [] } = jsonImportParsed.value;

  const metaPayload = {};
  for (const k of METADATA_KEYS) {
    if (metadata[k] !== undefined) metaPayload[k] = metadata[k];
  }
  if (metadata.client?.id) metaPayload.client_id = metadata.client.id;

  let metaApplied = false;
  if (Object.keys(metaPayload).length) {
    const metaResult = await store.update(id.value, metaPayload);
    if (!metaResult.success) {
      jsonImportMsg.value = { type: 'error', text: metaResult.error || 'Error al actualizar metadata. Las secciones no se aplicaron.' };
      return;
    }
    metaApplied = true;
  }

  const sectionsPayload = sections.map((s) => ({
    id: s.id,
    title: s.title,
    order: s.order,
    is_enabled: s.is_enabled,
    visibility: s.visibility,
    content_json: s.content_json,
  }));
  const secResult = await store.bulkUpdateSections(id.value, sectionsPayload);
  if (!secResult.success) {
    const detail = secResult.error || 'error desconocido';
    jsonImportMsg.value = metaApplied
      ? { type: 'error', text: `Se aplicaron los datos generales, pero fallaron las secciones: ${detail}. Corrige el JSON y vuelve a aplicar — la metadata ya está actualizada.` }
      : { type: 'error', text: `Error al aplicar las secciones: ${detail}.` };
    return;
  }

  jsonImportMsg.value = { type: 'success', text: 'JSON aplicado correctamente.' };
  jsonImportRaw.value = '';
  jsonImportParsed.value = null;
  jsonImportFileName.value = '';
  syncFormGeneral();
}

// ── Activity ──────────────────────────────────────────────────────────
async function onLogActivity(payload) {
  const r = await store.logActivity(id.value, payload.change_type, payload.description);
  showToast(r.success ? 'Actividad registrada.' : (r.error || 'Error al registrar.'), r.success ? 'success' : 'error');
}

// ── Transitions ───────────────────────────────────────────────────────
function onSendInitial() {
  requestConfirm({
    title: 'Enviar envío inicial',
    message: '¿Enviar el envío inicial al cliente por email y marcar el diagnóstico como «Enviado»?',
    variant: 'info',
    confirmText: 'Enviar',
    onConfirm: async () => {
      const r = await store.sendInitial(id.value);
      showToast(r.success ? 'Envío inicial entregado.' : (r.message || r.error || 'Error al enviar.'), r.success ? 'success' : 'error');
    },
  });
}

function onMarkAnalysis() {
  requestConfirm({
    title: 'Marcar en análisis',
    message: '¿Confirmar que el cliente autorizó? Se moverá a «En negociación».',
    variant: 'warning',
    confirmText: 'Confirmar',
    onConfirm: async () => {
      const r = await store.markInAnalysis(id.value);
      showToast(r.success ? 'Diagnóstico en negociación.' : (r.message || r.error || 'Error.'), r.success ? 'success' : 'error');
    },
  });
}

function onSendFinal() {
  requestConfirm({
    title: 'Enviar diagnóstico final',
    message: '¿Enviar el diagnóstico final al cliente?',
    variant: 'info',
    confirmText: 'Enviar',
    onConfirm: async () => {
      const r = await store.sendFinal(id.value);
      showToast(r.success ? 'Diagnóstico final enviado.' : (r.message || r.error || 'Error al enviar.'), r.success ? 'success' : 'error');
    },
  });
}

function onDelete() {
  requestConfirm({
    title: 'Eliminar diagnóstico',
    message: '¿Eliminar este diagnóstico? Esta acción no se puede deshacer.',
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const r = await store.remove(id.value);
      if (r?.success) {
        router.push(localePath('/panel/diagnostics'));
      } else {
        showToast(r?.error || 'Error al eliminar.', 'error');
      }
    },
  });
}

onMounted(() => store.fetchDetail(id.value));
onUnmounted(() => {
  if (urlCopiedTimer) clearTimeout(urlCopiedTimer);
  if (jsonCopiedTimer) clearTimeout(jsonCopiedTimer);
});
</script>
