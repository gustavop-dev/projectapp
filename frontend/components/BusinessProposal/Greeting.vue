<template>
  <section class="greeting-section min-h-screen flex items-center relative overflow-hidden bg-white">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 relative z-10">
      <div class="greeting-content max-w-7xl">
        <h1 class="main-title font-light text-esmerald leading-tight mb-8">
          Propuesta de Desarrollo Web, {{ clientName }}
        </h1>
        
        <p class="subtitle font-light text-green-light italic">
          "{{ inspirationalQuote }}"
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  clientName: {
    type: String,
    default: 'Juan Pablo'
  },
  inspirationalQuote: {
    type: String,
    default: 'Design is not just what it looks like and feels like. Design is how it works.'
  }
});
</script>

<style scoped>
.greeting-section {
  position: relative;
}

.main-title {
  font-size: clamp(3rem, 8vw, 8rem);
  animation: fadeInUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  opacity: 0;
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: clamp(1.25rem, 3vw, 2.5rem);
  animation: fadeInUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s forwards;
  opacity: 0;
  letter-spacing: 0.02em;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
