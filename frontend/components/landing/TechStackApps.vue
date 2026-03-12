<template>
  <section class="py-12 relative overflow-hidden">
    <div class="container mx-auto px-6 flex justify-center">
      <!-- Single Tech Bubble with mobile-focused icons -->
      <div class="tech-bubble">
        <img 
          src="~/assets/images/icons/figma.svg" 
          alt="Figma"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/flutter.png" 
          alt="Flutter"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/react-native-1.svg" 
          alt="React Native"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/apple-ios.webp" 
          alt="iOS"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/android.png" 
          alt="Android"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/stripe.svg" 
          alt="Stripe"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/pngwing.com.png" 
          alt="Django"
          class="tech-icon transition-transform hover:scale-110"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
</script>

<style scoped>
.tech-bubble {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
  padding: 24px 28px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.08),
    0 4px 8px rgba(0, 0, 0, 0.06),
    inset 0 -2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: default;
}

@media (min-width: 768px) {
  .tech-bubble {
    flex-wrap: nowrap;
    gap: 40px;
    padding: 36px 60px;
    border-radius: 80px;
  }
}

.tech-icon {
  height: 28px;
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
}

@media (min-width: 640px) {
  .tech-icon {
    height: 34px;
  }
}

@media (min-width: 768px) {
  .tech-icon {
    height: 40px;
  }
}

@media (min-width: 1024px) {
  .tech-icon {
    height: 48px;
  }
}

.tech-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 24px rgba(0, 0, 0, 0.1),
    0 6px 12px rgba(0, 0, 0, 0.08),
    inset 0 -2px 4px rgba(0, 0, 0, 0.05);
}

section {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
