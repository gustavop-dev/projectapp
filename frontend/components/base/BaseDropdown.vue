<script setup>
// Namespace import (instead of named) avoids a vue3-jest bug: babel derives
// `var _vue` from the last path segment of `@headlessui/vue`, which collides
// with the `var _vue = require("vue")` injected by the compiled template
// render function. The collision leaves $setup.Menu et al as undefined.
import * as HeadlessUI from '@headlessui/vue'
const { Menu, MenuButton, MenuItems, MenuItem } = HeadlessUI

defineProps({
  // Items: [{ label, onClick?, to?, icon?, disabled?, danger?, divider? }]
  items: { type: Array, required: true },
  align: { type: String, default: 'right' }, // left | right
  width: { type: String, default: 'w-56' },
})

function itemColorClass(danger, active) {
  if (danger) return active ? 'bg-danger-soft text-danger-strong' : 'text-danger-strong'
  return active ? 'bg-surface-raised text-text-default' : 'text-text-default'
}
</script>

<template>
  <Menu as="div" class="relative inline-block text-left">
    <MenuButton as="template">
      <slot name="trigger" />
    </MenuButton>

    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <MenuItems
        :class="[
          'absolute z-30 mt-2 origin-top rounded-xl bg-surface border border-border-default shadow-lg focus:outline-none p-1',
          width,
          align === 'right' ? 'right-0 origin-top-right' : 'left-0 origin-top-left',
        ]"
      >
        <template v-for="(item, idx) in items" :key="idx">
          <div v-if="item.divider" class="my-1 border-t border-border-muted" />
          <MenuItem v-else v-slot="{ active, disabled }" :disabled="item.disabled">
            <component
              :is="item.to ? 'NuxtLink' : 'button'"
              :to="item.to"
              :type="item.to ? undefined : 'button'"
              :disabled="disabled"
              :class="[
                'flex w-full items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors text-left',
                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
                itemColorClass(item.danger, active),
              ]"
              @click="item.onClick && item.onClick($event)"
            >
              <component v-if="item.icon" :is="item.icon" class="w-4 h-4 flex-shrink-0" />
              <span class="flex-1">{{ item.label }}</span>
            </component>
          </MenuItem>
        </template>
      </MenuItems>
    </transition>
  </Menu>
</template>
