<template>
  <div class="pastel-wrap" aria-hidden="true">
    <div class="blob p1" />
    <div class="blob p2" />
    <div class="blob p3" />
    <div class="blob p4" />
    <div class="blob p5" />
  </div>
</template>

<style scoped>
.pastel-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(135deg, #fce4ec 0%, #e8eaf6 25%, #e0f7fa 50%, #fff9c4 75%, #f3e5f5 100%);
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.85;
  will-change: transform;
}
.p1 {
  width: 65%; height: 65%; top: -15%; left: -10%;
  background: radial-gradient(circle, #f8bbd0, transparent 70%);
  animation: p1 7s ease-in-out infinite alternate;
}
.p2 {
  width: 55%; height: 55%; top: 15%; right: -15%;
  background: radial-gradient(circle, #b2ebf2, transparent 70%);
  animation: p2 9s ease-in-out infinite alternate;
}
.p3 {
  width: 70%; height: 70%; bottom: -20%; left: 15%;
  background: radial-gradient(circle, #d1c4e9, transparent 70%);
  animation: p3 8s ease-in-out infinite alternate;
}
.p4 {
  width: 50%; height: 50%; top: 40%; left: 35%;
  background: radial-gradient(circle, #fff59d, transparent 70%);
  animation: p4 6s ease-in-out infinite alternate;
}
.p5 {
  width: 45%; height: 45%; top: 5%; left: 55%;
  background: radial-gradient(circle, #c8e6c9, transparent 70%);
  animation: p5 10s ease-in-out infinite alternate;
}
@keyframes p1 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(20%,25%) scale(1.2)} }
@keyframes p2 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(-25%,15%) scale(1.25)} }
@keyframes p3 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(10%,-20%) scale(1.15)} }
@keyframes p4 { 0%{transform:translate(0,0) scale(1.05)} 100%{transform:translate(-15%,20%) scale(0.9)} }
@keyframes p5 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(15%,-15%) scale(1.2)} }
</style>
