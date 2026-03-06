import { ref, computed, onMounted, onUnmounted } from 'vue';

/**
 * Composable for countdown timer to proposal expiration.
 *
 * @param {import('vue').Ref<string>} expiresAt - ISO datetime string ref
 * @returns {object} Countdown state and computed values
 */
export function useExpirationTimer(expiresAt) {
  const now = ref(new Date());
  let interval = null;

  onMounted(() => {
    interval = setInterval(() => {
      now.value = new Date();
    }, 60000);
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

  const isExpired = computed(() => {
    if (diffMs.value === null) return false;
    return diffMs.value <= 0;
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
   * Human-readable countdown string, e.g. "2 días, 5 horas"
   */
  const formattedCountdown = computed(() => {
    if (isExpired.value) return 'Expirada';
    if (diffMs.value === null) return '';

    const totalHours = Math.floor(diffMs.value / (1000 * 60 * 60));
    const days = Math.floor(totalHours / 24);
    const hours = totalHours % 24;

    if (days > 0 && hours > 0) {
      return `${days} día${days !== 1 ? 's' : ''}, ${hours} hora${hours !== 1 ? 's' : ''}`;
    }
    if (days > 0) {
      return `${days} día${days !== 1 ? 's' : ''}`;
    }
    if (hours > 0) {
      return `${hours} hora${hours !== 1 ? 's' : ''}`;
    }
    return 'Menos de 1 hora';
  });

  return {
    daysRemaining,
    hoursRemaining,
    isExpired,
    urgencyLevel,
    formattedCountdown,
  };
}
