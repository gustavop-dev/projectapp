<template>
  <div class="section-editor" data-testid="section-editor">
    <!-- Section title -->
    <label class="block mb-5">
      <span class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Título de la sección</span>
      <input
        v-model="sectionTitle"
        type="text"
        class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
      />
    </label>

    <!-- Paste mode toggle -->
    <div v-if="hasPasteSupport" class="mb-5">
      <div class="flex items-center gap-3 mb-3">
        <button
          type="button"
          class="text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors"
          :class="!pasteMode
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'"
          @click="onTogglePasteMode(false)"
        >Formulario</button>
        <button
          type="button"
          class="text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors"
          :class="pasteMode
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'"
          @click="onTogglePasteMode(true)"
        >Pegar contenido</button>
        <button
          type="button"
          class="text-xs font-medium px-2 py-1.5 rounded-lg border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 hover:text-emerald-600 transition-colors"
          title="Previsualizar"
          @click="showPreview = true"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </button>
      </div>

      <div v-if="pasteMode" class="space-y-3">
        <p class="text-[11px] text-gray-500">
          El contenido de este campo se mostrará directamente en la propuesta del cliente.
          Puedes usar formato Markdown (negritas, listas, etc.).
        </p>
        <textarea
          v-model="pasteText"
          rows="18"
          data-testid="paste-textarea"
          placeholder="Escribe o pega aquí el contenido de esta sección..."
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono
                 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y"
        />
      </div>
    </div>

    <!-- Dynamic form fields based on section_type -->
    <div v-show="!pasteMode" class="space-y-5">
      <!-- GREETING -->
      <template v-if="sectionType === 'greeting'">
        <FieldInput v-model="form.proposalTitle" label="Título de la propuesta" />
        <p v-if="!form.proposalTitle && proposalData?.title" class="text-xs text-amber-600 -mt-3">
          ⚠ Vacío — se usará "{{ proposalData.title }}" del título de la propuesta.
        </p>
        <FieldInput v-model="form.clientName" label="Nombre del cliente" />
        <p v-if="!form.clientName && proposalData?.client_name" class="text-xs text-amber-600 -mt-3">
          ⚠ Vacío — se usará "{{ proposalData.client_name }}" de los datos generales.
        </p>
        <FieldTextarea v-model="form.inspirationalQuote" label="Frase inspiracional" :rows="2" />
      </template>

      <!-- EXECUTIVE SUMMARY -->
      <template v-else-if="sectionType === 'executive_summary'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="1" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.highlightsTitle" label="Título de highlights" />
        <FieldTextarea v-model="form.highlights" label="Highlights / Incluye" help="Un item por línea" :rows="4" />
      </template>

      <!-- CONTEXT DIAGNOSTIC -->
      <template v-else-if="sectionType === 'context_diagnostic'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="2" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.issuesTitle" label="Título de problemas" />
        <FieldTextarea v-model="form.issues" label="Problemas" help="Un problema por línea" :rows="4" />
        <FieldInput v-model="form.opportunityTitle" label="Título de oportunidad" />
        <FieldTextarea v-model="form.opportunity" label="Oportunidad" :rows="3" :isSingle="true" />
      </template>

      <!-- CONVERSION STRATEGY -->
      <template v-else-if="sectionType === 'conversion_strategy'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="3" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.intro" label="Introducción" :rows="4" :isSingle="true" />
        <!-- Steps: repeatable -->
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Pasos</label>
          <div v-for="(step, idx) in form.steps" :key="idx" class="mb-4 bg-gray-50 rounded-xl p-4 border border-gray-100">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-gray-400">Paso {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500 hover:text-red-700" @click="form.steps.splice(idx, 1)">Eliminar</button>
            </div>
            <FieldInput v-model="step.title" label="Título del paso" class="mb-2" />
            <FieldTextarea v-model="step.bullets" label="Bullets" help="Un bullet por línea" :rows="3" />
          </div>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium" @click="form.steps.push({ title: '', bullets: '' })">
            + Agregar paso
          </button>
        </div>
        <FieldInput v-model="form.resultTitle" label="Título del resultado" />
        <FieldTextarea v-model="form.result" label="Resultado esperado" :rows="3" :isSingle="true" />
      </template>

      <!-- DESIGN UX -->
      <template v-else-if="sectionType === 'design_ux'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="4" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.focusTitle" label="Título de enfoque" />
        <FieldTextarea v-model="form.focusItems" label="Items de enfoque" help="Un item por línea" :rows="4" />
        <FieldInput v-model="form.objectiveTitle" label="Título del objetivo" />
        <FieldTextarea v-model="form.objective" label="Objetivo" :rows="3" :isSingle="true" />
      </template>

      <!-- CREATIVE SUPPORT -->
      <template v-else-if="sectionType === 'creative_support'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="5" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
        <FieldInput v-model="form.includesTitle" label="Título de incluye" />
        <FieldTextarea v-model="form.includes" label="Incluye" help="Un item por línea" :rows="4" />
        <FieldTextarea v-model="form.closing" label="Cierre" :rows="3" :isSingle="true" />
      </template>

      <!-- DEVELOPMENT STAGES -->
      <template v-else-if="sectionType === 'development_stages'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="6" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.intro" label="Texto introductorio" :rows="2" :isSingle="true" />
        <FieldInput v-model="form.currentLabel" label="Etiqueta de etapa actual" placeholder="Actual" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Etapas</label>
          <draggable v-model="form.stages" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: stage, index: idx }">
              <div class="mb-4 bg-gray-50 rounded-xl p-4 border border-gray-100">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Etapa {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500 hover:text-red-700" @click="form.stages.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-[100px_1fr] gap-3 mb-2">
                  <EmojiIconField v-model="stage.icon" label="Icono" placeholder="✉️" />
                  <FieldInput v-model="stage.title" label="Título" />
                </div>
                <FieldTextarea v-model="stage.description" label="Descripción" :rows="2" :isSingle="true" />
                <label class="flex items-center gap-2 mt-2 text-xs">
                  <input type="checkbox" v-model="stage.current" class="rounded border-gray-300 text-emerald-600" />
                  <span class="text-gray-600">Etapa actual</span>
                </label>
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium" @click="form.stages.push({ icon: '', title: '', description: '', current: false })">
            + Agregar etapa
          </button>
        </div>
      </template>

      <!-- FUNCTIONAL REQUIREMENTS -->
      <template v-else-if="sectionType === 'functional_requirements'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="7" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.intro" label="Introducción" :rows="3" :isSingle="true" />

      </template>

      <!-- TIMELINE -->
      <template v-else-if="sectionType === 'timeline'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="8" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.introText" label="Texto introductorio" :rows="3" :isSingle="true" />
        <FieldInput v-model="form.totalDuration" label="Duración total" placeholder="Aproximadamente 1 mes" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Fases</label>
          <draggable v-model="form.phases" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: phase, index: idx }">
              <div class="mb-4 bg-gray-50 rounded-xl p-4 border border-gray-100">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Fase {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500 hover:text-red-700" @click="form.phases.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-2">
                  <FieldInput v-model="phase.title" label="Título" />
                  <FieldInput v-model="phase.duration" label="Duración" placeholder="2 semanas" />
                </div>
                <FieldTextarea v-model="phase.description" label="Descripción" :rows="2" :isSingle="true" />
                <FieldTextarea v-model="phase.tasks" label="Tareas" help="Una por línea" :rows="3" />
                <FieldInput v-model="phase.milestone" label="Hito / Milestone" class="mt-2" />
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium" @click="form.phases.push({ title: '', duration: '', description: '', tasks: '', milestone: '' })">
            + Agregar fase
          </button>
        </div>
      </template>

      <!-- INVESTMENT -->
      <template v-else-if="sectionType === 'investment'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="9" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.introText" label="Texto introductorio" :rows="2" :isSingle="true" />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.totalInvestment" label="Inversión total" placeholder="$3.500.000" />
          <div>
            <label class="block text-xs text-gray-500 mb-0.5">Moneda</label>
            <select
              v-model="form.currency"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white"
            >
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>
        <p v-if="proposalData?.total_investment && !form.totalInvestment" class="text-xs text-amber-600 -mt-3">
          ⚠ Vacío — se puede usar ${{ Number(proposalData.total_investment).toLocaleString() }} {{ proposalData.currency || 'COP' }} de los datos generales.
          <button type="button" class="ml-1 text-emerald-600 underline" @click="fillInvestmentFromProposal">
            Llenar automáticamente
          </button>
        </p>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Qué incluye</label>
          <draggable v-model="form.whatsIncluded" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: item, index: idx }">
              <div class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Item {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500" @click="form.whatsIncluded.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-[100px_1fr] gap-2 mb-1">
                  <EmojiIconField v-model="item.icon" label="Icono" placeholder="🎨" />
                  <FieldInput v-model="item.title" label="Título" />
                </div>
                <FieldInput v-model="item.description" label="Descripción" />
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.whatsIncluded.push({ icon: '', title: '', description: '' })">+ Agregar item</button>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Opciones de pago</label>
          <draggable v-model="form.paymentOptions" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: opt, index: idx }">
              <div class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Opción {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500" @click="form.paymentOptions.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <FieldInput v-model="opt.label" label="Etiqueta" placeholder="40% al firmar" />
                  <FieldInput v-model="opt.description" label="Descripción" placeholder="$596.000 COP" />
                </div>
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.paymentOptions.push({ label: '', description: '' })">+ Agregar opción</button>
        </div>
        <FieldTextarea v-model="form.paymentMethods" label="Métodos de pago" help="Uno por línea" :rows="3" />
        <FieldTextarea v-model="form.valueReasons" label="Razones de valor" help="Una por línea" :rows="3" />

        <!-- Interactive Modules (Cotizador) -->
        <div class="mt-4 border border-gray-200 rounded-xl overflow-hidden">
          <div class="flex items-center justify-between px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
               @click="modulesCollapsed = !modulesCollapsed">
            <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': !modulesCollapsed }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
              🧮 Módulos Interactivos (Cotizador)
            </h4>
            <span class="text-xs text-gray-400">{{ (form.modules || []).length }} módulos</span>
          </div>
          <div v-show="!modulesCollapsed" class="p-4 space-y-3">
            <p class="text-xs text-gray-500 mb-2">Define los módulos que el cliente podrá activar/desactivar en el cotizador interactivo.</p>
            <div v-for="(mod, mIdx) in form.modules" :key="mIdx" class="bg-gray-50 rounded-lg p-3 border border-gray-100">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] text-gray-400">Módulo {{ mIdx + 1 }}</span>
                <button type="button" class="text-[10px] text-red-500" @click="form.modules.splice(mIdx, 1)">Eliminar</button>
              </div>
              <div class="grid grid-cols-[120px_1fr_120px] gap-2 mb-1">
                <FieldInput v-model="mod.id" label="ID" placeholder="modulo-1" />
                <FieldInput v-model="mod.name" label="Nombre" placeholder="Sitio Web Principal" />
                <FieldInput v-model.number="mod.price" label="Precio" type="number" placeholder="0" />
              </div>
              <div class="grid grid-cols-2 gap-x-4 gap-y-1 mt-2">
                <label class="flex items-center gap-2">
                  <input type="checkbox" v-model="mod.included" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                  <span class="text-xs text-gray-600">Incluido por defecto</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" v-model="mod.show_price" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                  <span class="text-xs text-gray-600">Mostrar precio al cliente</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" v-model="mod.is_required" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                  <span class="text-xs text-gray-600">Obligatorio (no se puede quitar)</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" v-model="mod.removable" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                  <span class="text-xs text-gray-600">El cliente puede agregarlo/quitarlo</span>
                </label>
              </div>
            </div>
            <button type="button" class="text-xs text-emerald-600 font-medium" @click="(form.modules = form.modules || []).push({ id: '', name: '', price: 0, included: true, show_price: false, is_required: true, removable: false })">+ Agregar módulo</button>
          </div>
        </div>

        <!-- Hosting Plan -->
        <div class="mt-4 border border-gray-200 rounded-xl overflow-hidden">
          <div class="flex items-center justify-between px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
               @click="hostingCollapsed = !hostingCollapsed">
            <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': !hostingCollapsed }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
              ☁️ Plan de Hosting
            </h4>
          </div>
          <div v-show="!hostingCollapsed" class="p-4 space-y-4">
            <FieldInput v-model="form.hostingPlan.title" label="Título" placeholder="Hosting, Mantenimiento y Soporte" />
            <FieldTextarea v-model="form.hostingPlan.description" label="Descripción" :rows="2" :isSingle="true" />
            <div>
              <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Especificaciones</label>
              <draggable v-model="form.hostingPlan.specs" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
                <template #item="{ element: spec, index: idx }">
                  <div class="mb-2 bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div class="flex items-center justify-between mb-1">
                      <div class="flex items-center gap-2">
                        <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                        <span class="text-[10px] text-gray-400">{{ idx + 1 }}</span>
                      </div>
                      <button type="button" class="text-[10px] text-red-500" @click="form.hostingPlan.specs.splice(idx, 1)">Eliminar</button>
                    </div>
                    <div class="grid grid-cols-[80px_1fr_1fr] gap-2">
                      <EmojiIconField v-model="spec.icon" label="Icono" placeholder="🧠" />
                      <FieldInput v-model="spec.label" label="Etiqueta" placeholder="vCPU" />
                      <FieldInput v-model="spec.value" label="Valor" placeholder="1 núcleo de vCPU" />
                    </div>
                  </div>
                </template>
              </draggable>
              <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.hostingPlan.specs.push({ icon: '', label: '', value: '' })">+ Agregar especificación</button>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FieldInput v-model="form.hostingPlan.monthlyPrice" label="Precio mensual" placeholder="$49.999 COP" />
              <FieldInput v-model="form.hostingPlan.monthlyLabel" label="Etiqueta mensual" placeholder="por mes" />
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FieldInput v-model="form.hostingPlan.annualPrice" label="Precio anual" placeholder="$680.000 COP" />
              <FieldInput v-model="form.hostingPlan.annualLabel" label="Etiqueta anual" placeholder="Hosting anual — Año 1" />
            </div>
            <FieldTextarea v-model="form.hostingPlan.renewalNote" label="Nota de renovación (visible al cliente)" help="Fórmula de incremento anual, SMLMV, etc." :rows="4" :isSingle="true" />
            <FieldTextarea v-model="form.hostingPlan.coverageNote" label="Nota de cobertura (solo PDF)" help="Descripción de los 3 componentes del hosting (mantenimiento, soporte, recursos)" :rows="3" :isSingle="true" />
          </div>
        </div>
      </template>

      <!-- FINAL NOTE -->
      <template v-else-if="sectionType === 'final_note'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="10" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.message" label="Mensaje" :rows="5" :isSingle="true" />
        <FieldTextarea v-model="form.personalNote" label="Nota personal" :rows="3" :isSingle="true" />
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <FieldInput v-model="form.teamName" label="Nombre del equipo" />
          <FieldInput v-model="form.teamRole" label="Rol" />
          <FieldInput v-model="form.contactEmail" label="Email de contacto" />
        </div>
        <FieldInput v-model="form.signature" label="URL de la firma (imagen)" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Badges de compromiso</label>
          <draggable v-model="form.commitmentBadges" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: badge, index: idx }">
              <div class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Badge {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500" @click="form.commitmentBadges.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-[100px_1fr] gap-2 mb-1">
                  <EmojiIconField v-model="badge.icon" label="Icono" placeholder="🤝" />
                  <FieldInput v-model="badge.title" label="Título" />
                </div>
                <FieldInput v-model="badge.description" label="Descripción" />
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.commitmentBadges.push({ icon: '', title: '', description: '' })">+ Agregar badge</button>
        </div>
        <FieldTextarea v-model="form.validityMessage" label="Mensaje de vigencia" :rows="2" :isSingle="true" />
        <FieldTextarea v-model="form.thankYouMessage" label="Mensaje de agradecimiento" :rows="2" :isSingle="true" />
      </template>

      <!-- NEXT STEPS -->
      <template v-else-if="sectionType === 'next_steps'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="11" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.introMessage" label="Mensaje de introducción" :rows="3" :isSingle="true" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Pasos</label>
          <draggable v-model="form.steps" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: step, index: idx }">
              <div class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Paso {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500" @click="form.steps.splice(idx, 1)">Eliminar</button>
                </div>
                <FieldInput v-model="step.title" label="Título" class="mb-1" />
                <FieldInput v-model="step.description" label="Descripción" />
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.steps.push({ title: '', description: '' })">+ Agregar paso</button>
        </div>
        <FieldTextarea v-model="form.ctaMessage" label="Mensaje CTA" :rows="2" :isSingle="true" />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <p class="text-xs text-gray-400 mb-2">CTA Primario</p>
            <FieldInput v-model="form.primaryCTA.text" label="Texto" class="mb-1" />
            <FieldInput v-model="form.primaryCTA.link" label="Link" />
          </div>
          <div class="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <p class="text-xs text-gray-400 mb-2">CTA Secundario</p>
            <FieldInput v-model="form.secondaryCTA.text" label="Texto" class="mb-1" />
            <FieldInput v-model="form.secondaryCTA.link" label="Link" />
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Métodos de contacto</label>
          <draggable v-model="form.contactMethods" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: method, index: idx }">
              <div class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Método {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500" @click="form.contactMethods.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
                  <EmojiIconField v-model="method.icon" label="Icono" placeholder="📧" />
                  <FieldInput v-model="method.title" label="Título" />
                  <FieldInput v-model="method.value" label="Valor" />
                  <FieldInput v-model="method.link" label="Link" />
                </div>
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.contactMethods.push({ icon: '', title: '', value: '', link: '' })">+ Agregar método</button>
        </div>
        <FieldTextarea v-model="form.validityMessage" label="Mensaje de vigencia" :rows="2" :isSingle="true" />
        <FieldTextarea v-model="form.thankYouMessage" label="Mensaje de agradecimiento" :rows="2" :isSingle="true" />
      </template>
    </div>

    <!-- Functional requirements groups: always visible regardless of paste mode -->
    <template v-if="sectionType === 'functional_requirements'">
      <!-- Groups: collapsible -->
      <div v-for="(group, gIdx) in form.groups" :key="group.id || gIdx" :data-testid="`requirement-group-${group.id || gIdx}`" class="mt-4 border border-gray-200 rounded-xl overflow-hidden">
        <!-- Collapse header -->
        <div class="flex flex-wrap items-center justify-between gap-2 px-3 sm:px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
             @click="group._collapsed = !group._collapsed">
          <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': !group._collapsed }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            <span>{{ group.icon }}</span> {{ group.title }}
            <span class="text-[10px] text-gray-400 font-normal">({{ (group.items || []).length }} elementos)</span>
          </h4>
          <div class="flex flex-wrap items-center gap-2" @click.stop>
            <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
              :class="!group._pasteMode ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-500 border-gray-200'"
              @click="onToggleGroupPaste(group, false)">Formulario</button>
            <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
              :class="group._pasteMode ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-500 border-gray-200'"
              @click="onToggleGroupPaste(group, true)">Pegar contenido</button>
            <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 transition-colors"
              @click="openSubPreview(group, gIdx)">
              <svg class="w-3.5 h-3.5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
            <button v-if="group.id !== 'views' && group.id !== 'components' && group.id !== 'features' && group.id !== 'integrations_api' && group.id !== 'admin_module'"
              type="button" class="text-xs text-red-500 hover:text-red-700 ml-2" @click="form.groups.splice(gIdx, 1)">Eliminar</button>
          </div>
        </div>

        <!-- Collapse content -->
        <div v-show="!group._collapsed" class="p-4">
          <!-- Paste mode for this group -->
          <div v-if="group._pasteMode" class="space-y-3">
            <p class="text-[11px] text-gray-500">Contenido Markdown para esta sub-sección.</p>
            <textarea v-model="group._pasteText" rows="10" data-testid="group-paste-textarea" placeholder="Escribe o pega aquí el contenido de este grupo..."
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:ring-1 focus:ring-emerald-500 outline-none resize-y" />
          </div>

          <!-- Form mode for this group -->
          <div v-else class="space-y-3">
            <div class="grid grid-cols-[100px_1fr] gap-3">
              <EmojiIconField v-model="group.icon" label="Icono" placeholder="🖥️" />
              <FieldInput v-model="group.title" label="Título del grupo" />
            </div>
            <FieldTextarea v-model="group.description" label="Descripción" :rows="2" :isSingle="true" />
            <div>
              <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Elementos</label>
              <draggable v-model="group.items" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
                <template #item="{ element: item, index: iIdx }">
                  <div class="mb-2 bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div class="flex items-center justify-between mb-1">
                      <div class="flex items-center gap-2">
                        <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                        <span class="text-[10px] text-gray-400">{{ iIdx + 1 }}</span>
                      </div>
                      <button type="button" class="text-[10px] text-red-500" @click="group.items.splice(iIdx, 1)">Eliminar</button>
                    </div>
                    <div class="grid grid-cols-[90px_1fr] gap-2 mb-1">
                      <EmojiIconField v-model="item.icon" label="Icono" placeholder="🏠" />
                      <FieldInput v-model="item.name" label="Nombre" />
                    </div>
                    <div class="grid grid-cols-[1fr_120px] gap-2">
                      <FieldTextarea v-model="item.description" label="Descripción" :rows="2" :isSingle="true" />
                      <FieldInput v-model.number="item.price" label="Precio" type="number" placeholder="0" />
                    </div>
                    <div class="grid grid-cols-3 gap-x-3 gap-y-1 mt-2">
                      <label class="flex items-center gap-1.5">
                        <input type="checkbox" v-model="item.show_price" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                        <span class="text-[10px] text-gray-500">Mostrar precio</span>
                      </label>
                      <label class="flex items-center gap-1.5">
                        <input type="checkbox" v-model="item.is_required" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                        <span class="text-[10px] text-gray-500">Obligatorio</span>
                      </label>
                      <label class="flex items-center gap-1.5">
                        <input type="checkbox" v-model="item.removable" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                        <span class="text-[10px] text-gray-500">Puede quitarse</span>
                      </label>
                    </div>
                  </div>
                </template>
              </draggable>
              <button type="button" class="text-xs text-emerald-600 font-medium" @click="group.items.push({ icon: '', name: '', description: '', price: null, show_price: false, is_required: true, removable: false })">+ Agregar elemento</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Additional Modules: collapsible -->
      <div class="mt-6">
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Módulos Adicionales</label>
        <div v-for="(mod, mIdx) in form.additionalModules" :key="mIdx" class="mb-4 border border-gray-200 rounded-xl overflow-hidden">
          <div class="flex flex-wrap items-center justify-between gap-2 px-3 sm:px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
               @click="mod._collapsed = !mod._collapsed">
            <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': !mod._collapsed }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
              <span>{{ mod.icon || '🧩' }}</span> {{ mod.title || 'Módulo adicional' }}
            </h4>
            <div class="flex flex-wrap items-center gap-2" @click.stop>
              <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
                :class="!mod._pasteMode ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-500 border-gray-200'"
                @click="onToggleGroupPaste(mod, false)">Formulario</button>
              <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
                :class="mod._pasteMode ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-500 border-gray-200'"
                @click="onToggleGroupPaste(mod, true)">Pegar contenido</button>
              <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 transition-colors"
                @click="openSubPreview(mod, mIdx, true)">
                <svg class="w-3.5 h-3.5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              <button type="button" class="text-xs text-red-500 hover:text-red-700 ml-2" @click="form.additionalModules.splice(mIdx, 1)">Eliminar</button>
            </div>
          </div>
          <div v-show="!mod._collapsed" class="p-4">
            <div v-if="mod._pasteMode" class="space-y-3">
              <p class="text-[11px] text-gray-500">Contenido Markdown para este módulo.</p>
              <textarea v-model="mod._pasteText" rows="8" placeholder="Escribe o pega aquí el contenido de este módulo..."
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:ring-1 focus:ring-emerald-500 outline-none resize-y" />
            </div>
            <div v-else class="space-y-3">
              <div class="grid grid-cols-[100px_1fr] gap-3">
                <EmojiIconField v-model="mod.icon" label="Icono" placeholder="🧩" />
                <FieldInput v-model="mod.title" label="Título del módulo" />
              </div>
              <FieldTextarea v-model="mod.description" label="Descripción" :rows="2" :isSingle="true" />
              <div>
                <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Elementos</label>
                <draggable v-model="mod.items" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
                  <template #item="{ element: item, index: iIdx }">
                    <div class="mb-2 bg-gray-50 rounded-lg p-3 border border-gray-100">
                      <div class="flex items-center justify-between mb-1">
                        <div class="flex items-center gap-2">
                          <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                          <span class="text-[10px] text-gray-400">{{ iIdx + 1 }}</span>
                        </div>
                        <button type="button" class="text-[10px] text-red-500" @click="mod.items.splice(iIdx, 1)">Eliminar</button>
                      </div>
                      <div class="grid grid-cols-[90px_1fr] gap-2 mb-1">
                        <EmojiIconField v-model="item.icon" label="Icono" />
                        <FieldInput v-model="item.name" label="Nombre" />
                      </div>
                      <FieldTextarea v-model="item.description" label="Descripción" :rows="2" :isSingle="true" />
                      <div class="grid grid-cols-3 gap-x-3 gap-y-1 mt-2">
                        <label class="flex items-center gap-1.5">
                          <input type="checkbox" v-model="item.show_price" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                          <span class="text-[10px] text-gray-500">Mostrar precio</span>
                        </label>
                        <label class="flex items-center gap-1.5">
                          <input type="checkbox" v-model="item.is_required" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                          <span class="text-[10px] text-gray-500">Obligatorio</span>
                        </label>
                        <label class="flex items-center gap-1.5">
                          <input type="checkbox" v-model="item.removable" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                          <span class="text-[10px] text-gray-500">Puede quitarse</span>
                        </label>
                      </div>
                    </div>
                  </template>
                </draggable>
                <button type="button" class="text-xs text-emerald-600 font-medium" @click="mod.items.push({ icon: '', name: '', description: '', price: null, show_price: false, is_required: true, removable: false })">+ Agregar elemento</button>
              </div>
            </div>
          </div>
        </div>
        <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
          @click="form.additionalModules.push({ icon: '🧩', title: '', description: '', items: [], _pasteMode: false, _pasteText: '', _collapsed: false })">
          + Agregar módulo adicional
        </button>
      </div>
    </template>

    <!-- Raw JSON toggle -->
    <div class="mt-6 border-t border-gray-100 pt-4">
      <button type="button" class="text-xs text-gray-400 hover:text-gray-600" @click="showRawJson = !showRawJson">
        {{ showRawJson ? 'Ocultar' : 'Mostrar' }} JSON crudo
      </button>
      <div v-if="showRawJson" class="mt-2">
        <textarea
          v-model="rawJsonText"
          rows="10"
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-xs font-mono bg-gray-50 resize-y outline-none"
          readonly
        />
      </div>
    </div>

    <!-- Save button -->
    <div class="flex flex-wrap items-center gap-3 mt-5">
      <button
        type="button"
        :disabled="isSaving"
        class="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium
               hover:bg-emerald-700 transition-colors disabled:opacity-50"
        @click="handleSave"
      >
        {{ isSaving ? 'Guardando...' : 'Guardar Sección' }}
      </button>
      <button
        type="button"
        class="px-5 py-2 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium
               hover:bg-gray-50 transition-colors"
        @click="showPreview = true"
      >
        <span class="flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          Previsualizar
        </span>
      </button>
      <span v-if="savedMsg" class="text-xs text-green-600">{{ savedMsg }}</span>
    </div>

    <!-- Section preview modal -->
    <SectionPreviewModal
      :visible="showPreview"
      :section="previewSection"
      :proposalData="proposalData"
      @close="showPreview = false"
    />

    <!-- Sub-section preview modal -->
    <SectionPreviewModal
      :visible="showSubPreview"
      :section="previewSection"
      :proposalData="proposalData"
      :subSection="subPreviewData"
      @close="showSubPreview = false"
    />
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch, h } from 'vue';
import EmojiIconField from '~/components/BusinessProposal/admin/EmojiIconField.vue';
import SectionPreviewModal from '~/components/BusinessProposal/admin/SectionPreviewModal.vue';
import draggable from 'vuedraggable';
import {
  arrToText, textToArr,
  buildFormFromJson as _buildFormFromJson,
  formToJson as _formToJson,
  formToReadableText as _formToReadableText,
  groupToReadableText as _groupToReadableText,
} from '~/components/BusinessProposal/admin/sectionEditorUtils.js';

