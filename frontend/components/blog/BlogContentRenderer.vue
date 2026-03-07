<template>
  <div v-if="hasJsonContent" class="blog-json-content">
    <!-- Introduction -->
    <p class="text-xl mb-12 text-esmerald/80 leading-relaxed font-regular">
      {{ contentJson.intro }}
    </p>

    <!-- Sections -->
    <div v-for="(section, index) in contentJson.sections" :key="index" class="mb-16">
      <h2 class="text-2xl md:text-3xl lg:text-4xl font-light mb-6 tracking-tight text-esmerald">
        {{ section.heading }}
      </h2>

      <p v-if="section.content" class="text-lg mb-6 text-green-light leading-relaxed font-regular">
        {{ section.content }}
      </p>

      <!-- List with check icons -->
      <ul v-if="section.list && section.list.length" class="space-y-4 mb-6">
        <li v-for="(item, i) in section.list" :key="i" class="flex items-start gap-3">
          <svg class="w-6 h-6 flex-shrink-0 mt-1 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span class="text-lg text-green-light leading-relaxed font-regular">{{ item }}</span>
        </li>
      </ul>

      <!-- Subsections as cards -->
      <div v-if="section.subsections && section.subsections.length" class="space-y-4 sm:space-y-6">
        <div
          v-for="(sub, i) in section.subsections"
          :key="i"
          class="bg-esmerald-light rounded-2xl p-5 sm:p-8 border border-gray-200/40"
        >
          <h3 class="text-xl font-medium mb-3 text-esmerald">{{ sub.title }}</h3>
          <p class="text-base text-green-light leading-relaxed font-regular">{{ sub.description }}</p>
        </div>
      </div>

      <!-- Timeline with numbered steps -->
      <div v-if="section.timeline && section.timeline.length" class="space-y-4">
        <div v-for="(item, i) in section.timeline" :key="i" class="flex gap-6">
          <div class="flex flex-col items-center">
            <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 bg-esmerald-light">
              <span class="text-lg font-bold text-esmerald">{{ i + 1 }}</span>
            </div>
            <div v-if="i < section.timeline.length - 1" class="w-0.5 h-full mt-2 bg-gray-200" />
          </div>
          <div class="pb-8">
            <h4 class="text-lg font-medium mb-2 text-esmerald">{{ item.step }}</h4>
            <p class="text-base text-green-light leading-relaxed font-regular">{{ item.description }}</p>
          </div>
        </div>
      </div>

      <!-- Examples as grid cards -->
      <div v-if="section.examples && section.examples.length" class="grid md:grid-cols-2 gap-4">
        <div
          v-for="(example, i) in section.examples"
          :key="i"
          class="bg-esmerald-light rounded-xl p-6"
        >
          <p class="text-base font-regular text-esmerald leading-relaxed">{{ example }}</p>
        </div>
      </div>
    </div>

    <!-- Conclusion -->
    <div v-if="contentJson.conclusion" class="bg-esmerald rounded-2xl p-6 sm:p-10 mb-10 sm:mb-12">
      <p class="text-lg sm:text-xl mb-4 sm:mb-6 text-white/90 leading-relaxed font-regular">
        {{ contentJson.conclusion }}
      </p>
      <p v-if="contentJson.cta" class="text-lg text-white/60 leading-relaxed font-light">
        {{ contentJson.cta }}
      </p>
    </div>
  </div>

  <!-- Fallback: HTML content via v-html -->
  <div v-else-if="htmlContent" class="blog-html-content" v-html="htmlContent" />
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  contentJson: {
    type: Object,
    default: () => ({}),
  },
  htmlContent: {
    type: String,
    default: '',
  },
});

const hasJsonContent = computed(() => {
  return props.contentJson
    && typeof props.contentJson === 'object'
    && props.contentJson.intro
    && Array.isArray(props.contentJson.sections);
});
</script>

<style scoped>
.blog-html-content :deep(h2) {
  font-family: 'Ubuntu-Light', sans-serif;
  font-size: 1.75rem;
  color: #002921;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
}

.blog-html-content :deep(h3) {
  font-family: 'Ubuntu-Regular', sans-serif;
  font-size: 1.25rem;
  color: #002921;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

.blog-html-content :deep(p) {
  font-family: 'Ubuntu-Regular', sans-serif;
  color: #809490;
  line-height: 1.75;
  margin-bottom: 1rem;
}

.blog-html-content :deep(a) {
  color: #002921;
  text-decoration: underline;
}

.blog-html-content :deep(strong) {
  color: #002921;
  font-family: 'Ubuntu-Medium', sans-serif;
}

.blog-html-content :deep(ul),
.blog-html-content :deep(ol) {
  color: #809490;
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.blog-html-content :deep(li) {
  margin-bottom: 0.5rem;
  font-family: 'Ubuntu-Regular', sans-serif;
}

.blog-html-content :deep(blockquote) {
  border-left: 3px solid #F0FF3D;
  padding-left: 1rem;
  color: #002921;
  font-style: italic;
  font-family: 'Ubuntu-Regular', sans-serif;
  margin: 1.5rem 0;
}
</style>
