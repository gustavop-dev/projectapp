import { ref } from 'vue';

import {
  COMMUNICATION_PANEL_DEFAULT,
  useCommunicationPanelWidth,
} from '../../composables/useCommunicationPanelWidth';

function container() {
  return ref({ getBoundingClientRect: () => ({ left: 100, width: 1000 }) });
}

describe('useCommunicationPanelWidth', () => {
  it('starts at the compact communications default', () => {
    const { width, gridStyle } = useCommunicationPanelWidth(container());

    expect(width.value).toBe(COMMUNICATION_PANEL_DEFAULT);
    expect(gridStyle.value).toEqual({ '--communications-panel-w': '288px' });
  });

  it('clamps a hydrated value to the panel bounds', () => {
    const { width, hydrateWidth } = useCommunicationPanelWidth(container());
    hydrateWidth(900);

    expect(width.value).toBe(400);
  });

  it('reports the width when a pointer resize finishes', () => {
    const onPersist = jest.fn();
    const { width, onHandleDown, onHandleMove, onHandleUp } =
      useCommunicationPanelWidth(container(), { onPersist });

    onHandleDown();
    onHandleMove({ clientX: 430 });
    expect(width.value).toBe(330);
    onHandleUp();
    expect(onPersist).toHaveBeenCalledWith(330);
  });

  it('reports the default after a reset', () => {
    const onPersist = jest.fn();
    const { width, resizeWidth, resetWidth } = useCommunicationPanelWidth(
      container(), { onPersist },
    );
    resizeWidth(360);
    onPersist.mockClear();

    resetWidth();

    expect(width.value).toBe(COMMUNICATION_PANEL_DEFAULT);
    expect(onPersist).toHaveBeenCalledWith(COMMUNICATION_PANEL_DEFAULT);
  });
});
