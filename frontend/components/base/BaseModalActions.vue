<template>
  <div
    class="flex flex-col-reverse gap-2 border-t border-border-muted px-4 py-4 panel-portrait:flex-row panel-portrait:justify-end panel-portrait:px-6"
    data-testid="base-modal-actions"
  >
    <slot />
  </div>
</template>

<style scoped>
@media (max-width: 599px) {
  :deep(.base-button:not(.base-button--link)) {
    width: 100%;
  }
}
</style>
