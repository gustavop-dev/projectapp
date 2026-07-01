/**
 * Tests the backward-compatible usePanelToast wrapper: legacy showToast() calls
 * must now flow through the richer usePanelNotify queue.
 */

import { usePanelToast } from '../../composables/usePanelToast';
import { usePanelNotify } from '../../composables/usePanelNotify';

describe('usePanelToast (compat wrapper)', () => {
  let toast;
  let notify;

  beforeEach(() => {
    toast = usePanelToast();
    notify = usePanelNotify();
    notify.clearAll();
  });

  afterEach(() => {
    notify.clearAll();
  });

  it('showToast pushes a notification with text as the title', () => {
    toast.showToast({ type: 'success', text: 'Guardado' });
    expect(notify.notifications.value).toHaveLength(1);
    expect(notify.notifications.value[0]).toMatchObject({ type: 'success', title: 'Guardado' });
  });

  it('maps error type through', () => {
    toast.showToast({ type: 'error', text: 'Falló' });
    expect(notify.notifications.value[0]).toMatchObject({ type: 'error', title: 'Falló' });
  });

  it('clearToast empties the queue', () => {
    toast.showToast({ type: 'success', text: 'a' });
    toast.showToast({ type: 'error', text: 'b' });
    toast.clearToast();
    expect(notify.notifications.value).toHaveLength(0);
  });

  it('legacy toastMsg ref stays null (old PanelToast is a no-op)', () => {
    toast.showToast({ type: 'success', text: 'x' });
    expect(toast.toastMsg.value).toBeNull();
  });
});
