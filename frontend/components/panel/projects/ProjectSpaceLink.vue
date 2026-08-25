<template>
  <BaseActionButton
    v-if="projectId != null"
    action="open-platform"
    variant="ghost"
    size="sm"
    label="Abrir el espacio del proyecto"
    tooltip="Abrir el espacio en la plataforma (pestaña nueva)"
    :disabled="isBridging"
    :data-testid="dataTestid"
    @click.stop="openSpace"
  />
</template>

<script setup>
import { usePanelToPlatformBridge } from '~/composables/usePanelToPlatformBridge';

/**
 * Jump from any panel reference of a project to its platform space (PA-50).
 *
 * The panel row and the space are the SAME `accounts.Project`, so the id is
 * the whole reference — nothing to store or resolve by name. The session
 * bridge mints the platform JWT and opens a new tab (panel and platform are
 * different working contexts); on bridge failure it lands on /platform/login,
 * never a broken link. Renders nothing without an id, so "Sin proyecto"
 * cells stay exactly as they are.
 */
const props = defineProps({
  projectId: { type: [Number, String], default: null },
  dataTestid: { type: String, default: 'project-space-link' },
});

const { goToPlatform, isBridging } = usePanelToPlatformBridge();

function openSpace() {
  goToPlatform(`/platform/projects/${props.projectId}`);
}
</script>
