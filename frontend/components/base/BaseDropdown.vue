<script setup>
// Namespace import (instead of named) avoids a vue3-jest bug: babel derives
// `var _vue` from the last path segment of `@headlessui/vue`, which collides
// with the `var _vue = require("vue")` injected by the compiled template
// render function. The collision leaves $setup.Menu et al as undefined.
import { resolveComponent } from 'vue'
import * as HeadlessUI from '@headlessui/vue'
import BaseActionIcon from './BaseActionIcon.vue'
import { getPanelAction } from '~/config/panelActions'
const { Menu, MenuButton, MenuItems, MenuItem } = HeadlessUI

// String names in <component :is> can't resolve Nuxt auto-imported
// components, so `to` items rendered a dead <nuxtlink> element.
const NuxtLinkComponent = resolveComponent('NuxtLink')

defineProps({
  // Items: [{ action?, label?, description?, onClick?, to?, href?, icon?, disabled?, danger?, divider?, testid? }]
  //
  // `description` is a muted second line under the label. It exists so a
  // DISABLED item can explain itself: Headless UI's disabled MenuItems take no
  // focus and swallow pointer events, so a tooltip on one is unreachable — and
  // a dead action with no visible reason is the callejón this codebase keeps
  // arguing against.
  items: { type: Array, required: true },
  align: { type: String, default: 'right' }, // left | right
  // Which way the panel opens. `top` is for triggers anchored to the bottom of
  // the viewport (a sticky bulk bar), where the default downward panel would
  // render off screen.
  placement: { type: String, default: 'bottom' }, // bottom | top
  width: { type: String, default: 'w-56' },
})

function itemColorClass(danger, active) {
  if (danger) return active ? 'bg-danger-soft text-danger-strong' : 'text-danger-strong'
  return active ? 'bg-surface-raised text-text-default' : 'text-text-default'
}

function itemLabel(item) {
  if (item.label) return item.label
  return item.action ? getPanelAction(item.action).label : ''
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
          'absolute z-30 rounded-xl bg-surface border border-border-default shadow-raised focus:outline-none p-1',
          width,
          // The offset and the transform origin travel together: a drop-up has
          // to grow from its bottom edge or the scale-95 transition reads as
          // the panel sliding out of the trigger backwards.
          placement === 'top' ? 'bottom-full mb-2' : 'mt-2',
          align === 'right'
            ? (placement === 'top' ? 'right-0 origin-bottom-right' : 'right-0 origin-top-right')
            : (placement === 'top' ? 'left-0 origin-bottom-left' : 'left-0 origin-top-left'),
        ]"
      >
        <template v-for="(item, idx) in items" :key="idx">
          <div v-if="item.divider" class="my-1 border-t border-border-muted" />
          <MenuItem v-else v-slot="{ active, disabled }" :disabled="item.disabled">
            <component
              :is="item.href ? 'a' : item.to ? NuxtLinkComponent : 'button'"
              :to="item.to"
              :href="item.href"
              :target="item.href ? (item.target || '_blank') : undefined"
              :rel="item.href ? 'noopener noreferrer' : undefined"
              :type="item.to || item.href ? undefined : 'button'"
              :disabled="disabled"
              :data-testid="item.testid || undefined"
              :class="[
                'base-dropdown-item flex min-h-11 w-full items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors text-left',
                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
                itemColorClass(item.danger, active),
              ]"
              @click="item.onClick && item.onClick($event)"
            >
              <BaseActionIcon v-if="item.action" :action="item.action" />
              <component v-else-if="item.icon" :is="item.icon" class="w-4 h-4 flex-shrink-0" aria-hidden="true" />
              <span class="flex-1 min-w-0">
                <span class="block">{{ itemLabel(item) }}</span>
                <span v-if="item.description" class="block text-xs text-text-muted mt-0.5">
                  {{ item.description }}
                </span>
              </span>
            </component>
          </MenuItem>
        </template>
      </MenuItems>
    </transition>
  </Menu>
</template>
