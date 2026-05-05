<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <h1 class="text-2xl font-light text-text-default">Calendario de Blog</h1>
      <div class="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
        <NuxtLink
          :to="localePath('/panel/blog')"
          class="inline-flex flex-1 sm:flex-initial items-center justify-center gap-2 px-4 py-2.5 border border-border-default text-text-default rounded-xl
                 font-medium text-sm hover:bg-surface-raised transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          Lista
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/blog/create')"
          class="inline-flex flex-1 sm:flex-initial items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-xl
                 font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Post
        </NuxtLink>
      </div>
    </div>

    <!-- Week navigation -->
    <div class="bg-surface rounded-xl shadow-sm border border-border-muted mb-6 overflow-hidden">
      <div class="flex items-center justify-between gap-2 px-3 sm:px-6 py-3 sm:py-4 border-b border-border-muted">
        <button
          type="button"
          class="p-2 rounded-lg hover:bg-surface-raised transition-colors text-text-muted shrink-0"
          @click="prevWeek"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div class="text-center min-w-0 flex-1">
          <h2 class="text-xs sm:text-sm font-semibold text-text-default truncate">{{ weekRangeLabel }}</h2>
          <p class="text-[10px] sm:text-xs text-text-subtle mt-0.5">Semana {{ weekNumber }}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            type="button"
            class="px-3 py-1.5 text-xs font-medium text-text-brand border border-emerald-200 dark:border-emerald-500/30 rounded-lg hover:bg-primary-soft transition-colors"
            @click="goToToday"
          >
            Hoy
          </button>
          <button
            type="button"
            class="p-2 rounded-lg hover:bg-surface-raised transition-colors text-text-muted"
            @click="nextWeek"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex justify-center py-12">
        <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
      </div>

      <!-- Week grid (md+) -->
      <div v-else class="hidden md:grid grid-cols-7 divide-x divide-gray-100 dark:divide-white/[0.04]">
        <div
          v-for="day in weekDays"
          :key="day.date"
          class="min-h-[160px] p-3 min-w-0"
          :class="{ 'bg-primary-soft dark:bg-primary-soft': day.isToday }"
        >
          <!-- Day header -->
          <div class="mb-2">
            <p class="text-[10px] uppercase tracking-wider text-text-subtle font-medium">{{ day.dayName }}</p>
            <p
              class="text-sm font-semibold"
              :class="day.isToday ? 'text-text-brand' : 'text-text-default dark:text-white'"
            >
              {{ day.dayNumber }}
            </p>
          </div>

          <!-- Posts for this day -->
          <div class="space-y-1.5">
            <NuxtLink
              v-for="post in day.posts"
              :key="post.id"
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="block px-2 py-1.5 rounded-lg text-xs transition-colors cursor-pointer min-w-0"
              :class="postCardClass(post)"
            >
              <p class="font-medium truncate leading-tight">{{ post.title_es }}</p>
              <p v-if="post.category" class="text-[10px] opacity-70 mt-0.5 truncate">{{ post.category }}</p>
            </NuxtLink>
          </div>

          <!-- Empty state -->
          <p v-if="day.posts.length === 0" class="text-[10px] text-text-subtle dark:text-white/20 mt-3">Sin posts</p>
        </div>
      </div>

      <!-- Mobile day list (vertical) -->
      <div v-if="!isLoading" class="md:hidden divide-y divide-border-muted">
        <div
          v-for="day in weekDays"
          :key="`m-${day.date}`"
          class="px-4 py-3"
          :class="{ 'bg-primary-soft dark:bg-primary-soft': day.isToday }"
        >
          <div class="flex items-baseline justify-between gap-2 mb-2">
            <div class="flex items-baseline gap-2 min-w-0">
              <p class="text-[10px] uppercase tracking-wider text-text-subtle font-medium shrink-0">{{ day.dayName }}</p>
              <p
                class="text-base font-semibold"
                :class="day.isToday ? 'text-text-brand' : 'text-text-default dark:text-white'"
              >
                {{ day.dayNumber }}
              </p>
            </div>
            <span v-if="day.posts.length > 0" class="text-[10px] text-text-subtle shrink-0">{{ day.posts.length }} {{ day.posts.length === 1 ? 'post' : 'posts' }}</span>
          </div>
          <div v-if="day.posts.length > 0" class="space-y-1.5">
            <NuxtLink
              v-for="post in day.posts"
              :key="`m-post-${post.id}`"
              :to="localePath(`/panel/blog/${post.id}/edit`)"
              class="block px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer min-w-0"
              :class="postCardClass(post)"
            >
              <p class="font-medium leading-tight break-words">{{ post.title_es }}</p>
              <p v-if="post.category" class="text-xs opacity-70 mt-0.5 break-words">{{ post.category }}</p>
            </NuxtLink>
          </div>
          <p v-else class="text-xs text-text-subtle dark:text-white/30">Sin posts</p>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2 sm:gap-6 text-xs text-text-muted">
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-primary-soft border border-emerald-200 dark:border-emerald-500/30 inline-block" />
        Publicado
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-blue-100 dark:bg-blue-500/20 border border-blue-200 dark:border-blue-500/30 inline-block" />
        Programado
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-surface-raised border border-border-default inline-block" />
        Borrador
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useBlogStore } from '~/stores/blog';
import { usePanelRefresh } from '~/composables/usePanelRefresh';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const blogStore = useBlogStore();
const isLoading = ref(false);

