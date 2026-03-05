/**
 * Mock for Nuxt's #imports auto-import system.
 *
 * Provides stubs for commonly used Nuxt composables and utilities
 * so that stores and composables can be tested in isolation with Jest.
 */
import { ref, computed, reactive, watch, onMounted, onUnmounted, onBeforeUnmount, nextTick, inject, getCurrentInstance } from 'vue';

export {
  ref,
  computed,
  reactive,
  watch,
  onMounted,
  onUnmounted,
  onBeforeUnmount,
  nextTick,
  inject,
  getCurrentInstance,
};

export const useRuntimeConfig = () => ({
  public: {
    apiBase: 'http://localhost:8000/api',
  },
});

export const useRoute = () => ({
  params: {},
  query: {},
  path: '/',
  fullPath: '/',
  name: 'index___en-us',
});

export const useRouter = () => ({
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  currentRoute: { value: { path: '/' } },
});

export const useI18n = () => ({
  t: jest.fn((key) => key),
  tm: jest.fn((key) => ({})),
  locale: ref('en-us'),
  locales: ref([{ code: 'es-co' }, { code: 'en-us' }]),
});

export const useSwitchLocalePath = () => jest.fn((locale) => `/${locale}`);
export const useLocalePath = () => jest.fn((path) => path);
export const useLocaleHead = () => ref({ htmlAttrs: { lang: 'en' }, link: [] });

export const navigateTo = jest.fn();
export const definePageMeta = jest.fn();
export const useHead = jest.fn();
export const useSeoMeta = jest.fn();
export const useNuxtApp = () => ({
  $i18n: { locale: { value: 'es' } },
});
