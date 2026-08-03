/**
 * Single frontend copy of the deduction catalog.
 *
 * Mirrors `ExpenseRecord.DeductionType` (backend enum). Consumed by the
 * income liquidation modal (the only place deductions are created) and by
 * the Gastos filters — keep the three in sync.
 */
export const DEDUCTION_TYPE_OPTIONS = [
  { value: 'gateway_fee', label: 'Comisión plataforma de pago' },
  { value: 'bank_fee', label: 'Comisión bancaria' },
  { value: 'withholding', label: 'Retención en la fuente' },
  { value: 'other', label: 'Otro' },
];