// Current week offset from today (0 = this week)
const weekOffset = ref(0);

function getMonday(d) {
  const date = new Date(d);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  date.setDate(diff);
  date.setHours(0, 0, 0, 0);
  return date;
}

const currentMonday = computed(() => {
  const today = new Date();
  const monday = getMonday(today);
  monday.setDate(monday.getDate() + weekOffset.value * 7);
  return monday;
});

const currentSunday = computed(() => {
  const sun = new Date(currentMonday.value);
  sun.setDate(sun.getDate() + 6);
  return sun;
});

const weekDays = computed(() => {
  const days = [];
  const dayNames = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
  const today = new Date();
  const todayStr = formatDateISO(today);

  for (let i = 0; i < 7; i++) {
    const d = new Date(currentMonday.value);
    d.setDate(d.getDate() + i);
    const dateStr = formatDateISO(d);
    const postsForDay = (blogStore.calendarPosts || []).filter(p => p.date === dateStr);

    days.push({
      date: dateStr,
      dayName: dayNames[i],
      dayNumber: d.getDate(),
      isToday: dateStr === todayStr,
      posts: postsForDay,
    });
  }
  return days;
});

const weekRangeLabel = computed(() => {
  const opts = { month: 'short', day: 'numeric' };
  const start = currentMonday.value.toLocaleDateString('es-CO', opts);
  const endOpts = { ...opts, year: 'numeric' };
  const end = currentSunday.value.toLocaleDateString('es-CO', endOpts);
  return `${start} — ${end}`;
});

const weekNumber = computed(() => {
  const d = new Date(currentMonday.value);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const week1 = new Date(d.getFullYear(), 0, 4);
  return 1 + Math.round(((d - week1) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7);
});

function formatDateISO(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function prevWeek() { weekOffset.value--; }
function nextWeek() { weekOffset.value++; }
function goToToday() { weekOffset.value = 0; }

function postCardClass(post) {
  if (post.calendar_status === 'published') return 'bg-primary-soft text-emerald-800 dark:text-emerald-300 hover:bg-primary-soft border border-emerald-200 dark:border-emerald-500/20';
  if (post.calendar_status === 'scheduled') return 'bg-blue-50 dark:bg-blue-500/10 text-blue-800 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-500/20 border border-blue-200 dark:border-blue-500/20';
  return 'bg-surface-raised text-text-muted hover:bg-surface-raised border border-border-default';
}

async function fetchWeekData() {
  isLoading.value = true;
  const start = formatDateISO(currentMonday.value);
  const end = formatDateISO(currentSunday.value);
  await blogStore.fetchCalendarPosts(start, end);
  isLoading.value = false;
}

watch(weekOffset, () => { fetchWeekData(); });

onMounted(() => { fetchWeekData(); });
usePanelRefresh(fetchWeekData);
</script>
