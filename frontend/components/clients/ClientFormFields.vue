<script setup>
/**
 * The client field set, shared by every surface that creates or edits a client.
 *
 * One component rather than one copy per modal on purpose: create, edit and the
 * three inline "crear al vuelo" panels used to ask for different subsets, so a
 * client filed from one of them came out incomplete and had to be edited right
 * after. Sharing the fields is what keeps them in step — order and layout
 * included.
 *
 * Only `name` is required; everything else is labelled "(opcional)" and may be
 * filled in later.
 */
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseFormRow from '~/components/base/BaseFormRow.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import { BILLING_CODE_MAX_LENGTH } from '~/utils/billingCode';

const props = defineProps({
  /** `{ name, email, phone, company, nit, billing_code }` */
  modelValue: { type: Object, required: true },
  /** Prefix for each field's data-testid, e.g. `clients-new` -> `clients-new-name`. */
  testidPrefix: { type: String, required: true },
  /** Compact 3-column strip for the inline panels; stacked otherwise. */
  dense: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue']);

function update(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value });
}
</script>

<template>
  <div :class="dense ? 'space-y-3' : 'space-y-4'">
    <BaseFormRow :cols="dense ? 3 : 1" :gap="dense ? 3 : 4">
      <BaseFormField label="Nombre" required :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.name"
          type="text"
          required
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-name`"
          @update:model-value="update('name', $event)"
        />
      </BaseFormField>
      <BaseFormField label="Email (opcional)" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.email"
          type="email"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-email`"
          @update:model-value="update('email', $event)"
        />
      </BaseFormField>
      <BaseFormField label="Teléfono (opcional)" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.phone"
          type="tel"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-phone`"
          @update:model-value="update('phone', $event)"
        />
      </BaseFormField>
      <BaseFormField label="Empresa (opcional)" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.company"
          type="text"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-company`"
          @update:model-value="update('company', $event)"
        />
      </BaseFormField>
    </BaseFormRow>

    <!-- Billing identity: what the cuenta de cobro needs to name and number
         the document. Paired because they are filled together or not at all.
         The row is what keeps both inputs starting at the same height, since
         "Código de facturación (opcional)" wraps to two lines and "C.C. / NIT"
         does not. The label names both documents the field accepts: most
         clients are personas naturales whose cédula goes here, and "NIT"
         alone made them second-guess it. -->
    <BaseFormRow>
      <BaseFormField label="C.C. / NIT (opcional)" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.nit"
          type="text"
          :size="dense ? 'sm' : 'md'"
          placeholder="Para cuentas de cobro"
          :data-testid="`${testidPrefix}-nit`"
          @update:model-value="update('nit', $event)"
        />
      </BaseFormField>
      <BaseFormField label="Código de facturación (opcional)" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.billing_code"
          type="text"
          :size="dense ? 'sm' : 'md'"
          :maxlength="BILLING_CODE_MAX_LENGTH"
          class="uppercase"
          placeholder="Ej: G&M (numeración PA-G&M-001)"
          :data-testid="`${testidPrefix}-billing-code`"
          @update:model-value="update('billing_code', $event)"
        />
      </BaseFormField>
    </BaseFormRow>
  </div>
</template>
