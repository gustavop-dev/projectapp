import { defineStore } from 'pinia';
import { DEFAULT_SCOPE, matchesScope, normalizeScope } from '~/utils/archiveScope';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';
import { normalizeApiError, normalizeBlobApiError } from './services/normalize_api_error';

// Fuera del store para que no sean reactivos: descartan respuestas viejas
// cuando dos peticiones se pisan (búsqueda con debounce, refrescos encadenados).
let listToken = 0;
let searchToken = 0;

export const useDocumentStore = defineStore('documents', {
  /**
   * State of the Document store.
   *
   * Properties:
   * - documents (Array): List of documents (admin).
   * - currentDocument (Object|null): Currently viewed/edited document.
   * - isLoading (Boolean): Whether a fetch operation is in progress.
   * - isUpdating (Boolean): Whether a mutation operation is in progress.
   * - error (String|null): Last error message.
   */
  state: () => ({
    documents: [],
    // Resultados de búsqueda: viven aparte porque la búsqueda es global
    // (ignora carpeta y estado) y no debe pisar la lista de navegación.
    searchResults: [],
    counts: {
      documents: { active: 0, archived: 0, unfiled_active: 0, unfiled_archived: 0 },
      folders: { active: 0, archived: 0 },
    },
    currentDocument: null,
    isLoading: false,
    // La búsqueda tiene su propia bandera: comparte skeleton con la lista pero
    // no debe pisar isLoading, que gobierna los fetch de navegación.
    isSearchLoading: false,
    isUpdating: false,
    error: null,
    // Dónde: 'all' | 'root' | 'none' | <folder id>
    activeFolderId: 'all',
    // Estado, eje independiente de la carpeta: 'active' | 'archived' | 'all'
    archiveScope: DEFAULT_SCOPE,
    archivedOrder: 'recent',
    activeTagIds: [],
  }),

  getters: {
    /**
     * getDocumentById: Find a document in the list by its ID.
     */
    getDocumentById: (state) => (id) =>
      state.documents.find((d) => d.id === id),
  },

  actions: {
    /**
     * fetchDocuments: List all documents (admin), applying current filters.
     * Pass `{ folder, scope, tags, order }` to override for this call.
     *
     * `scope` sale de los overrides o cae a 'active', NUNCA del store: esta
     * acción también la consumen create.vue, [id]/edit.vue y las pestañas de
     * diagnóstico y propuestas, que jamás deben heredar el scope archivado.
     * La página del gestor es la única que pasa el suyo explícito.
     */
    async fetchDocuments(overrides = {}) {
      const token = ++listToken;
      this.isLoading = true;
      this.error = null;
      try {
        const folder = overrides.folder !== undefined ? overrides.folder : this.activeFolderId;
        const tags = overrides.tags !== undefined ? overrides.tags : this.activeTagIds;
        const scope = normalizeScope(overrides.scope);
        const order = overrides.order !== undefined ? overrides.order : this.archivedOrder;

        const params = new URLSearchParams();
        // 'root' se resuelve en el cliente: la partición necesita el árbol de
        // carpetas completo, que el store de carpetas ya tiene cargado.
        if (folder && folder !== 'all' && folder !== 'root') {
          params.set('folder', folder === 'none' ? 'none' : String(folder));
        }
        params.set('scope', scope);
        if (Array.isArray(tags) && tags.length > 0) {
          params.set('tags', tags.join(','));
        }
        if (scope === 'archived' && order === 'oldest') params.set('order', 'oldest');

        const response = await get_request(`documents/?${params.toString()}`);
        // Con búsqueda debounced y refrescos por mutación, las respuestas fuera
        // de orden son probables: sólo escribe la última pedida.
        if (token === listToken) this.documents = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching documents:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudieron cargar los documentos.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * searchDocuments: busca por título o cliente en TODO el gestor.
     *
     * Ignora la carpeta actual y el estado a propósito: buscar sirve para
     * encontrar algo cuya ubicación no se recuerda, y acotarlo al scope visible
     * es justo lo que impedía dar con lo archivado.
     */
    async searchDocuments(term) {
      const token = ++searchToken;
      this.isSearchLoading = true;
      this.error = null;
      try {
        const params = new URLSearchParams({ scope: 'all', search: term });
        const response = await get_request(`documents/?${params.toString()}`);
        if (token === searchToken) this.searchResults = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'search_failed';
        console.error('Error searching documents:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo completar la búsqueda.'),
        };
      } finally {
        // Sólo la última búsqueda pedida apaga la bandera: una respuesta vieja
        // no debe cortar el skeleton de la que sigue en vuelo.
        if (token === searchToken) this.isSearchLoading = false;
      }
    },

    /**
     * fetchCounts: totales autoritativos para el panel lateral.
     *
     * No se pueden derivar de la lista: viene filtrada por carpeta, y sumar el
     * `document_count` de cada carpeta ignora los documentos sin carpeta y
     * duplica los que sí la tienen.
     */
    async fetchCounts() {
      try {
        const response = await get_request('documents/counts/');
        // Merge y no reemplazo: un payload parcial no debe vaciar el sidebar.
        this.counts = {
          documents: { ...this.counts.documents, ...(response.data?.documents || {}) },
          folders: { ...this.counts.folders, ...(response.data?.folders || {}) },
        };
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching document counts:', error);
        return { success: false, errors: error.response?.data };
      }
    },

    /**
     * Reconcilia una fila que cambió de estado con el scope que se está viendo.
     *
     * Bajo 'all' la fila se queda y sólo cambia su insignia; bajo un scope
     * concreto se va si dejó de pertenecer.
     */
    _reconcileScope(id, updated) {
      if (matchesScope(updated, this.archiveScope)) {
        const index = this.documents.findIndex((d) => d.id === id);
        if (index !== -1) this.documents.splice(index, 1, updated);
      } else {
        this.documents = this.documents.filter((d) => d.id !== id);
      }
      this.searchResults = this.searchResults.map((d) => (d.id === id ? updated : d));
    },

    /** archiveDocument: take a document out of the main view, keeping it. */
    async archiveDocument(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`documents/${id}/archive/`, {});
        this._reconcileScope(id, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'archive_failed';
        console.error('Error archiving document:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo archivar el documento.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * unarchiveDocument: lo devuelve a la vista principal.
     *
     * `restoredChain` son las carpetas contenedoras que el backend reabrió para
     * que el documento quede alcanzable; la UI las nombra en el aviso.
     */
    async unarchiveDocument(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`documents/${id}/unarchive/`, {});
        this._reconcileScope(id, response.data);
        return {
          success: true,
          data: response.data,
          restoredChain: response.data?.restored_chain || [],
          movedToRoot: !!response.data?.moved_to_root,
        };
      } catch (error) {
        this.error = 'unarchive_failed';
        console.error('Error unarchiving document:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo restaurar el documento.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * setFilters: Update active filters and refetch the list.
     * @param {object} filters - { folder?, scope?, tags?, order? }
     */
    async setFilters({ folder, scope, tags, order } = {}) {
      if (folder !== undefined) this.activeFolderId = folder;
      if (scope !== undefined) this.archiveScope = normalizeScope(scope);
      if (order !== undefined) this.archivedOrder = order;
      if (tags !== undefined) this.activeTagIds = Array.isArray(tags) ? [...tags] : [];
      return this.fetchDocuments({ scope: this.archiveScope });
    },

    /**
     * toggleTagFilter: Toggle a tag id in the current filter set and refetch.
     */
    async toggleTagFilter(tagId) {
      const idx = this.activeTagIds.indexOf(tagId);
      if (idx === -1) this.activeTagIds.push(tagId);
      else this.activeTagIds.splice(idx, 1);
      // El scope viaja explícito, como en setFilters: fetchDocuments no lo
      // hereda del store, y omitirlo aquí sacaba al usuario de Archivados.
      return this.fetchDocuments({ scope: this.archiveScope });
    },

    /**
     * fetchDocument: Retrieve full document detail for admin editing.
     * @param {number} id - Document ID.
     */
    async fetchDocument(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`documents/${id}/detail/`);
        this.currentDocument = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_detail_failed';
        console.error('Error fetching document:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo cargar el documento.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * createFromMarkdown: Create a new document from markdown content.
     * @param {object} data - { title, client_name, language, cover_type, content_markdown }.
     */
    async createFromMarkdown(data) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('documents/create-from-markdown/', data);
        this.currentDocument = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_from_markdown_failed';
        console.error('Error creating document from markdown:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo crear el documento.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updateDocument: Update document metadata and/or content.
     * @param {number} id - Document ID.
     * @param {object} data - Fields to update.
     */
    async updateDocument(id, data) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`documents/${id}/update/`, data);
        this.currentDocument = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating document:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudieron guardar los cambios.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deleteDocument: Delete a document.
     * @param {number} id - Document ID.
     */
    async deleteDocument(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`documents/${id}/delete/`);
        this.documents = this.documents.filter((d) => d.id !== id);
        // También de los resultados de búsqueda: lo archivado se puede borrar
        // desde ahí, y sin esto la fila se quedaría en pantalla.
        this.searchResults = this.searchResults.filter((d) => d.id !== id);
        if (this.currentDocument?.id === id) {
          this.currentDocument = null;
        }
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting document:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo eliminar el documento.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * duplicateDocument: Create a deep copy of a document as a new draft.
     * @param {number} id - Document ID to duplicate.
     */
    async duplicateDocument(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`documents/${id}/duplicate/`, {});
        this.documents.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'duplicate_failed';
        console.error('Error duplicating document:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo duplicar el documento.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * getDocumentMarkdown: Fetch only the markdown content of a document without
     * touching isLoading or currentDocument (safe to call from list views).
     * @param {number} id - Document ID.
     */
    async getDocumentMarkdown(id) {
      try {
        const response = await get_request(`documents/${id}/detail/`);
        return { success: true, markdown: response.data.content_markdown || '' };
      } catch (error) {
        console.error('Error fetching document markdown:', error);
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo obtener el markdown del documento.'),
        };
      }
    },

    /**
     * getEmailDefaults: Fetch default greeting/subject/footer for the email composer.
     */
    async getEmailDefaults() {
      try {
        const response = await get_request('emails/defaults/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching email defaults:', error);
        return { success: false };
      }
    },

    /**
     * sendDocumentEmail: Send a branded email with optional document PDFs attached.
     * @param {object} payload - { recipient_email, subject, greeting, footer, sections, document_ids }
     */
    async sendDocumentEmail(payload) {
      try {
        const formData = new FormData();
        formData.append('recipient_email', payload.recipient_email);
        formData.append('subject', payload.subject);
        formData.append('greeting', payload.greeting || '');
        formData.append('footer', payload.footer || '');
        formData.append('sections', JSON.stringify(payload.sections || []));
        formData.append('document_ids', JSON.stringify(payload.document_ids || []));
        const response = await create_request('emails/send/', formData);
        return { success: true, data: response.data };
      } catch (error) {
        const data = error.response?.data;
        const errorCode = error.response?.status === 429 ? 'rate_limited' : 'send_failed';
        return {
          success: false,
          errors: data,
          ...normalizeApiError(error, 'No se pudo enviar el correo.'),
          code: errorCode,
        };
      }
    },

    /**
     * downloadPdf: Download a document as PDF in the chosen template style.
     * @param {number} id - Document ID.
     * @param {string} title - Filename (without extension).
     * @param {string|null} template - 'friendly' | 'professional' | null (server default).
     */
    async downloadPdf(id, title = 'document', template = null) {
      try {
        const valid = template === 'friendly' || template === 'professional';
        const url = valid
          ? `documents/${id}/pdf/?template=${template}`
          : `documents/${id}/pdf/`;
        const response = await get_request(url, { responseType: 'blob' });
        const objectUrl = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = objectUrl;
        link.setAttribute('download', `${title}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(objectUrl);
        return { success: true };
      } catch (error) {
        console.error('Error downloading PDF:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...(await normalizeBlobApiError(error, 'No se pudo descargar el PDF.')),
        };
      }
    },
  },
});
