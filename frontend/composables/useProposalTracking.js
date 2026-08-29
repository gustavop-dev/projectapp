import { ref, watch, onBeforeUnmount, onMounted } from 'vue';

function _getCsrfToken() {
  /* c8 ignore next */
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Composable for tracking section-level engagement in a proposal.
 *
 * Tracks which section the client is viewing, how long they spend on each,
 * and sends batched data to the backend every FLUSH_INTERVAL_MS and on
 * page unload via navigator.sendBeacon.
 *
 * @param {import('vue').Ref<string>} proposalUuid - Reactive proposal UUID.
 * @param {import('vue').Ref<object>} currentPanel - Reactive current panel object.
 * @param {import('vue').Ref<string>} [viewMode] - Reactive proposal view mode.
 */
export function useProposalTracking(proposalUuid, currentPanel, viewMode) {
  // Skip all tracking for admin previews to avoid polluting analytics
  if (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('preview') === '1') {
    return;
  }

  const FLUSH_INTERVAL_MS = 30_000;

  const sessionId = ref('');
  const sectionLog = ref([]);
  let currentEntry = null;
  let flushTimer = null;
  let flushPromise = null;
  let isPaused = false;
  let beaconFinalized = false;
  let visibilityHandler = null;
  let beforeUnloadHandler = null;

  function generateSessionId() {
    // Prefer crypto.randomUUID for collision-resistant IDs; fall back to
    // a time + Math.random mix on older browsers / jsdom.
    /* c8 ignore next 3 */
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return 'ses_' + crypto.randomUUID();
    }
    return 'ses_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
  }

  function getOrCreateSessionId() {
    if (typeof sessionStorage === 'undefined') return generateSessionId();
    const key = `proposal_session_${proposalUuid.value}`;
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = generateSessionId();
      sessionStorage.setItem(key, id);
    }
    return id;
  }

  function startSectionTimer(panel) {
    /* c8 ignore next */
    if (!panel) return;
    currentEntry = {
      section_type: panel.section_type || '',
      section_title: panel.title || '',
      subsection_key: panel._technicalFragment || panel._contractClause || '',
      entered_at: new Date().toISOString(),
      _startTime: performance.now(),
    };
  }

  function stopSectionTimer() {
    if (!currentEntry) return;
    const elapsed = (performance.now() - currentEntry._startTime) / 1000;
    sectionLog.value.push({
      section_type: currentEntry.section_type,
      section_title: currentEntry.section_title,
      subsection_key: currentEntry.subsection_key,
      entered_at: currentEntry.entered_at,
      time_spent_seconds: Math.round(elapsed * 10) / 10,
    });
    currentEntry = null;
  }

  function buildPayload() {
    const mode = viewMode?.value || 'unknown';
    // Finalize current section before flushing
    if (currentEntry) {
      const elapsed = (performance.now() - currentEntry._startTime) / 1000;
      // Don't stop the timer, just snapshot
      return {
        session_id: sessionId.value,
        view_mode: mode,
        sections: [
          ...sectionLog.value,
          {
            section_type: currentEntry.section_type,
            section_title: currentEntry.section_title,
            subsection_key: currentEntry.subsection_key,
            entered_at: currentEntry.entered_at,
            time_spent_seconds: Math.round(elapsed * 10) / 10,
          },
        ],
      };
    }
    return {
      session_id: sessionId.value,
      view_mode: mode,
      sections: [...sectionLog.value],
    };
  }

  async function flush() {
    if (isPaused) return;
    if (flushPromise) return flushPromise;

    const payload = buildPayload();
    if (!payload.sections.length || !proposalUuid.value) return;

    // Only remove the exact completed entries included in this request.
    // Visibility changes can clear the queue and append a fresh segment while
    // a slow request is still in flight; positional slicing would drop it.
    const completedEntriesSent = new Set(sectionLog.value);

    flushPromise = (async () => {
      try {
        const url = `/api/proposals/${proposalUuid.value}/track/`;
        const headers = { 'Content-Type': 'application/json' };
        const csrf = _getCsrfToken();
        if (csrf) headers['X-CSRFToken'] = csrf;
        const response = await fetch(url, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        });
        if (response.ok) {
          sectionLog.value = sectionLog.value.filter(
            (entry) => !completedEntriesSent.has(entry)
          );
        }
      } catch (_err) {
        // Silently fail — tracking is non-critical
      }
    })();

    try {
      await flushPromise;
    } finally {
      flushPromise = null;
    }
  }

  function flushBeacon() {
    if (beaconFinalized) return;
    const payload = buildPayload();
    if (!payload.sections.length || !proposalUuid.value) return;
    const url = `/api/proposals/${proposalUuid.value}/track/`;
    try {
      const queued = navigator.sendBeacon(url, new Blob(
        [JSON.stringify(payload)],
        { type: 'application/json' }
      )) !== false;
      if (queued) {
        // sendBeacon has taken ownership of these completed entries. Clearing
        // them prevents beforeunload/unmount from sending the same final slice.
        sectionLog.value = [];
        beaconFinalized = true;
      }
    } catch (_err) {
      // Silently fail
    }
  }

  function startFlushTimer() {
    if (!flushTimer) {
      flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);
    }
  }

  function stopFlushTimer() {
    if (flushTimer) {
      clearInterval(flushTimer);
      flushTimer = null;
    }
  }

  // Watch for section changes
  watch(
    () => currentPanel.value,
    (newPanel, oldPanel) => {
      if (oldPanel && newPanel !== oldPanel) {
        stopSectionTimer();
      }
      if (newPanel && !isPaused) {
        startSectionTimer(newPanel);
      }
    },
    { immediate: false }
  );

  onMounted(() => {
    sessionId.value = getOrCreateSessionId();

    isPaused = typeof document !== 'undefined' && document.visibilityState === 'hidden';

    // Start timers only while the page is actually visible. Hidden tabs do
    // not represent engaged reading time and must not keep a heartbeat alive.
    if (currentPanel.value && !isPaused) {
      startSectionTimer(currentPanel.value);
    }

    if (!isPaused) startFlushTimer();

    // Flush on page unload
    if (typeof window !== 'undefined') {
      beforeUnloadHandler = () => {
        if (!isPaused) stopSectionTimer();
        flushBeacon();
      };
      window.addEventListener('beforeunload', beforeUnloadHandler);
      visibilityHandler = () => {
        if (document.visibilityState === 'hidden') {
          if (isPaused) return;
          isPaused = true;
          stopFlushTimer();
          stopSectionTimer();
          flushBeacon();
        } else if (isPaused) {
          isPaused = false;
          beaconFinalized = false;
          if (currentPanel.value) startSectionTimer(currentPanel.value);
          startFlushTimer();
        }
      };
      document.addEventListener('visibilitychange', visibilityHandler);
    }
  });

  onBeforeUnmount(() => {
    if (isPaused) {
      flushBeacon();
    } else {
      stopSectionTimer();
      flush();
    }
    stopFlushTimer();
    if (typeof window !== 'undefined') {
      if (beforeUnloadHandler) {
        window.removeEventListener('beforeunload', beforeUnloadHandler);
      }
      if (visibilityHandler) {
        document.removeEventListener('visibilitychange', visibilityHandler);
      }
    }
  });

  return { sessionId, sectionLog, flush };
}
