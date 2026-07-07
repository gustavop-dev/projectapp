<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <FieldInput v-model="form.index" label="Índice" placeholder="4" />
    <FieldInput v-model="form.title" label="Título" />
  </div>
  <FieldTextarea v-model="form.subtitle" label="Subtítulo" :rows="2" :isSingle="true" />
  <FieldTextarea
    v-model="form.methodology"
    label="Cómo calculamos esto (metodología)"
    :rows="3"
    :isSingle="true"
    placeholder="Partimos del tráfico esperado del mercado local; asumimos que de cada 100 visitas X agendan; proyectamos a 12 meses. Cada escenario cambia ese supuesto."
  />
  <p class="text-[10px] text-text-subtle -mt-2">Se muestra al cliente justo encima de los escenarios para que entienda de dónde salen los números. Lenguaje llano, 2-3 frases.</p>

  <div>
    <label class="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">KPIs / Métricas destacadas</label>
    <p class="text-[10px] text-text-subtle mb-2">Tarjetas que aparecen al inicio. Incluye fuentes verificables cuando uses números de mercado.</p>
    <draggable v-model="form.kpis" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
      <template #item="{ element: kpi, index: idx }">
        <div class="mb-3 bg-surface-raised rounded-xl p-3 border border-border-muted">
          <div class="flex items-center justify-between mb-1">
            <div class="flex items-center gap-2">
              <span class="drag-handle cursor-grab text-text-subtle hover:text-text-muted">⠿</span>
              <span class="text-xs text-text-subtle">KPI {{ idx + 1 }}</span>
            </div>
            <button type="button" class="text-xs text-danger-strong" @click="form.kpis.splice(idx, 1)">Eliminar</button>
          </div>
          <div class="grid grid-cols-[100px_120px_1fr] gap-2 mb-1">
            <EmojiIconField v-model="kpi.icon" label="Icono" placeholder="📈" />
            <FieldInput v-model="kpi.value" label="Valor" placeholder="≈90K" />
            <FieldInput v-model="kpi.label" label="Etiqueta" placeholder="Visualizaciones diarias" />
          </div>
          <FieldInput v-model="kpi.sublabel" label="Subtítulo (opcional)" placeholder="mes 6, escenario realista" />
          <FieldInput v-model="kpi.source" label="Fuente (opcional)" placeholder="Stickermanager benchmark" />
        </div>
      </template>
    </draggable>
    <button type="button" class="text-xs text-text-brand font-medium" @click="if (!form.kpis) form.kpis = []; form.kpis.push({ icon: '', value: '', label: '', sublabel: '', source: '' })">+ Agregar KPI</button>
  </div>

  <FieldInput v-model="form.scenariosTitle" label="Título de escenarios" placeholder="Escenarios proyectados al primer año" />
  <div>
    <label class="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Escenarios (cons / real / opt)</label>
    <p class="text-[10px] text-text-subtle mb-2">Cada escenario tiene supuestos (las palancas que lo distinguen, 2-4) y una lista de métricas. Marca "Énfasis" en la métrica final (totales); el "cómo se calculó" es obligatorio en esa métrica.</p>
    <draggable v-model="form.scenarios" item-key="_idx" handle=".drag-handle" ghost-class="opacity-30">
      <template #item="{ element: scenario, index: sIdx }">
        <div class="mb-3 bg-surface-raised rounded-xl p-3 border border-border-muted">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="drag-handle cursor-grab text-text-subtle hover:text-text-muted">⠿</span>
              <span class="text-xs text-text-subtle">Escenario {{ sIdx + 1 }}</span>
            </div>
            <button type="button" class="text-xs text-danger-strong" @click="form.scenarios.splice(sIdx, 1)">Eliminar</button>
          </div>
          <div class="grid grid-cols-[80px_120px_1fr] gap-2 mb-2">
            <EmojiIconField v-model="scenario.icon" label="Icono" placeholder="🌱" />
            <FieldInput v-model="scenario.name" label="ID" placeholder="conservative" />
            <FieldInput v-model="scenario.label" label="Etiqueta" placeholder="Conservador" />
          </div>
          <label class="block text-[10px] text-text-subtle mb-1">Supuestos (palancas que distinguen este escenario)</label>
          <div v-for="(assumption, aIdx) in (scenario.assumptions || [])" :key="'a-' + aIdx" class="grid grid-cols-[1fr_28px] gap-2 mb-1 items-center">
            <FieldInput v-model="scenario.assumptions[aIdx]" label="" placeholder="3 de cada 100 visitas agendan" />
            <button type="button" class="text-xs text-danger-strong" @click="scenario.assumptions.splice(aIdx, 1)">×</button>
          </div>
          <button type="button" class="text-[11px] text-text-brand font-medium mt-1 mb-2" @click="if (!scenario.assumptions) scenario.assumptions = []; scenario.assumptions.push('')">+ Supuesto</button>
          <label class="block text-[10px] text-text-subtle mb-1">Métricas</label>
          <div v-for="(metric, mIdx) in (scenario.metrics || [])" :key="'m-' + mIdx" class="bg-surface rounded-lg p-2 mb-1 border border-border-muted">
            <div class="grid grid-cols-[1fr_120px_60px_28px] gap-2 items-center">
              <FieldInput v-model="metric.label" label="" placeholder="MAU mes 6" />
              <FieldInput v-model="metric.value" label="" placeholder="80K" />
              <label class="flex items-center gap-1 text-[10px] text-text-subtle cursor-pointer">
                <input type="checkbox" v-model="metric.emphasis" class="rounded" />
                Énfasis
              </label>
              <button type="button" class="text-xs text-danger-strong" @click="scenario.metrics.splice(mIdx, 1)">×</button>
            </div>
            <FieldInput v-model="metric.basis" label="" placeholder="Cómo se calculó — ej. ≈ 6.500 clientes × $43.000 ticket promedio" class="mt-1" />
          </div>
          <button type="button" class="text-[11px] text-text-brand font-medium mt-1" @click="if (!scenario.metrics) scenario.metrics = []; scenario.metrics.push({ label: '', value: '', basis: '', emphasis: false })">+ Métrica</button>
        </div>
      </template>
    </draggable>
    <button type="button" class="text-xs text-text-brand font-medium" @click="if (!form.scenarios) form.scenarios = []; form.scenarios.push({ name: '', label: '', icon: '', assumptions: [], metrics: [] })">+ Agregar escenario</button>
  </div>

  <FieldTextarea v-model="form.ctaNote" label="Nota de cierre" :rows="2" :isSingle="true" placeholder="En cualquier escenario, los ingresos cubren la inversión antes de…" />
</template>

<script setup>
import { FieldInput, FieldTextarea } from './fields.js';
import EmojiIconField from '~/components/BusinessProposal/admin/EmojiIconField.vue';
import draggable from 'vuedraggable';

defineProps({
  form: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
});
</script>
