/**
 * Tests for the usePanelNotify composable (panel-wide notification queue).
 *
 * Covers: push/success/error/warning/info, string shorthand, queueing,
 *         manual dismiss, clearAll, and auto-dismiss via timers.
 */

import { usePanelNotify } from '../../composables/usePanelNotify';

describe('usePanelNotify', () => {
  let notify;

  beforeEach(() => {
    jest.useFakeTimers();
    notify = usePanelNotify();
    notify.clearAll(); // module-level singleton: reset between tests
  });

  afterEach(() => {
    notify.clearAll();
    jest.useRealTimers();
  });

  it('pushes a notification with the given fields and returns an id', () => {
    const id = notify.error({ title: 'Boom', detail: 'why', action: { label: 'Fix', to: '/x' } });
    expect(typeof id).toBe('number');
    expect(notify.notifications.value).toHaveLength(1);
    const n = notify.notifications.value[0];
    expect(n).toMatchObject({ id, type: 'error', title: 'Boom', detail: 'why' });
    expect(n.action).toEqual({ label: 'Fix', to: '/x' });
  });

  it('accepts a string shorthand as the title', () => {
    notify.success('Guardado');
    expect(notify.notifications.value[0]).toMatchObject({ type: 'success', title: 'Guardado' });
  });

  it('sets the type for each convenience method', () => {
    notify.success({ title: 'a' });
    notify.warning({ title: 'b' });
    notify.info({ title: 'c' });
    expect(notify.notifications.value.map((n) => n.type)).toEqual(['success', 'warning', 'info']);
  });

  it('queues multiple notifications in order', () => {
    notify.info({ title: 'one' });
    notify.info({ title: 'two' });
    expect(notify.notifications.value.map((n) => n.title)).toEqual(['one', 'two']);
  });

  it('dismisses a specific notification by id', () => {
    const first = notify.info({ title: 'one' });
    notify.info({ title: 'two' });
    notify.dismiss(first);
    expect(notify.notifications.value.map((n) => n.title)).toEqual(['two']);
  });

  it('auto-dismisses after the type default duration', () => {
    notify.success({ title: 'bye' }); // success default = 4000ms
    expect(notify.notifications.value).toHaveLength(1);
    jest.advanceTimersByTime(4000);
    expect(notify.notifications.value).toHaveLength(0);
  });

  it('honors an explicit duration', () => {
    notify.error({ title: 'stay', duration: 100 });
    jest.advanceTimersByTime(99);
    expect(notify.notifications.value).toHaveLength(1);
    jest.advanceTimersByTime(1);
    expect(notify.notifications.value).toHaveLength(0);
  });

  it('does not auto-dismiss when duration is 0 (sticky)', () => {
    notify.error({ title: 'sticky', duration: 0 });
    jest.advanceTimersByTime(100000);
    expect(notify.notifications.value).toHaveLength(1);
  });

  it('clearAll removes every notification', () => {
    notify.info({ title: 'a' });
    notify.info({ title: 'b' });
    notify.clearAll();
    expect(notify.notifications.value).toHaveLength(0);
  });
});
