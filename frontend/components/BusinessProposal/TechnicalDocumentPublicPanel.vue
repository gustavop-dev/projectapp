<template>
  <section ref="sectionRef" class="technical-doc-public min-h-screen w-full bg-white flex items-center">
    <div class="w-full px-6 md:px-12 lg:px-24 py-12 md:py-10">
      <div class="max-w-5xl mx-auto">
        <!-- Intro -->
        <template v-if="fragment === 'intro'">
          <div data-animate="fade-up" class="mb-8">
            <h2 class="text-esmerald font-light text-3xl md:text-5xl leading-tight mb-6">
              {{ titles.intro }}
            </h2>
            <p v-if="purposeText" class="text-esmerald/80 font-light text-lg md:text-xl leading-relaxed whitespace-pre-wrap">
              {{ purposeText }}
            </p>
          </div>
          <div v-if="anchorLabels.length" data-animate="fade-up" class="rounded-2xl border border-esmerald/15 bg-esmerald/5 p-6 md:p-8">
            <h3 class="text-xs uppercase tracking-[0.2em] text-green-light font-medium mb-4">
              {{ language === 'en' ? 'In this document' : 'En este documento' }}
            </h3>
            <ul class="space-y-2">
              <li v-for="(label, i) in anchorLabels" :key="i" class="text-esmerald/90 font-light text-sm md:text-base flex gap-2">
                <span class="text-esmerald/40 font-mono text-xs mt-0.5">{{ i + 1 }}.</span>
                <span>{{ label }}</span>
              </li>
            </ul>
          </div>
          <p class="mt-10 text-center text-xs text-esmerald/50 font-light">
            {{ supportLine }}
          </p>
        </template>

        <!-- Stack -->
        <template v-else-if="fragment === 'stack'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-8">{{ titles.stack }}</h2>
          <div class="overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm text-left">
              <thead class="bg-esmerald text-lemon">
                <tr>
                  <th class="px-4 py-3 font-medium">{{ language === 'en' ? 'Layer' : 'Capa' }}</th>
                  <th class="px-4 py-3 font-medium">{{ language === 'en' ? 'Technology' : 'Tecnología' }}</th>
                  <th class="px-4 py-3 font-medium">{{ language === 'en' ? 'Why' : 'Por qué' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in stackRows" :key="i" class="border-t border-esmerald/10 odd:bg-white even:bg-esmerald/[0.03]">
                  <td class="px-4 py-3 text-esmerald/90">{{ row.layer }}</td>
                  <td class="px-4 py-3 text-esmerald/90">{{ row.technology }}</td>
                  <td class="px-4 py-3 text-esmerald/70 font-light">{{ row.rationale }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Architecture -->
        <template v-else-if="fragment === 'architecture'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.architecture }}</h2>
          <p v-if="arch.summary" class="text-esmerald/80 font-light leading-relaxed mb-8 whitespace-pre-wrap">{{ arch.summary }}</p>
          <div v-if="patternRows.length" class="overflow-x-auto rounded-xl border border-esmerald/10 mb-6">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Component' : 'Componente' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Pattern' : 'Patrón' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Description' : 'Descripción' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in patternRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90">{{ row.component }}</td>
                  <td class="px-4 py-2 text-esmerald/90">{{ row.pattern }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.description }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="arch.diagramNote" class="text-sm text-esmerald/60 font-light whitespace-pre-wrap">{{ arch.diagramNote }}</p>
        </template>

        <!-- Data model -->
        <template v-else-if="fragment === 'dataModel'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.dataModel }}</h2>
          <p v-if="dm.summary" class="text-esmerald/80 font-light leading-relaxed mb-4 whitespace-pre-wrap">{{ dm.summary }}</p>
          <p v-if="dm.relationships" class="text-esmerald/70 font-light text-sm mb-8 whitespace-pre-wrap">{{ dm.relationships }}</p>
          <div v-if="entityRows.length" class="overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Entity' : 'Entidad' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Description' : 'Descripción' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Key fields' : 'Campos clave' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in entityRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90">{{ row.name }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.description }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.keyFields }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Growth readiness -->
        <template v-else-if="fragment === 'growthReadiness'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.growthReadiness }}</h2>
          <p v-if="growthSummary" class="text-esmerald/80 font-light leading-relaxed mb-8 whitespace-pre-wrap">{{ growthSummary }}</p>
          <div v-if="growthStrategyRows.length" class="overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Dimension' : 'Dimensión' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Preparation' : 'Preparación' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Evolution' : 'Evolución' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in growthStrategyRows" :key="'gr-' + i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90 align-top">{{ row.dimension }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light align-top whitespace-pre-wrap">{{ row.preparation }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light align-top whitespace-pre-wrap">{{ row.evolution }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Epics -->
        <template v-else-if="fragment === 'epics'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.epics }}</h2>
          <div class="space-y-8">
            <article
              v-for="(epic, ei) in epicsList"
              :key="'epic-card-' + ei"
              class="rounded-2xl border border-esmerald/15 bg-gradient-to-b from-white to-esmerald/[0.03] shadow-sm overflow-hidden"
            >
              <header class="px-5 py-4 border-b border-esmerald/10 bg-esmerald/[0.04]">
                <h3 class="text-lg md:text-xl font-medium text-esmerald leading-snug">
                  {{ epic.title || epic.epicKey }}
                </h3>
                <p v-if="epic.description" class="text-sm text-esmerald/65 font-light mt-2 whitespace-pre-wrap leading-relaxed">
                  {{ epic.description }}
                </p>
              </header>
              <div class="overflow-x-auto">
                <table class="w-full text-sm text-left">
                  <thead class="bg-esmerald text-lemon text-xs uppercase tracking-wide">
                    <tr>
                      <th class="px-4 py-3 font-medium">{{ language === 'en' ? 'Requirement' : 'Requerimiento' }}</th>
                      <th class="px-4 py-3 font-medium w-28">{{ language === 'en' ? 'Priority' : 'Prioridad' }}</th>
                      <th class="px-4 py-3 font-medium w-52">{{ language === 'en' ? 'Summary' : 'Resumen' }}</th>
                      <th class="px-4 py-3 font-medium w-32 text-right">{{ language === 'en' ? 'Detail' : 'Detalle' }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(req, ri) in epic.requirements"
                      :key="'req-row-' + ei + '-' + ri"
                      class="border-t border-esmerald/10 odd:bg-white even:bg-esmerald/[0.02]"
                    >
                      <td class="px-4 py-3 text-esmerald/90 font-medium align-top">
                        {{ req.title }}
                        <code v-if="req.flowKey" class="block mt-1 text-[10px] text-esmerald/45 font-mono">{{ req.flowKey }}</code>
                      </td>
                      <td class="px-4 py-3 align-top">
                        <span
                          v-if="req.priority"
                          class="inline-block text-[10px] uppercase tracking-wider px-2 py-1 rounded-full bg-esmerald/12 text-esmerald/85"
                        >{{ priorityLabel(req.priority) }}</span>
                        <span v-else class="text-esmerald/35">—</span>
                      </td>
                      <td class="px-4 py-3 text-esmerald/65 font-light align-top text-xs leading-relaxed">
                        {{ snippetText(req.description) }}
                      </td>
                      <td class="px-4 py-3 align-top text-right">
                        <button
                          type="button"
                          class="text-xs font-medium text-teal-700 hover:text-teal-900 underline decoration-teal-600/40 underline-offset-2"
                          @click="openRequirementModal(epic.title || epic.epicKey, req)"
                        >
                          {{ language === 'en' ? 'Open' : 'Abrir' }}
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          </div>
        </template>

        <!-- API -->
        <template v-else-if="fragment === 'api'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.api }}</h2>
          <p v-if="apiSummary" class="text-esmerald/80 font-light leading-relaxed mb-8 whitespace-pre-wrap">{{ apiSummary }}</p>
          <div v-if="apiDomainRows.length" class="overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Domain' : 'Dominio' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Summary' : 'Resumen' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in apiDomainRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90">{{ row.domain }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light whitespace-pre-wrap">{{ row.summary }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Integrations -->
        <template v-else-if="fragment === 'integrations'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-8">{{ titles.integrations }}</h2>
          <div v-if="includedRows.length" class="mb-8">
            <h3 class="text-sm font-semibold text-esmerald mb-3">{{ language === 'en' ? 'Included' : 'Incluidas' }}</h3>
            <div class="overflow-x-auto rounded-xl border border-esmerald/10 text-xs md:text-sm">
              <table class="w-full text-left">
                <thead class="bg-esmerald text-lemon">
                  <tr>
                    <th class="px-3 py-2">{{ language === 'en' ? 'Service' : 'Servicio' }}</th>
                    <th class="px-3 py-2">{{ language === 'en' ? 'Provider' : 'Proveedor' }}</th>
                    <th class="px-3 py-2">{{ language === 'en' ? 'Connection' : 'Conexión' }}</th>
                    <th class="px-3 py-2">{{ language === 'en' ? 'Data' : 'Datos' }}</th>
                    <th class="px-3 py-2">{{ language === 'en' ? 'Account' : 'Cuenta' }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in includedRows" :key="i" class="border-t border-esmerald/10">
                    <td class="px-3 py-2 text-esmerald/90">{{ row.service }}</td>
                    <td class="px-3 py-2 text-esmerald/80">{{ row.provider }}</td>
                    <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.connection }}</td>
                    <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.dataExchange }}</td>
                    <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.accountOwner }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-if="excludedRows.length" class="mb-8">
            <h3 class="text-sm font-semibold text-esmerald mb-3">{{ language === 'en' ? 'Not included' : 'No incluidas' }}</h3>
            <div class="overflow-x-auto rounded-xl border border-esmerald/10 text-sm">
              <table class="w-full text-left">
                <thead class="bg-esmerald/10 text-esmerald">
                  <tr>
                    <th class="px-4 py-2">{{ language === 'en' ? 'Service' : 'Servicio' }}</th>
                    <th class="px-4 py-2">{{ language === 'en' ? 'Reason' : 'Motivo' }}</th>
                    <th class="px-4 py-2">{{ language === 'en' ? 'Future' : 'Futuro' }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in excludedRows" :key="i" class="border-t border-esmerald/10">
                    <td class="px-4 py-2 text-esmerald/90">{{ row.service }}</td>
                    <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.reason }}</td>
                    <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.availability }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-if="integrationNoteLines.length" class="mt-6">
            <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
              <h3 class="text-sm font-semibold text-esmerald">{{ language === 'en' ? 'Technical notes' : 'Notas técnicas' }}</h3>
              <button
                v-if="integrationNoteLines.length > INTEGRATION_NOTES_INLINE_MAX"
                type="button"
                class="text-xs font-medium text-teal-700 hover:underline"
                @click="integrationNotesModalOpen = true"
              >
                {{ language === 'en' ? 'View all in table' : 'Ver todas en tabla' }}
              </button>
            </div>
            <div class="overflow-x-auto rounded-xl border border-esmerald/10">
              <table class="w-full text-sm">
                <thead class="bg-esmerald/10 text-esmerald">
                  <tr>
                    <th class="px-3 py-2 w-12 text-left font-medium">#</th>
                    <th class="px-3 py-2 text-left font-medium">{{ language === 'en' ? 'Note' : 'Nota' }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(line, i) in integrationNotesVisible"
                    :key="'note-' + i"
                    class="border-t border-esmerald/10"
                  >
                    <td class="px-3 py-2 text-esmerald/50 font-mono text-xs align-top">{{ i + 1 }}</td>
                    <td class="px-3 py-2 text-esmerald/80 font-light align-top">{{ line }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

        <!-- Environments -->
        <template v-else-if="fragment === 'environments'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.environments }}</h2>
          <p v-if="environmentsNote" class="text-esmerald/80 font-light mb-8 whitespace-pre-wrap">{{ environmentsNote }}</p>
          <div v-if="environmentRows.length" class="overflow-x-auto rounded-xl border border-esmerald/10 text-sm">
            <table class="w-full text-left">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-3 py-2">{{ language === 'en' ? 'Name' : 'Nombre' }}</th>
                  <th class="px-3 py-2">{{ language === 'en' ? 'Purpose' : 'Propósito' }}</th>
                  <th class="px-3 py-2">URL</th>
                  <th class="px-3 py-2">DB</th>
                  <th class="px-3 py-2">{{ language === 'en' ? 'Access' : 'Acceso' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in environmentRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-3 py-2 text-esmerald/90">{{ row.name }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.purpose }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light break-all">{{ row.url }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.database }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.whoAccesses }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Security -->
        <template v-else-if="fragment === 'security'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-8">{{ titles.security }}</h2>
          <div class="overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald text-lemon">
                <tr>
                  <th class="px-4 py-3 text-left font-medium">{{ language === 'en' ? 'Aspect' : 'Aspecto' }}</th>
                  <th class="px-4 py-3 text-left font-medium">{{ language === 'en' ? 'Implementation' : 'Implementación' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in securityRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-3 text-esmerald/90">{{ row.aspect }}</td>
                  <td class="px-4 py-3 text-esmerald/70 font-light whitespace-pre-wrap">{{ row.implementation }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Performance -->
        <template v-else-if="fragment === 'performance'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-8">{{ titles.performance }}</h2>
          <div v-if="metricRows.length" class="mb-8 overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Metric' : 'Métrica' }}</th>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Target' : 'Objetivo' }}</th>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'How measured' : 'Medición' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in metricRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90">{{ row.metric }}</td>
                  <td class="px-4 py-2 text-esmerald/80">{{ row.target }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.howMeasured }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="practiceLines.length" class="overflow-x-auto rounded-xl border border-esmerald/10 mt-6">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Practice' : 'Práctica' }}</th>
                  <th class="px-4 py-2 text-left font-medium">{{ language === 'en' ? 'Description' : 'Descripción' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in practiceLines" :key="'pr-' + i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90 font-medium align-top whitespace-nowrap">{{ row.strategy }}</td>
                  <td class="px-4 py-2 text-esmerald/75 font-light align-top">{{ row.description }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Backups -->
        <template v-else-if="fragment === 'backups'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-6">{{ titles.backups }}</h2>
          <p class="text-esmerald/80 font-light leading-relaxed whitespace-pre-wrap">{{ backupsNote }}</p>
        </template>

        <!-- Quality -->
        <template v-else-if="fragment === 'quality'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-8">{{ titles.quality }}</h2>
          <div v-if="qualityDimRows.length" class="mb-8 overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Dimension' : 'Dimensión' }}</th>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Evaluates' : 'Evalúa' }}</th>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Standard' : 'Estándar' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in qualityDimRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90">{{ row.dimension }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.evaluates }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light">{{ row.standard }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="qualityTestRows.length" class="mb-8 overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald text-lemon">
                <tr>
                  <th class="px-3 py-2 text-left">{{ language === 'en' ? 'Type' : 'Tipo' }}</th>
                  <th class="px-3 py-2 text-left">{{ language === 'en' ? 'Validates' : 'Valida' }}</th>
                  <th class="px-3 py-2 text-left">{{ language === 'en' ? 'Tool' : 'Herramienta' }}</th>
                  <th class="px-3 py-2 text-left">{{ language === 'en' ? 'When' : 'Cuándo' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in qualityTestRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-3 py-2 text-esmerald/90">{{ row.type }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.validates }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.tool }}</td>
                  <td class="px-3 py-2 text-esmerald/70 font-light">{{ row.whenRun }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="criticalFlowsNote" class="text-sm text-esmerald/75 font-light whitespace-pre-wrap">{{ criticalFlowsNote }}</p>
        </template>

        <!-- Decisions -->
        <template v-else-if="fragment === 'decisions'">
          <h2 class="text-esmerald font-light text-3xl md:text-4xl mb-8">{{ titles.decisions }}</h2>
          <div class="overflow-x-auto rounded-xl border border-esmerald/10">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Decision' : 'Decisión' }}</th>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Alternative' : 'Alternativa' }}</th>
                  <th class="px-4 py-2 text-left">{{ language === 'en' ? 'Reason' : 'Razón' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in decisionRows" :key="i" class="border-t border-esmerald/10">
                  <td class="px-4 py-2 text-esmerald/90 whitespace-pre-wrap">{{ row.decision }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light whitespace-pre-wrap">{{ row.alternative }}</td>
                  <td class="px-4 py-2 text-esmerald/70 font-light whitespace-pre-wrap">{{ row.reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="requirementModal"
        class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/45 backdrop-blur-[2px]"
        role="dialog"
        aria-modal="true"
        :aria-label="language === 'en' ? 'Requirement detail' : 'Detalle del requerimiento'"
        @click.self="closeRequirementModal"
      >
        <div
          class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[min(88vh,720px)] overflow-hidden flex flex-col border border-esmerald/10"
          @click.stop
        >
          <div class="flex items-start justify-between gap-3 px-5 py-4 border-b border-esmerald/10 bg-esmerald/[0.04]">
            <div class="min-w-0">
              <p class="text-[10px] uppercase tracking-wider text-esmerald/50 font-medium mb-1">
                {{ requirementModal.epicTitle }}
              </p>
              <h3 class="text-lg font-medium text-esmerald leading-snug">{{ requirementModal.req.title }}</h3>
            </div>
            <button
              type="button"
              class="shrink-0 w-9 h-9 rounded-full border border-esmerald/20 text-esmerald/70 hover:bg-esmerald/10 text-lg leading-none"
              aria-label="Close"
              @click="closeRequirementModal"
            >
              ×
            </button>
          </div>
          <div class="overflow-y-auto px-5 py-4">
            <table class="w-full text-sm border-collapse">
              <tbody>
                <tr v-if="requirementModal.req.flowKey" class="border-b border-esmerald/10">
                  <th class="text-left py-2 pr-4 text-xs font-semibold text-esmerald/60 align-top w-36">flowKey</th>
                  <td class="py-2 text-esmerald/90 font-mono text-xs">{{ requirementModal.req.flowKey }}</td>
                </tr>
                <tr v-if="requirementModal.req.priority" class="border-b border-esmerald/10">
                  <th class="text-left py-2 pr-4 text-xs font-semibold text-esmerald/60 align-top">
                    {{ language === 'en' ? 'Priority' : 'Prioridad' }}
                  </th>
                  <td class="py-2">
                    <span class="text-[10px] uppercase tracking-wider px-2 py-1 rounded-full bg-esmerald/12 text-esmerald/85">
                      {{ priorityLabel(requirementModal.req.priority) }}
                    </span>
                  </td>
                </tr>
                <tr v-if="requirementModal.req.description" class="border-b border-esmerald/10">
                  <th class="text-left py-2 pr-4 text-xs font-semibold text-esmerald/60 align-top">
                    {{ language === 'en' ? 'Description' : 'Descripción' }}
                  </th>
                  <td class="py-2 text-esmerald/80 font-light whitespace-pre-wrap leading-relaxed">{{ requirementModal.req.description }}</td>
                </tr>
                <tr v-if="requirementModal.req.configuration" class="border-b border-esmerald/10">
                  <th class="text-left py-2 pr-4 text-xs font-semibold text-esmerald/60 align-top">
                    {{ language === 'en' ? 'Configuration' : 'Configuración' }}
                  </th>
                  <td class="py-2 text-esmerald/75 font-light text-xs whitespace-pre-wrap leading-relaxed">{{ requirementModal.req.configuration }}</td>
                </tr>
                <tr v-if="requirementModal.req.usageFlow">
                  <th class="text-left py-2 pr-4 text-xs font-semibold text-esmerald/60 align-top">
                    {{ language === 'en' ? 'Usage flow' : 'Flujo de uso' }}
                  </th>
                  <td class="py-2 text-esmerald/75 font-light text-xs whitespace-pre-wrap leading-relaxed">{{ requirementModal.req.usageFlow }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="integrationNotesModalOpen"
        class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/45 backdrop-blur-[2px]"
        role="dialog"
        aria-modal="true"
        @click.self="integrationNotesModalOpen = false"
      >
        <div
          class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[min(88vh,640px)] overflow-hidden flex flex-col border border-esmerald/10"
          @click.stop
        >
          <div class="flex items-center justify-between px-5 py-3 border-b border-esmerald/10">
            <h3 class="text-sm font-semibold text-esmerald">{{ language === 'en' ? 'All technical notes' : 'Todas las notas técnicas' }}</h3>
            <button
              type="button"
              class="w-9 h-9 rounded-full border border-esmerald/20 text-esmerald/70 hover:bg-esmerald/10"
              aria-label="Close"
              @click="integrationNotesModalOpen = false"
            >
              ×
            </button>
          </div>
          <div class="overflow-y-auto p-4">
            <table class="w-full text-sm">
              <thead class="bg-esmerald/10 text-esmerald">
                <tr>
                  <th class="px-3 py-2 w-12 text-left font-medium">#</th>
                  <th class="px-3 py-2 text-left font-medium">{{ language === 'en' ? 'Note' : 'Nota' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(line, i) in integrationNoteLines" :key="'mod-note-' + i" class="border-t border-esmerald/10">
                  <td class="px-3 py-2 text-esmerald/50 font-mono text-xs align-top">{{ i + 1 }}</td>
                  <td class="px-3 py-2 text-esmerald/80 font-light align-top">{{ line }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';
import {
  technicalFragmentHasContent,
  FRAGMENT_ORDER,
  TECH_PANEL_TITLES,
} from '~/utils/technicalProposalPanels';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  fragment: { type: String, required: true },
  contentJson: { type: Object, default: () => ({}) },
  language: { type: String, default: 'es' },
});

const titles = computed(() => TECH_PANEL_TITLES[props.language] || TECH_PANEL_TITLES.es);

const supportLine = computed(() => (
  props.language === 'en'
    ? 'Support terms follow the commercial proposal.'
    : 'Condiciones de soporte según propuesta comercial.'
));

const purposeText = computed(() => {
  const p = props.contentJson?.purpose;
  return typeof p === 'string' ? p.trim() : '';
});

const anchorLabels = computed(() => {
  const doc = props.contentJson || {};
  const loc = titles.value;
  return FRAGMENT_ORDER
    .filter((f) => f !== 'intro' && technicalFragmentHasContent(f, doc))
    .map((f) => loc[f]);
});

function filterRows(rows, keys) {
  if (!Array.isArray(rows)) return [];
  return rows.filter((r) => keys.some((k) => typeof r?.[k] === 'string' && r[k].trim()));
}

const stackRows = computed(() => filterRows(props.contentJson?.stack, ['layer', 'technology', 'rationale']));

const arch = computed(() => props.contentJson?.architecture || {});
const patternRows = computed(() => filterRows(arch.value.patterns, ['component', 'pattern', 'description']));

const dm = computed(() => props.contentJson?.dataModel || {});
const entityRows = computed(() => filterRows(dm.value.entities, ['name', 'description', 'keyFields']));

const gr = computed(() => props.contentJson?.growthReadiness || {});
const growthSummary = computed(() => {
  const s = gr.value.summary;
  return typeof s === 'string' ? s.trim() : '';
});
const growthStrategyRows = computed(() =>
  filterRows(gr.value.strategies, ['dimension', 'preparation', 'evolution']),
);

const epicsList = computed(() => {
  const epics = props.contentJson?.epics;
  if (!Array.isArray(epics)) return [];
  return epics.map((ep) => ({
    ...ep,
    requirements: filterRows(ep.requirements, ['title', 'description', 'configuration', 'usageFlow', 'flowKey']),
  })).filter((ep) => ep.title?.trim() || ep.epicKey?.trim() || ep.description?.trim() || (ep.requirements && ep.requirements.length));
});

const apiSummary = computed(() => {
  const s = props.contentJson?.apiSummary;
  return typeof s === 'string' ? s.trim() : '';
});
const apiDomainRows = computed(() => filterRows(props.contentJson?.apiDomains, ['domain', 'summary']));

const integ = computed(() => props.contentJson?.integrations || {});
const includedRows = computed(() => filterRows(integ.value.included, ['service', 'provider', 'connection', 'dataExchange', 'accountOwner']));
const excludedRows = computed(() => filterRows(integ.value.excluded, ['service', 'reason', 'availability']));
const INTEGRATION_NOTES_INLINE_MAX = 5;

const integrationNoteLines = computed(() => {
  const n = integ.value.notes;
  if (typeof n !== 'string' || !n.trim()) return [];
  return n.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
});

const integrationNotesVisible = computed(() =>
  integrationNoteLines.value.slice(0, INTEGRATION_NOTES_INLINE_MAX),
);

const requirementModal = ref(null);
const integrationNotesModalOpen = ref(false);

let _reqEsc = null;
let _notesEsc = null;

watch(requirementModal, (v) => {
  if (_reqEsc) {
    window.removeEventListener('keydown', _reqEsc);
    _reqEsc = null;
  }
  if (v) {
    _reqEsc = (e) => {
      if (e.key === 'Escape') requirementModal.value = null;
    };
    window.addEventListener('keydown', _reqEsc);
  }
});

watch(integrationNotesModalOpen, (open) => {
  if (_notesEsc) {
    window.removeEventListener('keydown', _notesEsc);
    _notesEsc = null;
  }
  if (open) {
    _notesEsc = (e) => {
      if (e.key === 'Escape') integrationNotesModalOpen.value = false;
    };
    window.addEventListener('keydown', _notesEsc);
  }
});

onUnmounted(() => {
  if (_reqEsc) window.removeEventListener('keydown', _reqEsc);
  if (_notesEsc) window.removeEventListener('keydown', _notesEsc);
});

function openRequirementModal(epicTitle, req) {
  requirementModal.value = { epicTitle, req };
}

function closeRequirementModal() {
  requirementModal.value = null;
}

function snippetText(text, max = 120) {
  if (typeof text !== 'string' || !text.trim()) return '—';
  const t = text.trim();
  return t.length <= max ? t : `${t.slice(0, max).trim()}…`;
}

const environmentsNote = computed(() => {
  const n = props.contentJson?.environmentsNote;
  return typeof n === 'string' ? n.trim() : '';
});
const environmentRows = computed(() => filterRows(props.contentJson?.environments, ['name', 'purpose', 'url', 'database', 'whoAccesses']));

const securityRows = computed(() => filterRows(props.contentJson?.security, ['aspect', 'implementation']));

const pq = computed(() => props.contentJson?.performanceQuality || {});
const metricRows = computed(() => filterRows(pq.value.metrics, ['metric', 'target', 'howMeasured']));
const practiceLines = computed(() => filterRows(pq.value.practices, ['strategy', 'description']));

const backupsNote = computed(() => {
  const n = props.contentJson?.backupsNote;
  return typeof n === 'string' ? n.trim() : '';
});

const qual = computed(() => props.contentJson?.quality || {});
const qualityDimRows = computed(() => filterRows(qual.value.dimensions, ['dimension', 'evaluates', 'standard']));
const qualityTestRows = computed(() => filterRows(qual.value.testTypes, ['type', 'validates', 'tool', 'whenRun']));
const criticalFlowsNote = computed(() => {
  const n = qual.value.criticalFlowsNote;
  return typeof n === 'string' ? n.trim() : '';
});

const decisionRows = computed(() => filterRows(props.contentJson?.decisions, ['decision', 'alternative', 'reason']));

const PRIORITY_I18N = {
  es: { critical: 'Crítico', high: 'Alta', medium: 'Media', low: 'Baja' },
  en: { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' },
};

function priorityLabel(p) {
  const map = PRIORITY_I18N[props.language] || PRIORITY_I18N.es;
  return map[p] || p;
}
</script>
