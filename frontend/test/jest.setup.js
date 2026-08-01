import { config } from '@vue/test-utils';
import BaseButton from '../components/base/BaseButton.vue';

if (typeof globalThis.structuredClone === 'undefined') {
  globalThis.structuredClone = (obj) => JSON.parse(JSON.stringify(obj));
}

// Nuxt auto-imports everything under components/, so a component that renders
// <BaseButton> resolves it for free in the app. Jest has no such mechanism:
// without this, BaseButton silently renders as an unresolved component and any
// findAll('button') in a spec comes back empty. Registering it globally keeps
// specs honest as buttons migrate to the design system. Specs that register it
// locally still win — local components take precedence over global ones.
config.global.components = {
  ...config.global.components,
  BaseButton,
};