// --- Inline sub-components (render functions for prod compatibility) ---
const FieldInput = {
  props: { modelValue: String, label: String, placeholder: String },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('label', { class: 'block' }, [
      props.label ? h('span', { class: 'block text-xs text-gray-500 mb-0.5' }, props.label) : null,
      h('input', {
        value: props.modelValue,
        placeholder: props.placeholder,
        class: 'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none',
        onInput: (e) => emit('update:modelValue', e.target.value),
      }),
    ]);
  },
};

const FieldTextarea = {
  props: { modelValue: String, label: String, help: String, rows: { type: Number, default: 4 }, isSingle: Boolean },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('label', { class: 'block' }, [
      props.label ? h('span', { class: 'block text-xs text-gray-500 mb-0.5' }, props.label) : null,
      h('textarea', {
        value: props.modelValue,
        rows: props.rows,
        class: 'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y',
        onInput: (e) => emit('update:modelValue', e.target.value),
      }),
      props.help ? h('p', { class: 'text-[10px] text-gray-400 mt-0.5' }, props.help) : null,
    ]);
  },
};

const props = defineProps({
  section: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['save']);

const sectionType = computed(() => props.section.section_type);
const sectionTitle = ref(props.section.title);
const isSaving = ref(false);
const showPreview = ref(false);
const showSubPreview = ref(false);
const subPreviewData = ref(null);

const previewSection = computed(() => {
  const contentJson = formToJson(form, sectionType.value);
  if (pasteMode.value) {
    contentJson._editMode = 'paste';
    contentJson.rawText = pasteText.value;
  }
  return {
    id: props.section.id,
    section_type: sectionType.value,
    title: sectionTitle.value,
    content_json: contentJson,
  };
});
const savedMsg = ref('');
const showRawJson = ref(false);
const hostingCollapsed = ref(true);
const modulesCollapsed = ref(true);
const initialContent = props.section.content_json || {};
const pasteMode = ref(initialContent._editMode === 'paste');
const pasteText = ref(initialContent.rawText || '');

const hasPasteSupport = computed(() => true);

function formToReadableText() {
  return _formToReadableText(form, sectionType.value);
}

function onTogglePasteMode(on) {
  pasteMode.value = on;
  if (on) {
    pasteText.value = formToReadableText();
  }
}

function groupToReadableText(group) {
  return _groupToReadableText(group);
}

function onToggleGroupPaste(group, on) {
  group._pasteMode = on;
  if (on) {
    group._pasteText = groupToReadableText(group);
  }
}

function openSubPreview(group, idx, isAdditional = false) {
  const baseIndex = form.index || '7';
  const offset = isAdditional ? form.groups.length + idx + 1 : idx + 1;
  subPreviewData.value = {
    group: { ...group, items: [...(group.items || [])] },
    subIndex: `${baseIndex}.${offset}`,
  };
  showSubPreview.value = true;
}

function fillInvestmentFromProposal() {
  if (!props.proposalData?.total_investment) return;
  const total = Number(props.proposalData.total_investment);
  const currency = props.proposalData.currency || 'COP';
  const fmt = (n) => '$' + Math.round(n).toLocaleString();
  form.totalInvestment = fmt(total);
  form.currency = currency;
  // Auto-fill 40/30/30 payment split
  form.paymentOptions = [
    { label: '40% al firmar el contrato ✍️', description: fmt(total * 0.4) + ' ' + currency },
    { label: '30% al aprobar el diseño final ✅', description: fmt(total * 0.3) + ' ' + currency },
    { label: '30% al desplegar el sitio web 🚀', description: fmt(total * 0.3) + ' ' + currency },
  ];
}

function parseInvestmentNumber(str) {
  if (!str) return 0;
  return Number(String(str).replace(/[^0-9.]/g, '')) || 0;
}

function recalcPaymentDescriptions() {
  const total = parseInvestmentNumber(form.totalInvestment);
  if (!total) return;
  const cur = form.currency || 'COP';
  const fmt = (n) => '$' + Math.round(n).toLocaleString();
  for (const opt of form.paymentOptions) {
    const pctMatch = opt.label?.match(/(\d+)%/);
    if (pctMatch) {
      const pct = Number(pctMatch[1]) / 100;
      opt.description = fmt(total * pct) + ' ' + cur;
    }
  }
}

// --- Build form state from content_json ---
const form = reactive(buildFormFromJson(props.section.content_json || {}, props.section.section_type));

// Auto-fill investment from proposal data if section is empty
if (sectionType.value === 'investment' && !form.totalInvestment && props.proposalData?.total_investment) {
  fillInvestmentFromProposal();
}

watch(() => props.section, (s) => {
  sectionTitle.value = s.title;
  Object.assign(form, buildFormFromJson(s.content_json || {}, s.section_type));
}, { deep: true });

// Auto-recalculate payment option descriptions when investment or currency changes
if (sectionType.value === 'investment') {
  watch([() => form.totalInvestment, () => form.currency], () => {
    recalcPaymentDescriptions();
  });
}

// Auto-sync paste text from form data (keeps paste area current while editing in form mode)
watch(
  () => _formToReadableText(form, sectionType.value),
  (newText) => {
    if (!pasteMode.value) pasteText.value = newText;
  },
);

// Auto-sync group/module paste text for functional_requirements subsections
if (sectionType.value === 'functional_requirements') {
  watch(
    () => {
      return [...form.groups, ...form.additionalModules].map(g => {
        const itemsSig = (g.items || []).map(i =>
          `${i.icon}|${i.name}|${i.description}`
        ).join('~');
        return `${g.title}|${g.icon}|${g.description}|${itemsSig}`;
      }).join('||');
    },
    () => {
      for (const g of form.groups) {
        if (!g._pasteMode) g._pasteText = _groupToReadableText(g);
      }
      for (const m of form.additionalModules) {
        if (!m._pasteMode) m._pasteText = _groupToReadableText(m);
      }
    },
  );
}

// --- Helpers: JSON ↔ form conversion (delegated to sectionEditorUtils.js) ---

function buildFormFromJson(json, type) {
  return _buildFormFromJson(json, type, props.proposalData);
}

function formToJson(formData, type) {
  return _formToJson(formData, type);
}

const rawJsonText = computed(() => {
  try {
    return JSON.stringify(formToJson(form, sectionType.value), null, 2);
  } catch { return '{}'; }
});

function handleSave() {
  isSaving.value = true;
  savedMsg.value = '';
  try {
    const contentJson = formToJson(form, sectionType.value);
    if (pasteMode.value) {
      contentJson._editMode = 'paste';
      contentJson.rawText = pasteText.value;
    } else {
      contentJson._editMode = 'form';
      delete contentJson.rawText;
    }
    emit('save', {
      sectionId: props.section.id,
      payload: {
        title: sectionTitle.value,
        is_wide_panel: props.section.is_wide_panel,
        content_json: contentJson,
      },
    });
    savedMsg.value = '✓ Guardado';
    setTimeout(() => { savedMsg.value = ''; }, 3000);
  } finally {
    isSaving.value = false;
  }
}
</script>
