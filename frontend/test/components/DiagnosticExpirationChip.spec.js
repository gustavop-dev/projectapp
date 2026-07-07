import { mount } from '@vue/test-utils';
import DiagnosticExpirationChip from '../../components/WebAppDiagnostic/DiagnosticExpirationChip.vue';

function mountChip(props) {
  return mount(DiagnosticExpirationChip, { props });
}

describe('DiagnosticExpirationChip', () => {
  it('renders nothing without an expiry date', () => {
    const wrapper = mountChip({ expiresAt: null, isExpired: false, daysRemaining: null });
    expect(wrapper.find('[data-testid="diagnostic-expiration-chip"]').exists()).toBe(false);
  });

  it('shows an expired chip in danger tone', () => {
    const wrapper = mountChip({ expiresAt: '2026-01-01T00:00:00Z', isExpired: true, daysRemaining: 0 });
    const chip = wrapper.find('[data-testid="diagnostic-expiration-chip"]');
    expect(chip.text()).toBe('Expirado');
    expect(chip.classes()).toContain('text-danger-strong');
  });

  it('warns in danger tone when 1 day or less remains', () => {
    const wrapper = mountChip({ expiresAt: '2026-12-31T00:00:00Z', isExpired: false, daysRemaining: 1 });
    const chip = wrapper.find('[data-testid="diagnostic-expiration-chip"]');
    expect(chip.text()).toBe('Vence mañana');
    expect(chip.classes()).toContain('text-danger-strong');
  });

  it('uses warning tone in the 2-7 day window', () => {
    const wrapper = mountChip({ expiresAt: '2026-12-31T00:00:00Z', isExpired: false, daysRemaining: 3 });
    const chip = wrapper.find('[data-testid="diagnostic-expiration-chip"]');
    expect(chip.text()).toBe('Vence en 3 d');
    expect(chip.classes()).toContain('text-warning-strong');
  });

  it('uses a calm muted tone when comfortably ahead', () => {
    const wrapper = mountChip({ expiresAt: '2026-12-31T00:00:00Z', isExpired: false, daysRemaining: 15 });
    const chip = wrapper.find('[data-testid="diagnostic-expiration-chip"]');
    expect(chip.text()).toBe('Vence en 15 d');
    expect(chip.classes()).toContain('text-text-muted');
  });
});
