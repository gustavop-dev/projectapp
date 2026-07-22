import { formatMoney, formatCompactMoney } from '~/utils/formatMoney';

/**
 * Shared value formatters for the stats-modal chart primitives.
 * Axes stay compact ("$1,2M"); tooltips keep the full COP figure.
 */

const numberFormatter = new Intl.NumberFormat('es-CO');

export function axisFormatter(valueFormat) {
  if (valueFormat === 'money') return (value) => formatCompactMoney(value);
  if (valueFormat === 'percent') return (value) => `${Math.round(value)}%`;
  return (value) => numberFormatter.format(Math.round(value));
}

export function tooltipFormatter(valueFormat) {
  if (valueFormat === 'money') return (value) => formatMoney(value, 'COP');
  if (valueFormat === 'percent') {
    return (value) =>
      value === null || value === undefined ? '—' : `${Math.round(value * 10) / 10}%`;
  }
  return (value) =>
    value === null || value === undefined ? '—' : numberFormatter.format(value);
}
