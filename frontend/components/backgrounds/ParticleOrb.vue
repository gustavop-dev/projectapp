<template>
  <div class="particle-orb" aria-hidden="true">
    <div class="orb-core" />
    <div class="ring ring-1" />
    <div class="ring ring-2" />
    <div class="ring ring-3" />
    <div class="particles">
      <span v-for="i in 40" :key="i" class="particle" :style="particleStyle(i)" />
    </div>
  </div>
</template>

<script setup>
function particleStyle(i) {
  const angle = (i / 40) * 360;
  const radius = 30 + Math.random() * 20;
  const duration = 6 + Math.random() * 8;
  const delay = Math.random() * -10;
  const size = 2 + Math.random() * 3;
  return {
    '--angle': `${angle}deg`,
    '--radius': `${radius}%`,
    '--duration': `${duration}s`,
    '--delay': `${delay}s`,
    '--size': `${size}px`,
    '--opacity': `${0.3 + Math.random() * 0.7}`,
  };
}
</script>

<style scoped>
.particle-orb {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at center, #0a1628 0%, #060d1a 50%, #020408 100%);
  overflow: hidden;
}

.orb-core {
  position: absolute;
  width: 35%;
  height: 35%;
  border-radius: 50%;
  background: radial-gradient(circle at 40% 40%, #4a9eff 0%, #2060c0 30%, #103060 60%, transparent 75%);
  box-shadow:
    0 0 80px 20px rgba(74, 158, 255, 0.3),
    0 0 160px 60px rgba(74, 158, 255, 0.15),
    inset 0 0 40px 10px rgba(74, 158, 255, 0.2);
  animation: pulse 4s ease-in-out infinite alternate;
}

.ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(74, 158, 255, 0.15);
}

.ring-1 {
  width: 45%;
  height: 45%;
  animation: rotate3d1 20s linear infinite;
  transform: rotateX(60deg);
}

.ring-2 {
  width: 55%;
  height: 55%;
  border-color: rgba(100, 200, 255, 0.1);
  animation: rotate3d2 25s linear infinite reverse;
  transform: rotateX(70deg) rotateY(20deg);
}

.ring-3 {
  width: 65%;
  height: 65%;
  border-color: rgba(74, 158, 255, 0.08);
  animation: rotate3d3 30s linear infinite;
  transform: rotateX(50deg) rotateY(-30deg);
}

.particles {
  position: absolute;
  width: 100%;
  height: 100%;
}

.particle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  background: rgba(74, 158, 255, var(--opacity));
  box-shadow: 0 0 6px 1px rgba(74, 158, 255, 0.4);
  animation: orbit var(--duration) linear var(--delay) infinite;
  transform-origin: 0 0;
}

@keyframes pulse {
  0% { transform: scale(1); filter: brightness(1); }
  100% { transform: scale(1.05); filter: brightness(1.15); }
}

@keyframes rotate3d1 {
  from { transform: rotateX(60deg) rotateZ(0deg); }
  to { transform: rotateX(60deg) rotateZ(360deg); }
}

@keyframes rotate3d2 {
  from { transform: rotateX(70deg) rotateY(20deg) rotateZ(0deg); }
  to { transform: rotateX(70deg) rotateY(20deg) rotateZ(360deg); }
}

@keyframes rotate3d3 {
  from { transform: rotateX(50deg) rotateY(-30deg) rotateZ(0deg); }
  to { transform: rotateX(50deg) rotateY(-30deg) rotateZ(360deg); }
}

@keyframes orbit {
  0% {
    transform: rotate(var(--angle)) translateX(var(--radius)) rotate(calc(-1 * var(--angle)));
    opacity: var(--opacity);
  }
  50% {
    opacity: calc(var(--opacity) * 0.3);
  }
  100% {
    transform: rotate(calc(var(--angle) + 360deg)) translateX(var(--radius)) rotate(calc(-1 * (var(--angle) + 360deg)));
    opacity: var(--opacity);
  }
}
</style>
