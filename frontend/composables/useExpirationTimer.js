import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

/**
 * Composable for countdown timer to proposal expiration.
 *
 * @param {import('vue').Ref<string>} expiresAt - ISO datetime string ref
 * @returns {object} Countdown state and computed values
 */
export function useExpirationTimer(expiresAt) {
  const now = ref(new Date());
  let interval = null;

  function startInterval(ms) {
    if (interval) clearInterval(interval);
    interval = setInterval(() => {
      now.value = new Date();
    }, ms);
  }

  onMounted(() => {
    startInterval(60000);
  });

  onUnmounted(() => {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  });

  const expiresDate = computed(() => {
    const val = expiresAt?.value || expiresAt;
    if (!val) return null;
    return new Date(val);
  });

  const diffMs = computed(() => {
    if (!expiresDate.value) return null;
    return expiresDate.value.getTime() - now.value.getTime();
  });

  const daysRemaining = computed(() => {
    if (diffMs.value === null) return null;
    return Math.max(Math.floor(diffMs.value / (1000 * 60 * 60 * 24)), 0);
  });

  const hoursRemaining = computed(() => {
    if (diffMs.value === null) return null;
    return Math.max(Math.floor(diffMs.value / (1000 * 60 * 60)), 0);
  });

  const minutesRemaining = computed(() => {
    if (diffMs.value === null) return null;
    return Math.max(Math.floor(diffMs.value / (1000 * 60)), 0);
  });

  const isExpired = computed(() => {
    if (diffMs.value === null) return false;
    return diffMs.value <= 0;
  });

  /**
   * True when <48h remain — triggers real-time HH:MM display.
   */
  const isCountdownMode = computed(() => {
    if (hoursRemaining.value === null) return false;
    return !isExpired.value && hoursRemaining.value < 48;
  });

  // Switch to 1s interval when entering countdown mode (<48h)
  watch(isCountdownMode, (active) => {
    startInterval(active ? 1000 : 60000);
  });

  /**
   * Urgency level based on remaining time.
   * - 'calm': more than 3 days
   * - 'warning': 1-3 days
   * - 'urgent': less than 1 day
   * - 'expired': already expired
   */
  const urgencyLevel = computed(() => {
    if (isExpired.value) return 'expired';
    if (daysRemaining.value === null) return 'calm';
    if (daysRemaining.value < 1) return 'urgent';
    if (daysRemaining.value <= 3) return 'warning';
    if (daysRemaining.value <= 7) return 'notice';
    return 'calm';
  });

  /**
   * Human-readable countdown string.
   * When <48h: shows "HH:MM" (e.g. "23:45").
   * Otherwise: "2 días", "5 horas", etc.
   */
  const formattedCountdown = computed(() => {
    if (isExpired.value) return 'Expirada';
    if (diffMs.value === null) return '';

    const totalHours = Math.floor(diffMs.value / (1000 * 60 * 60));

    // Real-time HH:MM when under 48 hours
    if (totalHours < 48) {
      const totalMinutes = Math.floor(diffMs.value / (1000 * 60));
      const hrs = Math.floor(totalMinutes / 60);
      const mins = totalMinutes % 60;
      return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
    }

    const days = Math.floor(totalHours / 24);
    if (days > 0) {
      return `${days} día${days !== 1 ? 's' : ''}`;
    }
    return 'Menos de 1 hora';
  });

  return {
    daysRemaining,
    hoursRemaining,
    minutesRemaining,
    isExpired,
    isCountdownMode,
    urgencyLevel,
    formattedCountdown,
  };
}
