<template>
  <div
    ref="containerRef"
    class="waves-component relative overflow-hidden"
    :style="containerStyle"
    aria-hidden="true"
  >
    <svg
      ref="svgRef"
      class="block w-full h-full"
      xmlns="http://www.w3.org/2000/svg"
    />
    <div
      class="pointer-dot"
      :style="{
        position: 'absolute',
        top: 0,
        left: 0,
        width: `${pointerSize}rem`,
        height: `${pointerSize}rem`,
        background: strokeColor,
        borderRadius: '50%',
        transform: 'translate3d(calc(var(--x) - 50%), calc(var(--y) - 50%), 0)',
        willChange: 'transform',
      }"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { createNoise2D } from 'simplex-noise';

const props = defineProps({
  strokeColor: { type: String, default: '#c8d96a' },
  backgroundColor: { type: String, default: '#1a2e1a' },
  pointerSize: { type: Number, default: 0.5 },
});

const containerRef = ref(null);
const svgRef = ref(null);

const containerStyle = computed(() => ({
  backgroundColor: props.backgroundColor,
  position: 'absolute',
  top: 0,
  left: 0,
  margin: 0,
  padding: 0,
  width: '100%',
  height: '100%',
  overflow: 'hidden',
  '--x': '-0.5rem',
  '--y': '50%',
}));

const mouse = {
  x: -10, y: 0, lx: 0, ly: 0,
  sx: 0, sy: 0, v: 0, vs: 0, a: 0, set: false,
};

let paths = [];
let lines = [];
let noise = null;
let raf = null;
let bounding = null;

function setSize() {
  if (!containerRef.value || !svgRef.value) return;
  bounding = containerRef.value.getBoundingClientRect();
  svgRef.value.style.width = `${bounding.width}px`;
  svgRef.value.style.height = `${bounding.height}px`;
}

function setLines() {
  if (!svgRef.value || !bounding) return;
  const { width, height } = bounding;
  lines = [];
  paths.forEach(p => p.remove());
  paths = [];

  const xGap = 8;
  const yGap = 8;
  const oWidth = width + 200;
  const oHeight = height + 30;
  const totalLines = Math.ceil(oWidth / xGap);
  const totalPoints = Math.ceil(oHeight / yGap);
  const xStart = (width - xGap * totalLines) / 2;
  const yStart = (height - yGap * totalPoints) / 2;

  for (let i = 0; i < totalLines; i++) {
    const points = [];
    for (let j = 0; j < totalPoints; j++) {
      points.push({
        x: xStart + xGap * i,
        y: yStart + yGap * j,
        wave: { x: 0, y: 0 },
        cursor: { x: 0, y: 0, vx: 0, vy: 0 },
      });
    }

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', props.strokeColor);
    path.setAttribute('stroke-width', '1');
    svgRef.value.appendChild(path);
    paths.push(path);
    lines.push(points);
  }
}

function onResize() {
  setSize();
  setLines();
}

function onMouseMove(e) {
  updateMousePosition(e.pageX, e.pageY);
}

function onTouchMove(e) {
  e.preventDefault();
  const touch = e.touches[0];
  updateMousePosition(touch.clientX, touch.clientY);
}

function updateMousePosition(x, y) {
  if (!bounding) return;
  mouse.x = x - bounding.left;
  mouse.y = y - bounding.top + window.scrollY;

  if (!mouse.set) {
    mouse.sx = mouse.x;
    mouse.sy = mouse.y;
    mouse.lx = mouse.x;
    mouse.ly = mouse.y;
    mouse.set = true;
  }

  if (containerRef.value) {
    containerRef.value.style.setProperty('--x', `${mouse.sx}px`);
    containerRef.value.style.setProperty('--y', `${mouse.sy}px`);
  }
}

function movePoints(time) {
  if (!noise) return;
  lines.forEach((points) => {
    points.forEach((p) => {
      const move = noise(
        (p.x + time * 0.008) * 0.003,
        (p.y + time * 0.003) * 0.002
      ) * 8;

      p.wave.x = Math.cos(move) * 12;
      p.wave.y = Math.sin(move) * 6;

      const dx = p.x - mouse.sx;
      const dy = p.y - mouse.sy;
      const d = Math.hypot(dx, dy);
      const l = Math.max(175, mouse.vs);

      if (d < l) {
        const s = 1 - d / l;
        const f = Math.cos(d * 0.001) * s;
        p.cursor.vx += Math.cos(mouse.a) * f * l * mouse.vs * 0.00035;
        p.cursor.vy += Math.sin(mouse.a) * f * l * mouse.vs * 0.00035;
      }

      p.cursor.vx += (0 - p.cursor.x) * 0.01;
      p.cursor.vy += (0 - p.cursor.y) * 0.01;
      p.cursor.vx *= 0.95;
      p.cursor.vy *= 0.95;
      p.cursor.x += p.cursor.vx;
      p.cursor.y += p.cursor.vy;
      p.cursor.x = Math.min(50, Math.max(-50, p.cursor.x));
      p.cursor.y = Math.min(50, Math.max(-50, p.cursor.y));
    });
  });
}

function moved(point, withCursor = true) {
  return {
    x: point.x + point.wave.x + (withCursor ? point.cursor.x : 0),
    y: point.y + point.wave.y + (withCursor ? point.cursor.y : 0),
  };
}

function drawLines() {
  lines.forEach((points, i) => {
    if (points.length < 2 || !paths[i]) return;
    const first = moved(points[0], false);
    let d = `M ${first.x} ${first.y}`;
    for (let j = 1; j < points.length; j++) {
      const c = moved(points[j]);
      d += `L ${c.x} ${c.y}`;
    }
    paths[i].setAttribute('d', d);
  });
}

function tick(time) {
  mouse.sx += (mouse.x - mouse.sx) * 0.1;
  mouse.sy += (mouse.y - mouse.sy) * 0.1;

  const dx = mouse.x - mouse.lx;
  const dy = mouse.y - mouse.ly;
  mouse.v = Math.hypot(dx, dy);
  mouse.vs += (mouse.v - mouse.vs) * 0.1;
  mouse.vs = Math.min(100, mouse.vs);
  mouse.lx = mouse.x;
  mouse.ly = mouse.y;
  mouse.a = Math.atan2(dy, dx);

  if (containerRef.value) {
    containerRef.value.style.setProperty('--x', `${mouse.sx}px`);
    containerRef.value.style.setProperty('--y', `${mouse.sy}px`);
  }

  movePoints(time);
  drawLines();
  raf = requestAnimationFrame(tick);
}

onMounted(() => {
  if (!containerRef.value || !svgRef.value) return;
  noise = createNoise2D();
  setSize();
  setLines();

  window.addEventListener('resize', onResize);
  window.addEventListener('mousemove', onMouseMove);
  containerRef.value.addEventListener('touchmove', onTouchMove, { passive: false });

  raf = requestAnimationFrame(tick);
});

onBeforeUnmount(() => {
  if (raf) cancelAnimationFrame(raf);
  window.removeEventListener('resize', onResize);
  window.removeEventListener('mousemove', onMouseMove);
  containerRef.value?.removeEventListener('touchmove', onTouchMove);
});
</script>
