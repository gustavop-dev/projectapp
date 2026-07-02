/**
 * Tests for DocumentActionsSheet.vue.
 *
 * Covers: visibility (modelValue / document), header (title + client),
 * actions list rendering with "Editar contenido" first, per-action emits
 * plus auto-close, danger styling for delete, and the Cancelar close.
 */

import { mount } from '@vue/test-utils';
import DocumentActionsSheet from '../../components/panel/documents/DocumentActionsSheet.vue';

const baseDocument = { id: 7, title: 'Contrato de Servicios', client_name: 'ACME Corp' };

function mountSheet(props = {}) {
  return mount(DocumentActionsSheet, {
    props: { modelValue: true, document: baseDocument, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

// Los botones de acción son los que viven en la lista `.p-2` (excluye la X y "Cancelar").
function actionButtons(wrapper) {
  return wrapper.findAll('.p-2 button');
}

function actionByLabel(wrapper, label) {
  return actionButtons(wrapper).find((btn) => btn.text().includes(label));
}

describe('DocumentActionsSheet', () => {
  describe('visibility', () => {
    it('does not render content when modelValue is false', () => {
      const wrapper = mountSheet({ modelValue: false });

      expect(wrapper.text()).not.toContain('Contrato de Servicios');
    });

    it('does not render content when document is null', () => {
      const wrapper = mountSheet({ document: null });

      expect(wrapper.text()).not.toContain('Renombrar');
    });
  });

  describe('header', () => {
    it('renders the document title', () => {
      const wrapper = mountSheet();

      expect(wrapper.text()).toContain('Contrato de Servicios');
    });

    it('renders the client name when present', () => {
      const wrapper = mountSheet();

      expect(wrapper.text()).toContain('ACME Corp');
    });
  });

  describe('actions list', () => {
    it('renders every action label', () => {
      const wrapper = mountSheet();
      const labels = [
        'Editar contenido', 'Renombrar', 'Mover a carpeta', 'Enviar por correo',
        'Descargar PDF', 'Copiar markdown', 'Duplicar', 'Eliminar',
      ];

      labels.forEach((label) => {
        expect(actionByLabel(wrapper, label)).toBeTruthy();
      });
    });

    it('lists "Editar contenido" as the first action', () => {
      const wrapper = mountSheet();

      expect(actionButtons(wrapper).at(0).text()).toContain('Editar contenido');
    });
  });

  describe('action emits', () => {
    it('emits edit when "Editar contenido" is clicked', async () => {
      const wrapper = mountSheet();
      await actionByLabel(wrapper, 'Editar contenido').trigger('click');

      expect(wrapper.emitted('edit')).toHaveLength(1);
    });

    it('closes after an action is triggered', async () => {
      const wrapper = mountSheet();
      await actionByLabel(wrapper, 'Editar contenido').trigger('click');

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('emits rename when "Renombrar" is clicked', async () => {
      const wrapper = mountSheet();
      await actionByLabel(wrapper, 'Renombrar').trigger('click');

      expect(wrapper.emitted('rename')).toHaveLength(1);
    });

    it('emits duplicate when "Duplicar" is clicked', async () => {
      const wrapper = mountSheet();
      await actionByLabel(wrapper, 'Duplicar').trigger('click');

      expect(wrapper.emitted('duplicate')).toHaveLength(1);
    });

    it('emits delete when "Eliminar" is clicked', async () => {
      const wrapper = mountSheet();
      await actionByLabel(wrapper, 'Eliminar').trigger('click');

      expect(wrapper.emitted('delete')).toHaveLength(1);
    });
  });

  describe('danger styling', () => {
    it('styles the delete action as danger', () => {
      const wrapper = mountSheet();

      expect(actionByLabel(wrapper, 'Eliminar').classes().join(' ')).toContain('text-danger-strong');
    });
  });

  describe('close', () => {
    it('emits update:modelValue false when Cancelar is clicked', async () => {
      const wrapper = mountSheet();
      const cancel = wrapper.findAll('button').find((btn) => btn.text() === 'Cancelar');
      await cancel.trigger('click');

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });
  });
});
