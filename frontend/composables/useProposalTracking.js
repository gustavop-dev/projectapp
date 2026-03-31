import { ref, watch, onBeforeUnmount, onMounted } from 'vue';

function _getCsrfToken() {
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
 * @param {import('vue').Ref<string>} [viewMode] - Reactive view mode ('executive', 'detailed', or 'technical').
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
  let visibilityHandler = null;

  function generateSessionId() {
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
    if (!panel) return;
    currentEntry = {
      section_type: panel.section_type || '',
      section_title: panel.title || '',
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
    const payload = buildPayload();
    if (!payload.sections.length || !proposalUuid.value) return;

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
        // Clear flushed entries (keep current running entry)
        sectionLog.value = [];
      }
    } catch (_err) {
      // Silently fail — tracking is non-critical
    }
  }

  function flushBeacon() {
    const payload = buildPayload();
    if (!payload.sections.length || !proposalUuid.value) return;
    const url = `/api/proposals/${proposalUuid.value}/track/`;
    try {
      navigator.sendBeacon(url, new Blob(
        [JSON.stringify(payload)],
        { type: 'application/json' }
      ));
    } catch (_err) {
      // Silently fail
    }
  }

  // Watch for section changes
  watch(
    () => currentPanel.value,
    (newPanel, oldPanel) => {
      if (oldPanel && newPanel !== oldPanel) {
        stopSectionTimer();
      }
      if (newPanel) {
        startSectionTimer(newPanel);
      }
    },
    { immediate: false }
  );

  onMounted(() => {
    sessionId.value = getOrCreateSessionId();

    // Start timer for initial section
    if (currentPanel.value) {
      startSectionTimer(currentPanel.value);
    }

    // Periodic flush
    flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);

    // Flush on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', flushBeacon);
      visibilityHandler = () => {
        if (document.visibilityState === 'hidden') {
          flushBeacon();
        }
      };
      document.addEventListener('visibilitychange', visibilityHandler);
    }
  });

  onBeforeUnmount(() => {
    stopSectionTimer();
    flush();
    if (flushTimer) clearInterval(flushTimer);
    if (typeof window !== 'undefined') {
      window.removeEventListener('beforeunload', flushBeacon);
      if (visibilityHandler) {
        document.removeEventListener('visibilitychange', visibilityHandler);
      }
    }
  });

  return { sessionId, sectionLog, flush };
}
