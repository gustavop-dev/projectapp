<template>
  <!-- Displays a loading screen while the app is initializing -->
  <LoadingScreen v-show="loading"></LoadingScreen>

  <!-- Main router view, only shown when loading is complete -->
  <RouterView v-show="!loading"/>
</template>

<script setup>
import { useLanguageStore } from '@/stores/language';
import { ref, onMounted, watch } from 'vue';
import LoadingScreen from '@/components/layouts/LoadingScreen.vue';
import { RouterView } from 'vue-router';

const languageStore = useLanguageStore(); // Access the language store
const loading = ref(true); // State to track whether the app is still loading

/**
 * Initializes the app by detecting the browser language and setting the lang attribute in the HTML.
 * Ensures that language-related data is loaded before hiding the loading screen.
 */
const initializeApp = async () => {
  // Detect browser language if it's not set yet
  if (!languageStore.currentLanguage) {
    await languageStore.detectBrowserLanguage();  // Automatically loads global messages
  }

  // Set the initial lang attribute based on the current language
  document.documentElement.lang = languageStore.currentLanguage;

  // Mark the app as fully loaded only after initializing the language settings
  loading.value = false;
};

// Watch for changes in the current language and update the lang attribute dynamically
watch(() => languageStore.currentLanguage, (newLang) => {
  document.documentElement.lang = newLang;
});

// Lifecycle hook that runs when the component is mounted
onMounted(async () => {
  // Initialize the app and wait for it to be ready before hiding the loading screen
  await initializeApp();
});
</script>

<style>
/* Hide horizontal overflow */
body {
  overflow-x: hidden;
}
</style>

