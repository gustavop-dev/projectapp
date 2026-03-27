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
        <div class="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-800">
          💰 <strong>Inversión total:</strong> ${{ Number(proposalData?.total_investment || 0).toLocaleString() }} {{ proposalData?.currency || 'COP' }}
          <span class="text-xs text-blue-600 ml-2">(se edita en la pestaña "General")</span>
        </div>
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
              <FieldInput v-model.number="form.hostingPlan.hostingPercent" label="% de inversión total" type="number" placeholder="30" />
            </div>
            <div v-if="form.hostingPlan.hostingPercent > 0 && proposalData?.total_investment" class="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-800">
              💡 <strong>Hosting anual estimado:</strong> ${{ Math.round(Number(proposalData.total_investment) * form.hostingPlan.hostingPercent / 100).toLocaleString() }} {{ proposalData?.currency || 'COP' }}
              <span class="text-xs text-blue-600 ml-2">({{ form.hostingPlan.hostingPercent }}% de ${{ Number(proposalData.total_investment).toLocaleString() }})</span>
            </div>
            <!-- Billing Tiers -->
            <div>
              <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Frecuencias de pago del hosting</label>
              <div class="space-y-3">
                <div v-for="(tier, tIdx) in form.hostingPlan.billingTiers" :key="tIdx"
                     class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3 border border-gray-100 dark:border-gray-600">
                  <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
                    <FieldInput v-model="tier.label" label="Etiqueta" :placeholder="tier.frequency === 'semiannual' ? 'Semestral' : tier.frequency === 'quarterly' ? 'Trimestral' : 'Mensual'" />
                    <FieldInput v-model.number="tier.months" label="Meses" type="number" :placeholder="String(tier.months)" />
                    <FieldInput v-model.number="tier.discountPercent" label="% Descuento" type="number" placeholder="0" />
                    <FieldInput v-model="tier.badge" label="Badge" placeholder="Mejor precio" />
                    <div class="flex items-end pb-1">
                      <span v-if="form.hostingPlan.hostingPercent > 0 && proposalData?.total_investment" class="text-xs text-emerald-600 font-medium">
                        ${{ Math.round(Math.round(Number(proposalData.total_investment) * form.hostingPlan.hostingPercent / 100 / 12) * (100 - (tier.discountPercent || 0)) / 100).toLocaleString() }} /mes
                      </span>
                    </div>
                  </div>
                </div>
              </div>
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

      <!-- PROPOSAL SUMMARY -->
      <template v-else-if="sectionType === 'proposal_summary'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="10" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.subtitle" label="Subtítulo" :rows="2" :isSingle="true" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">KPIs personalizados</label>
          <p class="text-[10px] text-gray-400 mb-2">Métricas clave que aparecerán como tarjetas destacadas al inicio del resumen. Incluye fuentes verificables.</p>
          <div v-for="(kpi, idx) in (form.kpis || [])" :key="'kpi-' + idx" class="mb-2 bg-emerald-50/50 rounded-xl p-3 border border-emerald-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-emerald-600 font-medium">KPI {{ idx + 1 }}</span>
              <button type="button" class="text-xs text-red-500" @click="form.kpis.splice(idx, 1)">Eliminar</button>
            </div>
            <div class="grid grid-cols-[120px_1fr] gap-2 mb-1">
              <FieldInput v-model="kpi.value" label="Valor" placeholder="+40%" />
              <FieldInput v-model="kpi.label" label="Etiqueta" placeholder="Incremento en conversión web" />
            </div>
            <FieldInput v-model="kpi.source" label="Fuente" placeholder="HubSpot 2024" />
          </div>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="if (!form.kpis) form.kpis = []; form.kpis.push({ value: '', label: '', source: '' })">+ Agregar KPI</button>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Tarjetas de resumen</label>
          <draggable v-model="form.cards" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
            <template #item="{ element: card, index: idx }">
              <div class="mb-3 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-2">
                    <span class="drag-handle cursor-grab text-gray-300 hover:text-gray-500">⠿</span>
                    <span class="text-xs text-gray-400">Tarjeta {{ idx + 1 }}</span>
                  </div>
                  <button type="button" class="text-xs text-red-500" @click="form.cards.splice(idx, 1)">Eliminar</button>
                </div>
                <div class="grid grid-cols-[100px_1fr] gap-2 mb-1">
                  <EmojiIconField v-model="card.icon" label="Icono" placeholder="💰" />
                  <FieldInput v-model="card.title" label="Título" />
                </div>
                <FieldInput v-model="card.description" label="Descripción" />
                <div class="mt-1">
                  <label class="block text-[10px] text-gray-400 mb-0.5">Fuente del valor</label>
                  <select v-model="card.source" class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs bg-white focus:ring-1 focus:ring-emerald-500 outline-none">
                    <option value="static">Estático (solo texto)</option>
                    <option value="total_investment">Inversión total (auto)</option>
                    <option value="timeline_duration">Duración del cronograma (auto)</option>
                    <option value="expires_at">Fecha de expiración (auto)</option>
                    <option value="cta">Call-to-action</option>
                  </select>
                </div>
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.cards.push({ icon: '', title: '', description: '', source: 'static' })">+ Agregar tarjeta</button>
        </div>
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

      <!-- PROCESS METHODOLOGY -->
      <template v-else-if="sectionType === 'process_methodology'">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FieldInput v-model="form.index" label="Índice" placeholder="5" />
          <FieldInput v-model="form.title" label="Título" />
        </div>
        <FieldTextarea v-model="form.intro" label="Introducción" :rows="3" :isSingle="true" />
        <div>
          <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Pasos del proceso</label>
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
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <EmojiIconField v-model="step.icon" label="Icono" placeholder="🔍" />
                  <FieldInput v-model="step.title" label="Título" />
                </div>
                <FieldInput v-model="step.description" label="Descripción" class="mt-1" />
                <FieldInput v-model="step.clientAction" label="Acción del cliente (opcional)" class="mt-1" />
              </div>
            </template>
          </draggable>
          <button type="button" class="text-xs text-emerald-600 font-medium" @click="form.steps.push({ icon: '', title: '', description: '', clientAction: '' })">+ Agregar paso</button>
        </div>
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
            <label class="flex items-center gap-1 cursor-pointer" title="Si está marcado, este módulo aparecerá preseleccionado en la calculadora del cliente">
              <input type="checkbox" v-model="group.selected" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
              <span class="text-[10px] text-gray-500 font-medium">Seleccionado</span>
            </label>
            <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
              :class="group.is_calculator_module ? 'bg-blue-100 text-blue-700 border-blue-300' : 'bg-gray-50 text-gray-400 border-gray-200'"
              :title="group.is_calculator_module ? 'Este módulo aparece en la calculadora de inversión del cliente' : 'Este módulo NO aparece en la calculadora de inversión'"
              @click="group.is_calculator_module = !group.is_calculator_module">
              {{ group.is_calculator_module ? '🧮 En calc.' : '🧮 No calc.' }}
            </button>
            <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
              :class="group.is_visible !== false ? 'bg-emerald-100 text-emerald-700 border-emerald-300' : 'bg-red-50 text-red-500 border-red-200'"
              :title="group.is_visible !== false ? 'Este módulo se muestra en la propuesta del cliente' : 'Este módulo está oculto en la propuesta del cliente'"
              @click="group.is_visible = group.is_visible === false ? true : false">
              {{ group.is_visible !== false ? '👁 Visible' : '🚫 Oculto' }}
            </button>
            <button v-if="group.id !== 'views' && group.id !== 'components' && group.id !== 'features'"
              type="button" class="text-xs text-red-500 hover:text-red-700 ml-2" title="Eliminar este grupo de la propuesta" @click="form.groups.splice(gIdx, 1)">Eliminar</button>
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
            <div class="grid grid-cols-[100px_1fr_auto] gap-3 items-end">
              <EmojiIconField v-model="group.icon" label="Icono" placeholder="🖥️" />
              <FieldInput v-model="group.title" label="Título del grupo" />
              <div class="flex flex-col gap-1" title="Porcentaje de la inversión total que representa este módulo. Se usa para calcular el precio en la calculadora">
                <label class="text-[10px] text-gray-500 font-medium uppercase">% del precio</label>
                <input type="number" v-model.number="group.price_percent" min="0" max="100" step="1" placeholder="0"
                  class="w-20 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-emerald-500 outline-none" />
              </div>
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
                    <FieldTextarea v-model="item.description" label="Descripción" :rows="2" :isSingle="true" />
                  </div>
                </template>
              </draggable>
              <button type="button" class="text-xs text-emerald-600 font-medium" @click="group.items.push({ icon: '', name: '', description: '' })">+ Agregar elemento</button>
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
              <label class="flex items-center gap-1 cursor-pointer" title="Si está marcado, este módulo aparecerá preseleccionado en la calculadora del cliente">
                <input type="checkbox" v-model="mod.selected" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                <span class="text-[10px] text-gray-500 font-medium">Seleccionado</span>
              </label>
              <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
                :class="mod.is_calculator_module ? 'bg-blue-100 text-blue-700 border-blue-300' : 'bg-gray-50 text-gray-400 border-gray-200'"
                :title="mod.is_calculator_module ? 'Este módulo aparece en la calculadora de inversión del cliente' : 'Este módulo NO aparece en la calculadora de inversión'"
                @click="mod.is_calculator_module = !mod.is_calculator_module">
                {{ mod.is_calculator_module ? '🧮 En calc.' : '🧮 No calc.' }}
              </button>
              <button type="button" class="text-[10px] font-medium px-2 py-1 rounded border transition-colors"
                :class="mod.is_visible !== false ? 'bg-emerald-100 text-emerald-700 border-emerald-300' : 'bg-red-50 text-red-500 border-red-200'"
                :title="mod.is_visible !== false ? 'Este módulo se muestra en la propuesta del cliente' : 'Este módulo está oculto en la propuesta del cliente'"
                @click="mod.is_visible = mod.is_visible === false ? true : false">
                {{ mod.is_visible !== false ? '👁 Visible' : '🚫 Oculto' }}
              </button>
              <button type="button" class="text-xs text-red-500 hover:text-red-700 ml-2" title="Eliminar este módulo de la propuesta" @click="form.additionalModules.splice(mIdx, 1)">Eliminar</button>
            </div>
          </div>
          <div v-show="!mod._collapsed" class="p-4">
            <div v-if="mod._pasteMode" class="space-y-3">
              <p class="text-[11px] text-gray-500">Contenido Markdown para este módulo.</p>
              <textarea v-model="mod._pasteText" rows="8" placeholder="Escribe o pega aquí el contenido de este módulo..."
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:ring-1 focus:ring-emerald-500 outline-none resize-y" />
            </div>
            <div v-else class="space-y-3">
              <div class="grid grid-cols-[100px_1fr_auto] gap-3 items-end">
                <EmojiIconField v-model="mod.icon" label="Icono" placeholder="🧩" />
                <FieldInput v-model="mod.title" label="Título del módulo" />
                <div class="flex flex-col gap-1" title="Porcentaje de la inversión total que representa este módulo. Se usa para calcular el precio en la calculadora">
                  <label class="text-[10px] text-gray-500 font-medium uppercase">% del precio</label>
                  <input type="number" v-model.number="mod.price_percent" min="0" max="100" step="1" placeholder="0"
                    class="w-20 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-emerald-500 outline-none" />
                </div>
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
                    </div>
                  </template>
                </draggable>
                <button type="button" class="text-xs text-emerald-600 font-medium" @click="mod.items.push({ icon: '', name: '', description: '' })">+ Agregar elemento</button>
              </div>
            </div>
          </div>
        </div>
        <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
          @click="form.additionalModules.push({ icon: '🧩', title: '', description: '', items: [], _pasteMode: false, _pasteText: '', _collapsed: false, is_calculator_module: false, selected: false })">
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
    <p v-if="validationError" class="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{{ validationError }}</p>

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
  props: { modelValue: [String, Number], label: String, placeholder: String },
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

