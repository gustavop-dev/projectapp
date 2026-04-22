/**
 * Tests for useDocRefsAttachment composable.
 *
 * Covers: initial state, removeDocRef, handleDocRefsAttach (add / remove / no-dup),
 * appendDocRefsToFormData, resetDocRefs.
 */
const { useDocRefsAttachment } = require('../../composables/useDocRefsAttachment');

describe('useDocRefsAttachment', () => {
  let docRefs, removeDocRef, handleDocRefsAttach, appendDocRefsToFormData, resetDocRefs;

  beforeEach(() => {
    const result = useDocRefsAttachment();
    docRefs = result.docRefs;
    removeDocRef = result.removeDocRef;
    handleDocRefsAttach = result.handleDocRefsAttach;
    appendDocRefsToFormData = result.appendDocRefsToFormData;
    resetDocRefs = result.resetDocRefs;
  });

  it('starts with an empty docRefs array', () => {
    expect(docRefs.value).toEqual([]);
  });

  describe('removeDocRef', () => {
    it('removes the item at the given index', () => {
      docRefs.value = [
        { key: 'a', label: 'A', ref: { source: 'commercial_pdf' } },
        { key: 'b', label: 'B', ref: { source: 'technical_pdf' } },
      ];
      removeDocRef(0);
      expect(docRefs.value).toHaveLength(1);
      expect(docRefs.value[0].key).toBe('b');
    });

    it('removes the last item', () => {
      docRefs.value = [{ key: 'x', label: 'X', ref: { source: 'nda_final' } }];
      removeDocRef(0);
      expect(docRefs.value).toEqual([]);
    });
  });

  describe('handleDocRefsAttach', () => {
    it('adds new refs from picked list', () => {
      handleDocRefsAttach([
        { key: 'commercial_pdf', label: 'Propuesta', ref: { source: 'commercial_pdf' } },
      ]);
      expect(docRefs.value).toHaveLength(1);
      expect(docRefs.value[0].key).toBe('commercial_pdf');
    });

    it('removes existing refs that are not in the picked list', () => {
      docRefs.value = [
        { key: 'commercial_pdf', label: 'A', ref: { source: 'commercial_pdf' } },
        { key: 'technical_pdf', label: 'B', ref: { source: 'technical_pdf' } },
      ];
      handleDocRefsAttach([
        { key: 'commercial_pdf', label: 'A', ref: { source: 'commercial_pdf' } },
      ]);
      expect(docRefs.value).toHaveLength(1);
      expect(docRefs.value[0].key).toBe('commercial_pdf');
    });

    it('does not duplicate refs with the same key', () => {
      docRefs.value = [
        { key: 'commercial_pdf', label: 'A', ref: { source: 'commercial_pdf' } },
      ];
      handleDocRefsAttach([
        { key: 'commercial_pdf', label: 'A', ref: { source: 'commercial_pdf' } },
        { key: 'technical_pdf', label: 'B', ref: { source: 'technical_pdf' } },
      ]);
      expect(docRefs.value).toHaveLength(2);
      expect(docRefs.value.map(r => r.key)).toEqual(['commercial_pdf', 'technical_pdf']);
    });

    it('results in empty list when picked is empty', () => {
      docRefs.value = [{ key: 'a', label: 'A', ref: { source: 'commercial_pdf' } }];
      handleDocRefsAttach([]);
      expect(docRefs.value).toEqual([]);
    });
  });

  describe('appendDocRefsToFormData', () => {
    it('appends serialized refs when docRefs is non-empty', () => {
      docRefs.value = [
        { key: 'contract_pdf', label: 'Contrato', ref: { source: 'contract_pdf' } },
      ];
      const formData = { append: jest.fn() };
      appendDocRefsToFormData(formData);
      expect(formData.append).toHaveBeenCalledWith(
        'doc_refs',
        JSON.stringify([{ source: 'contract_pdf' }]),
      );
    });

    it('does not append anything when docRefs is empty', () => {
      const formData = { append: jest.fn() };
      appendDocRefsToFormData(formData);
      expect(formData.append).not.toHaveBeenCalled();
    });

    it('serializes the ref payload, not the whole doc ref object', () => {
      docRefs.value = [
        {
          key: 'proposal_document:42',
          label: 'Legal annex',
          ref: { source: 'proposal_document', id: 42 },
        },
      ];
      const formData = { append: jest.fn() };
      appendDocRefsToFormData(formData);
      const appended = JSON.parse(formData.append.mock.calls[0][1]);
      expect(appended).toEqual([{ source: 'proposal_document', id: 42 }]);
    });
  });

  describe('resetDocRefs', () => {
    it('clears the docRefs array', () => {
      docRefs.value = [
        { key: 'a', label: 'A', ref: { source: 'commercial_pdf' } },
        { key: 'b', label: 'B', ref: { source: 'technical_pdf' } },
      ];
      resetDocRefs();
      expect(docRefs.value).toEqual([]);
    });
  });
});
