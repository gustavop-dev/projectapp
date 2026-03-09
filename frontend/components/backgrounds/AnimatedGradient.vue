<template>
  <div class="grad-wrap" aria-hidden="true">
    <div class="blob b1" />
    <div class="blob b2" />
    <div class="blob b3" />
    <div class="blob b4" />
    <div class="blob b5" />
    <div class="blob b6" />
  </div>
</template>

<style scoped>
.grad-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(160deg, #0a3d6b 0%, #1a6fa0 30%, #2898c8 55%, #60c0d8 80%, #e8a0c0 100%);
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  mix-blend-mode: screen;
  will-change: transform;
}
.b1 {
  width: 70%; height: 70%; top: -20%; left: -15%;
  background: radial-gradient(circle, rgba(240,160,210,0.9), transparent 70%);
  animation: d1 6s ease-in-out infinite alternate;
}
.b2 {
  width: 60%; height: 60%; top: 10%; right: -20%;
  background: radial-gradient(circle, rgba(100,200,240,0.8), transparent 70%);
  animation: d2 8s ease-in-out infinite alternate;
}
.b3 {
  width: 80%; height: 80%; bottom: -30%; left: 10%;
  background: radial-gradient(circle, rgba(240,130,190,0.85), transparent 70%);
  animation: d3 7s ease-in-out infinite alternate;
}
.b4 {
  width: 50%; height: 50%; top: 30%; left: 40%;
  background: radial-gradient(circle, rgba(60,180,220,0.9), transparent 70%);
  animation: d4 5s ease-in-out infinite alternate;
}
.b5 {
  width: 55%; height: 55%; bottom: 0; right: 5%;
  background: radial-gradient(circle, rgba(240,230,130,0.7), transparent 70%);
  animation: d5 9s ease-in-out infinite alternate;
}
.b6 {
  width: 45%; height: 45%; top: -5%; left: 50%;
  background: radial-gradient(circle, rgba(180,140,240,0.7), transparent 70%);
  animation: d6 7.5s ease-in-out infinite alternate;
}
@keyframes d1 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(25%,30%) scale(1.2)} }
@keyframes d2 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(-30%,20%) scale(1.3)} }
@keyframes d3 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(15%,-25%) scale(1.15)} }
@keyframes d4 { 0%{transform:translate(0,0) scale(1.1)} 100%{transform:translate(-20%,15%) scale(0.9)} }
@keyframes d5 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(20%,-20%) scale(1.25)} }
@keyframes d6 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(-15%,25%) scale(1.1)} }
</style>