const emit = defineEmits(['save', 'syncHostingPercent']);

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
const validationError = ref('');
const showRawJson = ref(false);
const hostingCollapsed = ref(true);
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

function recalcPaymentFromProposal() {
  if (!props.proposalData?.total_investment) return;
  const total = Number(props.proposalData.total_investment);
  if (!total) return;
  const cur = props.proposalData.currency || 'COP';
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

// Auto-recalculate payment option descriptions when proposal investment changes
if (sectionType.value === 'investment') {
  watch(() => props.proposalData?.total_investment, () => {
    recalcPaymentFromProposal();
  });

  // Sync hosting_percent from General tab → hostingPlan.hostingPercent
  watch(() => props.proposalData?.hosting_percent, (newVal) => {
    if (newVal != null && form.hostingPlan && form.hostingPlan.hostingPercent !== newVal) {
      form.hostingPlan.hostingPercent = newVal;
    }
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

function validateOptionalPrices() {
  const missing = [];
  const type = sectionType.value;

  if (type === 'investment') {
    const modules = form.modules || [];
    for (const mod of modules) {
      if (mod.is_required === false && !mod.price) {
        missing.push(mod.name || 'Módulo sin nombre');
      }
    }
  } else if (type === 'functional_requirements') {
    const allGroups = [...(form.groups || []), ...(form.additionalModules || [])];
    for (const group of allGroups) {
      for (const item of (group.items || [])) {
        if (item.is_required === false && !item.price) {
          missing.push(item.name || 'Elemento sin nombre');
        }
      }
    }
  }

  return missing;
}

function handleSave() {
  isSaving.value = true;
  savedMsg.value = '';
  validationError.value = '';
  try {
    // Hard validation: optional items must have a price
    const missingPrices = validateOptionalPrices();
    if (missingPrices.length > 0) {
      validationError.value = `No se puede guardar: los siguientes elementos opcionales (Obligatorio = No) no tienen precio asignado: ${missingPrices.join(', ')}`;
      isSaving.value = false;
      return;
    }

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
    // Sync hostingPercent back to General tab when saving the investment section
    if (sectionType.value === 'investment' && form.hostingPlan?.hostingPercent != null) {
      emit('syncHostingPercent', form.hostingPlan.hostingPercent);
    }
    savedMsg.value = '✓ Guardado';
    setTimeout(() => { savedMsg.value = ''; }, 3000);
  } finally {
    isSaving.value = false;
  }
}
</script>
