<template>
  <section
    v-if="isOpen || chips.length || searchValue"
    class="mb-4 overflow-visible rounded-xl border border-border-default bg-surface"
    data-testid="communications-filter-panel"
  >
    <div v-show="isOpen" class="grid gap-3 p-3 panel-portrait:grid-cols-2 panel-desktop:grid-cols-4">
      <BaseFilterDropdown
        label="Estado del hilo"
        :model-value="modelValue.status"
        :options="threadStatusOptions"
        test-id="communications-status-filter"
        @update:model-value="setValue('status', $event)"
      />
      <BaseFilterDropdown
        label="Estado del mensaje"
        :model-value="modelValue.message_status"
        :options="messageStatusOptions"
        test-id="communications-message-status-filter"
        @update:model-value="setValue('message_status', $event)"
      />
      <BaseFilterDropdown
        label="Canal"
        :model-value="modelValue.channel"
        :options="channelOptions"
        test-id="communications-channel-filter"
        @update:model-value="setValue('channel', $event)"
      />
      <BaseFilterDropdown
        label="Dirección"
        :model-value="modelValue.direction"
        :options="directionOptions"
        test-id="communications-direction-filter"
        @update:model-value="setValue('direction', $event)"
      />
      <BaseFilterDropdown
        label="Respuesta del cliente"
        :model-value="modelValue.reply_status"
        :options="replyStatusOptions"
        test-id="communications-reply-status-filter"
        @update:model-value="setValue('reply_status', $event)"
      />

      <BaseFormField label="Desde">
        <BaseInput
          type="date"
          :model-value="modelValue.date_from"
          data-testid="communications-date-from-filter"
          @update:model-value="setValue('date_from', $event)"
        />
      </BaseFormField>
      <BaseFormField label="Hasta">
        <BaseInput
          type="date"
          :model-value="modelValue.date_to"
          data-testid="communications-date-to-filter"
          @update:model-value="setValue('date_to', $event)"
        />
      </BaseFormField>

      <p class="panel-portrait:col-span-2 panel-desktop:col-span-4 text-[11px] text-text-subtle" data-testid="communications-filter-logic-hint">
        Dentro de un filtro los valores se suman; entre filtros se restringen. Respuesta del cliente sólo evalúa mensajes salientes enviados.
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-2 border-t border-border-muted px-3 py-2.5 first:border-t-0">
      <span class="text-xs font-medium tabular-nums text-text-muted">
        {{ resultsCount }} {{ resultsCount === 1 ? 'hilo' : 'hilos' }}
      </span>

      <span
        v-if="searchValue"
        class="inline-flex items-center gap-1 rounded-full bg-info-soft px-2.5 py-1 text-xs font-medium text-info-strong"
      >
        “{{ searchValue }}”
        <BaseActionButton
          action="remove"
          label="Quitar búsqueda"
          size="sm"
          class="-my-1 -mr-1"
          @click="$emit('clear-search')"
        />
      </span>

      <span
        v-for="chip in chips"
        :key="chip.id"
        class="inline-flex items-center gap-1 rounded-full bg-info-soft px-2.5 py-1 text-xs font-medium text-info-strong"
      >
        <span>{{ chip.label }}:</span>
        <span v-for="(value, index) in chip.values" :key="value.token" class="inline-flex items-center gap-1">
          {{ index ? ', ' : '' }}{{ value.label }}
          <BaseActionButton
            action="remove"
            :label="`Quitar ${chip.label} ${value.label}`"
            size="sm"
            class="-my-1"
            @click="value.clear"
          />
        </span>
      </span>

      <BaseButton
        v-if="chips.length || searchValue"
        variant="link"
        size="sm"
        class="ml-auto"
        data-testid="communications-filter-reset"
        @click="$emit('reset')"
      >
        Limpiar filtros
      </BaseButton>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  facets: { type: Object, default: () => ({ filters: {} }) },
  isOpen: { type: Boolean, default: false },
  resultsCount: { type: Number, default: 0 },
  searchValue: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue', 'reset', 'clear-search']);

const definitions = {
  status: {
    label: 'Hilo',
    options: [
      { value: 'open', label: 'Abierto' },
      { value: 'closed', label: 'Cerrado' },
    ],
  },
  message_status: {
    label: 'Mensaje',
    options: [
      { value: 'draft', label: 'Borrador' },
      { value: 'sent', label: 'Enviado' },
      { value: 'received', label: 'Recibido' },
      { value: 'failed', label: 'Fallido' },
    ],
  },
  channel: {
    label: 'Canal',
    options: [
      { value: 'email', label: 'Correo' },
      { value: 'whatsapp', label: 'WhatsApp' },
    ],
  },
  direction: {
    label: 'Dirección',
    options: [
      { value: 'outgoing', label: 'Saliente' },
      { value: 'incoming', label: 'Entrante' },
    ],
  },
  reply_status: {
    label: 'Respuesta',
    options: [
      { value: 'answered', label: 'Respondido' },
      { value: 'unanswered', label: 'Sin respuesta' },
    ],
  },
};

function optionsWithCounts(key) {
  const counts = props.facets?.filters?.[key] || {};
  return definitions[key].options.map((option) => ({
    ...option,
    count: Number(counts[option.value] || 0),
  }));
}

const threadStatusOptions = computed(() => optionsWithCounts('status'));
const messageStatusOptions = computed(() => optionsWithCounts('message_status'));
const channelOptions = computed(() => optionsWithCounts('channel'));
const directionOptions = computed(() => optionsWithCounts('direction'));
const replyStatusOptions = computed(() => optionsWithCounts('reply_status'));

function setValue(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}

function optionLabel(key, value) {
  return definitions[key].options.find((option) => option.value === value)?.label || String(value);
}

const chips = computed(() => {
  const rows = [];
  for (const key of ['status', 'message_status', 'channel', 'direction', 'reply_status']) {
    const selected = Array.isArray(props.modelValue[key]) ? props.modelValue[key] : [];
    if (!selected.length) continue;
    rows.push({
      id: key,
      label: definitions[key].label,
      values: selected.map((token) => ({
        token,
        label: optionLabel(key, token),
        clear: () => setValue(key, selected.filter((value) => value !== token)),
      })),
    });
  }

  const dateFrom = props.modelValue.date_from;
  const dateTo = props.modelValue.date_to;
  if (dateFrom || dateTo) {
    rows.push({
      id: 'dates',
      label: 'Fecha',
      values: [{
        token: 'range',
        label: dateFrom && dateTo ? `${dateFrom} – ${dateTo}` : (dateFrom ? `desde ${dateFrom}` : `hasta ${dateTo}`),
        clear: () => emit('update:modelValue', {
          ...props.modelValue, date_from: '', date_to: '',
        }),
      }],
    });
  }
  return rows;
});
</script>
