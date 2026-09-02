import { defineStore } from 'pinia';
import {
  create_request,
  delete_request,
  get_request,
  patch_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';

let candidateToken = 0;
let threadToken = 0;
let threadListToken = 0;

export const useDocumentThreadStore = defineStore('document-threads', {
  state: () => ({
    currentThread: null,
    threads: [],
    threadCount: 0,
    candidates: [],
    candidateCount: 0,
    candidateNext: null,
    candidatePrevious: null,
    detailCache: {},
    isLoadingThread: false,
    isLoadingThreads: false,
    isLoadingCandidates: false,
    isLoadingDetail: false,
    isSaving: false,
    error: null,
  }),

  actions: {
    async fetchThread(documentId) {
      const token = ++threadToken;
      this.isLoadingThread = true;
      this.error = null;
      try {
        const response = await get_request(`documents/${documentId}/thread/`);
        const data = response.data || null;
        if (token === threadToken) this.currentThread = data;
        return { success: true, data };
      } catch (error) {
        const stale = token !== threadToken;
        if (!stale) this.error = 'thread_fetch_failed';
        return {
          success: false,
          stale,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo cargar el hilo.'),
        };
      } finally {
        if (token === threadToken) this.isLoadingThread = false;
      }
    },

    async fetchThreads({
      search = '',
      order = 'recent',
      page = 1,
      pageSize = 20,
    } = {}) {
      const token = ++threadListToken;
      this.isLoadingThreads = true;
      this.error = null;
      try {
        const params = new URLSearchParams({
          order,
          page: String(page),
          page_size: String(pageSize),
        });
        if (search.trim()) params.set('search', search.trim());
        const response = await get_request(`document-threads/?${params.toString()}`);
        if (token === threadListToken) {
          this.threads = response.data?.results || [];
          this.threadCount = response.data?.count || 0;
        }
        return { success: true, data: response.data };
      } catch (error) {
        const stale = token !== threadListToken;
        if (!stale) this.error = 'thread_list_failed';
        return {
          success: false,
          stale,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudieron cargar los hilos.'),
        };
      } finally {
        if (token === threadListToken) this.isLoadingThreads = false;
      }
    },

    async fetchCandidates({
      documentId,
      threadId = null,
      search = '',
      includeArchived = false,
      page = 1,
      pageSize = 20,
    }) {
      const token = ++candidateToken;
      this.isLoadingCandidates = true;
      this.error = null;
      try {
        const params = new URLSearchParams({
          document_id: String(documentId),
          scope: includeArchived ? 'all' : 'active',
          page: String(page),
          page_size: String(pageSize),
        });
        if (threadId) params.set('thread_id', String(threadId));
        if (search.trim()) params.set('search', search.trim());
        const response = await get_request(`document-threads/candidates/?${params.toString()}`);
        if (token === candidateToken) {
          this.candidates = response.data?.results || [];
          this.candidateCount = response.data?.count || 0;
          this.candidateNext = response.data?.next || null;
          this.candidatePrevious = response.data?.previous || null;
        }
        return { success: true, data: response.data };
      } catch (error) {
        const stale = token !== candidateToken;
        if (!stale) this.error = 'candidate_fetch_failed';
        return {
          success: false,
          stale,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudieron buscar documentos.'),
        };
      } finally {
        if (token === candidateToken) this.isLoadingCandidates = false;
      }
    },

    async fetchDocumentDetail(documentId) {
      if (this.detailCache[documentId]) {
        return { success: true, data: this.detailCache[documentId] };
      }
      this.isLoadingDetail = true;
      try {
        const response = await get_request(`documents/${documentId}/detail/`);
        this.detailCache = { ...this.detailCache, [documentId]: response.data };
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo cargar el documento.'),
        };
      } finally {
        this.isLoadingDetail = false;
      }
    },

    async createThread(payload) {
      return this._save(async () => {
        const response = await create_request('document-threads/', payload);
        this.currentThread = response.data;
        return response.data;
      });
    },

    async updateThread(threadId, payload) {
      return this._save(async () => {
        const response = await patch_request(`document-threads/${threadId}/`, payload);
        this.currentThread = response.data?.dissolved ? null : response.data;
        return response.data;
      });
    },

    async dissolveThread(threadId) {
      return this._save(async () => {
        await delete_request(`document-threads/${threadId}/`);
        this.currentThread = null;
        return null;
      });
    },

    async _save(operation) {
      this.isSaving = true;
      this.error = null;
      try {
        const data = await operation();
        return { success: true, data };
      } catch (error) {
        this.error = 'thread_save_failed';
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo guardar el hilo.'),
        };
      } finally {
        this.isSaving = false;
      }
    },

    reset() {
      threadToken += 1;
      candidateToken += 1;
      this.currentThread = null;
      this.candidates = [];
      this.candidateCount = 0;
      this.candidateNext = null;
      this.candidatePrevious = null;
      this.isLoadingThread = false;
      this.isLoadingCandidates = false;
      this.isLoadingDetail = false;
      this.error = null;
    },
  },
});
