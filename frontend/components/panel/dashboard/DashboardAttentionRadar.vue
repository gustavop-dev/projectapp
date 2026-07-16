<template>
  <section aria-labelledby="attention-radar-title" data-testid="attention-radar">
    <h2
      id="attention-radar-title"
      class="mb-3 text-xs font-semibold uppercase tracking-widest text-text-muted"
    >
      Radar de atención
    </h2>

    <div
      v-if="!items.length"
      class="flex items-center gap-3 rounded-xl border border-success-soft bg-success-soft px-5 py-4"
      data-testid="attention-radar-empty"
    >
      <CheckCircleIcon class="w-6 h-6 shrink-0 text-success-strong" aria-hidden="true" />
      <p class="text-sm text-success-strong font-medium">
        Nada requiere tu atención. Todo al día.
      </p>
    </div>

    <ul v-else class="space-y-2" data-testid="attention-radar-list">
      <li v-for="item in items" :key="item.type">
        <NuxtLink
          :to="localePath(config(item).route)"
          class="group flex items-center gap-3 rounded-xl border-l-4 bg-surface border border-border-muted px-4 py-3 shadow-card
                 transition-shadow duration-base motion-reduce:transition-none hover:shadow-raised
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
          :class="severityBorder(item.severity)"
          :data-testid="`attention-item-${item.type}`"
        >
          <span
            class="flex w-9 h-9 shrink-0 items-center justify-center rounded-full"
            :class="severityBadge(item.severity)"
          >
            <component :is="config(item).icon" class="w-5 h-5" aria-hidden="true" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-sm font-medium text-text-default">
              {{ config(item).text(item) }}
            </span>
            <span class="block text-xs text-text-subtle mt-0.5">
              {{ config(item).module }}
            </span>
          </span>
          <span
            class="text-xs font-medium text-text-subtle group-hover:text-text-brand transition-colors motion-reduce:transition-none"
            aria-hidden="true"
          >
            Resolver →
          </span>
        </NuxtLink>
      </li>
    </ul>
  </section>
</template>

<script setup>
import {
  CheckCircleIcon,
  ClipboardDocumentListIcon,
  CreditCardIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  PaperAirplaneIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/vue/24/outline';

/**
 * Cross-module actionable list: each backend attention item maps to
 * Spanish copy, a module label, an icon and a deep-link. Severity only
 * changes the visual accent (danger/warning/info status tokens).
 */
defineProps({
  /** Backend items: [{ type, severity, count, meta }] sorted by severity. */
  items: { type: Array, default: () => [] },
});

const localePath = useLocalePath();

function plural(count, singular, plural_) {
  return count === 1 ? singular : plural_;
}

const TYPE_CONFIG = {
  documents_overdue: {
    icon: DocumentTextIcon,
    module: 'Documentos',
    route: '/panel/documents',
    text: ({ count }) =>
      `${count} ${plural(count, 'cuenta de cobro vencida', 'cuentas de cobro vencidas')}`,
  },
  emails_failed: {
    icon: EnvelopeIcon,
    module: 'Emails',
    route: '/panel/emails',
    text: ({ count }) =>
      `${count} ${plural(count, 'email fallido', 'emails fallidos')} en los últimos 7 días`,
  },
  tasks_overdue: {
    icon: ClipboardDocumentListIcon,
    module: 'Tareas',
    route: '/panel/tasks',
    text: ({ count, meta }) => {
      const base = `${count} ${plural(count, 'tarea vencida', 'tareas vencidas')}`;
      return meta?.high_priority
        ? `${base} · ${meta.high_priority} de alta prioridad`
        : base;
    },
  },
  proposals_stale: {
    icon: PaperAirplaneIcon,
    module: 'Propuestas',
    route: '/panel/proposals',
    text: ({ count, meta }) =>
      `${count} ${plural(count, 'propuesta enviada', 'propuestas enviadas')} sin abrir hace más de ${meta?.days ?? 7} días`,
  },
  recurring_due: {
    icon: CreditCardIcon,
    module: 'Contabilidad',
    route: '/panel/accounting/recurring',
    text: ({ count, meta }) => {
      const base = `${count} ${plural(count, 'pago recurrente', 'pagos recurrentes')}`;
      if (meta?.next_days === 0) return `${base} — el próximo vence hoy`;
      if (meta?.next_days === 1) return `${base} — el próximo vence mañana`;
      return `${base} en los próximos 7 días`;
    },
  },
};

const FALLBACK_CONFIG = {
  icon: QuestionMarkCircleIcon,
  module: 'Panel',
  route: '/panel',
  text: ({ count }) => `${count} pendientes`,
};

function config(item) {
  return TYPE_CONFIG[item.type] || FALLBACK_CONFIG;
}

const SEVERITY_BORDER = {
  danger: 'border-l-danger-strong',
  warning: 'border-l-warning-strong',
  info: 'border-l-info-strong',
};

const SEVERITY_BADGE = {
  danger: 'bg-danger-soft text-danger-strong',
  warning: 'bg-warning-soft text-warning-strong',
  info: 'bg-info-soft text-info-strong',
};

function severityBorder(severity) {
  return SEVERITY_BORDER[severity] || SEVERITY_BORDER.info;
}

function severityBadge(severity) {
  return SEVERITY_BADGE[severity] || SEVERITY_BADGE.info;
}
</script>
