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
 * Only `name` is required; the panel convention marks required fields with an
 * asterisk, so the absence of that marker already communicates optionality.
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
  /** Field-scoped validation returned by the local form or the API. */
  errors: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['update:modelValue', 'clear-error']);

function update(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value });
  emit('clear-error', field);
}

function errorFor(field) {
  const value = props.errors[field];
  if (Array.isArray(value)) {
    return value.find((message) => typeof message === 'string' && message.trim()) || '';
  }
  return typeof value === 'string' ? value : '';
}
</script>

<template>
  <div :class="dense ? 'space-y-3' : 'space-y-4'">
    <BaseFormRow :cols="dense ? 3 : 1" :gap="dense ? 3 : 4">
      <BaseFormField
        v-slot="{ invalid, errorId }"
        label="Nombre"
        required
        required-message="Escribe el nombre del cliente."
        :error="errorFor('name')"
        :size="dense ? 'sm' : 'md'"
      >
        <BaseInput
          :model-value="modelValue.name"
          type="text"
          required
          :error="invalid"
          :aria-describedby="errorId"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-name`"
          @update:model-value="update('name', $event)"
        />
      </BaseFormField>
      <BaseFormField v-slot="{ invalid, errorId }" label="Email" :error="errorFor('email')" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.email"
          type="email"
          :error="invalid"
          :aria-describedby="errorId"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-email`"
          @update:model-value="update('email', $event)"
        />
      </BaseFormField>
      <BaseFormField v-slot="{ invalid, errorId }" label="Teléfono" :error="errorFor('phone')" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.phone"
          type="tel"
          :error="invalid"
          :aria-describedby="errorId"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-phone`"
          @update:model-value="update('phone', $event)"
        />
      </BaseFormField>
      <BaseFormField v-slot="{ invalid, errorId }" label="Empresa" :error="errorFor('company')" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.company"
          type="text"
          :error="invalid"
          :aria-describedby="errorId"
          :size="dense ? 'sm' : 'md'"
          :data-testid="`${testidPrefix}-company`"
          @update:model-value="update('company', $event)"
        />
      </BaseFormField>
    </BaseFormRow>

    <!-- Billing identity: what the cuenta de cobro needs to name and number
         the document. Paired because they are filled together or not at all.
         The row is what keeps both inputs starting at the same height, since
         the billing-code label can be longer than "C.C. / NIT". The label
         names both documents the field accepts: most
         clients are personas naturales whose cédula goes here, and "NIT"
         alone made them second-guess it. -->
    <BaseFormRow>
      <BaseFormField v-slot="{ invalid, errorId }" label="C.C. / NIT" :error="errorFor('nit')" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.nit"
          type="text"
          :error="invalid"
          :aria-describedby="errorId"
          :size="dense ? 'sm' : 'md'"
          placeholder="Para cuentas de cobro"
          :data-testid="`${testidPrefix}-nit`"
          @update:model-value="update('nit', $event)"
        />
      </BaseFormField>
      <BaseFormField v-slot="{ invalid, errorId }" label="Código de facturación" :error="errorFor('billing_code')" :size="dense ? 'sm' : 'md'">
        <BaseInput
          :model-value="modelValue.billing_code"
          type="text"
          :error="invalid"
          :aria-describedby="errorId"
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
