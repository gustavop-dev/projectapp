<template>
  <div class="locale-switcher">
    <button 
      class="locale-button"
      @click="toggleDropdown"
      :aria-expanded="isDropdownOpen"
      aria-haspopup="true"
    >
      <span class="current-locale">
        {{ currentLocale?.flag }} {{ currentLocale?.name }}
      </span>
      <svg 
        class="dropdown-icon" 
        :class="{ 'rotated': isDropdownOpen }"
        width="16" 
        height="16" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2"
      >
        <polyline points="6,9 12,15 18,9"></polyline>
      </svg>
    </button>
    
    <div 
      v-if="isDropdownOpen" 
      class="dropdown-menu"
      @click.stop
    >
      <button
        v-for="locale in availableLocales"
        :key="locale.code"
        class="locale-option"
        :class="{ 'active': isActiveLocale(locale.code) }"
        @click="handleLocaleChange(locale.code)"
        :disabled="isActiveLocale(locale.code)"
      >
        <span class="locale-flag">{{ locale.flag }}</span>
        <span class="locale-name">{{ locale.name }}</span>
        <svg 
          v-if="isActiveLocale(locale.code)"
          class="check-icon" 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2"
        >
          <polyline points="20,6 9,17 4,12"></polyline>
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useLocaleNavigation } from '@/composables/useLocaleNavigation';
import { useLanguageStore } from '@/stores/language';

export default {
  name: 'LocaleSwitcher',
  setup() {
    const isDropdownOpen = ref(false);
    const { switchLocale, isActiveLocale, availableLocales } = useLocaleNavigation();
    const languageStore = useLanguageStore();

    const currentLocale = computed(() => {
      return availableLocales.value.find(locale => 
        locale.code === languageStore.currentLocale
      );
    });

    const toggleDropdown = () => {
      isDropdownOpen.value = !isDropdownOpen.value;
    };

    const handleLocaleChange = (localeCode) => {
      if (!isActiveLocale(localeCode)) {
        switchLocale(localeCode);
      }
      isDropdownOpen.value = false;
    };

    const handleClickOutside = (event) => {
      if (!event.target.closest('.locale-switcher')) {
        isDropdownOpen.value = false;
      }
    };

    onMounted(() => {
      document.addEventListener('click', handleClickOutside);
    });

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside);
    });

    return {
      isDropdownOpen,
      currentLocale,
      availableLocales,
      isActiveLocale,
      toggleDropdown,
      handleLocaleChange
    };
  }
};
</script>

<style scoped>
.locale-switcher {
  position: relative;
  display: inline-block;
}

.locale-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.locale-button:hover {
  border-color: #c1c8cd;
  background: #f8f9fa;
}

.locale-button:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.current-locale {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.dropdown-icon {
  transition: transform 0.2s ease;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.locale-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
  text-align: left;
}

.locale-option:hover:not(:disabled) {
  background: #f8f9fa;
}

.locale-option.active {
  background: #e7f3ff;
  cursor: default;
}

.locale-option:disabled {
  cursor: default;
}

.locale-flag {
  font-size: 16px;
}

.locale-name {
  flex: 1;
  font-weight: 500;
}

.check-icon {
  color: #007bff;
  flex-shrink: 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .locale-button {
    padding: 6px 10px;
    font-size: 13px;
  }
  
  .current-locale {
    gap: 4px;
  }
  
  .locale-option {
    padding: 8px 10px;
    font-size: 13px;
  }
}
</style>