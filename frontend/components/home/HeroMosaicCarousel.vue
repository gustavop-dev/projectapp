<template>
  <!-- Decorative background mosaic. aria-hidden: it carries no information,
       the hero copy does. Drag to scrub; it auto-pans on its own otherwise. -->
  <div
    ref="viewport"
    class="mosaic"
    :class="{ 'is-dragging': isDragging }"
    aria-hidden="true"
    @pointerdown="onPointerDown"
  >
    <div ref="track" class="mosaic__track">
      <!-- One set of columns repeated LOOP_TIMES for a seamless infinite loop
           that always over-covers the viewport. -->
      <div
        v-for="(col, i) in loopColumns"
        :key="i"
        class="mosaic__col"
      >
        <div
          v-for="(tile, j) in col.tiles"
          :key="j"
          class="mosaic__tile"
        >
          <img
            :src="tile.src"
            alt=""
            draggable="false"
            loading="lazy"
            decoding="async"
            class="mosaic__img"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useEventListener, usePreferredReducedMotion } from '@vueuse/core'
import gsap from 'gsap'

import m01 from '~/assets/images/hero/mosaic/mosaic-01.webp'
import m02 from '~/assets/images/hero/mosaic/mosaic-02.webp'
import m03 from '~/assets/images/hero/mosaic/mosaic-03.webp'
import m04 from '~/assets/images/hero/mosaic/mosaic-04.webp'
import m05 from '~/assets/images/hero/mosaic/mosaic-05.webp'
import m06 from '~/assets/images/hero/mosaic/mosaic-06.webp'
import m07 from '~/assets/images/hero/mosaic/mosaic-07.webp'
import m08 from '~/assets/images/hero/mosaic/mosaic-08.webp'
import m09 from '~/assets/images/hero/mosaic/mosaic-09.webp'

// The source images are all landscape (4:3). We display them at varied
// *landscape* aspect ratios so they read as the horizontal artwork they are,
// while the variety + per-column vertical offset gives the staggered
// Pinterest feel.
const SRCS = [m01, m02, m03, m04, m05, m06, m07, m08, m09]

// Few BIG tiles: wide columns with exactly 2 equal-height rows each, so the
// mosaic reads as two clean rows (no vertical stagger) and only ~2-3 columns
// are ever on screen — calm enough not to compete with the copy.
// 5 columns × 2 tiles cycles the 9 images (one repeats).
const COLS_PER_SET = 5
const TILES_PER_COL = 2

const columns = Array.from({ length: COLS_PER_SET }, (_, c) => ({
  tiles: Array.from({ length: TILES_PER_COL }, (_, r) => {
    const idx = c * TILES_PER_COL + r
    return { src: SRCS[idx % SRCS.length] }
  }),
}))

// Repeat the set so that, after wrapping, the remaining columns always span
// wider than any realistic viewport (no blank gap on the leading edge).
const LOOP_TIMES = 3
const loopColumns = computed(() =>
  Array.from({ length: LOOP_TIMES }, () => columns).flat(),
)

const viewport = ref(null)
const track = ref(null)
const isDragging = ref(false)

const reducedMotion = usePreferredReducedMotion()

// --- Motion state (plain vars, not reactive — touched every frame) ---
const AUTO_SPEED = 18 // px/sec ambient drift, leftward
let pos = 0 // current translateX (px)
let velocity = 0 // px/sec, used for inertia after a drag
let loopWidth = 0 // width of ONE column set; the seamless wrap distance
let dragStartX = 0
let dragStartPos = 0
let lastMoveX = 0
let lastMoveT = 0
let tickerFn = null
let setX = null

const measure = () => {
  if (!track.value) return
  const cols = track.value.children
  if (cols.length > COLS_PER_SET) {
    // Exact repeat distance: where the first column of the 2nd set sits minus
    // the first column of the 1st set. Immune to padding/gap rounding.
    loopWidth = cols[COLS_PER_SET].offsetLeft - cols[0].offsetLeft
  } else {
    loopWidth = track.value.scrollWidth / LOOP_TIMES
  }
}

const update = (time, deltaMs) => {
  const dt = Math.min(deltaMs, 50) / 1000 // clamp to avoid jumps on tab refocus

  if (isDragging.value) {
    // Position is driven directly by the pointer while dragging.
  } else if (Math.abs(velocity) > AUTO_SPEED + 1) {
    // Coast after release, decaying toward the ambient drift speed.
    pos += velocity * dt
    velocity += (-AUTO_SPEED - velocity) * Math.min(1, dt * 3)
  } else if (reducedMotion.value !== 'reduce') {
    pos -= AUTO_SPEED * dt
    velocity = -AUTO_SPEED
  }

  if (loopWidth > 0) {
    pos = gsap.utils.wrap(-loopWidth, 0, pos)
  }
  if (setX) setX(pos)
}

const onPointerDown = (e) => {
  if (!viewport.value) return
  isDragging.value = true
  dragStartX = e.clientX
  dragStartPos = pos
  lastMoveX = e.clientX
  lastMoveT = e.timeStamp
  velocity = 0
  viewport.value.setPointerCapture?.(e.pointerId)
}

const onPointerMove = (e) => {
  if (!isDragging.value) return
  pos = dragStartPos + (e.clientX - dragStartX)
  if (loopWidth > 0) pos = gsap.utils.wrap(-loopWidth, 0, pos)
  if (setX) setX(pos) // apply immediately so the drag tracks the pointer 1:1
  // Track instantaneous velocity for the release fling.
  const dtMs = e.timeStamp - lastMoveT
  if (dtMs > 0) {
    velocity = ((e.clientX - lastMoveX) / dtMs) * 1000
    lastMoveX = e.clientX
    lastMoveT = e.timeStamp
  }
}

const endDrag = (e) => {
  if (!isDragging.value) return
  isDragging.value = false
  viewport.value?.releasePointerCapture?.(e.pointerId)
  // velocity carries into update() as inertia; clamp so a hard fling settles.
  velocity = gsap.utils.clamp(-2600, 2600, velocity)
}

onMounted(() => {
  setX = gsap.quickSetter(track.value, 'x', 'px')
  measure()
  setX(pos)
  tickerFn = update
  gsap.ticker.add(tickerFn)

  useEventListener(window, 'pointermove', onPointerMove)
  useEventListener(window, 'pointerup', endDrag)
  useEventListener(window, 'pointercancel', endDrag)
  useEventListener(window, 'resize', measure)
})

onBeforeUnmount(() => {
  if (tickerFn) gsap.ticker.remove(tickerFn)
})
</script>

<style scoped>
.mosaic {
  position: absolute;
  inset: 0;
  overflow: hidden;
  cursor: grab;
  touch-action: pan-y; /* let vertical page scroll through; we own horizontal */
  background: theme('colors.slate.100', #f1f5f9);
}
.mosaic.is-dragging {
  cursor: grabbing;
}

.mosaic__track {
  display: flex;
  height: 100%;
  gap: 0.85rem;
  will-change: transform;
}

.mosaic__col {
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
  width: clamp(19rem, 40vw, 42rem);
  height: 100%;
  gap: 0.85rem;
}

.mosaic__tile {
  /* Two equal rows that fill the column height — clean, aligned, no stagger. */
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  overflow: hidden;
  border-radius: 1.25rem;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
}

.mosaic__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
}

@media (prefers-reduced-motion: reduce) {
  .mosaic__track {
    will-change: auto;
  }
}
</style>
