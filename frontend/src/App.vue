<template>
  <!-- Displays a loading screen while the app is initializing -->
  <LoadingScreen v-show="loading"></LoadingScreen>
  
  <!-- Main router view, only shown when loading is complete -->
  <RouterView v-show="!loading"/>
</template>

<script setup>
import { useLanguageStore } from '@/stores/language';
import { ref, onMounted, onBeforeMount, watch } from 'vue';
import LoadingScreen from '@/components/layouts/LoadingScreen.vue';
import { RouterView } from 'vue-router';

const languageStore = useLanguageStore(); // Access the language store
const loading = ref(true); // State to track whether the app is still loading

/**
 * Handles the load event, hides the loading screen once the app is loaded.
 */
const handleLoad = () => {
  loading.value = false;
};

/**
 * Initializes the app by detecting the browser language and setting the lang attribute in the HTML.
 * If the language is not set, it detects and loads the global messages based on the detected language.
 */
const initializeApp = async () => {
  // Detect browser language if it's not set yet
  if (!languageStore.currentLanguage) {
    languageStore.detectBrowserLanguage();  // Automatically loads global messages
  }

  // Set the initial lang attribute based on the current language
  document.documentElement.lang = languageStore.currentLanguage;
};

// Watch for changes in the current language and update the lang attribute dynamically
watch(() => languageStore.currentLanguage, (newLang) => {
  document.documentElement.lang = newLang;
});

// Lifecycle hook that runs before the component is mounted
onBeforeMount(async () => {
  await initializeApp(); // Initialize app before mounting
});

// Lifecycle hook that runs when the component is mounted
onMounted(() => {
  window.addEventListener('load', handleLoad); // Add event listener for load

  // Clean-up: remove the event listener when the component is unmounted
  return () => {
    window.removeEventListener('load', handleLoad);
  };
});
</script>

<style>
/* Hide horizontal overflow */
body {
  overflow-x: hidden;
}
</style>

