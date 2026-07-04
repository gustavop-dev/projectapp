<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">MCPs</h1>
      <p class="text-sm text-text-subtle mt-1">
        Conectores MCP para usar los módulos del panel desde Claude (claude.ai).
      </p>
    </div>

    <!-- Guía paso a paso (acordeón nativo, colapsado por defecto) -->
    <details
      class="group mb-6 bg-surface border border-border-muted rounded-xl shadow-sm"
      data-testid="mcps-guide"
    >
      <summary
        class="flex items-center gap-3 p-4 sm:p-5 cursor-pointer select-none list-none marker:hidden [&::-webkit-details-marker]:hidden"
      >
        <span class="text-sm font-semibold text-text-default">
          ¿Cómo conectar un conector a Claude?
        </span>
        <BaseBadge variant="primary" size="sm">Guía paso a paso</BaseBadge>
        <svg
          class="ml-auto h-4 w-4 flex-shrink-0 text-text-subtle transition-transform duration-200 group-open:rotate-180"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </summary>

      <div class="px-4 sm:px-5 pb-5 pt-1 border-t border-border-muted">
        <ol class="space-y-3 mt-4">
          <li
            v-for="(step, index) in guideSteps"
            :key="index"
            class="flex items-start gap-3"
          >
            <span
              class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-soft text-text-brand text-xs font-semibold"
            >
              {{ index + 1 }}
            </span>
            <p class="text-sm text-text-muted leading-relaxed" v-html="step" />
          </li>
        </ol>

        <p class="text-xs text-text-subtle mt-4 leading-relaxed">
          🔒 El token <strong class="font-semibold text-text-muted">es la credencial</strong>:
          trátalo como una contraseña (sólo <code class="text-xs bg-surface-muted rounded px-1 py-0.5">claude.ai</code>
          puede usarlo). <strong class="font-semibold text-text-muted">Contabilidad</strong> da acceso total de
          escritura a datos financieros — actívala sólo cuando la vayas a usar.
        </p>
      </div>
    </details>

    <div v-if="store.loading && store.connectors.length === 0" class="text-center py-16 text-text-subtle text-sm">
      Cargando conectores...
    </div>

    <div
      v-else-if="store.error && store.connectors.length === 0"
      data-testid="mcps-error"
      class="max-w-md bg-surface border border-border-muted rounded-xl shadow-sm p-6 text-center"
    >
      <p class="text-sm text-text-muted mb-4">{{ store.error }}</p>
      <BaseButton variant="secondary" size="sm" @click="store.fetchConnectors()">
        Reintentar
      </BaseButton>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-5 items-start">
      <div
        v-for="connector in store.connectors"
        :key="connector.slug"
        :data-testid="`mcp-card-${connector.slug}`"
        class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6"
      >
        <div class="flex items-start justify-between gap-3 mb-1">
          <h2 class="text-lg font-bold text-text-default">{{ connector.name }}</h2>
          <div class="flex items-center gap-2 flex-shrink-0">
            <span
              class="text-xs font-medium"
              :class="connector.is_active ? 'text-success-strong' : 'text-text-subtle'"
              :data-testid="`mcp-status-${connector.slug}`"
            >
              {{ connector.is_active ? 'Activo' : 'Inactivo' }}
            </span>
            <BaseToggle
              :model-value="connector.is_active"
              :aria-label="`Activar ${connector.name}`"
              :data-testid="`mcp-toggle-${connector.slug}`"
              @update:model-value="(value) => onToggle(connector, value)"
            />
          </div>
        </div>
        <p class="text-sm text-text-muted mb-4">{{ connector.description }}</p>

        <div class="flex items-center gap-2 text-sm mb-4">
          <span class="text-text-subtle">Token:</span>
          <code v-if="connector.has_token" class="text-xs bg-surface-muted rounded px-2 py-1">
            {{ connector.token_prefix }}…
          </code>
          <span v-else class="text-text-subtle">sin generar</span>
          <span v-if="connector.last_used_at" class="text-xs text-text-subtle ml-auto">
            Último uso: {{ formatDate(connector.last_used_at) }}
          </span>
        </div>

        <!-- Connection status derived from the latest MCP request -->
        <div
          class="flex items-start gap-2 text-sm rounded-lg px-3 py-2 mb-4"
          :class="statusFor(connector).box"
          :data-testid="`mcp-connection-${connector.slug}`"
        >
          <span class="mt-1 h-2 w-2 rounded-full flex-shrink-0" :class="statusFor(connector).dot" />
          <div>
            <span class="font-medium">{{ statusFor(connector).label }}</span>
            <template v-if="connector.recent_events?.length">
              <span class="text-text-muted">
                · {{ formatDate(connector.recent_events[0].created_at) }}
                · {{ eventLabel(connector.recent_events[0]) }}
              </span>
              <p v-if="!connector.recent_events[0].ok && connector.recent_events[0].detail" class="text-xs text-text-muted mt-0.5">
                {{ connector.recent_events[0].detail }}
              </p>
            </template>
          </div>
        </div>

        <details v-if="connector.recent_events?.length" class="mb-4">
          <summary
            class="text-xs font-semibold text-text-subtle uppercase tracking-wider cursor-pointer select-none"
            :data-testid="`mcp-activity-toggle-${connector.slug}`"
          >
            Actividad reciente ({{ connector.recent_events.length }})
          </summary>
          <ul class="mt-2 space-y-1.5" :data-testid="`mcp-activity-list-${connector.slug}`">
            <li
              v-for="(event, index) in connector.recent_events"
              :key="index"
              class="flex items-start gap-2 text-xs"
            >
              <span
                class="mt-1 h-1.5 w-1.5 rounded-full flex-shrink-0"
                :class="event.ok ? 'bg-success-strong' : 'bg-danger-strong'"
              />
              <span class="text-text-subtle whitespace-nowrap">{{ formatDate(event.created_at) }}</span>
              <span class="text-text-default">{{ eventLabel(event) }}</span>
              <span v-if="showDetail(event)" class="text-text-muted truncate">{{ event.detail }}</span>
            </li>
          </ul>
        </details>

        <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">
          Funciones disponibles
        </p>
        <ul class="space-y-1 mb-5">
          <li v-for="tool in connector.tools" :key="tool.name" class="text-sm">
            <code class="text-xs bg-surface-muted rounded px-1.5 py-0.5">{{ tool.name }}</code>
            <span class="text-text-muted ml-1">{{ tool.description }}</span>
          </li>
        </ul>

        <div class="flex items-center justify-end pt-4 border-t border-border-muted">
          <BaseButton
            variant="primary"
            size="sm"
            :data-testid="`mcp-generate-token-${connector.slug}`"
            @click="onGenerateToken(connector)"
          >
            {{ connector.has_token ? 'Regenerar token' : 'Generar token' }}
          </BaseButton>
        </div>
      </div>
    </div>

    <!-- One-time token modal -->
    <BaseModal v-model="tokenModal.open" size="lg" padding="md" :close-on-backdrop="false">
      <div data-testid="mcp-token-modal">
        <h3 class="text-lg font-bold text-text-default mb-2">URL del conector</h3>
        <p class="text-sm text-text-muted mb-4">
          Cópiala ahora: por seguridad no se volverá a mostrar. Pégala en
          claude.ai → Settings → Connectors → “Add custom connector”.
        </p>
        <code
          data-testid="mcp-token-url"
          class="block text-xs bg-surface-muted rounded p-3 break-all mb-4"
        >{{ tokenModal.url }}</code>
        <div class="flex items-center justify-end gap-2">
          <BaseButton variant="secondary" size="sm" data-testid="mcp-token-copy" @click="copyTokenUrl">
            {{ tokenModal.copied ? 'Copiada ✓' : 'Copiar URL' }}
          </BaseButton>
          <BaseButton variant="primary" size="sm" data-testid="mcp-token-close" @click="closeTokenModal">
            Listo, la guardé
          </BaseButton>
        </div>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import BaseBadge from '~/components/base/BaseBadge.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useMcpsStore } from '~/stores/mcps';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useMcpsStore();
