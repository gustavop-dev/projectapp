<template>
  <div class="technical-document-editor space-y-8" data-testid="technical-document-editor">
    <p class="text-xs text-text-muted">
      Detalle técnico: cómo se construye el sistema. Módulos del producto y requerimientos con <code class="text-[10px] bg-surface-raised px-1 rounded">epicKey</code> /
      <code class="text-[10px] bg-surface-raised px-1 rounded">flowKey</code> para enlazar después con el tablero en plataforma.
      Opcional: <code class="text-[10px] bg-surface-raised px-1 rounded">linked_module_ids</code> alinea el detalle técnico con módulos comerciales de la propuesta. Los ids legacy se normalizan automáticamente al guardar.
    </p>

    <div
      v-if="moduleLinkOptions.length"
      class="rounded-xl border border-dashed border-emerald-200 bg-primary-soft/40 p-4 space-y-2"
    >
      <p class="text-xs font-medium text-text-default">Plantilla genérica por módulo comercial</p>
      <p class="text-[11px] text-text-muted">
        Inserta un módulo con texto neutro y vínculo al alcance comercial. Si el vínculo apunta a alcance opcional, solo será visible cuando el cliente lo incluya.
      </p>
      <div class="flex flex-wrap items-end gap-2">
        <label class="text-xs text-text-muted/60 flex flex-col gap-1">
          <span>Módulo</span>
          <select
            v-model="stubModuleId"
            class="px-2 py-1.5 border dark:border-white/[0.08] rounded-lg text-sm min-w-[12rem] bg-surface dark:text-white"
          >
            <option value="">— Elegir —</option>
            <option v-for="opt in moduleLinkOptions" :key="'stub-'+opt.id" :value="opt.id">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <button
          type="button"
          class="text-xs px-3 py-2 bg-primary text-on-primary rounded-lg hover:bg-primary-strong"
          :disabled="!stubModuleId"
          @click="insertGenericStub"
        >
          Insertar módulo genérico
        </button>
      </div>
    </div>

    <!-- Propósito -->
    <section class="space-y-2">
      <h3 class="text-sm font-semibold text-text-default">Propósito</h3>
      <textarea
        v-model="doc.purpose"
        v-auto-resize
        data-testid="technical-purpose-textarea"
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 outline-none"
        placeholder="Una frase sobre qué cubre este documento..."
      />
    </section>

    <!-- Stack -->
    <section class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-default">Stack tecnológico</h3>
        <button type="button" class="text-xs text-text-brand hover:underline" @click="addStackRow">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.stack" :key="'st-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-surface-raised rounded-xl border border-border-muted">
        <input v-model="row.layer" placeholder="Capa" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <input v-model="row.technology" placeholder="Tecnología" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <div class="flex gap-2">
          <input v-model="row.rationale" placeholder="Justificación técnica" class="flex-1 px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
          <button type="button" class="text-xs text-red-500 shrink-0" @click="doc.stack.splice(i, 1)">✕</button>
        </div>
      </div>
    </section>

    <!-- Arquitectura -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">Arquitectura</h3>
      <textarea v-model="doc.architecture.summary" v-auto-resize class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm" placeholder="Resumen de capas y comunicación..." />
      <div class="flex items-center justify-between">
        <span class="text-xs text-text-muted">Patrones por componente</span>
        <button type="button" class="text-xs text-text-brand hover:underline" @click="addPatternRow">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.architecture.patterns" :key="'pat-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-surface-raised rounded-xl border border-border-muted">
        <input v-model="row.component" placeholder="Componente" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <input v-model="row.pattern" placeholder="Patrón" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <div class="flex gap-2">
          <input v-model="row.description" placeholder="Descripción" class="flex-1 px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
          <button type="button" class="text-xs text-red-500" @click="doc.architecture.patterns.splice(i, 1)">✕</button>
        </div>
      </div>
      <p class="text-xs text-text-muted">Diagramas / anexo (opcional)</p>
      <textarea
        v-model="doc.architecture.diagramNote"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm"
        placeholder="Nota breve si hay diagrama en anexo o URL externa..."
      />
    </section>

    <!-- Modelo de datos -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">Modelo de datos</h3>
      <textarea v-model="doc.dataModel.summary" v-auto-resize class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm" placeholder="Resumen..." />
      <p class="text-xs text-text-muted">Relaciones entre entidades (texto)</p>
      <textarea
        v-model="doc.dataModel.relationships"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm"
        placeholder="Ej. Usuario tiene muchos Pedidos..."
      />
      <div class="flex justify-end">
        <button type="button" class="text-xs text-text-brand hover:underline" @click="addEntityRow">+ Entidad</button>
      </div>
      <div v-for="(row, i) in doc.dataModel.entities" :key="'ent-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-surface-raised rounded-xl border border-border-muted">
        <input v-model="row.name" placeholder="Entidad" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <input v-model="row.description" placeholder="Descripción" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <div class="flex gap-2">
          <input v-model="row.keyFields" placeholder="Campos clave (texto libre)" class="flex-1 px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
          <button type="button" class="text-xs text-red-500" @click="doc.dataModel.entities.splice(i, 1)">✕</button>
        </div>
      </div>
    </section>

    <!-- Preparación para el crecimiento -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">Preparación para el crecimiento</h3>
      <p class="text-xs text-text-muted">
        Cómo se prepara el sistema para crecer (tráfico, datos, equipos, integraciones). Complementa «Rendimiento»; aquí el foco es capacidad de evolución, no solo métricas puntuales.
      </p>
      <textarea
        v-model="doc.growthReadiness.summary"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 outline-none"
        placeholder="Resumen: enfoque de crecimiento sin rediseño completo, supuestos y límites..."
      />
      <div class="flex items-center justify-between">
        <span class="text-xs text-text-muted">Estrategias por dimensión (tabla)</span>
        <button type="button" class="text-xs text-text-brand hover:underline" @click="addGrowthStrategyRow">+ Fila</button>
      </div>
      <div
        v-for="(row, i) in doc.growthReadiness.strategies"
        :key="'gr-' + i"
        class="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-surface-raised rounded-xl border border-border-muted"
      >
        <input v-model="row.dimension" placeholder="Dimensión (ej. tráfico, datos)" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <input v-model="row.preparation" placeholder="Preparación actual" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <div class="flex gap-2">
          <input v-model="row.evolution" placeholder="Evolución ante crecimiento" class="flex-1 px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
          <button type="button" class="text-xs text-red-500 shrink-0" @click="doc.growthReadiness.strategies.splice(i, 1)">✕</button>
        </div>
      </div>
    </section>

    <!-- Módulos del producto -->
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-default">Módulos del producto</h3>
        <button type="button" class="text-xs px-3 py-1.5 bg-primary text-on-primary rounded-lg" @click="addEpic">+ Módulo</button>
      </div>
      <div
        v-for="(epic, ei) in doc.epics"
        :key="'epic-' + ei"
        class="border border-border-default dark:border-white/[0.08] rounded-xl p-4 space-y-3 bg-surface"
      >
        <div class="flex flex-wrap gap-2 items-start justify-between">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 flex-1 min-w-0">
            <input v-model="epic.epicKey" placeholder="epicKey (slug único)" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm font-mono text-xs">
            <input v-model="epic.title" placeholder="Título del módulo" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
          </div>
          <button type="button" class="text-xs text-red-600" @click="doc.epics.splice(ei, 1)">Eliminar módulo</button>
        </div>
        <textarea v-model="epic.description" v-auto-resize data-testid="technical-epic-description-textarea" class="w-full px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm" placeholder="Descripción del módulo" />
        <div v-if="moduleLinkOptions.length" class="space-y-1">
          <p class="text-[11px] text-text-muted">Vincular este módulo técnico con alcance comercial (modo técnico / PDF técnico):</p>
          <div class="flex flex-wrap gap-x-3 gap-y-1">
            <label
              v-for="opt in moduleLinkOptions"
              :key="'epl-'+ei+'-'+opt.id"
              class="flex items-center gap-1.5 text-xs text-text-default cursor-pointer"
            >
              <input
                type="checkbox"
                :checked="epic.linked_module_ids.includes(opt.id)"
                class="rounded border-gray-300 dark:border-white/[0.08] text-text-brand"
                @change="toggleLinkedId(epic.linked_module_ids, opt.id)"
              >
              <span class="max-w-[14rem] truncate" :title="opt.label">{{ opt.label }}</span>
            </label>
          </div>
        </div>
        <div class="pl-3 border-l-2 border-emerald-200 space-y-2">
          <div class="flex justify-between items-center">
            <span class="text-xs font-medium text-text-muted/60">Requerimientos</span>
            <button type="button" class="text-xs text-text-brand" @click="addRequirement(epic)">+ Requerimiento</button>
          </div>
          <div
            v-for="(req, ri) in epic.requirements"
            :key="'req-' + ei + '-' + ri"
            class="p-3 bg-surface-raised rounded-lg space-y-2 text-sm"
          >
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input v-model="req.flowKey" placeholder="flowKey (slug único global)" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded font-mono text-xs">
              <input v-model="req.title" placeholder="Título (obligatorio)" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
              <select v-model="req.priority" class="px-2 py-1 border border-input-border bg-input-bg text-input-text rounded text-xs">
                <option value="">Prioridad (opc.)</option>
                <option value="critical">Crítico</option>
                <option value="high">Alta</option>
                <option value="medium">Media</option>
                <option value="low">Baja</option>
              </select>
            </div>
            <textarea v-model="req.description" v-auto-resize data-testid="technical-req-description-textarea" class="w-full px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-xs" placeholder="Descripción" />
            <textarea v-model="req.configuration" v-auto-resize class="w-full px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-xs" placeholder="Configuración (roles, permisos...)" />
            <textarea v-model="req.usageFlow" v-auto-resize class="w-full px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-xs" placeholder="Flujo de uso (ej. Login → Dashboard → ...)" />
            <div v-if="moduleLinkOptions.length" class="space-y-1 pt-1">
              <p class="text-[10px] text-text-muted">Vincular a alcance comercial (vacío = alcance base, siempre visible):</p>
              <div class="flex flex-wrap gap-x-2 gap-y-1">
                <label
                  v-for="opt in moduleLinkOptions"
                  :key="'rql-'+ei+'-'+ri+'-'+opt.id"
                  class="flex items-center gap-1 text-[11px] text-text-default cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :checked="req.linked_module_ids.includes(opt.id)"
                    class="rounded border-gray-300 dark:border-white/[0.08] text-text-brand"
                    @change="toggleLinkedId(req.linked_module_ids, opt.id)"
                  >
                  <span class="max-w-[10rem] truncate" :title="opt.label">{{ opt.label }}</span>
                </label>
              </div>
            </div>
            <button type="button" class="text-xs text-red-500" @click="epic.requirements.splice(ri, 1)">Quitar requerimiento</button>
          </div>
        </div>
      </div>
    </section>

    <!-- API (resumen por dominio) -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">API y endpoints (resumen)</h3>
      <textarea
        v-model="doc.apiSummary"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm"
        placeholder="Resumen de la API sin enumerar cada ruta..."
      />
      <div class="flex items-center justify-between">
        <span class="text-xs text-text-muted">Por dominio / módulo</span>
        <button type="button" class="text-xs text-text-brand hover:underline" @click="addApiDomain">+ Dominio</button>
      </div>
      <div v-for="(row, i) in doc.apiDomains" :key="'api-' + i" class="grid grid-cols-1 md:grid-cols-2 gap-2 p-3 bg-surface-raised rounded-xl border border-border-muted">
        <input v-model="row.domain" placeholder="Dominio o área" class="px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
        <div class="flex gap-2">
          <input v-model="row.summary" placeholder="Resumen de endpoints / contratos" class="flex-1 px-2 py-1.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm">
          <button type="button" class="text-xs text-red-500" @click="doc.apiDomains.splice(i, 1)">✕</button>
        </div>
      </div>
    </section>

    <!-- Integraciones -->
    <section class="space-y-4">
      <h3 class="text-sm font-semibold text-text-default">Integraciones incluidas</h3>
      <button type="button" class="text-xs text-text-brand mb-2" @click="addIncluded">+ Fila</button>
      <div v-for="(row, i) in doc.integrations.included" :key="'inc-' + i" class="grid grid-cols-1 md:grid-cols-5 gap-2 p-2 bg-surface-raised rounded-lg text-xs">
        <input v-model="row.service" placeholder="Servicio" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.provider" placeholder="Proveedor" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.connection" placeholder="Conexión" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.dataExchange" placeholder="Datos" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.accountOwner" placeholder="Responsable cuenta" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.integrations.included.splice(i, 1)">✕</button>
        </div>
      </div>
      <h3 class="text-sm font-semibold text-text-default pt-2">No incluidas</h3>
      <button type="button" class="text-xs text-text-brand mb-2" @click="addExcluded">+ Fila</button>
      <div v-for="(row, i) in doc.integrations.excluded" :key="'exc-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-2 bg-surface-raised rounded-lg text-xs">
        <input v-model="row.service" placeholder="Servicio" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.reason" placeholder="Motivo" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.availability" placeholder="Disponibilidad futura" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.integrations.excluded.splice(i, 1)">✕</button>
        </div>
      </div>
      <p class="text-xs text-text-muted pt-2">Notas técnicas (viñetas, una por línea)</p>
      <textarea
        v-model="doc.integrations.notes"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm font-mono text-xs"
        placeholder="Línea por línea..."
      />
    </section>

    <!-- Ambientes -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">Ambientes (opcional)</h3>
      <textarea
        v-model="doc.environmentsNote"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm"
        placeholder="Nota general sobre ambientes si no usas tabla..."
      />
      <div class="flex items-center justify-between">
        <span class="text-xs text-text-muted">Tabla por ambiente</span>
        <button type="button" class="text-xs text-text-brand hover:underline" @click="addEnvironmentRow">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.environments" :key="'env-' + i" class="grid grid-cols-1 md:grid-cols-5 gap-2 p-2 bg-surface-raised rounded-lg text-xs">
        <input v-model="row.name" placeholder="Nombre" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.purpose" placeholder="Propósito" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.url" placeholder="URL / acceso" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.database" placeholder="Base de datos" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.whoAccesses" placeholder="Quién accede" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.environments.splice(i, 1)">✕</button>
        </div>
      </div>
    </section>

    <!-- Seguridad -->
    <section class="space-y-2">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-semibold text-text-default">Seguridad técnica</h3>
        <button type="button" class="text-xs text-text-brand" @click="addSecurityRow">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.security" :key="'sec-' + i" class="flex gap-2 p-2 bg-surface-raised rounded-lg">
        <input v-model="row.aspect" placeholder="Aspecto" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-sm">
        <input v-model="row.implementation" placeholder="Implementación" class="flex-[2] px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-sm">
        <button type="button" class="text-red-500 text-xs" @click="doc.security.splice(i, 1)">✕</button>
      </div>
    </section>

    <!-- Rendimiento y calidad -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">Rendimiento y calidad</h3>
      <p class="text-xs text-text-muted">Métricas</p>
      <button type="button" class="text-xs text-text-brand" @click="addMetric">+ Métrica</button>
      <div v-for="(row, i) in doc.performanceQuality.metrics" :key="'met-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-2 bg-surface-raised rounded-lg text-sm">
        <input v-model="row.metric" placeholder="Métrica" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.target" placeholder="Objetivo" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.howMeasured" placeholder="Cómo se mide" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.performanceQuality.metrics.splice(i, 1)">✕</button>
        </div>
      </div>
      <p class="text-xs text-text-muted">Prácticas</p>
      <button type="button" class="text-xs text-text-brand" @click="addPractice">+ Práctica</button>
      <div v-for="(row, i) in doc.performanceQuality.practices" :key="'prac-' + i" class="flex gap-2 p-2 bg-surface-raised rounded-lg">
        <input v-model="row.strategy" placeholder="Estrategia" class="w-1/3 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-sm">
        <input v-model="row.description" placeholder="Descripción" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded text-sm">
        <button type="button" class="text-red-500" @click="doc.performanceQuality.practices.splice(i, 1)">✕</button>
      </div>
    </section>

    <!-- Backups -->
    <section class="space-y-2">
      <h3 class="text-sm font-semibold text-text-default">Backups</h3>
      <textarea
        v-model="doc.backupsNote"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm"
        placeholder="Hosting propio vs según proveedor del cliente..."
      />
    </section>

    <!-- Calidad (pruebas) -->
    <section class="space-y-3">
      <h3 class="text-sm font-semibold text-text-default">Calidad y pruebas</h3>
      <div class="flex items-center justify-between">
        <span class="text-xs text-text-muted">Dimensiones</span>
        <button type="button" class="text-xs text-text-brand" @click="addQualityDimension">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.quality.dimensions" :key="'qd-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-2 bg-surface-raised rounded-lg text-sm">
        <input v-model="row.dimension" placeholder="Dimensión" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.evaluates" placeholder="Qué evalúa" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.standard" placeholder="Estándar / umbral" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.quality.dimensions.splice(i, 1)">✕</button>
        </div>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-xs text-text-muted">Tipos de prueba</span>
        <button type="button" class="text-xs text-text-brand" @click="addTestType">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.quality.testTypes" :key="'qt-' + i" class="grid grid-cols-1 md:grid-cols-4 gap-2 p-2 bg-surface-raised rounded-lg text-xs">
        <input v-model="row.type" placeholder="Tipo" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.validates" placeholder="Qué valida" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.tool" placeholder="Herramienta" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.whenRun" placeholder="Cuándo" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.quality.testTypes.splice(i, 1)">✕</button>
        </div>
      </div>
      <p class="text-xs text-text-muted">Flujos críticos de aceptación (texto; no duplicar módulos)</p>
      <textarea
        v-model="doc.quality.criticalFlowsNote"
        v-auto-resize
        class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm"
        placeholder="Alineación con requerimientos priorizados..."
      />
    </section>

    <!-- Decisiones -->
    <section class="space-y-2">
      <div class="flex justify-between">
        <h3 class="text-sm font-semibold text-text-default">Decisiones técnicas (ADRs)</h3>
        <button type="button" class="text-xs text-text-brand" @click="addDecision">+ Fila</button>
      </div>
      <div v-for="(row, i) in doc.decisions" :key="'dec-' + i" class="grid grid-cols-1 md:grid-cols-3 gap-2 p-2 bg-surface-raised rounded-lg text-sm">
        <input v-model="row.decision" placeholder="Decisión" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <input v-model="row.alternative" placeholder="Alternativa descartada" class="px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
        <div class="flex gap-1">
          <input v-model="row.reason" placeholder="Razón" class="flex-1 px-2 py-1 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded">
          <button type="button" class="text-red-500" @click="doc.decisions.splice(i, 1)">✕</button>
        </div>
      </div>
    </section>

    <div class="flex items-center gap-4 pt-4 border-t dark:border-white/[0.06]">
      <button
        type="button"
        :disabled="isSaving"
        class="px-5 py-2.5 bg-primary text-on-primary rounded-xl text-sm font-medium hover:bg-primary-strong disabled:opacity-50"
        @click="handleSave"
      >
        {{ isSaving ? 'Guardando...' : 'Guardar detalle técnico' }}
      </button>
      <span v-if="savedMsg" class="text-sm text-text-brand">{{ savedMsg }}</span>
      <span v-if="validationError" class="text-sm text-red-600">{{ validationError }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { createGenericTechnicalEpicStub } from '~/utils/technicalModuleStub';
import {
  buildProposalModuleIdAliasMapFromOptions,
  normalizeLinkedModuleIds,
} from '~/utils/proposalModuleLinkOptions';

const vAutoResize = {
  mounted(el) {
    el.style.overflow = 'hidden';

    const computeMinHeight = () => {
      const rows = parseInt(el.getAttribute('rows'), 10) || 3;
      const cs = window.getComputedStyle(el);
      const lineHeight =
        parseFloat(cs.lineHeight) ||
        parseFloat(cs.fontSize) * 1.5;
      const paddingY =
        parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
      const borderY =
        parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
      return rows * lineHeight + paddingY + borderY;
    };

    el._autoResizeMinHeight = computeMinHeight();
    el._autoResizeHandler = () => {
      el.style.height = 'auto';
      const next = Math.max(el.scrollHeight, el._autoResizeMinHeight);
      if (el._autoResizeLastHeight === next) return;
      el._autoResizeLastHeight = next;
      el.style.height = next + 'px';
    };
    el.addEventListener('input', el._autoResizeHandler);
    el._autoResizeHandler();
  },
  updated(el) {
    if (!el._autoResizeHandler) return;
    el._autoResizeHandler();
  },
  beforeUnmount(el) {
    el.removeEventListener('input', el._autoResizeHandler);
  },
};

const props = defineProps({
  section: { type: Object, required: true },
  /** { id, label }[] from proposal FR + investment modules */
  moduleLinkOptions: { type: Array, default: () => [] },
});

const emit = defineEmits(['save']);

const isSaving = ref(false);
const savedMsg = ref('');
const validationError = ref('');
const stubModuleId = ref('');
const moduleAliasMap = computed(() =>
  buildProposalModuleIdAliasMapFromOptions(props.moduleLinkOptions),
);

function normLinkedIds(raw) {
  return normalizeLinkedModuleIds(raw, moduleAliasMap.value);
}

function toggleLinkedId(arr, id) {
  const i = arr.indexOf(id);
  if (i >= 0) arr.splice(i, 1);
  else arr.push(id);
}

function insertGenericStub() {
  if (!stubModuleId.value) return;
  const opt = props.moduleLinkOptions.find((o) => o.id === stubModuleId.value);
  doc.epics.push(createGenericTechnicalEpicStub(stubModuleId.value, opt?.label || ''));
}

function emptyDoc() {
  return {
    purpose: '',
    stack: [],
    architecture: { summary: '', patterns: [], diagramNote: '' },
    dataModel: { summary: '', relationships: '', entities: [] },
    growthReadiness: { summary: '', strategies: [] },
    epics: [],
    apiSummary: '',
    apiDomains: [],
    integrations: { included: [], excluded: [], notes: '' },
    environments: [],
    environmentsNote: '',
    security: [],
    performanceQuality: { metrics: [], practices: [] },
    backupsNote: '',
    quality: { dimensions: [], testTypes: [], criticalFlowsNote: '' },
    decisions: [],
  };
}

function mergeContent(src) {
  const e = emptyDoc();
  if (!src || typeof src !== 'object') return e;
  return {
    purpose: typeof src.purpose === 'string' ? src.purpose : e.purpose,
    stack: Array.isArray(src.stack) ? src.stack.map((r) => ({
      layer: r.layer || '',
      technology: r.technology || '',
      rationale: r.rationale || '',
    })) : e.stack,
    architecture: {
      summary: src.architecture?.summary || '',
      diagramNote: typeof src.architecture?.diagramNote === 'string' ? src.architecture.diagramNote : '',
      patterns: Array.isArray(src.architecture?.patterns)
        ? src.architecture.patterns.map((r) => ({
          component: r.component || '',
          pattern: r.pattern || '',
          description: r.description || '',
        }))
        : [],
    },
    dataModel: {
      summary: src.dataModel?.summary || '',
      relationships: typeof src.dataModel?.relationships === 'string' ? src.dataModel.relationships : '',
      entities: Array.isArray(src.dataModel?.entities)
        ? src.dataModel.entities.map((r) => ({
          name: r.name || '',
          description: r.description || '',
          keyFields: r.keyFields || '',
        }))
        : [],
    },
    growthReadiness: {
      summary: typeof src.growthReadiness?.summary === 'string' ? src.growthReadiness.summary : '',
      strategies: Array.isArray(src.growthReadiness?.strategies)
        ? src.growthReadiness.strategies.map((r) => ({
          dimension: r.dimension || '',
          preparation: r.preparation || '',
          evolution: r.evolution || '',
        }))
        : [],
    },
    apiSummary: typeof src.apiSummary === 'string' ? src.apiSummary : '',
    apiDomains: Array.isArray(src.apiDomains)
      ? src.apiDomains.map((r) => ({
        domain: r.domain || '',
        summary: r.summary || '',
      }))
      : [],
    epics: Array.isArray(src.epics)
      ? src.epics.map((ep) => ({
        epicKey: ep.epicKey || '',
        title: ep.title || '',
        description: ep.description || '',
        linked_module_ids: normLinkedIds(ep.linked_module_ids || ep.linkedModuleIds),
        requirements: Array.isArray(ep.requirements)
          ? ep.requirements.map((req) => ({
            flowKey: req.flowKey || '',
            title: req.title || '',
            description: req.description || '',
            configuration: req.configuration || '',
            usageFlow: req.usageFlow || '',
            priority: typeof req.priority === 'string' ? req.priority : '',
            linked_module_ids: normLinkedIds(req.linked_module_ids || req.linkedModuleIds),
          }))
          : [],
      }))
      : [],
    integrations: {
      notes: typeof src.integrations?.notes === 'string' ? src.integrations.notes : '',
      included: Array.isArray(src.integrations?.included)
        ? src.integrations.included.map((r) => ({
          service: r.service || '',
          provider: r.provider || '',
          connection: r.connection || '',
          dataExchange: r.dataExchange || '',
          accountOwner: r.accountOwner || '',
        }))
        : [],
      excluded: Array.isArray(src.integrations?.excluded)
        ? src.integrations.excluded.map((r) => ({
          service: r.service || '',
          reason: r.reason || '',
          availability: r.availability || '',
        }))
        : [],
    },
    environments: Array.isArray(src.environments)
      ? src.environments.map((r) => ({
        name: r.name || '',
        purpose: r.purpose || '',
        url: r.url || '',
        database: r.database || '',
        whoAccesses: r.whoAccesses || '',
      }))
      : [],
    environmentsNote: typeof src.environmentsNote === 'string' ? src.environmentsNote : '',
    security: Array.isArray(src.security)
      ? src.security.map((r) => ({ aspect: r.aspect || '', implementation: r.implementation || '' }))
      : [],
    performanceQuality: {
      metrics: Array.isArray(src.performanceQuality?.metrics)
        ? src.performanceQuality.metrics.map((r) => ({
          metric: r.metric || '',
          target: r.target || '',
          howMeasured: r.howMeasured || '',
        }))
        : [],
      practices: Array.isArray(src.performanceQuality?.practices)
        ? src.performanceQuality.practices.map((r) => ({
          strategy: r.strategy || '',
          description: r.description || '',
        }))
        : [],
    },
    backupsNote: typeof src.backupsNote === 'string' ? src.backupsNote : '',
    quality: {
      dimensions: Array.isArray(src.quality?.dimensions)
        ? src.quality.dimensions.map((r) => ({
          dimension: r.dimension || '',
          evaluates: r.evaluates || '',
          standard: r.standard || '',
        }))
        : [],
      testTypes: Array.isArray(src.quality?.testTypes)
        ? src.quality.testTypes.map((r) => ({
          type: r.type || '',
          validates: r.validates || '',
          tool: r.tool || '',
          whenRun: r.whenRun || '',
        }))
        : [],
      criticalFlowsNote: typeof src.quality?.criticalFlowsNote === 'string' ? src.quality.criticalFlowsNote : '',
    },
    decisions: Array.isArray(src.decisions)
      ? src.decisions.map((r) => ({
        decision: r.decision || '',
        alternative: r.alternative || '',
        reason: r.reason || '',
      }))
      : [],
  };
}

const doc = reactive(mergeContent(props.section.content_json));

watch(
  () => props.section.content_json,
  (cj) => {
    Object.assign(doc, mergeContent(cj));
  },
  { deep: true },
);

function addStackRow() {
  doc.stack.push({ layer: '', technology: '', rationale: '' });
}
function addPatternRow() {
  doc.architecture.patterns.push({ component: '', pattern: '', description: '' });
}
function addEntityRow() {
  doc.dataModel.entities.push({ name: '', description: '', keyFields: '' });
}
function addGrowthStrategyRow() {
  doc.growthReadiness.strategies.push({ dimension: '', preparation: '', evolution: '' });
}
function addEpic() {
  doc.epics.push({
    epicKey: '',
    title: '',
    description: '',
    linked_module_ids: [],
    requirements: [],
  });
}
function addRequirement(epic) {
  epic.requirements.push({
    flowKey: '',
    title: '',
    description: '',
    configuration: '',
    usageFlow: '',
    priority: '',
    linked_module_ids: [],
  });
}
function addApiDomain() {
  doc.apiDomains.push({ domain: '', summary: '' });
}
function addEnvironmentRow() {
  doc.environments.push({
    name: '',
    purpose: '',
    url: '',
    database: '',
    whoAccesses: '',
  });
}
function addQualityDimension() {
  doc.quality.dimensions.push({ dimension: '', evaluates: '', standard: '' });
}
function addTestType() {
  doc.quality.testTypes.push({ type: '', validates: '', tool: '', whenRun: '' });
}
function addIncluded() {
  doc.integrations.included.push({
    service: '',
    provider: '',
    connection: '',
    dataExchange: '',
    accountOwner: '',
  });
}
function addExcluded() {
  doc.integrations.excluded.push({ service: '', reason: '', availability: '' });
}
function addSecurityRow() {
  doc.security.push({ aspect: '', implementation: '' });
}
function addMetric() {
  doc.performanceQuality.metrics.push({ metric: '', target: '', howMeasured: '' });
}
function addPractice() {
  doc.performanceQuality.practices.push({ strategy: '', description: '' });
}
function addDecision() {
  doc.decisions.push({ decision: '', alternative: '', reason: '' });
}

const slugRe = /^[a-z0-9]+(-[a-z0-9]+)*$/;

function validate() {
  const keys = new Set();
  for (let ei = 0; ei < doc.epics.length; ei++) {
    const ep = doc.epics[ei];
    if (ep.epicKey && !slugRe.test(ep.epicKey)) {
      return `epicKey inválido en módulo "${ep.title || ei + 1}": use solo minúsculas, números y guiones.`;
    }
    if (ep.epicKey) {
      if (keys.has(`e:${ep.epicKey}`)) return `epicKey duplicado: ${ep.epicKey}`;
      keys.add(`e:${ep.epicKey}`);
    }
    for (let ri = 0; ri < ep.requirements.length; ri++) {
      const req = ep.requirements[ri];
      if (req.flowKey && !slugRe.test(req.flowKey)) {
        return `flowKey inválido: ${req.flowKey}`;
      }
      if (req.flowKey) {
        if (keys.has(`f:${req.flowKey}`)) return `flowKey duplicado: ${req.flowKey}`;
        keys.add(`f:${req.flowKey}`);
      }
      if ((req.title || '').trim() === '' && (req.flowKey || req.description || req.configuration || req.usageFlow)) {
        return 'Cada requerimiento con contenido debe tener título.';
      }
    }
  }
  return '';
}

function toJson() {
  return JSON.parse(JSON.stringify(doc));
}

function handleSave() {
  validationError.value = '';
  const err = validate();
  if (err) {
    validationError.value = err;
    return;
  }
  isSaving.value = true;
  savedMsg.value = '';
  emit('save', {
    sectionId: props.section.id,
    payload: {
      title: props.section.title,
      is_wide_panel: props.section.is_wide_panel,
      content_json: toJson(),
    },
  });
  savedMsg.value = '✓ Guardado';
  setTimeout(() => { savedMsg.value = ''; }, 3000);
  isSaving.value = false;
}
</script>
