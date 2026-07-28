<template>
  <div class="bg-surface rounded-xl border border-border-muted shadow-sm overflow-hidden mt-2">
    <p v-if="aliases.length === 0" class="px-5 py-6 text-sm text-text-subtle">
      Aún no hay alias aprendidos. Se crean al aprobar comercios en el chat.
    </p>
    <div v-else class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-border-muted text-left">
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Texto a mapear</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Comercio</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Categoría</th>
            <th class="px-5 py-3 text-right" />
          </tr>
        </thead>
        <tbody class="divide-y divide-border-muted">
          <tr
            v-for="alias in aliases"
            :key="alias.id"
            class="hover:bg-surface-raised transition-colors"
            :data-testid="`statement-alias-${alias.id}`"
          >
            <td
              class="px-5 py-2.5 text-xs text-text-subtle font-mono max-w-[240px]"
              :title="alias.match_text"
              :data-testid="`alias-cell-match_text-${alias.id}`"
            >
              <AccountingInlineCell
                :value="alias.match_text"
                :saving="inlineSavingKey === `${alias.id}:match_text`"
                @save="$emit('inline-save', alias, 'match_text', $event)"
              >
                <span class="block truncate">{{ alias.match_text }}</span>
              </AccountingInlineCell>
            </td>
            <td
              class="px-5 py-2.5 text-sm text-text-default"
              :data-testid="`alias-cell-merchant_name-${alias.id}`"
            >
              <AccountingInlineCell
                type="merchant"
                :value="alias.merchant_name"
                :options="merchantOptions"
                :saving="inlineSavingKey === `${alias.id}:merchant_name`"
                @save="$emit('inline-save', alias, 'merchant_name', $event)"
              >
                {{ alias.merchant_name }}
              </AccountingInlineCell>
            </td>
            <td
              class="px-5 py-2.5 text-sm text-text-muted"
              :data-testid="`alias-cell-default_category-${alias.id}`"
            >
              <AccountingInlineCell
                type="select"
                :value="alias.default_category"
                :options="categoryOptions"
                :saving="inlineSavingKey === `${alias.id}:default_category`"
                @save="$emit('inline-save', alias, 'default_category', $event)"
              >
                {{ alias.default_category_label }}
              </AccountingInlineCell>
            </td>
            <td class="px-5 py-2.5 text-right whitespace-nowrap">
              <button
                class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors"
                @click="$emit('delete', alias)"
              >
                Eliminar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import AccountingInlineCell from '~/components/accounting/AccountingInlineCell.vue';

/**
 * Learned merchants (aliases) mapped from an statement descriptor to a merchant
 * name and its default category. The three columns are click-to-edit, exactly
 * like the statement transaction rows — an alias learned wrong used to force a
 * delete-and-relearn round trip through the assistant chat.
 *
 * The merchant column reuses the `merchant` combobox so renaming an alias
 * offers the names already in use instead of quietly creating near-duplicates.
 * The combobox also emits the picked merchant's default category as save
 * metadata; here it is ignored on purpose, since the category of an alias is
 * the value being defined rather than one to inherit.
 */
defineProps({
  aliases: { type: Array, default: () => [] },
  /** Category choices for the inline select: [{ value, label }]. */
  categoryOptions: { type: Array, default: () => [] },
  /** Learned merchants for the inline combobox: [{ value, category, categoryLabel }]. */
  merchantOptions: { type: Array, default: () => [] },
  /** `${aliasId}:${field}` of the cell whose PATCH is in flight. */
  inlineSavingKey: { type: String, default: null },
});

defineEmits(['inline-save', 'delete']);
</script>