const notify = usePanelNotify();

const tokenModal = reactive({ open: false, url: '', copied: false });

// Pasos accionables para conectar un MCP, mostrados en el acordeón de la vista.
// Se permiten <strong> para resaltar la acción/etiqueta real de la UI.
const guideSteps = [
  '<strong>Genera el token:</strong> en la card del conector, pulsa «Generar token».',
  '<strong>Copia la URL:</strong> se muestra una sola vez en el modal («Copiar URL»). Formato <code class="text-xs bg-surface-muted rounded px-1 py-0.5">…/api/mcp/&lt;slug&gt;/&lt;token&gt;/</code>.',
  '<strong>Actívalo:</strong> enciende el toggle de la card (pasa a «Activo»).',
  '<strong>Conéctalo en claude.ai:</strong> Settings → Connectors → «Add custom connector» → pega la URL.',
  '<strong>Verifica:</strong> pídele algo al conector en el chat; aquí verás «Conectado» y la actividad reciente.',
];

const statusStyles = {
  connected: { label: 'Conectado', dot: 'bg-success-strong', box: 'bg-success-soft text-success-strong' },
  error: { label: 'Error de conexión', dot: 'bg-danger-strong', box: 'bg-danger-soft text-danger-strong' },
  none: { label: 'Sin actividad', dot: 'bg-surface-raised border border-border-default', box: 'bg-surface-muted text-text-muted' },
};

const eventLabels = {
  handshake: 'Conexión (initialize)',
  tool_call: 'Tool',
  auth_error: 'Error de autenticación',
  origin_rejected: 'Origin rechazado',
};

function statusFor(connector) {
  return statusStyles[connector.connection_status] || statusStyles.none;
}

function eventLabel(event) {
  const base = eventLabels[event.event] || event.event;
  if (event.event === 'tool_call' && event.ok && event.detail) {
    return `${base}: ${event.detail}`;
  }
  return base;
}

function showDetail(event) {
  // tool_call OK already carries its detail (the tool name) in the label.
  if (!event.detail) return false;
  return !(event.event === 'tool_call' && event.ok);
}

onMounted(() => {
  store.fetchConnectors();
});

function formatDate(iso) {
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
}

async function onToggle(connector, value) {
  const result = await store.toggleConnector(connector.slug, value);
  if (!result.success) {
    notify.error({ title: 'No se pudo actualizar el conector', detail: result.error });
  }
}

async function onGenerateToken(connector) {
  const result = await store.generateToken(connector.slug);
  if (!result.success) {
    notify.error({ title: 'No se pudo generar el token', detail: result.error });
    return;
  }
  tokenModal.url = result.data.connector_url;
  tokenModal.copied = false;
  tokenModal.open = true;
}

async function copyTokenUrl() {
  try {
    await navigator.clipboard.writeText(tokenModal.url);
    tokenModal.copied = true;
  } catch {
    notify.error({ title: 'No se pudo copiar', detail: 'Selecciona la URL manualmente.' });
  }
}

function closeTokenModal() {
  tokenModal.open = false;
  tokenModal.url = '';
}
</script>
