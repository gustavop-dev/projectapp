<template>
  <div class="animated-bg" aria-hidden="true">
    <div class="blob blob--esmerald"></div>
    <div class="blob blob--lemon"></div>
    <div class="blob blob--teal"></div>
    <div class="blob blob--mint"></div>
  </div>
</template>

<script setup>
// Purely decorative, animated mesh-gradient background for the home page.
</script>

<style scoped>
.animated-bg {
  position: fixed;
  inset: 0;
  z-index: -10;
  overflow: hidden;
  pointer-events: none;
  /* Soft base around primary-soft (#E6EFEF) so the page keeps its airy tone */
  background:
    linear-gradient(135deg, #eef4f2 0%, #e6efef 45%, #eef3ea 100%);
}

.blob {
  position: absolute;
  border-radius: 9999px;
  filter: blur(72px);
  will-change: transform;
}

/* Brand-tinted orbs — soft, low opacity so foreground stays readable */
.blob--esmerald {
  width: 44vw;
  height: 44vw;
  top: -10%;
  left: -8%;
  background: radial-gradient(circle at 30% 30%, rgba(0, 41, 33, 0.26), rgba(0, 41, 33, 0) 70%);
  animation: drift-a 28s ease-in-out infinite;
}
.blob--lemon {
  width: 36vw;
  height: 36vw;
  top: 4%;
  right: -10%;
  background: radial-gradient(circle at 30% 30%, rgba(240, 255, 61, 0.32), rgba(240, 255, 61, 0) 70%);
  animation: drift-b 34s ease-in-out infinite;
}
.blob--teal {
  width: 48vw;
  height: 48vw;
  bottom: -16%;
  left: 16%;
  background: radial-gradient(circle at 30% 30%, rgba(38, 166, 154, 0.22), rgba(38, 166, 154, 0) 70%);
  animation: drift-c 31s ease-in-out infinite;
}
.blob--mint {
  width: 30vw;
  height: 30vw;
  bottom: 8%;
  right: 14%;
  background: radial-gradient(circle at 30% 30%, rgba(129, 199, 132, 0.22), rgba(129, 199, 132, 0) 70%);
  animation: drift-d 38s ease-in-out infinite;
}

@keyframes drift-a {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  33% { transform: translate3d(12vw, 8vh, 0) scale(1.12); }
  66% { transform: translate3d(4vw, 16vh, 0) scale(0.95); }
}
@keyframes drift-b {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  33% { transform: translate3d(-14vw, 10vh, 0) scale(1.1); }
  66% { transform: translate3d(-6vw, 2vh, 0) scale(0.9); }
}
@keyframes drift-c {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(10vw, -12vh, 0) scale(1.15); }
}
@keyframes drift-d {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(-12vw, -8vh, 0) scale(1.08); }
}

@media (prefers-reduced-motion: reduce) {
  .blob {
    animation: none;
  }
}
</style>
