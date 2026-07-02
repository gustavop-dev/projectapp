<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">MCPs</h1>
      <p class="text-sm text-text-subtle mt-1">
        Conectores MCP para usar los módulos del panel desde Claude (claude.ai).
      </p>
    </div>

    <div v-if="store.loading && store.connectors.length === 0" class="text-center py-16 text-text-subtle text-sm">
      Cargando conectores...
    </div>

    <div
      v-else-if="store.error && store.connectors.length === 0"
      data-testid="mcps-error"
      class="max-w-2xl bg-surface border border-border-muted rounded-xl shadow-sm p-6 text-center"
    >
      <p class="text-sm text-text-muted mb-4">{{ store.error }}</p>
      <BaseButton variant="secondary" size="sm" @click="store.fetchConnectors()">
        Reintentar
      </BaseButton>
    </div>

    <div v-else class="max-w-2xl space-y-4">
      <div
        v-for="connector in store.connectors"
        :key="connector.slug"
        :data-testid="`mcp-card-${connector.slug}`"
        class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6"
      >
        <div class="flex items-start justify-between gap-3 mb-1">
          <h2 class="text-lg font-bold text-text-default">{{ connector.name }}</h2>
          <BaseToggle
            :model-value="connector.is_active"
            :aria-label="`Activar ${connector.name}`"
            :data-testid="`mcp-toggle-${connector.slug}`"
            @update:model-value="(value) => onToggle(connector, value)"
          />
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
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useMcpsStore } from '~/stores/mcps';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useMcpsStore();
const notify = usePanelNotify();

const tokenModal = reactive({ open: false, url: '', copied: false });

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
