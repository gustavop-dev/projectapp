import { ref } from 'vue';

/**
 * Shared state + helpers for the "Adjuntar desde Documentos" flow used by
 * both ProposalEmailsTab and DiagnosticEmailsTab. A doc_ref carries the
 * selection key, its display label, and the opaque backend ref payload.
 */
export function useDocRefsAttachment() {
  const docRefs = ref([]);

  function removeDocRef(idx) {
    docRefs.value.splice(idx, 1);
  }

  function handleDocRefsAttach(picked) {
    const pickedKeys = new Set(picked.map((r) => r.key));
    const existingKeys = new Set(docRefs.value.map((r) => r.key));
    docRefs.value = docRefs.value.filter((r) => pickedKeys.has(r.key));
    for (const ref of picked) {
      if (!existingKeys.has(ref.key)) docRefs.value.push(ref);
    }
  }

  function appendDocRefsToFormData(formData) {
    if (docRefs.value.length) {
      formData.append('doc_refs', JSON.stringify(docRefs.value.map((r) => r.ref)));
    }
  }

  function resetDocRefs() {
    docRefs.value = [];
  }

  return {
    docRefs,
    removeDocRef,
    handleDocRefsAttach,
    appendDocRefsToFormData,
    resetDocRefs,
  };
}
