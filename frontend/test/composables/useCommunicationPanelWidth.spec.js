import { ref } from 'vue';

import {
  COMMUNICATION_PANEL_DEFAULT,
  COMMUNICATION_PANEL_KEY,
  useCommunicationPanelWidth,
} from '../../composables/useCommunicationPanelWidth';

function container() {
  return ref({ getBoundingClientRect: () => ({ left: 100, width: 1000 }) });
}

describe('useCommunicationPanelWidth', () => {
  beforeEach(() => window.localStorage.clear());

  it('starts at the compact communications default', () => {
    const { width, gridStyle } = useCommunicationPanelWidth(container());

    expect(width.value).toBe(COMMUNICATION_PANEL_DEFAULT);
    expect(gridStyle.value).toEqual({ '--communications-panel-w': '288px' });
  });

  it('clamps a persisted value to the panel bounds', () => {
    window.localStorage.setItem(COMMUNICATION_PANEL_KEY, '900');

    const { width } = useCommunicationPanelWidth(container());

    expect(width.value).toBe(400);
  });

  it('persists the width when a pointer resize finishes', () => {
    const { width, onHandleDown, onHandleMove, onHandleUp } =
      useCommunicationPanelWidth(container());

    onHandleDown();
    onHandleMove({ clientX: 430 });
    expect(width.value).toBe(330);
    expect(window.localStorage.getItem(COMMUNICATION_PANEL_KEY)).toBeNull();
    onHandleUp();
    expect(window.localStorage.getItem(COMMUNICATION_PANEL_KEY)).toBe('330');
  });

  it('resets the width and removes the preference', () => {
    const { width, resizeWidth, resetWidth } = useCommunicationPanelWidth(container());
    resizeWidth(360);

    resetWidth();

    expect(width.value).toBe(COMMUNICATION_PANEL_DEFAULT);
    expect(window.localStorage.getItem(COMMUNICATION_PANEL_KEY)).toBeNull();
  });
});
