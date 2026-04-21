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
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
      Configura los valores iniciales que se aplicarán a las nuevas propuestas.
    </p>

    <!-- Tabs -->
    <ResponsiveTabs v-model="activeTab" :tabs="tabs" />

    <!-- ═══ TAB: Vista General ═══ -->
    <div v-show="activeTab === 'general'" class="max-w-2xl">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Estos son los valores por defecto que se aplican al crear una nueva propuesta. Puedes modificarlos aquí para que se pre-llenen automáticamente.
      </p>
      <form class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 sm:p-8 space-y-6" @submit.prevent="handleSaveGeneral">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma por defecto</label>
            <select v-model="generalForm.language"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white dark:bg-gray-700 dark:text-gray-100">
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Moneda</label>
            <select v-model="generalForm.currency"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white dark:bg-gray-700 dark:text-gray-100">
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Inversión total por defecto</label>
            <input v-model.number="generalForm.total_investment" type="number" min="0" step="0.01"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hosting (% de inversión)</label>
            <div class="flex items-center gap-3">
              <input v-model.number="generalForm.hosting_percent" type="number" min="0" max="100"
                class="w-32 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
              <span class="text-sm text-gray-500 dark:text-green-light/60">%</span>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dcto. semestral hosting (%)</label>
            <input v-model.number="generalForm.hosting_discount_semiannual" type="number" min="0" max="100"
              class="w-32 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dcto. trimestral hosting (%)</label>
            <input v-model.number="generalForm.hosting_discount_quarterly" type="number" min="0" max="100"
              class="w-32 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Recordatorio (días después de enviar)</label>
            <input v-model.number="generalForm.reminder_days" type="number" min="1" max="30"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Urgencia (días después de enviar)</label>
            <input v-model.number="generalForm.urgency_reminder_days" type="number" min="1" max="30"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fecha de expiración</label>
          <div class="flex items-center gap-3">
            <input v-model.number="generalForm.expiration_days" type="number" min="1" max="365"
              class="w-32 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
            <span class="text-sm text-gray-500">días</span>
          </div>
          <p class="text-xs text-gray-400 mt-1">3 semanas = 21 días.</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descuento por defecto (%)</label>
          <input v-model.number="generalForm.discount_percent" type="number" min="0" max="100"
            class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100" />
          <p class="text-xs text-gray-400 mt-1">0 = sin descuento en email de urgencia.</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Patrón de URL personalizada</label>
          <input
            v-model="generalForm.default_slug_pattern"
            type="text"
            data-testid="defaults-slug-pattern"
            class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-mono focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
            placeholder="{client_name}"
          />
          <p class="text-xs text-gray-400 mt-1">
            Placeholders: <code class="px-1 bg-gray-100 dark:bg-gray-700 rounded">{client_name}</code>,
            <code class="px-1 bg-gray-100 dark:bg-gray-700 rounded">{project_type}</code>,
            <code class="px-1 bg-gray-100 dark:bg-gray-700 rounded">{year}</code>.
            Se aplica al crear una propuesta si el vendedor no escribe una URL manualmente.
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Vista previa: <span class="font-mono text-emerald-600 dark:text-emerald-400">/proposal/{{ slugPatternPreview }}</span>
          </p>
        </div>
        <div class="flex items-center gap-3 pt-2">
          <button type="submit" :disabled="isSaving"
            class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50">
            {{ isSaving ? 'Guardando...' : 'Guardar Vista General' }}
          </button>
        </div>
      </form>
    </div>

    <!-- ═══ TAB: Secciones ═══ -->
    <div v-show="activeTab === 'sections'">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4 max-w-3xl">
        Edita las secciones comerciales del modelo por defecto. El
        <strong class="text-gray-700 dark:text-gray-300">detalle técnico</strong>
        (<code class="text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">technical_document</code>)
        tiene su propia pestaña <strong class="text-gray-700 dark:text-gray-300">Det. técnico</strong>
        con editor estructurado y JSON, igual que al editar una propuesta.
      </p>
      <!-- Language selector -->
      <div class="mb-6 flex items-center gap-3">
        <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Idioma:</span>
        <div class="flex gap-2">
          <button
            v-for="opt in languageOptions"
            :key="opt.value"
            type="button"
            class="px-4 py-2 rounded-xl text-sm font-medium border transition-colors"
            :class="selectedLang === opt.value
              ? 'bg-emerald-600 text-white border-emerald-600'
              : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600'"
            @click="switchLanguage(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
        <span v-if="configUpdatedAt" class="text-[11px] text-gray-400 ml-4">
          Última actualización: {{ formatDate(configUpdatedAt) }}
        </span>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-12 text-gray-400 text-sm">
        Cargando configuración...
      </div>

      <!-- Sections list (commercial only; technical → tab Det. técnico) -->
      <div v-else-if="sections.length" class="space-y-3">
        <div
          v-for="{ section, idx } in commercialDefaultsEntries"
          :key="`${selectedLang}-${section.section_type}-${idx}`"
          class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden"
        >
          <div
            class="px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            @click="toggleSection(idx)"
          >
            <div class="flex items-center gap-4">
              <span class="text-xs text-gray-400 font-mono w-6">{{ section.order + 1 }}</span>
              <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ section.title }}</span>
              <span class="text-xs text-gray-400">({{ section.section_type }})</span>
            </div>
            <div class="flex items-center gap-3">
              <span
                v-if="savedSections.has(idx)"
                class="text-xs text-emerald-600 font-medium"
              >✓ Modificado</span>
              <button
                type="button"
                class="p-1.5 rounded-lg text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
                title="Vista previa"
                @click.stop="handleSectionPreview(idx)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              <svg
                class="w-4 h-4 text-gray-400 transition-transform"
                :class="{ 'rotate-180': expandedSections.has(idx) }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div v-if="expandedSections.has(idx)" class="border-t border-gray-100 dark:border-gray-700 px-3 sm:px-6 py-4 sm:py-6">
            <SectionEditor
              :key="`editor-${selectedLang}-${section.section_type}-${idx}`"
              :section="toVirtualSection(section, idx)"
              :proposalData="{}"
              :all-sections="sections"
              @save="handleSaveSection"
            />
          </div>
        </div>
      </div>

      <div v-else class="text-center py-16">
        <p class="text-gray-500 text-sm">No se encontraron secciones por defecto.</p>
      </div>

      <!-- Sticky action bar for sections -->
      <div v-if="sections.length && !isLoading" class="sticky bottom-0 mt-6 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm border border-gray-100 dark:border-gray-700 rounded-xl shadow-lg px-5 py-3 flex flex-col sm:flex-row items-center justify-between gap-3 z-10">
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <span v-if="savedSections.size > 0" class="text-emerald-600 font-medium">
            {{ savedSections.size }} sección(es) modificada(s)
          </span>
          <span v-else>Sin cambios pendientes</span>
        </div>
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="px-5 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-colors"
            :disabled="isSaving"
            @click="handleReset"
          >
            Restaurar valores originales
          </button>
          <button
            type="button"
            class="px-5 py-2 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
            :disabled="savedSections.size === 0 || isSaving"
            @click="handleSaveAll"
          >
            {{ isSaving ? 'Guardando...' : 'Guardar Todos los Cambios' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ TAB: Det. técnico (misma UX que editar propuesta) ═══ -->
    <div v-show="activeTab === 'technical'" class="max-w-5xl">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Valores por defecto del bloque técnico (nuevas propuestas). Idioma actual:
        <strong>{{ selectedLang === 'es' ? 'Español' : 'English' }}</strong> — cambia el idioma en la pestaña Secciones si necesitas la otra plantilla.
      </p>
      <div class="flex gap-1 mb-4 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 max-w-sm">
        <button
          type="button"
          :class="[
            'flex-1 px-3 py-2 text-sm rounded-lg transition-all',
            defaultsTechnicalSubTab === 'editor'
              ? 'bg-white dark:bg-gray-700 shadow-sm font-medium text-gray-900 dark:text-gray-100'
              : 'text-gray-500',
          ]"
          @click="defaultsTechnicalSubTab = 'editor'"
        >
          Editor
        </button>
        <button
          type="button"
          :class="[
            'flex-1 px-3 py-2 text-sm rounded-lg transition-all',
            defaultsTechnicalSubTab === 'json'
              ? 'bg-white dark:bg-gray-700 shadow-sm font-medium text-gray-900 dark:text-gray-100'
              : 'text-gray-500',
          ]"
          @click="defaultsTechnicalSubTab = 'json'"
        >
          JSON
        </button>
      </div>

      <div v-show="defaultsTechnicalSubTab === 'editor'">
        <p
          v-if="technicalDocumentIndex < 0"
          class="text-sm text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg px-4 py-3"
        >
          No hay sección <code class="text-xs">technical_document</code> en la plantilla.
          Restaura valores originales desde Secciones o añade la entrada en la pestaña JSON.
        </p>
        <div v-else class="defaults-technical-editor">
          <TechnicalDocumentEditor
            :key="`defaults-tech-${selectedLang}-${technicalDocumentIndex}`"
            :section="technicalDefaultVirtualSection"
            @save="handleSaveSection"
          />
        </div>
      </div>

      <div v-show="defaultsTechnicalSubTab === 'json'" class="space-y-4">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Solo el objeto <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">content_json</code> del detalle técnico. Mismo esquema que en el editor. Pulsa «Aplicar» para actualizar la plantilla en memoria; luego
          <strong>Guardar todos los cambios</strong> en Secciones o guarda desde JSON global.
        </p>
        <textarea
          v-model="defaultsTechnicalJsonRaw"
          rows="24"
          class="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-xl text-xs font-mono bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200 resize-y outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <div v-if="defaultsTechnicalJsonError" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
          {{ defaultsTechnicalJsonError }}
        </div>
        <div
          v-if="defaultsTechnicalJsonMsg"
          class="text-sm px-4 py-2 rounded-lg"
          :class="defaultsTechnicalJsonMsg.type === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-50 text-red-600'"
        >
          {{ defaultsTechnicalJsonMsg.text }}
        </div>
        <button
          type="button"
          class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700"
          @click="handleApplyDefaultsTechnicalJson"
        >
          Aplicar a plantilla
        </button>
      </div>
    </div>

    <!-- ═══ TAB: Plantillas de Email ═══ -->
    <div v-show="activeTab === 'emails'">
      <!-- Category filter -->
      <div class="mb-6 flex flex-wrap items-center gap-3">
        <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Filtrar:</span>
        <button
          v-for="cat in emailCategoryOptions"
          :key="cat.value"
          type="button"
          class="px-4 py-2 rounded-xl text-sm font-medium border transition-colors"
          :class="emailSelectedCategory === cat.value
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:border-gray-500'"
          @click="emailSelectedCategory = cat.value"
        >
          {{ cat.label }}
          <span class="ml-1 text-xs opacity-70">({{ countByCategory(cat.value) }})</span>
        </button>
      </div>

      <div v-if="emailIsLoading" class="text-center py-12 text-gray-400 text-sm">
        Cargando plantillas...
      </div>

      <div v-else-if="filteredEmailTemplates.length" class="space-y-3">
        <div
          v-for="tpl in filteredEmailTemplates"
          :key="tpl.template_key"
          class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden"
        >
          <div
            class="px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            @click="toggleEmailTemplate(tpl.template_key)"
          >
            <div class="flex items-center gap-3 min-w-0">
              <span class="text-lg flex-shrink-0">{{ emailCategoryIcon(tpl.category) }}</span>
              <div class="min-w-0">
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100 block truncate">{{ tpl.name }}</span>
                <span class="text-xs text-gray-400 block truncate">{{ tpl.description }}</span>
              </div>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
              <span v-if="tpl.is_customized" class="text-xs text-emerald-600 font-medium bg-emerald-50 px-2 py-0.5 rounded-full">Personalizado</span>
              <span v-if="!tpl.is_active" class="text-xs text-red-600 font-medium bg-red-50 px-2 py-0.5 rounded-full">Desactivado</span>
              <span class="text-xs text-gray-400">{{ tpl.editable_fields_count }} campos</span>
              <button
                type="button"
                class="p-1.5 rounded-lg text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
                title="Vista previa"
                :disabled="emailIsPreviewLoading"
                @click.stop="handleEmailPreview(tpl.template_key)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              <svg
                class="w-4 h-4 text-gray-400 transition-transform"
                :class="{ 'rotate-180': emailExpandedTemplate === tpl.template_key }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <!-- Expanded editor -->
          <div v-if="emailExpandedTemplate === tpl.template_key" class="border-t border-gray-100 dark:border-gray-700">
            <div v-if="emailIsLoadingDetail" class="px-6 py-8 text-center text-gray-400 text-sm">
              Cargando campos editables...
            </div>
            <div v-else-if="emailTemplateDetail" class="px-4 sm:px-6 py-4 sm:py-6 space-y-5">
              <!-- Active toggle -->
              <div class="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-700">
                <div>
                  <span class="text-sm font-medium text-gray-900 dark:text-gray-100">Estado del email</span>
                  <p class="text-xs text-gray-400 mt-0.5">Desactiva para dejar de enviar este correo.</p>
                </div>
                <button
                  type="button"
                  class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                  :class="emailEditIsActive ? 'bg-emerald-600' : 'bg-gray-200'"
                  @click="emailEditIsActive = !emailEditIsActive"
                >
                  <span
                    class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                    :class="emailEditIsActive ? 'translate-x-5' : 'translate-x-0'"
                  />
                </button>
              </div>

              <!-- Editable fields -->
              <div v-for="field in emailTemplateDetail.editable_fields" :key="field.key" class="space-y-1.5">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    {{ field.label }}
                    <span v-if="field.is_overridden" class="text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full normal-case tracking-normal">modificado</span>
                  </label>
                  <button
                    v-if="emailEditFields[field.key] && emailEditFields[field.key] !== field.default_value"
                    type="button"
                    class="text-[10px] text-gray-400 hover:text-red-500 transition-colors"
                    @click="emailEditFields[field.key] = field.default_value || ''"
                  >restaurar campo</button>
                </div>
                <input
                  v-if="field.type === 'text'"
                  v-model="emailEditFields[field.key]"
                  type="text"
                  class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-gray-100 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors dark:bg-gray-700"
                  :placeholder="field.default_value"
                  :ref="el => { if (el) emailFieldRefs[field.key] = el }"
                  @focus="emailLastFocusedField = field.key"
                />
                <textarea
                  v-else
                  v-model="emailEditFields[field.key]"
                  rows="3"
                  class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-gray-100 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors resize-y dark:bg-gray-700"
                  :placeholder="field.default_value"
                  :ref="el => { if (el) emailFieldRefs[field.key] = el }"
                  @focus="emailLastFocusedField = field.key"
                />
                <p v-if="field.default_value" class="text-[11px] text-gray-400">
                  Por defecto: {{ truncateText(field.default_value, 100) }}
                </p>
              </div>

              <!-- Available variables -->
              <div v-if="emailTemplateDetail.available_variables?.length" class="pt-3 border-t border-gray-100 dark:border-gray-700">
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Variables disponibles
                  <span v-if="emailLastFocusedField" class="text-emerald-500 font-normal">(click para insertar en {{ emailLastFocusedField }})</span>
                  <span v-else class="text-gray-400 font-normal">(haz clic en un campo primero)</span>
                </p>
                <div class="flex flex-wrap gap-1.5">
                  <code
                    v-for="v in emailTemplateDetail.available_variables"
                    :key="v"
                    class="text-[11px] bg-gray-100 text-gray-600 px-2 py-1 rounded-lg cursor-pointer hover:bg-emerald-50 hover:text-emerald-700 transition-colors dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-emerald-900/30 dark:hover:text-emerald-400"
                    @click="emailInsertVariable(v)"
                  >
                    {<span>{{ v }}</span>}
                  </code>
                </div>
              </div>

              <!-- Action buttons -->
              <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
                <div class="flex items-center gap-2">
                  <button type="button" class="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-xl transition-colors" :disabled="emailIsPreviewLoading" @click="handleEmailPreview(tpl.template_key)">
                    {{ emailIsPreviewLoading ? 'Cargando...' : '👁 Vista previa' }}
                  </button>
                  <button type="button" class="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-colors" @click="handleResetEmailTemplate(tpl.template_key)">
                    Restaurar
                  </button>
                </div>
                <button type="button" class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50" :disabled="isSaving" @click="handleSaveEmailTemplate(tpl.template_key)">
                  {{ isSaving ? 'Guardando...' : 'Guardar Cambios' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-16">
        <p class="text-gray-500 text-sm">No se encontraron plantillas de email.</p>
      </div>
    </div>

    <!-- ═══ TAB: Prompt IA ═══ -->
    <div v-show="activeTab === 'prompt'" class="max-w-4xl">
      <PromptSubTabsPanel v-model="defaultsPromptSubTab" dark-track>
        <template #commercial>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Este prompt se usa con IA (ChatGPT, Claude, etc.) para generar propuestas comerciales personalizadas a partir del JSON plantilla.
          El detalle técnico por defecto se edita en la pestaña <strong class="text-gray-600 dark:text-gray-300">Det. técnico</strong>;
          para la IA solo técnica usa la subpestaña <strong class="text-gray-600 dark:text-gray-300">Técnico</strong> aquí abajo.
        </p>

        <!-- Action bar -->
        <div class="flex flex-wrap items-center gap-2 mb-4">
          <template v-if="!promptIsEditing">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="startEditPrompt"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              Editar
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="handleCopyPrompt"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              {{ promptCopied ? '¡Copiado!' : 'Copiar' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="promptDownload"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              Descargar .md
            </button>
            <button
              v-if="promptText !== promptDefault"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              @click="handleResetPrompt"
            >
              Restaurar original
            </button>
          </template>
          <template v-else>
            <button
              type="button"
              class="px-5 py-2 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
              @click="saveEditPrompt"
            >
              Guardar cambios
            </button>
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              @click="cancelEditPrompt"
            >
              Cancelar
            </button>
          </template>
        </div>

        <!-- Editing mode -->
        <div v-if="promptIsEditing" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <textarea
            v-model="promptEditBuffer"
            rows="30"
            class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-gray-800 dark:text-gray-200 bg-transparent border-0 outline-none resize-y focus:ring-0"
          ></textarea>
        </div>

        <!-- Read-only mode -->
        <div v-else class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
            <pre class="text-xs leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono break-words">{{ promptText }}</pre>
          </div>
        </div>

        <p v-if="promptText !== promptDefault" class="text-xs text-amber-600 mt-3">
          Este prompt ha sido personalizado. Usa "Restaurar original" para volver al valor por defecto.
        </p>
        </template>

        <template #technical>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Prompt para generar la clave <code class="text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">technicalDocument</code> (arquitectura, módulos del producto, requerimientos). Sin narrativa comercial ni precios.
          La estructura por defecto del detalle técnico está en la pestaña <strong class="text-gray-600 dark:text-gray-300">Det. técnico</strong> (editor o JSON) y en la pestaña <strong class="text-gray-600 dark:text-gray-300">JSON</strong> global.
        </p>
        <div class="flex flex-wrap items-center gap-2 mb-4">
          <template v-if="!technicalDefaultsPromptIsEditing">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="startEditTechnicalDefaultsPrompt"
            >
              Editar
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="handleCopyTechnicalDefaultsPrompt"
            >
              {{ technicalDefaultsPromptCopied ? '¡Copiado!' : 'Copiar' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="technicalDefaultsPromptDownload"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              Descargar .md
            </button>
            <button
              v-if="technicalDefaultsPromptText !== technicalDefaultsPromptDefault"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              @click="handleResetTechnicalDefaultsPrompt"
            >
              Restaurar original
            </button>
          </template>
          <template v-else>
            <button
              type="button"
              class="px-5 py-2 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
              @click="saveEditTechnicalDefaultsPrompt"
            >
              Guardar cambios
            </button>
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              @click="cancelEditTechnicalDefaultsPrompt"
            >
              Cancelar
            </button>
          </template>
        </div>
        <div v-if="technicalDefaultsPromptIsEditing" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <textarea
            v-model="technicalDefaultsPromptEditBuffer"
            rows="28"
            class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-gray-800 dark:text-gray-200 bg-transparent border-0 outline-none resize-y focus:ring-0"
          ></textarea>
        </div>
        <div v-else class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
            <pre class="text-xs leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono break-words">{{ technicalDefaultsPromptText }}</pre>
          </div>
        </div>
        <p v-if="technicalDefaultsPromptText !== technicalDefaultsPromptDefault" class="text-xs text-amber-600 mt-3">
          Prompt técnico personalizado. «Restaurar original» vuelve al valor por defecto.
        </p>
        </template>
      </PromptSubTabsPanel>
    </div>

    <!-- ═══ TAB: JSON ═══ -->
    <div v-show="activeTab === 'json'" class="max-w-4xl">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">
        Representación JSON de la configuración por defecto (secciones plantilla). Puedes editar directamente el JSON y guardar los cambios.
      </p>
      <ul class="text-xs text-gray-500 dark:text-gray-400 mb-4 list-disc list-inside space-y-1">
        <li>
          Debe existir una entrada con <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">section_type: &quot;technical_document&quot;</code> y su
          <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">content_json</code> (arquitectura, módulos del producto, <code class="text-[10px]">epicKey</code> / <code class="text-[10px]">flowKey</code>, etc.).
        </li>
        <li>
          Al importar una propuesta desde JSON global, la clave camelCase es <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">technicalDocument</code> — distinta de este formato de plantilla.
        </li>
      </ul>
      <p
        v-if="defaultsTechnicalEpicCount !== null"
        class="text-xs text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20 border border-teal-100 dark:border-teal-800 rounded-lg px-3 py-2 mb-4"
      >
        Vista rápida: <strong>{{ defaultsTechnicalEpicCount }}</strong> módulo(s) en el detalle técnico por defecto (idioma {{ selectedLang }}).
      </p>

      <!-- Action bar -->
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <template v-if="!jsonIsEditing">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="startEditJson"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            Editar
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="copyDefaultsJson"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            {{ defaultsJsonCopied ? '¡Copiado!' : 'Copiar' }}
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="downloadDefaultsJson"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            Descargar .json
          </button>
        </template>
        <template v-else>
          <button
            type="button"
            class="px-5 py-2 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
            :disabled="isSaving"
            @click="saveEditJson"
          >
            {{ isSaving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            @click="cancelEditJson"
          >
            Cancelar
          </button>
        </template>
      </div>

      <div v-if="defaultsJsonLoading" class="text-center py-8 text-gray-400 text-sm">
        Cargando JSON...
      </div>

      <!-- Editing mode -->
      <div v-else-if="jsonIsEditing" class="space-y-2">
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <textarea
            v-model="jsonEditBuffer"
            rows="24"
            class="w-full px-4 py-3 border-0 text-xs font-mono leading-relaxed
                   bg-transparent text-gray-800 dark:text-gray-200 outline-none resize-y focus:ring-0"
          />
        </div>
        <p v-if="jsonEditError" class="text-xs text-red-600 dark:text-red-400 px-1">
          {{ jsonEditError }}
        </p>
      </div>

      <!-- Read-only mode -->
      <div v-else class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div class="px-4 py-3 max-h-[70vh] overflow-y-auto">
          <pre class="text-xs leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono break-words">{{ defaultsJsonString }}</pre>
        </div>
      </div>
    </div>

    <!-- ═══ Shared modals ═══ -->

    <!-- Email preview modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div v-if="emailShowPreview" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" @click.self="emailShowPreview = false">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Vista Previa</h3>
                <p v-if="emailPreviewSubject" class="text-xs text-gray-500 mt-0.5 truncate max-w-md">Asunto: {{ emailPreviewSubject }}</p>
              </div>
              <button class="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors" @click="emailShowPreview = false">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <div class="flex-1 overflow-auto">
              <iframe v-if="emailPreviewHtml" :srcdoc="emailPreviewHtml" class="w-full h-full min-h-[500px] border-0" sandbox="allow-same-origin" />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Email reset confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div v-if="emailShowResetConfirm" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" @click.self="emailShowResetConfirm = false">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center">
            <div class="text-4xl mb-3">⚠️</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">¿Restaurar valores originales?</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Esto eliminará las personalizaciones de esta plantilla y volverá al contenido por defecto del sistema.</p>
            <div class="flex gap-3 justify-center">
              <button class="px-6 py-2.5 bg-red-600 text-white rounded-xl font-medium text-sm hover:bg-red-700 transition-colors" :disabled="isSaving" @click="confirmResetEmailTemplate">
                {{ isSaving ? 'Restaurando...' : 'Sí, restaurar' }}
              </button>
              <button class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="emailShowResetConfirm = false">Cancelar</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Section reset confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="showResetConfirm"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="showResetConfirm = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center">
            <div class="text-4xl mb-3">⚠️</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">¿Restaurar valores originales?</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Esto eliminará toda la configuración personalizada para <strong>{{ selectedLang === 'es' ? 'Español' : 'English' }}</strong>
              y volverá a los valores del sistema. Las propuestas existentes no se verán afectadas.
            </p>
            <div class="flex gap-3 justify-center">
              <button
                class="px-6 py-2.5 bg-red-600 text-white rounded-xl font-medium text-sm hover:bg-red-700 transition-colors"
                :disabled="isSaving"
                @click="confirmReset"
              >
                {{ isSaving ? 'Restaurando...' : 'Sí, restaurar' }}
              </button>
              <button
                class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
                @click="showResetConfirm = false"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Section preview modal -->
    <SectionPreviewModal
      :visible="showSectionPreview"
      :section="previewSection"
      :proposalData="{}"
      @close="showSectionPreview = false"
    />

    <!-- Feedback messages -->
    <Transition name="fade-modal">
      <div v-if="feedbackMsg" class="fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg text-sm font-medium"
        :class="feedbackType === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'"
      >
        {{ feedbackMsg }}
      </div>
    </Transition>

    <!-- Floating refresh button -->
    <button
      type="button"
      class="fixed bottom-[68px] right-6 z-50 w-12 h-12 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:opacity-50 flex items-center justify-center dark:bg-emerald-700 dark:hover:bg-emerald-600"
      :disabled="isRefreshing"
      :title="isRefreshing ? 'Actualizando...' : 'Actualizar datos'"
      @click="refreshData"
    >
      <svg class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import SectionEditor from '~/components/BusinessProposal/admin/SectionEditor.vue';
import TechnicalDocumentEditor from '~/components/BusinessProposal/admin/TechnicalDocumentEditor.vue';
import SectionPreviewModal from '~/components/BusinessProposal/admin/SectionPreviewModal.vue';
import PromptSubTabsPanel from '~/components/panel/PromptSubTabsPanel.vue';
import ResponsiveTabs from '~/components/ui/ResponsiveTabs.vue';
import { useSellerPrompt } from '~/composables/useSellerPrompt';
import { useTechnicalPrompt } from '~/composables/useTechnicalPrompt';
import { useConfirmModal } from '~/composables/useConfirmModal';


const proposalStore = useProposalStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const tabs = [
  { id: 'general', label: 'Vista General' },
  { id: 'sections', label: 'Secciones' },
  { id: 'technical', label: 'Det. técnico' },
  { id: 'emails', label: 'Plantillas de Email' },
  { id: 'prompt', label: 'Prompt Proposal' },
  { id: 'json', label: 'JSON' },
];
const route = useRoute();
const initialTab = ['general', 'sections', 'technical', 'emails', 'prompt', 'json'].includes(route.query.tab)
  ? route.query.tab
  : 'general';
const activeTab = ref(initialTab);

const languageOptions = [
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
];

// ── Shared state ──
const isRefreshing = ref(false);
const isSaving = ref(false);
const feedbackMsg = ref('');
const feedbackType = ref('success');

function showFeedback(msg, type = 'success') {
  feedbackMsg.value = msg;
  feedbackType.value = type;
  setTimeout(() => { feedbackMsg.value = ''; }, 3500);
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
}

// ── Vista General ──
const generalForm = ref({
  language: 'es',
  currency: 'COP',
  total_investment: 0,
  hosting_percent: 30,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  expiration_days: 21,
  reminder_days: 3,
  urgency_reminder_days: 7,
  discount_percent: 0,
  default_slug_pattern: '{client_name}',
});

const slugPatternPreview = computed(() => {
  const pattern = (generalForm.value.default_slug_pattern || '').trim() || '{client_name}';
  const sample = {
    '{client_name}': 'María López',
    '{project_type}': 'E-commerce',
    '{year}': String(new Date().getFullYear()),
  };
  let rendered = pattern;
  for (const [key, val] of Object.entries(sample)) rendered = rendered.split(key).join(val);
  return rendered
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 120) || 'propuesta';
});

async function handleSaveGeneral() {
  isSaving.value = true;
  try {
    const result = await proposalStore.saveProposalDefaults(
      generalForm.value.language,
      null,
      generalForm.value,
    );
    if (result.success) {
      if (generalForm.value.language !== selectedLang.value) {
        selectedLang.value = generalForm.value.language;
        await loadDefaults(selectedLang.value);
      }
      showFeedback('Valores generales guardados correctamente.', 'success');
    } else {
      showFeedback('Error al guardar los valores generales.', 'error');
    }
  } finally {
    isSaving.value = false;
  }
}

// ── Secciones ──
const selectedLang = ref('es');
const sections = ref([]);
const configUpdatedAt = ref(null);
const isLoading = ref(false);
const expandedSections = ref(new Set());
const savedSections = ref(new Set());
const showResetConfirm = ref(false);
const showSectionPreview = ref(false);
const previewSection = ref({});

/** Commercial sections only — technical defaults live in tab Det. técnico. */
const commercialDefaultsEntries = computed(() =>
  sections.value.map((section, idx) => ({ section, idx })).filter(
    ({ section }) => section.section_type !== 'technical_document',
  ),
);

const technicalDocumentIndex = computed(() =>
  sections.value.findIndex((s) => s.section_type === 'technical_document'),
);

const technicalDefaultVirtualSection = computed(() => {
  const idx = technicalDocumentIndex.value;
  if (idx < 0) return null;
  return toVirtualSection(sections.value[idx], idx);
});

const defaultsTechnicalSubTab = ref('editor');
const defaultsTechnicalJsonRaw = ref('{}');
const defaultsTechnicalJsonError = ref('');
const defaultsTechnicalJsonMsg = ref(null);

const defaultsTechnicalEpicCount = computed(() => {
  const idx = technicalDocumentIndex.value;
  if (idx < 0) return null;
  const epics = sections.value[idx]?.content_json?.epics;
  if (!Array.isArray(epics)) return 0;
  return epics.length;
});

function refreshDefaultsTechnicalJson() {
  defaultsTechnicalJsonError.value = '';
  defaultsTechnicalJsonMsg.value = null;
  const idx = technicalDocumentIndex.value;
  if (idx < 0) {
    defaultsTechnicalJsonRaw.value = '{}';
    return;
  }
  const cj = sections.value[idx]?.content_json;
  try {
    defaultsTechnicalJsonRaw.value = JSON.stringify(
      cj && typeof cj === 'object' ? cj : {},
      null,
      2,
    );
  } catch {
    defaultsTechnicalJsonRaw.value = '{}';
  }
}

function handleApplyDefaultsTechnicalJson() {
  defaultsTechnicalJsonError.value = '';
  defaultsTechnicalJsonMsg.value = null;
  const idx = technicalDocumentIndex.value;
  if (idx < 0) {
    defaultsTechnicalJsonError.value = 'No hay sección technical_document en la plantilla.';
    return;
  }
  let parsed;
  try {
    parsed = JSON.parse(defaultsTechnicalJsonRaw.value.trim());
  } catch (e) {
    defaultsTechnicalJsonError.value = `JSON inválido: ${e.message}`;
    return;
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    defaultsTechnicalJsonError.value = 'El contenido debe ser un objeto JSON.';
    return;
  }
  sections.value[idx] = {
    ...sections.value[idx],
    content_json: parsed,
  };
  savedSections.value = new Set([...savedSections.value, idx]);
  defaultsTechnicalJsonMsg.value = {
    type: 'success',
    text: 'Plantilla técnica actualizada en memoria. Usa «Guardar todos los cambios» en Secciones (o guarda desde JSON global).',
  };
}

watch(defaultsTechnicalSubTab, (sub) => {
  if (sub === 'json') {
    refreshDefaultsTechnicalJson();
  }
});

watch(activeTab, (tab) => {
  if (tab === 'technical' && defaultsTechnicalSubTab.value === 'json') {
    refreshDefaultsTechnicalJson();
  }
});

function handleSectionPreview(idx) {
  if (idx >= 0 && idx < sections.value.length) {
    previewSection.value = toVirtualSection(sections.value[idx], idx);
    showSectionPreview.value = true;
  }
}

function toVirtualSection(section, idx) {
  return {
    id: `default-${idx}`,
    section_type: section.section_type,
    title: section.title,
    content_json: section.content_json || {},
    is_wide_panel: section.is_wide_panel || false,
    is_enabled: true,
  };
}

function toggleSection(idx) {
  const s = new Set(expandedSections.value);
  if (s.has(idx)) s.delete(idx);
  else s.add(idx);
  expandedSections.value = s;
}

function handleSaveSection({ sectionId, payload }) {
  const idx = typeof sectionId === 'string' && sectionId.startsWith('default-')
    ? parseInt(sectionId.replace('default-', ''), 10)
    : sectionId;

  if (idx >= 0 && idx < sections.value.length) {
    sections.value[idx] = {
      ...sections.value[idx],
      title: payload.title,
      content_json: payload.content_json,
    };
    savedSections.value = new Set([...savedSections.value, idx]);
    showFeedback('Sección actualizada localmente. Guarda todos los cambios para persistir.', 'success');
  }
}

async function loadDefaults(lang) {
  isLoading.value = true;
  expandedSections.value = new Set();
  savedSections.value = new Set();
  try {
    const result = await proposalStore.fetchProposalDefaults(lang);
    if (result.success && result.data) {
      sections.value = result.data.sections_json || [];
      configUpdatedAt.value = result.data.updated_at;
      generalForm.value = {
        ...generalForm.value,
        language: lang,
        expiration_days: Number.isInteger(Number(result.data.expiration_days))
          ? Number(result.data.expiration_days)
          : 21,
        default_slug_pattern: typeof result.data.default_slug_pattern === 'string'
          ? result.data.default_slug_pattern
          : '{client_name}',
      };
    }
  } finally {
    isLoading.value = false;
  }
}

async function switchLanguage(lang) {
  if (lang === selectedLang.value) return;
  if (savedSections.value.size > 0) {
    requestConfirm({
      title: 'Cambios sin guardar',
      message: 'Tienes cambios sin guardar. ¿Deseas cambiar de idioma y perder los cambios?',
      variant: 'warning',
      confirmText: 'Cambiar idioma',
      onConfirm: async () => {
        selectedLang.value = lang;
        await loadDefaults(lang);
      },
    });
    return;
  }
  selectedLang.value = lang;
  await loadDefaults(lang);
}

async function handleSaveAll() {
  isSaving.value = true;
  try {
    const result = await proposalStore.saveProposalDefaults(selectedLang.value, sections.value);
    if (result.success) {
      savedSections.value = new Set();
      configUpdatedAt.value = result.data?.updated_at || new Date().toISOString();
      showFeedback('Valores por defecto guardados correctamente.', 'success');
    } else {
      showFeedback('Error al guardar los valores por defecto.', 'error');
    }
  } finally {
    isSaving.value = false;
  }
}

function handleReset() {
  showResetConfirm.value = true;
}

async function confirmReset() {
  isSaving.value = true;
  try {
    const result = await proposalStore.resetProposalDefaults(selectedLang.value);
    if (result.success) {
      showResetConfirm.value = false;
      savedSections.value = new Set();
      await loadDefaults(selectedLang.value);
      showFeedback('Valores restaurados a los originales del sistema.', 'success');
    } else {
      showFeedback('Error al restaurar los valores por defecto.', 'error');
    }
  } finally {
    isSaving.value = false;
  }
}

// ── Plantillas de Email ──
const emailCategoryOptions = [
  { value: 'all', label: 'Todos' },
  { value: 'client', label: 'Cliente' },
  { value: 'internal', label: 'Interno' },
  { value: 'contact', label: 'Contacto' },
];

const emailTemplates = ref([]);
const emailSelectedCategory = ref('all');
const emailExpandedTemplate = ref(null);
const emailTemplateDetail = ref(null);
const emailEditFields = ref({});
const emailEditIsActive = ref(true);
const emailIsLoading = ref(false);
const emailLastFocusedField = ref('');
const emailFieldRefs = ref({});
const emailIsLoadingDetail = ref(false);
const emailIsPreviewLoading = ref(false);
const emailShowPreview = ref(false);
const emailPreviewHtml = ref('');
const emailPreviewSubject = ref('');
const emailShowResetConfirm = ref(false);
const emailResetTargetKey = ref('');

const filteredEmailTemplates = computed(() => {
  if (emailSelectedCategory.value === 'all') return emailTemplates.value;
  return emailTemplates.value.filter(t => t.category === emailSelectedCategory.value);
});

function countByCategory(cat) {
  if (cat === 'all') return emailTemplates.value.length;
  return emailTemplates.value.filter(t => t.category === cat).length;
}

function emailInsertVariable(name) {
  const varText = `{${name}}`;
  if (emailLastFocusedField.value && emailEditFields.value[emailLastFocusedField.value] !== undefined) {
    emailEditFields.value[emailLastFocusedField.value] += varText;
    showFeedback(`Variable ${varText} insertada`, 'success');
  } else {
    navigator.clipboard?.writeText(varText);
    showFeedback(`Variable ${varText} copiada (selecciona un campo para insertar directamente)`, 'success');
  }
}

function emailCategoryIcon(cat) {
  const icons = { client: '📧', internal: '🔔', contact: '📨' };
  return icons[cat] || '📧';
}

function truncateText(str, len) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '...' : str;
}

async function toggleEmailTemplate(key) {
  if (emailExpandedTemplate.value === key) {
    emailExpandedTemplate.value = null;
    emailTemplateDetail.value = null;
    return;
  }
  emailExpandedTemplate.value = key;
  emailTemplateDetail.value = null;
  emailLastFocusedField.value = '';
  emailIsLoadingDetail.value = true;
  try {
    const result = await proposalStore.fetchEmailTemplateDetail(key);
    if (result.success) {
      emailTemplateDetail.value = result.data;
      emailEditIsActive.value = result.data.is_active;
      emailEditFields.value = {};
      for (const field of result.data.editable_fields) {
        emailEditFields.value[field.key] = field.current_value || '';
      }
    }
  } finally {
    emailIsLoadingDetail.value = false;
  }
}

async function handleSaveEmailTemplate(templateKey) {
  isSaving.value = true;
  try {
    const result = await proposalStore.saveEmailTemplate(templateKey, {
      content_overrides: emailEditFields.value,
      is_active: emailEditIsActive.value,
    });
    if (result.success) {
      showFeedback('Plantilla guardada correctamente.', 'success');
      await loadEmailTemplates();
    } else {
      showFeedback('Error al guardar la plantilla.', 'error');
    }
  } finally {
    isSaving.value = false;
  }
}

async function handleEmailPreview(templateKey) {
  emailIsPreviewLoading.value = true;
  try {
    const result = await proposalStore.previewEmailTemplate(templateKey);
    if (result.success) {
      emailPreviewHtml.value = result.data.html_preview;
      emailPreviewSubject.value = result.data.subject;
      emailShowPreview.value = true;
    } else {
      showFeedback('Error al generar la vista previa.', 'error');
    }
  } finally {
    emailIsPreviewLoading.value = false;
  }
}

function handleResetEmailTemplate(templateKey) {
  emailResetTargetKey.value = templateKey;
  emailShowResetConfirm.value = true;
}

async function confirmResetEmailTemplate() {
  isSaving.value = true;
  try {
    const result = await proposalStore.resetEmailTemplate(emailResetTargetKey.value);
    if (result.success) {
      emailShowResetConfirm.value = false;
      showFeedback('Plantilla restaurada a los valores originales.', 'success');
      await loadEmailTemplates();
      if (emailExpandedTemplate.value === emailResetTargetKey.value) {
        await toggleEmailTemplate(emailResetTargetKey.value);
        await toggleEmailTemplate(emailResetTargetKey.value);
      }
    } else {
      showFeedback('Error al restaurar la plantilla.', 'error');
    }
  } finally {
    isSaving.value = false;
  }
}

async function loadEmailTemplates() {
  emailIsLoading.value = true;
  try {
    const result = await proposalStore.fetchEmailTemplates();
    if (result.success) {
      emailTemplates.value = result.data;
    }
  } finally {
    emailIsLoading.value = false;
  }
}

// ── Prompt IA ──
const {
  promptText,
  isEditing: promptIsEditing,
  DEFAULT_PROMPT: promptDefault,
  loadSavedPrompt,
  savePrompt: promptSave,
  resetPrompt: promptReset,
  copyPrompt: promptCopy,
  downloadPrompt: promptDownload,
} = useSellerPrompt();

const promptEditBuffer = ref('');
const promptCopied = ref(false);

function startEditPrompt() {
  promptEditBuffer.value = promptText.value;
  promptIsEditing.value = true;
}

function cancelEditPrompt() {
  promptIsEditing.value = false;
}

function saveEditPrompt() {
  promptSave(promptEditBuffer.value);
  promptIsEditing.value = false;
  showFeedback('Prompt guardado correctamente.', 'success');
}

function handleResetPrompt() {
  promptReset();
  promptIsEditing.value = false;
  showFeedback('Prompt restaurado al valor original.', 'success');
}

async function handleCopyPrompt() {
  await promptCopy();
  promptCopied.value = true;
  setTimeout(() => { promptCopied.value = false; }, 2000);
  showFeedback('Prompt copiado al portapapeles.', 'success');
}

const defaultsPromptSubTab = ref('commercial');

const {
  promptText: technicalDefaultsPromptText,
  isEditing: technicalDefaultsPromptIsEditing,
  DEFAULT_PROMPT: technicalDefaultsPromptDefault,
  loadSavedPrompt: loadTechnicalDefaultsPrompt,
  savePrompt: technicalDefaultsPromptSave,
  resetPrompt: technicalDefaultsPromptReset,
  copyPrompt: technicalDefaultsPromptCopy,
  downloadPrompt: technicalDefaultsPromptDownload,
} = useTechnicalPrompt();

const technicalDefaultsPromptEditBuffer = ref('');
const technicalDefaultsPromptCopied = ref(false);

function startEditTechnicalDefaultsPrompt() {
  technicalDefaultsPromptEditBuffer.value = technicalDefaultsPromptText.value;
  technicalDefaultsPromptIsEditing.value = true;
}
function cancelEditTechnicalDefaultsPrompt() {
  technicalDefaultsPromptIsEditing.value = false;
}
function saveEditTechnicalDefaultsPrompt() {
  technicalDefaultsPromptSave(technicalDefaultsPromptEditBuffer.value);
  technicalDefaultsPromptIsEditing.value = false;
  showFeedback('Prompt técnico guardado correctamente.', 'success');
}
async function handleCopyTechnicalDefaultsPrompt() {
  await technicalDefaultsPromptCopy();
  technicalDefaultsPromptCopied.value = true;
  setTimeout(() => { technicalDefaultsPromptCopied.value = false; }, 2000);
  showFeedback('Prompt técnico copiado al portapapeles.', 'success');
}
function handleResetTechnicalDefaultsPrompt() {
  technicalDefaultsPromptReset();
  technicalDefaultsPromptIsEditing.value = false;
  showFeedback('Prompt técnico restaurado al valor original.', 'success');
}

// ── JSON tab ──
const defaultsJsonLoading = ref(false);
const defaultsJsonCopied = ref(false);
const jsonIsEditing = ref(false);
const jsonEditBuffer = ref('');
const jsonEditError = ref('');

const defaultsJsonString = computed(() => {
  try {
    const payload = {
      language: selectedLang.value,
      general: generalForm.value,
      sections: sections.value,
    };
    return JSON.stringify(payload, null, 2);
  } catch {
    return '{}';
  }
});

function startEditJson() {
  jsonEditBuffer.value = defaultsJsonString.value;
  jsonEditError.value = '';
  jsonIsEditing.value = true;
}

function cancelEditJson() {
  jsonIsEditing.value = false;
  jsonEditError.value = '';
}

async function saveEditJson() {
  jsonEditError.value = '';

  let parsed;
  try {
    parsed = JSON.parse(jsonEditBuffer.value);
  } catch (e) {
    jsonEditError.value = `JSON inválido: ${e.message}`;
    return;
  }

  if (!parsed.sections || !Array.isArray(parsed.sections)) {
    jsonEditError.value = 'El JSON debe contener un array "sections".';
    return;
  }

  const requiredKeys = ['section_type', 'title', 'order', 'content_json'];
  for (let i = 0; i < parsed.sections.length; i++) {
    const section = parsed.sections[i];
    if (typeof section !== 'object' || section === null) {
      jsonEditError.value = `La sección en índice ${i} debe ser un objeto.`;
      return;
    }
    const missing = requiredKeys.filter(k => !(k in section));
    if (missing.length > 0) {
      jsonEditError.value = `La sección en índice ${i} le faltan campos: ${missing.join(', ')}`;
      return;
    }
  }

  const lang = parsed.language || selectedLang.value;

  isSaving.value = true;
  try {
    const result = await proposalStore.saveProposalDefaults(lang, parsed.sections);
    if (result.success) {
      sections.value = parsed.sections;
      if (parsed.general) {
        Object.assign(generalForm.value, parsed.general);
      }
      savedSections.value = new Set();
      configUpdatedAt.value = result.data?.updated_at || new Date().toISOString();
      jsonIsEditing.value = false;
      showFeedback('JSON guardado correctamente.', 'success');
    } else {
      jsonEditError.value = 'Error al guardar. Verifica la estructura del JSON.';
      showFeedback('Error al guardar el JSON.', 'error');
    }
  } finally {
    isSaving.value = false;
  }
}

async function copyDefaultsJson() {
  if (typeof navigator !== 'undefined' && navigator.clipboard) {
    await navigator.clipboard.writeText(defaultsJsonString.value);
    defaultsJsonCopied.value = true;
    setTimeout(() => { defaultsJsonCopied.value = false; }, 2000);
    showFeedback('JSON copiado al portapapeles.', 'success');
  }
}

function downloadDefaultsJson() {
  const blob = new Blob([defaultsJsonString.value], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `defaults-${selectedLang.value}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function refreshData() {
  isRefreshing.value = true;
  try {
    await loadDefaults(selectedLang.value);
    await loadEmailTemplates();
  } finally {
    isRefreshing.value = false;
  }
}

onMounted(() => {
  loadDefaults(selectedLang.value);
  loadEmailTemplates();
  loadSavedPrompt();
  loadTechnicalDefaultsPrompt();
});
</script>

<style scoped>
.defaults-technical-editor :deep(.technical-document-editor textarea) {
  min-height: 5.5rem;
}
</style>
