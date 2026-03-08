<template>
  <div>
    <!-- Header row -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <NuxtLink to="/panel/blog" class="text-gray-400 hover:text-gray-600 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </NuxtLink>
        <h1 class="text-2xl font-light text-gray-900">Editar Blog Post</h1>
      </div>
      <button
        v-if="loaded"
        type="button"
        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors"
        :class="showPreview
          ? 'bg-emerald-600 text-white hover:bg-emerald-700'
          : 'border border-gray-200 text-gray-700 hover:bg-gray-50'"
        @click="togglePreview"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
        {{ showPreview ? 'Cerrar preview' : 'Vista previa' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="blogStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
    </div>

    <!-- Main layout: form + optional preview -->
    <div v-else-if="loaded" class="flex gap-6" :class="showPreview ? 'lg:flex-row flex-col' : ''">
      <!-- Form column -->
      <form
        class="space-y-6 flex-1 min-w-0"
        :class="showPreview ? '' : 'max-w-3xl'"
        @submit.prevent="handleSubmit"
      >
        <!-- Slug -->
        <div>
          <label for="slug" class="block text-sm font-medium text-gray-700 mb-1">Slug</label>
          <input id="slug" v-model="form.slug" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
          <p class="text-xs text-gray-400 mt-1">URL: /blog/{{ form.slug || '...' }}</p>
        </div>

        <!-- Metadata row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
            <select v-model="form.category" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white">
              <option value="">Sin categoría</option>
              <option v-for="cat in blogStore.availableCategories" :key="cat.slug" :value="cat.slug">{{ cat.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Autor</label>
            <select v-model="form.author" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white">
              <option value="projectapp-team">Project App Team</option>
              <option value="gustavo-perez">Gustavo Pérez — CEO</option>
              <option value="carlos-blanco">Carlos Blanco — CFO</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tiempo lectura (min)</label>
            <input v-model.number="form.read_time_minutes" type="number" min="0" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
          </div>
          <div class="flex items-end">
            <label class="relative inline-flex items-center cursor-pointer gap-3">
              <input v-model="form.is_featured" type="checkbox" class="sr-only peer" />
              <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600" />
              <span class="text-sm text-gray-700">Destacado</span>
            </label>
          </div>
        </div>

        <!-- Español Section -->
        <fieldset class="border border-gray-200 rounded-xl p-5 space-y-4">
          <legend class="text-sm font-medium text-gray-700 px-2">Español</legend>
          <div>
            <label for="title_es" class="block text-sm font-medium text-gray-700 mb-1">Título (ES)</label>
            <input id="title_es" v-model="form.title_es" type="text" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
          </div>
          <div>
            <label for="excerpt_es" class="block text-sm font-medium text-gray-700 mb-1">Resumen (ES)</label>
            <textarea id="excerpt_es" v-model="form.excerpt_es" rows="2" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
          </div>
          <div>
            <label for="content_es" class="block text-sm font-medium text-gray-700 mb-1">Contenido HTML (ES)</label>
            <textarea id="content_es" v-model="form.content_es" rows="6" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Contenido JSON (ES)</label>
            <textarea v-model="form.content_json_es_raw" rows="10" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" placeholder='{ "intro": "...", "sections": [...], "conclusion": "...", "cta": "..." }' />
            <p class="text-xs text-gray-400 mt-1">JSON estructurado con intro, sections, conclusion y cta. Tiene prioridad sobre el HTML.</p>
          </div>
        </fieldset>

        <!-- English Section -->
        <fieldset class="border border-gray-200 rounded-xl p-5 space-y-4">
          <legend class="text-sm font-medium text-gray-700 px-2">English</legend>
          <div>
            <label for="title_en" class="block text-sm font-medium text-gray-700 mb-1">Title (EN)</label>
            <input id="title_en" v-model="form.title_en" type="text" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
          </div>
          <div>
            <label for="excerpt_en" class="block text-sm font-medium text-gray-700 mb-1">Excerpt (EN)</label>
            <textarea id="excerpt_en" v-model="form.excerpt_en" rows="2" required class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
          </div>
          <div>
            <label for="content_en" class="block text-sm font-medium text-gray-700 mb-1">Content HTML (EN)</label>
            <textarea id="content_en" v-model="form.content_en" rows="6" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Content JSON (EN)</label>
            <textarea v-model="form.content_json_en_raw" rows="10" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-mono focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" placeholder='{ "intro": "...", "sections": [...], "conclusion": "...", "cta": "..." }' />
          </div>
        </fieldset>

        <!-- SEO Section -->
        <fieldset class="border border-gray-200 rounded-xl p-5 space-y-6">
          <legend class="text-sm font-medium text-gray-700 px-2">SEO</legend>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Meta título (ES)</label>
              <input v-model="form.meta_title_es" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="Título SEO en español (60 caracteres recomendado)" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Meta title (EN)</label>
              <input v-model="form.meta_title_en" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="SEO title in English (60 characters recommended)" />
            </div>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Meta descripción (ES)</label>
              <textarea v-model="form.meta_description_es" rows="3" class="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm leading-relaxed focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" placeholder="Descripción SEO en español (150-160 caracteres recomendado)" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Meta description (EN)</label>
              <textarea v-model="form.meta_description_en" rows="3" class="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm leading-relaxed focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-y" placeholder="SEO description in English (150-160 characters recommended)" />
            </div>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Keywords (ES)</label>
              <input v-model="form.meta_keywords_es" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="cortinas inteligentes, automatización hogar, domotica" />
              <p class="text-xs text-gray-400 mt-1">Separadas por coma. Palabras clave objetivo para SEO.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Keywords (EN)</label>
              <input v-model="form.meta_keywords_en" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="smart blinds, home automation, domotics" />
            </div>
          </div>
        </fieldset>

        <!-- Cover image -->
        <fieldset class="border border-gray-200 rounded-xl p-5 space-y-4">
          <legend class="text-sm font-medium text-gray-700 px-2">Imagen de portada</legend>

          <!-- File upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Subir archivo</label>
            <div class="flex items-center gap-3">
              <label class="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                Seleccionar imagen
                <input type="file" accept="image/*" class="hidden" @change="handleCoverUpload" />
              </label>
              <span v-if="uploadFileName" class="text-xs text-gray-500">{{ uploadFileName }}</span>
              <span v-if="isUploading" class="text-xs text-emerald-600">Subiendo...</span>
            </div>
          </div>

          <!-- OR divider -->
          <div class="flex items-center gap-3">
            <div class="flex-1 border-t border-gray-200" />
            <span class="text-xs text-gray-400">o pegar URL externa</span>
            <div class="flex-1 border-t border-gray-200" />
          </div>

          <!-- URL input -->
          <div>
            <label for="cover_image_url" class="block text-sm font-medium text-gray-700 mb-1">URL de imagen</label>
            <input id="cover_image_url" v-model="form.cover_image_url" type="url" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="https://example.com/image.jpg" />
          </div>

          <!-- Preview -->
          <div v-if="coverImagePreview" class="mt-2 rounded-xl overflow-hidden border border-gray-200 max-w-md">
            <img :src="coverImagePreview" alt="Preview" class="w-full h-auto" @error="imgError = true" />
            <p v-if="imgError" class="text-xs text-red-400 p-2">No se pudo cargar la imagen.</p>
          </div>

          <!-- Credit -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Crédito de imagen</label>
              <input v-model="form.cover_image_credit" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="Foto de John Doe en Unsplash" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">URL del crédito</label>
              <input v-model="form.cover_image_credit_url" type="url" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="https://unsplash.com/@johndoe" />
            </div>
          </div>
        </fieldset>

        <!-- Sources -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="block text-sm font-medium text-gray-700">Fuentes</label>
            <button type="button" class="text-xs text-emerald-600 hover:text-emerald-700 transition-colors" @click="addSource">+ Agregar fuente</button>
          </div>
          <div v-for="(source, idx) in form.sources" :key="idx" class="flex gap-2 mb-2">
            <input v-model="source.name" type="text" class="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="Nombre de la fuente" />
            <input v-model="source.url" type="url" class="flex-[2] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" placeholder="https://..." />
            <button type="button" class="text-gray-400 hover:text-red-500 transition-colors px-2" @click="removeSource(idx)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <p v-if="form.sources.length === 0" class="text-xs text-gray-400">No hay fuentes agregadas.</p>
        </div>

        <!-- Publishing options -->
        <fieldset class="border border-gray-200 rounded-xl p-5 space-y-4">
          <legend class="text-sm font-medium text-gray-700 px-2">Publicación</legend>
          <div class="flex flex-col gap-3">
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="publishMode" type="radio" value="draft" name="publishMode" class="w-4 h-4 text-emerald-600 focus:ring-emerald-500" />
              <span class="text-sm text-gray-700">Borrador</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="publishMode" type="radio" value="now" name="publishMode" class="w-4 h-4 text-emerald-600 focus:ring-emerald-500" />
              <span class="text-sm text-gray-700">Publicar ahora</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="publishMode" type="radio" value="schedule" name="publishMode" class="w-4 h-4 text-emerald-600 focus:ring-emerald-500" />
              <span class="text-sm text-gray-700">Programar publicación</span>
            </label>
            <div v-if="publishMode === 'schedule'" class="ml-7">
              <input v-model="scheduledDate" type="datetime-local" class="px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all" />
              <p class="text-xs text-gray-400 mt-1">El post se publicará automáticamente en la fecha seleccionada.</p>
            </div>
          </div>
        </fieldset>

        <!-- Error / Success -->
        <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>
        <p v-if="successMsg" class="text-sm text-emerald-600">{{ successMsg }}</p>

        <!-- Actions -->
        <div class="flex gap-3 pt-4">
          <button type="submit" :disabled="blogStore.isUpdating" class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50">
            {{ blogStore.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
          </button>
          <a v-if="post?.slug" :href="`/blog/${post.slug}`" target="_blank" class="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors inline-flex items-center gap-1">
            Ver en blog
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
          </a>
        </div>
      </form>

      <!-- Preview panel: desktop (inline) -->
      <aside
        v-if="showPreview"
        class="hidden lg:block w-[45%] flex-shrink-0 sticky top-20 self-start max-h-[calc(100vh-6rem)] overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-sm"
      >
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700">Vista previa</span>
          <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
            <button
              type="button"
              :class="['px-3 py-1 text-xs rounded-md transition-colors', previewLang === 'es' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500']"
              @click="previewLang = 'es'"
            >ES</button>
            <button
              type="button"
              :class="['px-3 py-1 text-xs rounded-md transition-colors', previewLang === 'en' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500']"
              @click="previewLang = 'en'"
            >EN</button>
          </div>
        </div>
        <div class="p-6">
          <div v-if="previewCategory" class="mb-4">
            <span class="px-3 py-1.5 rounded-full text-xs bg-emerald-50 text-emerald-700 font-medium capitalize">{{ previewCategory }}</span>
          </div>
          <h1 class="text-2xl font-light text-gray-900 mb-3 leading-tight">{{ previewTitle }}</h1>
          <p class="text-sm text-gray-500 mb-4 leading-relaxed">{{ previewExcerpt }}</p>
          <div v-if="coverImagePreview" class="mb-6 rounded-xl overflow-hidden border border-gray-200">
            <img :src="coverImagePreview" alt="Cover" class="w-full h-auto" />
          </div>
          <div v-if="form.read_time_minutes" class="text-xs text-gray-400 mb-6">{{ form.read_time_minutes }} min de lectura</div>
          <BlogContentRenderer :content-json="previewContentJson" :html-content="previewHtmlContent" />
        </div>
      </aside>
    </div>

    <!-- Preview drawer: mobile/tablet -->
    <Teleport to="body">
      <Transition name="drawer">
        <div v-if="showPreview && isMobilePreview" class="fixed inset-0 z-50 flex justify-end" @click.self="showPreview = false">
          <div class="absolute inset-0 bg-black/30" @click="showPreview = false" />
          <div class="relative w-[90vw] max-w-lg h-full bg-white shadow-2xl overflow-y-auto">
            <div class="sticky top-0 bg-white z-10 p-4 border-b border-gray-100 flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700">Vista previa</span>
              <div class="flex items-center gap-3">
                <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
                  <button
                    type="button"
                    :class="['px-3 py-1 text-xs rounded-md transition-colors', previewLang === 'es' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500']"
                    @click="previewLang = 'es'"
                  >ES</button>
                  <button
                    type="button"
                    :class="['px-3 py-1 text-xs rounded-md transition-colors', previewLang === 'en' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500']"
                    @click="previewLang = 'en'"
                  >EN</button>
                </div>
                <button type="button" class="text-gray-400 hover:text-gray-600" @click="showPreview = false">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            <div class="p-6">
              <div v-if="previewCategory" class="mb-4">
                <span class="px-3 py-1.5 rounded-full text-xs bg-emerald-50 text-emerald-700 font-medium capitalize">{{ previewCategory }}</span>
              </div>
              <h1 class="text-2xl font-light text-gray-900 mb-3 leading-tight">{{ previewTitle }}</h1>
              <p class="text-sm text-gray-500 mb-4 leading-relaxed">{{ previewExcerpt }}</p>
              <div v-if="coverImagePreview" class="mb-6 rounded-xl overflow-hidden border border-gray-200">
                <img :src="coverImagePreview" alt="Cover" class="w-full h-auto" />
              </div>
              <div v-if="form.read_time_minutes" class="text-xs text-gray-400 mb-6">{{ form.read_time_minutes }} min de lectura</div>
              <BlogContentRenderer :content-json="previewContentJson" :html-content="previewHtmlContent" />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useBlogStore } from '~/stores/blog';
import BlogContentRenderer from '~/components/blog/BlogContentRenderer.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const blogStore = useBlogStore();
const post = computed(() => blogStore.currentPost);
const loaded = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const imgError = ref(false);
const uploadFileName = ref('');
const isUploading = ref(false);

const showPreview = ref(false);
const previewLang = ref('es');
const windowWidth = ref(1024);
const isMobilePreview = computed(() => windowWidth.value < 1024);

const publishMode = ref('draft');
const scheduledDate = ref('');

function handleResize() { windowWidth.value = window.innerWidth; }

function togglePreview() { showPreview.value = !showPreview.value; }

const form = reactive({
  title_es: '',
  title_en: '',
  slug: '',
  excerpt_es: '',
  excerpt_en: '',
  content_es: '',
  content_en: '',
  content_json_es_raw: '',
  content_json_en_raw: '',
  cover_image: '',
  cover_image_url: '',
  sources: [],
  category: '',
  author: 'projectapp-team',
  read_time_minutes: 0,
  is_featured: false,
  is_published: false,
  meta_title_es: '',
  meta_title_en: '',
  meta_description_es: '',
  meta_description_en: '',
  meta_keywords_es: '',
  meta_keywords_en: '',
  cover_image_credit: '',
  cover_image_credit_url: '',
});

onMounted(async () => {
  windowWidth.value = window.innerWidth;
  window.addEventListener('resize', handleResize);
  blogStore.fetchCategories();

  const result = await blogStore.fetchAdminPost(route.params.id);
  if (result.success && result.data) {
    populateForm(result.data);
  }
  loaded.value = true;
});

onUnmounted(() => { window.removeEventListener('resize', handleResize); });

function jsonToStr(val) {
  if (!val || (typeof val === 'object' && Object.keys(val).length === 0)) return '';
  return JSON.stringify(val, null, 2);
}

function strToJson(str) {
  if (!str || !str.trim()) return {};
  try { return JSON.parse(str); }
  catch { return {}; }
}

function populateForm(data) {
  form.title_es = data.title_es || '';
  form.title_en = data.title_en || '';
  form.slug = data.slug || '';
  form.excerpt_es = data.excerpt_es || '';
  form.excerpt_en = data.excerpt_en || '';
  form.content_es = data.content_es || '';
  form.content_en = data.content_en || '';
  form.content_json_es_raw = jsonToStr(data.content_json_es);
  form.content_json_en_raw = jsonToStr(data.content_json_en);
  form.cover_image = data.cover_image_display || data.cover_image || '';
  form.cover_image_url = data.cover_image_url || '';
  form.sources = Array.isArray(data.sources)
    ? data.sources.map(s => ({ ...s }))
    : [];
  form.category = data.category || '';
  form.read_time_minutes = data.read_time_minutes || 0;
  form.is_featured = data.is_featured || false;
  form.is_published = data.is_published || false;
  form.author = data.author || 'projectapp-team';
  form.meta_title_es = data.meta_title_es || '';
  form.meta_title_en = data.meta_title_en || '';
  form.meta_description_es = data.meta_description_es || '';
  form.meta_description_en = data.meta_description_en || '';
  form.meta_keywords_es = data.meta_keywords_es || '';
  form.meta_keywords_en = data.meta_keywords_en || '';
  form.cover_image_credit = data.cover_image_credit || '';
  form.cover_image_credit_url = data.cover_image_credit_url || '';

  if (data.is_published) {
    publishMode.value = 'now';
  } else if (data.published_at && new Date(data.published_at) > new Date()) {
    publishMode.value = 'schedule';
    const dt = new Date(data.published_at);
    scheduledDate.value = dt.toISOString().slice(0, 16);
  } else {
    publishMode.value = 'draft';
  }
}

const previewTitle = computed(() => previewLang.value === 'en' ? form.title_en : form.title_es);
const previewExcerpt = computed(() => previewLang.value === 'en' ? form.excerpt_en : form.excerpt_es);
const previewCategory = computed(() => form.category);
const previewContentJson = computed(() => {
  const raw = previewLang.value === 'en' ? form.content_json_en_raw : form.content_json_es_raw;
  return strToJson(raw);
});
const previewHtmlContent = computed(() => previewLang.value === 'en' ? form.content_en : form.content_es);

const coverImagePreview = computed(() => form.cover_image || form.cover_image_url || '');

watch(() => form.cover_image_url, () => {
  imgError.value = false;
});

async function handleCoverUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  uploadFileName.value = file.name;
  isUploading.value = true;
  const result = await blogStore.uploadCoverImage(route.params.id, file);
  isUploading.value = false;
  if (result.success) {
    form.cover_image = result.data.cover_image_display || '';
    successMsg.value = 'Imagen subida correctamente.';
    setTimeout(() => { successMsg.value = ''; }, 3000);
  } else {
    errorMsg.value = 'Error al subir la imagen.';
  }
}

function addSource() {
  form.sources.push({ name: '', url: '' });
}

function removeSource(idx) {
  form.sources.splice(idx, 1);
}

async function handleSubmit() {
  errorMsg.value = '';
  successMsg.value = '';

  const payload = {
    title_es: form.title_es,
    title_en: form.title_en,
    slug: form.slug,
    excerpt_es: form.excerpt_es,
    excerpt_en: form.excerpt_en,
    content_es: form.content_es,
    content_en: form.content_en,
    content_json_es: strToJson(form.content_json_es_raw),
    content_json_en: strToJson(form.content_json_en_raw),
    sources: form.sources.filter(s => s.name && s.url),
    category: form.category,
    read_time_minutes: form.read_time_minutes,
    is_featured: form.is_featured,
    author: form.author,
    meta_title_es: form.meta_title_es,
    meta_title_en: form.meta_title_en,
    meta_description_es: form.meta_description_es,
    meta_description_en: form.meta_description_en,
    meta_keywords_es: form.meta_keywords_es,
    meta_keywords_en: form.meta_keywords_en,
    cover_image_credit: form.cover_image_credit,
    cover_image_credit_url: form.cover_image_credit_url,
  };

  if (publishMode.value === 'now') {
    payload.is_published = true;
    payload.published_at = null;
  } else if (publishMode.value === 'schedule') {
    payload.is_published = false;
    payload.published_at = scheduledDate.value ? new Date(scheduledDate.value).toISOString() : null;
  } else {
    payload.is_published = false;
    payload.published_at = null;
  }

  if (form.cover_image_url) {
    payload.cover_image_url = form.cover_image_url;
  }

  const result = await blogStore.updatePost(route.params.id, payload);
  if (result.success) {
    successMsg.value = 'Post actualizado correctamente.';
    setTimeout(() => { successMsg.value = ''; }, 3000);
  } else {
    errorMsg.value = 'Error al actualizar el post. Revisa los campos.';
  }
}
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.3s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child,
.drawer-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
