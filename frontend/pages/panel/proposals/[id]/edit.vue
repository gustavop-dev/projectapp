<template>
  <div>
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
    <ContractParamsModal
      :visible="showContractModal"
      :proposal="proposal"
      :initial-params="proposal?.contract_params || {}"
      :is-editing="contractModalEditing"
      @confirm="handleContractConfirm"
      @cancel="showContractModal = false"
    />
    <ProposalActionsModal
      :visible="showActionsModal"
      :proposal="proposal || {}"
      @close="showActionsModal = false"
      @send="handleSend"
      @send-multi="showMultiSendModal = true"
      @resend="handleResend"
      @negotiate="openContractModal(false)"
      @approve="handleStatusChange('accepted')"
      @launch="handleLaunchToPlatform"
      @finish="handleMarkAsFinished"
      @reject="handleStatusChange('rejected')"
      @discount-offer="openDiscountOfferModal"
    />
    <ProposalMultiSendModal
      :visible="showMultiSendModal"
      :current-proposal="proposal || {}"
      @close="showMultiSendModal = false"
      @sent="handleMultiSendSent"
    />
    <BusinessProposalAdminSyncPreviewModal
      :visible="syncPreviewVisible"
      :project-info="syncPreviewData?.project"
      :deliverable-info="syncPreviewData?.deliverable"
      :diff="syncPreviewData?.diff"
      :is-applying="syncApplying"
      @confirm="handleSyncConfirm"
      @cancel="handleSyncCancel"
    />
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-text-muted hover:text-text-default transition-colors">
        ← Volver a propuestas
      </NuxtLink>
    </div>

    <!-- Sticky header: title + investment + status -->
    <div v-if="proposal"
         class="sticky top-0 z-30 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-3 mb-6 bg-surface/80 backdrop-blur-md border-b border-border-muted transition-all">
      <div class="flex flex-wrap items-center gap-2 sm:gap-3">
        <h1 class="text-lg sm:text-xl font-light text-text-default truncate">{{ proposal.title }}</h1>
        <span v-if="proposal.total_investment > 0" class="text-sm sm:text-base font-light text-text-subtle whitespace-nowrap">
          ({{ formatInvestment(proposal.total_investment, proposal.currency) }})
        </span>
        <span
          v-if="hasCustomizedEffectiveTotal"
          data-testid="general-finance-effective-total-badge"
          class="text-xs px-2 py-0.5 rounded-full font-medium bg-warning-soft text-warning-strong whitespace-nowrap"
          :title="`Total efectivo visible al cliente según módulos seleccionados`"
        >
          Cliente ve: {{ formatInvestment(effectiveTotalInvestment, proposal.currency) }}
        </span>
        <span class="text-xs px-2.5 py-0.5 rounded-full font-medium" :class="statusClass(proposal.status)">
          {{ proposal.status }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="proposalStore.isLoading" class="text-center py-12 text-text-subtle text-sm">
      Cargando...
    </div>

    <template v-else-if="proposal">
      <!-- Tabs -->
      <BaseTabs v-model="activeTab" :tabs="tabs" />

      <!-- Tab: General -->
      <div v-show="activeTab === 'general'">
        <TabSplitLayout ratio="1:1" :aside-first-mobile="true">
          <template #aside>
        <!-- Editable slug (URL personalizada) -->
        <div class="bg-surface border border-border-muted rounded-xl p-4 sm:p-5 mb-4">
          <label class="text-xs font-medium text-text-muted uppercase tracking-wider" for="proposal-slug-input">
            URL personalizada
          </label>
          <div class="mt-2 flex flex-wrap items-stretch gap-2">
            <div class="flex-1 min-w-[260px] flex items-stretch rounded-lg border border-border-default bg-surface-raised focus-within:border-focus-ring focus-within:ring-1 focus-within:ring-focus-ring/30">
              <span class="px-3 flex items-center text-xs text-text-subtle border-r border-border-default select-none">/proposal/</span>
              <input
                id="proposal-slug-input"
                v-model="slugDraft"
                type="text"
                data-testid="proposal-slug-input"
                class="flex-1 bg-transparent px-3 py-2 text-sm text-text-default placeholder:text-text-subtle focus:outline-none font-mono"
                placeholder="maria-lopez"
                maxlength="120"
                @keydown.enter.prevent="saveSlug"
              />
            </div>
            <button
              type="button"
              class="px-3 py-2 text-xs font-medium rounded-lg bg-primary text-white hover:bg-primary disabled:opacity-50"
              :disabled="slugSaving || slugDraft === (proposal.slug || '')"
              @click="saveSlug"
            >
              {{ slugSaving ? 'Guardando…' : (slugSaved ? 'Guardado' : 'Guardar') }}
            </button>
            <button
              type="button"
              class="px-3 py-2 text-xs font-medium rounded-lg border border-border-default text-text-muted hover:border-border-default"
              :title="'Regenerar desde el nombre del cliente'"
              @click="regenerateSlugFromName"
            >
              Regenerar
            </button>
          </div>
          <p v-if="slugError" class="text-xs text-danger-strong mt-2">{{ slugError }}</p>
          <p v-else class="text-xs text-text-subtle mt-2">
            Solo minúsculas, números y guiones. El cliente verá esta URL en el enlace.
          </p>
        </div>

        <div
          class="mb-4 rounded-xl border border-primary/30 bg-primary-soft px-4 py-3 sm:px-5 sm:py-4 text-sm"
          aria-label="Identificación y estado de la propuesta"
        >
          <span class="inline-flex items-center gap-1 mb-3 px-2 py-0.5 rounded-full bg-primary-soft text-[10px] font-medium uppercase tracking-wider text-text-brand">
            Identificación
          </span>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span class="text-text-subtle text-xs">UUID</span>
              <p class="text-text-muted font-mono text-xs mt-0.5">{{ proposal.uuid }}</p>
            </div>
            <div>
              <div class="flex items-center gap-1">
                <span class="text-text-subtle text-xs">URL pública</span>
                <button type="button"
                  :title="copied ? 'Copiado!' : 'Copiar URL'"
                  @click="copyUrl"
                  class="text-text-subtle hover:text-text-brand transition-colors">
                  <DocumentDuplicateIcon v-if="!copied" class="w-3.5 h-3.5" />
                  <CheckIcon v-else class="w-3.5 h-3.5 text-success-strong" />
                </button>
              </div>
              <p class="mt-0.5">
                <a :href="'/proposal/' + publicIdentifier" target="_blank" class="text-text-brand hover:underline text-xs break-all">
                  /proposal/{{ publicIdentifier }}
                </a>
              </p>
              <div v-for="link in proposalModeLinks" :key="link.mode" class="mt-2">
                <div class="flex items-center gap-1">
                  <span class="text-text-subtle text-xs">{{ link.labelUrl }}</span>
                  <button type="button"
                    :title="copiedMode === link.mode ? 'Copiado!' : 'Copiar URL'"
                    @click="copyModeUrl(link.mode)"
                    class="text-text-subtle hover:text-text-brand transition-colors">
                    <DocumentDuplicateIcon v-if="copiedMode !== link.mode" class="w-3.5 h-3.5" />
                    <CheckIcon v-else class="w-3.5 h-3.5 text-success-strong" />
                  </button>
                </div>
                <p class="mt-0.5">
                  <a :href="'/proposal/' + publicIdentifier + '?mode=' + link.mode" target="_blank" class="text-text-brand hover:underline text-xs break-all">
                    /proposal/{{ publicIdentifier }}?mode={{ link.mode }}
                  </a>
                </p>
              </div>
            </div>
            <div>
              <span class="text-text-subtle text-xs">Vistas</span>
              <p class="text-text-muted mt-0.5">{{ proposal.view_count }}</p>
            </div>
            <div>
              <span class="text-text-subtle text-xs">Enviada</span>
              <p class="text-text-muted mt-0.5">
                {{ proposal.sent_at ? new Date(proposal.sent_at).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' }) : '—' }}
              </p>
            </div>
            <div v-if="proposal.platform_onboarding_completed_at">
              <span class="text-text-subtle text-xs">Plataforma lanzada</span>
              <p class="text-text-muted mt-0.5 text-xs">
                {{ new Date(proposal.platform_onboarding_completed_at).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }) }}
              </p>
            </div>
            <div v-if="!hasDocumentsTab">
              <span class="text-text-subtle text-xs">PDFs</span>
              <div class="flex items-center gap-3 mt-0.5 flex-wrap">
                <a :href="'/api/proposals/' + proposal.uuid + '/pdf/'"
                   target="_blank"
                   class="inline-flex items-center gap-1.5 text-text-brand hover:text-text-brand text-xs font-medium transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Propuesta comercial
                </a>
                <span class="text-text-subtle text-xs">|</span>
                <a :href="'/api/proposals/' + proposal.uuid + '/pdf/?doc=technical'"
                   target="_blank"
                   class="inline-flex items-center gap-1.5 text-text-brand hover:text-text-brand text-xs font-medium transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Detalle técnico
                </a>
              </div>
            </div>
            <div class="sm:col-span-2">
              <div class="flex items-start gap-6 flex-wrap">
                <div>
                  <div class="flex items-center gap-1">
                    <span class="text-text-subtle text-xs">Estado activo</span>
                    <BaseTooltip position="right">
                      <template #trigger>
                        <QuestionMarkCircleIcon class="w-3 h-3 text-text-subtle hover:text-text-muted transition-colors" />
                      </template>
                      {{ tt.activeStatus }}
                    </BaseTooltip>
                  </div>
                  <div class="flex items-center gap-2 mt-1">
                    <BaseToggle
                      :model-value="proposal.is_active"
                      size="sm"
                      aria-label="Activar propuesta"
                      @update:model-value="handleToggleActive"
                    />
                    <span class="text-xs" :class="proposal.is_active ? 'text-primary' : 'text-text-subtle'">
                      {{ proposal.is_active ? 'Activa' : 'Inactiva' }}
                    </span>
                  </div>
                </div>
                <div>
                  <div class="flex items-center gap-1">
                    <span class="text-text-subtle text-xs">Automatizaciones</span>
                    <BaseTooltip position="right">
                      <template #trigger>
                        <QuestionMarkCircleIcon class="w-3 h-3 text-text-subtle hover:text-text-muted transition-colors" />
                      </template>
                      {{ tt.automations }}
                    </BaseTooltip>
                  </div>
                  <div class="flex items-center gap-2 mt-1">
                    <BaseToggle
                      :model-value="form.automations_paused"
                      size="sm"
                      on-class="bg-warning-strong"
                      off-class="bg-primary"
                      aria-label="Pausar automatizaciones"
                      @update:model-value="toggleAutomationsPaused"
                    />
                    <span class="text-xs" :class="form.automations_paused ? 'text-warning-strong' : 'text-primary'">
                      {{ form.automations_paused ? '⏸ Pausadas' : 'Activas' }}
                    </span>
                  </div>
                  <p class="text-[10px] text-text-subtle mt-1">Pausar emails automáticos (recordatorio, urgencia, inactividad).</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div data-testid="general-finance-sidebar" class="bg-surface border border-border-muted rounded-xl p-4 sm:p-5 mb-4 space-y-5">
          <h3 class="text-xs font-medium text-text-muted uppercase tracking-wider">
            Inversión, pagos y hosting
          </h3>
          <div data-testid="general-finance-investment-card" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Inversión total</label>
              <BaseInput v-model.number="form.total_investment" type="number" min="0" step="0.01" data-testid="general-finance-total-investment" />
              <p
                v-if="hasCustomizedEffectiveTotal"
                data-testid="general-finance-effective-total-note"
                class="text-xs text-warning-strong mt-1.5"
              >
                Total efectivo visible al cliente:
                <strong>{{ formatInvestment(effectiveTotalInvestment, proposal.currency) }}</strong>
                (incluye módulos adicionales seleccionados).
              </p>
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Moneda</label>
              <BaseSelect
                v-model="form.currency"
                data-testid="general-finance-currency"
                :options="[{ value: 'COP', label: 'COP' }, { value: 'USD', label: 'USD' }]"
              />
            </div>
          </div>
          <div v-if="investmentSection" class="bg-primary-soft border border-primary/30 rounded-xl px-4 py-3">
            <label class="block text-sm font-medium text-text-brand mb-2">Porcentajes de pago (sección Inversión)</label>
            <div v-if="investmentPaymentPercentages.length" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label
                v-for="(_, idx) in investmentPaymentPercentages"
                :key="`payment-percent-${idx}`"
                class="block"
              >
                <span class="block text-xs text-text-brand mb-1">Pago {{ idx + 1 }}</span>
                <div class="flex items-center gap-2">
                  <BaseInput
                    v-model.number="investmentPaymentPercentages[idx]"
                    type="number"
                    size="sm"
                    min="0"
                    max="100"
                    step="0.01"
                    @blur="normalizeGeneralPaymentPercentage(idx)"
                  />
                  <span class="text-sm text-text-brand">%</span>
                </div>
                <span
                  v-if="form.total_investment > 0 && investmentPaymentPercentages[idx] > 0"
                  class="block text-xs text-text-brand mt-1 font-medium"
                >
                  {{ paymentAmounts[idx] }}
                </span>
              </label>
            </div>
            <p v-else class="text-xs text-text-brand">No se detectaron porcentajes en "Secciones → Inversión → Opciones de pago".</p>
            <p class="text-xs text-text-brand mt-2">Se sincroniza con los porcentajes definidos en "Secciones → Inversión → Opciones de pago".</p>
          </div>
          <div data-testid="general-finance-hosting-card">
            <div class="flex items-center gap-1.5 mb-1">
              <label class="block text-sm font-medium text-text-default">Hosting (% de inversión total)</label>
              <BaseTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-text-subtle hover:text-text-muted transition-colors" />
                </template>
                {{ tt.hostingPercent }}
              </BaseTooltip>
            </div>
            <div class="flex items-center gap-3">
              <BaseInput
                v-model.number="form.hosting_percent"
                data-testid="general-finance-hosting-percent"
                type="number"
                min="0"
                max="100"
                class="w-32"
              />
              <span class="text-sm text-text-muted">%</span>
            </div>
            <div v-if="form.hosting_percent > 0 && form.total_investment > 0" class="mt-3 bg-info-soft border border-info-strong/30 rounded-xl overflow-hidden">
              <div class="px-4 py-2 text-[11px] uppercase tracking-wider text-info-strong/70 border-b border-info-strong/20">
                Precio que verá el cliente (por mes)
              </div>
              <div class="grid grid-cols-[1fr_auto_auto] gap-x-4 text-sm divide-y divide-info-strong/20">
                <div class="px-4 py-2 text-info-strong font-medium">Base mensual</div>
                <div class="px-4 py-2 text-info-strong font-semibold text-right whitespace-nowrap">
                  ${{ hostingMonthlyBase.toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-info-strong/70 text-right whitespace-nowrap">referencia</div>

                <div class="px-4 py-2 text-info-strong font-medium">
                  Trimestral
                  <span v-if="form.hosting_discount_quarterly" class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_quarterly }}% dcto)</span>
                </div>
                <div class="px-4 py-2 font-semibold text-right whitespace-nowrap"
                     :class="form.hosting_discount_quarterly ? 'text-text-brand' : 'text-info-strong'">
                  ${{ hostingMonthlyWithDiscount(form.hosting_discount_quarterly).toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-info-strong/70 text-right whitespace-nowrap">
                  total ${{ hostingPeriodTotal(form.hosting_discount_quarterly, 3).toLocaleString() }} / 3 meses
                </div>

                <div class="px-4 py-2 text-info-strong font-medium">
                  Semestral
                  <span v-if="form.hosting_discount_semiannual" class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_semiannual }}% dcto)</span>
                </div>
                <div class="px-4 py-2 font-semibold text-right whitespace-nowrap"
                     :class="form.hosting_discount_semiannual ? 'text-text-brand' : 'text-info-strong'">
                  ${{ hostingMonthlyWithDiscount(form.hosting_discount_semiannual).toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-info-strong/70 text-right whitespace-nowrap">
                  total ${{ hostingPeriodTotal(form.hosting_discount_semiannual, 6).toLocaleString() }} / 6 meses
                </div>

                <div class="px-4 py-2 text-info-strong font-medium">
                  Anual
                  <span v-if="form.hosting_discount_annual" class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_annual }}% dcto)</span>
                </div>
                <div class="px-4 py-2 font-semibold text-right whitespace-nowrap"
                     :class="form.hosting_discount_annual ? 'text-text-brand' : 'text-info-strong'">
                  ${{ hostingMonthlyWithDiscount(form.hosting_discount_annual).toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-info-strong/70 text-right whitespace-nowrap">
                  total ${{ hostingPeriodTotal(form.hosting_discount_annual, 12).toLocaleString() }} {{ form.currency }} / 12 meses
                </div>

                <div class="px-4 py-2 text-info-strong font-medium">☁️ Anual (referencia)</div>
                <div class="px-4 py-2 text-info-strong font-semibold text-right whitespace-nowrap">
                  ${{ hostingAnnualAmount.toLocaleString() }} {{ form.currency }}
                </div>
                <div class="px-4 py-2 text-[11px] text-info-strong/70 text-right whitespace-nowrap">sin descuento</div>
              </div>
            </div>
            <p class="text-xs text-text-subtle mt-1">Sincronizado automáticamente con el Plan de Hosting que ve el cliente en "Tu inversión y cómo pagar".</p>
          </div>
          <div data-testid="general-finance-discounts-card" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Dcto. anual (%)</label>
              <BaseInput
                v-model.number="form.hosting_discount_annual"
                data-testid="general-finance-annual-discount"
                type="number"
                min="0"
                max="100"
                class="w-32"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Dcto. semestral (%)</label>
              <BaseInput
                v-model.number="form.hosting_discount_semiannual"
                data-testid="general-finance-semiannual-discount"
                type="number"
                min="0"
                max="100"
                class="w-32"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Dcto. trimestral (%)</label>
              <BaseInput
                v-model.number="form.hosting_discount_quarterly"
                data-testid="general-finance-quarterly-discount"
                type="number"
                min="0"
                max="100"
                class="w-32"
              />
            </div>
          </div>
        </div>

          </template>

          <template #main>
        <!-- Editable form -->
        <form class="bg-surface rounded-xl shadow-sm border border-border-muted" @submit.prevent="handleUpdate">
          <div class="p-4 sm:p-8 space-y-6">
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Título</label>
            <BaseInput v-model="form.title" type="text" required />
          </div>
          <!-- Client picker (autocomplete + snapshot fields) -->
          <div class="space-y-4 border border-border-muted rounded-xl p-4 bg-surface-raised">
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Cliente</label>
              <ClientAutocomplete
                v-model="form.client_id"
                :initial-label="form.client_name"
                test-id="proposal-edit-client-autocomplete"
                @select="onClientSelected"
                @create-new="onCreateInlineClient"
              />
              <p class="text-xs text-text-subtle mt-1">
                Busca un cliente existente o escribe uno nuevo. Si no eliges email, se generará uno temporal y las automatizaciones quedarán pausadas.
              </p>
            </div>

            <!-- Placeholder warning badge -->
            <div
              v-if="proposal?.client?.is_email_placeholder"
              class="flex items-start gap-2 px-3 py-2 rounded-lg bg-warning-soft border border-warning-strong/30"
            >
              <span class="text-warning-strong text-xs font-medium">
                📧 Email pendiente — las automatizaciones de correo están pausadas para este cliente.
              </span>
            </div>

            <!-- Snapshot fields (still editable, but clearly subordinated) -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-text-muted mb-1">Nombre snapshot</label>
                <BaseInput
                  id="edit-client-name"
                  v-model="form.client_name"
                  type="text"
                  required
                  size="sm"
                  data-testid="edit-client-name"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-muted mb-1">Email del cliente</label>
                <BaseInput
                  id="edit-client-email"
                  v-model="form.client_email"
                  type="email"
                  size="sm"
                  data-testid="edit-client-email"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-muted mb-1">Teléfono / WhatsApp</label>
                <BaseInput
                  id="edit-client-phone"
                  v-model="form.client_phone"
                  type="tel"
                  size="sm"
                  placeholder="+57 300 123 4567"
                  data-testid="edit-client-phone"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-muted mb-1">Empresa</label>
                <BaseInput
                  id="edit-client-company"
                  v-model="form.client_company"
                  type="text"
                  size="sm"
                  placeholder="Acme Inc."
                  data-testid="edit-client-company"
                />
              </div>
            </div>

          </div>

          <div>
            <label class="block text-sm font-medium text-text-default mb-1" for="edit-email-intro">
              Texto introductorio del correo
            </label>
            <p class="text-xs text-text-muted mb-2">
              Párrafo descriptivo que aparecerá en el correo enviado al cliente cuando reciba la propuesta. Si lo dejas vacío se usa un texto por defecto basado en el título.
            </p>
            <BaseTextarea
              id="edit-email-intro"
              v-model="form.email_intro"
              :rows="5"
              size="sm"
              placeholder="Ej. Esta primera fase contempla la construcción de la plataforma base de tu firma..."
              data-testid="edit-email-intro"
            />
          </div>

          <div class="space-y-3 pt-2 border-t border-input-border">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h4 class="text-sm font-medium text-text-default">Configuración del correo (diseño nuevo)</h4>
                <p class="text-xs text-text-muted mt-1">
                  Estos campos llenan los bloques del correo comercial: lista "Qué incluye", card "Método en 3 fases" y firma. Si los dejas vacíos se omiten o se usa el método estándar de marca.
                </p>
              </div>
              <button
                type="button"
                class="shrink-0 px-3 py-1.5 text-xs font-medium border border-input-border rounded-lg hover:bg-surface-raised transition-colors"
                data-testid="edit-email-preview-btn"
                @click="openEmailPreview"
              >
                👁 Vista previa
              </button>
            </div>

            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Firmado por</label>
              <BaseSelect v-model="form.email_signed_by" data-testid="edit-email-signed-by">
                <option value="gustavo">Gustavo Pérez · CEO</option>
                <option value="carlos">Carlos Blanco · CTO</option>
              </BaseSelect>
              <p class="text-xs text-text-subtle mt-1">Nombre y cargo que firman al pie del correo.</p>
            </div>

            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-text-default">Qué incluye (bullets)</label>
                <button
                  type="button"
                  class="text-xs text-primary hover:underline disabled:opacity-50"
                  :disabled="form.email_features.length >= MAX_EMAIL_FEATURES"
                  data-testid="edit-add-feature"
                  @click="addEmailFeature"
                >
                  + Agregar ítem
                </button>
              </div>
              <p class="text-xs text-text-muted mb-2">
                Hasta 8 ítems. Si queda vacío el bloque no se renderiza.
              </p>
              <div v-if="form.email_features.length === 0" class="text-xs text-text-subtle italic">
                Sin ítems — el bloque no aparecerá en el correo.
              </div>
              <div
                v-for="(_, idx) in form.email_features"
                :key="`feature-${idx}`"
                class="flex items-start gap-2 mb-2"
              >
                <span class="text-xs font-medium text-text-muted pt-2 w-6">
                  {{ String(idx + 1).padStart(2, '0') }}
                </span>
                <BaseTextarea
                  v-model="form.email_features[idx]"
                  :rows="2"
                  size="sm"
                  class="flex-1"
                  placeholder="Ej. Dashboard en tiempo real con filtros por ruta, conductor y estado."
                />
                <button
                  type="button"
                  class="text-xs text-danger-strong hover:underline pt-2"
                  @click="removeEmailFeature(idx)"
                >
                  Quitar
                </button>
              </div>
            </div>

            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-text-default">Método en 3 fases</label>
                <button
                  type="button"
                  class="text-xs text-primary hover:underline"
                  @click="ensureMethodPhases"
                >
                  Restaurar método estándar
                </button>
              </div>
              <p class="text-xs text-text-muted mb-2">
                Card oscura del correo. Si lo dejas con los valores estándar usa los textos de marca; puedes personalizarlos por propuesta.
              </p>
              <div
                v-for="(phase, idx) in form.email_method_phases"
                :key="`phase-${idx}`"
                class="grid grid-cols-1 sm:grid-cols-[60px,1fr,90px,1fr] gap-2 mb-2 items-start"
              >
                <BaseInput
                  v-model="form.email_method_phases[idx].number"
                  size="sm"
                  placeholder="01"
                  class="text-center"
                />
                <BaseInput
                  v-model="form.email_method_phases[idx].title"
                  size="sm"
                  placeholder="Diagnóstico"
                />
                <BaseInput
                  v-model="form.email_method_phases[idx].duration"
                  size="sm"
                  placeholder="5 días"
                />
                <BaseTextarea
                  v-model="form.email_method_phases[idx].description"
                  :rows="2"
                  size="sm"
                  placeholder="Mapeo de procesos y alcance final."
                />
              </div>
              <p class="text-xs text-text-subtle">Orden de columnas: número · título · duración · descripción.</p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Tipo de proyecto</label>
              <BaseSelect v-model="form.project_type">
                <option value="">— Sin definir —</option>
                <option value="website">Sitio Web</option>
                <option value="ecommerce">E-commerce</option>
                <option value="webapp">Aplicación Web</option>
                <option value="landing">Landing Page</option>
                <option value="redesign">Rediseño</option>
                <option value="mobile_app">App Móvil</option>
                <option value="branding">Branding / Identidad Visual</option>
                <option value="cms">Sistema CMS</option>
                <option value="portal">Portal / Intranet</option>
                <option value="api_integration">Integración de APIs</option>
                <option value="marketplace">Marketplace</option>
                <option value="erp">Sistema ERP / Administrativo</option>
                <option value="booking">Sistema de Reservas</option>
                <option value="dashboard">Dashboard / Reportes</option>
                <option value="crm">Sistema CRM</option>
                <option value="saas">SaaS / Plataforma</option>
                <option value="chatbot">Chatbot / Asistente Virtual</option>
                <option value="ai_tool">Herramienta con IA</option>
                <option value="automation">Automatización / RPA</option>
                <option value="data_analytics">Analítica de Datos / BI</option>
                <option value="plugin_extension">Plugin / Extensión</option>
                <option value="other">Otro</option>
              </BaseSelect>
              <BaseInput
                v-if="form.project_type === 'other'"
                v-model="form.project_type_custom"
                type="text"
                placeholder="Especificar tipo de proyecto..."
                class="mt-2"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Tipo de mercado</label>
              <BaseSelect v-model="form.market_type">
                <option value="">— Sin definir —</option>
                <option value="b2b">B2B</option>
                <option value="b2c">B2C</option>
                <option value="saas">SaaS</option>
                <option value="retail">Retail</option>
                <option value="services">Servicios profesionales</option>
                <option value="health">Salud</option>
                <option value="education">Educación</option>
                <option value="real_estate">Inmobiliaria</option>
                <option value="fintech">Fintech / Finanzas</option>
                <option value="restaurant">Restaurantes / F&amp;B</option>
                <option value="tourism">Turismo / Hospitalidad</option>
                <option value="logistics">Logística / Transporte</option>
                <option value="sports">Deportes / Fitness</option>
                <option value="legal">Servicios Legales / Jurídico</option>
                <option value="construction">Construcción / Arquitectura</option>
                <option value="media">Medios / Entretenimiento</option>
                <option value="ngo">ONG / Sector Público</option>
                <option value="agriculture">Agro / Tecnología Agrícola</option>
                <option value="tech">Tecnología / Software</option>
                <option value="consulting">Consultoría / Asesoría</option>
                <option value="automotive">Automotriz</option>
                <option value="fashion">Moda / Textil</option>
                <option value="beauty">Belleza / Cuidado Personal</option>
                <option value="manufacturing">Manufactura / Industrial</option>
                <option value="energy">Energía / Utilities</option>
                <option value="gaming">Videojuegos / Gaming</option>
                <option value="other">Otro</option>
              </BaseSelect>
              <BaseInput
                v-if="form.market_type === 'other'"
                v-model="form.market_type_custom"
                type="text"
                placeholder="Especificar tipo de mercado..."
                class="mt-2"
              />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Idioma</label>
            <BaseSelect
              v-model="form.language"
              :options="[{ value: 'es', label: 'Español' }, { value: 'en', label: 'English' }]"
            />
            <p class="text-xs text-text-subtle mt-1">Solo afecta los títulos por defecto al crear. Cambiar aquí no regenera las secciones existentes.</p>
          </div>
          <div>
            <div class="flex items-center gap-1.5 mb-1">
              <label class="block text-sm font-medium text-text-default">Fecha de expiración</label>
              <BaseTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-text-subtle hover:text-text-muted transition-colors" />
                </template>
                {{ tt.expirationDate }}
              </BaseTooltip>
            </div>
            <div class="flex items-center gap-2">
              <BaseInput
                v-model="form.expires_at"
                type="datetime-local"
                class="flex-1"
              />
              <BaseInput
                v-model.number="expiryDaysInput"
                type="number"
                min="1"
                max="365"
                class="w-20 text-center"
              />
              <span class="text-xs text-text-subtle whitespace-nowrap">días</span>
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Recordatorio (días después de enviar)</label>
              <BaseInput v-model.number="form.reminder_days" type="number" min="1" max="30" />
              <p class="text-xs text-text-subtle mt-1">Se enviará un email recordatorio al cliente X días después de enviar la propuesta.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Urgencia (días después de enviar)</label>
              <BaseInput v-model.number="form.urgency_reminder_days" type="number" min="1" max="30" />
              <p class="text-xs text-text-subtle mt-1">Se enviará un email de urgencia X días después de enviar (incluye descuento si % > 0).</p>
            </div>
          </div>
          <div>
            <div class="flex items-center gap-1.5 mb-1">
              <label class="block text-sm font-medium text-text-default">Descuento (%)</label>
              <BaseTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-text-subtle hover:text-text-muted transition-colors" />
                </template>
                {{ tt.discount }}
              </BaseTooltip>
            </div>
            <BaseInput
              v-model.number="form.discount_percent"
              data-testid="general-finance-general-discount"
              type="number"
              min="0"
              max="100"
            />
            <p class="text-xs text-text-subtle mt-1">0 = sin descuento en email de urgencia.</p>
          </div>

          </div>

          <!-- Sticky action bar -->
          <div class="sticky bottom-0 rounded-b-xl bg-surface/95 backdrop-blur-sm border-t border-border-muted px-4 sm:px-5 py-3 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-20">
            <div class="flex flex-col-reverse sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-3">
              <div class="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
                <BaseButton
                  type="submit"
                  variant="primary"
                  size="md"
                  :loading="proposalStore.isUpdating"
                  :disabled="proposalStore.isUpdating"
                  data-testid="proposal-edit-submit"
                  class="flex-1 sm:flex-none"
                >
                  {{ proposalStore.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
                </BaseButton>

                <BaseButton
                  variant="secondary"
                  size="md"
                  data-testid="proposal-actions-menu"
                  aria-label="Acciones de la propuesta"
                  title="Más acciones"
                  class="!w-10 !h-10 !p-0 flex-shrink-0"
                  @click="showActionsModal = true"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                    <path fill-rule="evenodd" d="M14.615 1.595a.75.75 0 0 1 .359.852L12.982 9.75h7.268a.75.75 0 0 1 .548 1.262l-10.5 11.25a.75.75 0 0 1-1.272-.71l1.992-7.302H3.818a.75.75 0 0 1-.548-1.262l10.5-11.25a.75.75 0 0 1 .845-.143Z" clip-rule="evenodd" />
                  </svg>
                </BaseButton>
              </div>

              <button
                v-if="nextAction"
                type="button"
                :disabled="nextAction.disabled"
                :data-testid="'proposal-next-action-' + nextAction.key"
                :class="['px-4 sm:px-5 py-2 rounded-xl font-medium text-sm transition-all shadow-sm active:scale-[0.98] disabled:opacity-50 w-full sm:w-auto sm:ml-auto', nextAction.colorClass]"
                @click="handleNextAction"
              >
                {{ nextAction.label }}
              </button>
            </div>
          </div>
        </form>
          </template>
        </TabSplitLayout>
      </div>

      <!-- Tab: Correos -->
      <div v-show="activeTab === 'emails'">
        <ProposalEmailsTab v-if="proposal" :proposal="proposal" />
      </div>

      <!-- Tab: Documentos -->
      <div v-show="activeTab === 'documents'" class="max-w-7xl mx-auto">
        <ProposalDocumentsTab
          v-if="hasProposalDocuments"
          :proposal="proposal"
          :documents="proposal.proposal_documents || []"
          @refresh="refreshData"
          @edit-contract="openContractModal(true)"
          @generate-contract="openContractModal(false)"
        />
      </div>

      <!-- Tab: Cronograma -->
      <div v-show="activeTab === 'schedule'" class="max-w-7xl mx-auto">
        <ProjectScheduleEditor v-if="proposal" :proposal="proposal" />
      </div>

      <!-- Tab: Prompt Proposal -->
      <div v-show="activeTab === 'prompt'" class="max-w-7xl mx-auto">
        <ProposalPromptTab :proposal="proposal" />
      </div>

      <!-- Tab: Desarrollo (checklist Markdown) -->
      <div v-show="activeTab === 'development'">
        <DevChecklistTab
          :proposal="proposal"
          :refreshing="isRefreshing"
          @refresh="refreshData"
        />
      </div>

      <!-- Tab: JSON -->
      <div v-show="activeTab === 'json'">
        <ProposalJsonTab :proposal="proposal" :active="activeTab === 'json'" @applied="handleJsonApplied" />
      </div>

      <!-- Tab: Activity -->
      <div v-show="activeTab === 'activity'" class="max-w-5xl mx-auto">
        <ProposalActivityTab :proposal="proposal" />
      </div>

      <!-- Tab: Analytics -->
      <div v-show="activeTab === 'analytics'" class="max-w-screen-2xl mx-auto">
        <ProposalAnalytics :proposalId="proposal.id" :proposal="proposal" />
      </div>

      <!-- Tab: Detalle técnico -->
      <div v-show="activeTab === 'technical'" class="max-w-7xl mx-auto">
        <BaseSegmented
          v-model="technicalSubTab"
          class="mb-4 max-w-sm"
          full-width
          :options="[
            { value: 'editor', label: 'Editor', testId: 'technical-editor-subtab' },
            { value: 'json', label: 'JSON', testId: 'technical-json-subtab' },
          ]"
        />
        <div v-show="technicalSubTab === 'editor'">
          <p v-if="!technicalSection" class="text-sm text-warning-strong bg-warning-soft border border-warning-strong/30 rounded-lg px-4 py-3">
            No se encontró la sección «Detalle técnico». Ejecuta migraciones o crea la propuesta de nuevo.
          </p>
          <template v-else>
            <BaseCheckbox
              :model-value="technicalSection.is_enabled"
              class="mb-4"
              @update:model-value="toggleTechnicalSectionEnabled"
            >
              Visible en la propuesta (cuando exista vista pública del modo técnico)
            </BaseCheckbox>
            <TechnicalDocumentEditor
              :key="technicalSection.id"
              :section="technicalSection"
              :module-link-options="technicalModuleLinkOptions"
              :item-link-options="technicalItemLinkOptions"
              @save="handleSaveSection"
            />
          </template>
        </div>
        <div v-show="technicalSubTab === 'json'" class="space-y-4">
          <p class="text-xs text-text-muted">
            Solo el objeto <code class="bg-surface-raised px-1 rounded">content_json</code> del detalle técnico. Debe ser JSON válido (mismo esquema que el editor).
          </p>
          <JsonStatsPanel :stats="technicalJsonStats" test-id="technical-json-stats" />
          <BaseTextarea
            v-model="technicalJsonRaw"
            data-testid="technical-json-textarea"
            :rows="JSON_TEXTAREA_ROWS"
            class="font-mono"
          />
          <div v-if="technicalJsonError" class="text-sm text-danger-strong bg-danger-soft px-4 py-2 rounded-lg">{{ technicalJsonError }}</div>
          <BaseButton variant="primary" size="lg" @click="handleApplyTechnicalJson">
            Guardar JSON
          </BaseButton>
        </div>
      </div>

      <!-- Tab: Sections -->
      <div v-show="activeTab === 'sections'" class="max-w-7xl mx-auto">
        <ProposalSectionsTab
          :proposal="proposal"
          :module-link-options="technicalModuleLinkOptions"
          :item-link-options="technicalItemLinkOptions"
          @send="handleSend"
          @resend="handleResend"
          @sync-hosting-percent="handleSyncHostingPercent"
          @dirty-state-change="sectionsDirty = $event"
        />
      </div>
    </template>

    <!-- Pre-send scorecard modal -->
    <BaseModal v-model="showSendChecklist" size="md" padding="md">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-lg font-bold text-text-default">Scorecard pre-envío</h3>
        <BaseBadge
          v-if="scorecardData"
          :variant="scorecardData.score >= 8 ? 'success' : scorecardData.score >= 5 ? 'warning' : 'danger'"
        >
          {{ scorecardData.score }}/10
        </BaseBadge>
      </div>
      <p class="text-sm text-text-muted mb-5">{{ scorecardLoading ? 'Verificando...' : 'Verifica que todo esté listo antes de enviar.' }}</p>
      <ul v-if="!scorecardLoading" class="space-y-3 mb-6">
        <li v-for="(item, idx) in sendChecklist" :key="idx" class="flex items-center gap-3">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-sm flex-shrink-0"
            :class="item.pass ? 'bg-success-soft text-success-strong' : item.blocker ? 'bg-danger-soft text-danger-strong' : 'bg-warning-soft text-warning-strong'">
            {{ item.pass ? '✓' : '✗' }}
          </span>
          <div class="flex-1 min-w-0">
            <span class="text-sm" :class="item.pass ? 'text-text-muted' : item.blocker ? 'text-danger-strong font-medium' : 'text-warning-strong'">{{ item.label }}</span>
            <span v-if="!item.pass && item.blocker" class="ml-1 text-[10px] text-danger-strong font-semibold uppercase">bloqueante</span>
          </div>
        </li>
      </ul>
      <div v-else class="flex items-center justify-center py-8">
        <span class="text-sm text-text-subtle">Cargando scorecard...</span>
      </div>
      <div class="flex gap-3 justify-end">
        <BaseButton variant="ghost" size="lg" @click="showSendChecklist = false">
          Cancelar
        </BaseButton>
        <BaseButton
          variant="primary"
          size="lg"
          class="!bg-info-strong hover:!bg-info-strong/90"
          :disabled="!allChecksPassing || scorecardLoading"
          @click="confirmSend"
        >
          Enviar al Cliente
        </BaseButton>
      </div>
    </BaseModal>

    <BaseModal v-model="isPreviewOpen" size="5xl" padding="none">
      <div class="flex flex-col h-[85vh]">
        <div class="flex items-center justify-between gap-4 p-4 border-b border-input-border">
          <div>
            <h3 class="text-base font-medium text-text-default">Vista previa del correo</h3>
            <p class="text-xs text-text-muted mt-0.5">
              Render real usando los datos guardados de la propuesta + los cambios actuales de la sección de configuración de correo.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <select
              v-model="previewTemplateKey"
              class="px-3 py-2 border border-input-border bg-input-bg text-input-text rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              data-testid="edit-email-preview-select"
            >
              <option v-for="tpl in PREVIEWABLE_EMAIL_TEMPLATES" :key="tpl.key" :value="tpl.key">
                {{ tpl.label }}
              </option>
            </select>
            <button
              type="button"
              class="px-3 py-2 text-sm font-medium border border-input-border rounded-lg hover:bg-surface-raised transition-colors"
              :disabled="previewLoading"
              @click="loadPreview"
            >
              {{ previewLoading ? 'Cargando…' : '↻ Recargar' }}
            </button>
            <button
              type="button"
              class="px-3 py-2 text-sm font-medium text-text-muted hover:text-text-default transition-colors"
              @click="isPreviewOpen = false"
            >
              Cerrar
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-hidden bg-[#f4f1ea]">
          <div v-if="previewLoading" class="flex items-center justify-center h-full text-text-muted text-sm">
            Generando vista previa…
          </div>
          <div v-else-if="previewError" class="flex items-center justify-center h-full text-danger-strong text-sm px-6 text-center">
            {{ previewError }}
          </div>
          <iframe
            v-else-if="previewHtml"
            :srcdoc="previewHtml"
            class="w-full h-full border-0"
            sandbox="allow-same-origin"
            title="Vista previa del correo"
          ></iframe>
        </div>
      </div>
    </BaseModal>

    <BaseModal v-model="showDiscountModal" size="5xl" padding="none">
      <div class="flex flex-col h-[85vh]">
        <div class="flex items-center justify-between gap-4 p-4 border-b border-input-border">
          <div class="flex items-center gap-4">
            <div class="flex flex-col items-center justify-center rounded-2xl bg-danger-strong px-4 py-2 text-white leading-none">
              <span class="text-3xl font-black tracking-tight">-{{ proposal?.discount_percent }}%</span>
              <span class="text-[10px] font-semibold uppercase tracking-widest opacity-90">descuento</span>
            </div>
            <div>
              <h3 class="text-base font-medium text-text-default">Enviar oferta de descuento</h3>
              <p class="text-xs text-text-muted mt-0.5">
                Revisa el correo antes de enviarlo a {{ proposal?.client_email }}.
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="px-3 py-2 text-sm font-medium border border-input-border rounded-lg hover:bg-surface-raised transition-colors"
              :disabled="discountPreviewLoading"
              @click="loadDiscountPreview"
            >
              {{ discountPreviewLoading ? 'Cargando…' : '↻ Recargar' }}
            </button>
            <BaseButton
              variant="primary"
              size="md"
              class="!bg-danger-strong hover:!bg-danger-strong/90"
              :disabled="discountSending || discountPreviewLoading"
              @click="confirmSendDiscountOffer"
            >
              {{ discountSending ? 'Enviando…' : 'Enviar oferta' }}
            </BaseButton>
            <button
              type="button"
              class="px-3 py-2 text-sm font-medium text-text-muted hover:text-text-default transition-colors"
              @click="showDiscountModal = false"
            >
              Cerrar
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-hidden bg-[#f4f1ea]">
          <div v-if="discountPreviewLoading" class="flex items-center justify-center h-full text-text-muted text-sm">
            Generando vista previa…
          </div>
          <div v-else-if="discountPreviewError" class="flex items-center justify-center h-full text-danger-strong text-sm px-6 text-center">
            {{ discountPreviewError }}
          </div>
          <iframe
            v-else-if="discountPreviewHtml"
            :srcdoc="discountPreviewHtml"
            class="w-full h-full border-0"
            sandbox="allow-same-origin"
            title="Vista previa de la oferta de descuento"
          ></iframe>
        </div>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import {
  QuestionMarkCircleIcon,
  DocumentDuplicateIcon,
  CheckIcon,
} from '@heroicons/vue/24/outline';
import ProposalSectionsTab from '~/components/panel/proposal/ProposalSectionsTab.vue';
import { DEFAULT_HOSTING_PERCENT } from '~/stores/proposals_constants';
import TechnicalDocumentEditor from '~/components/BusinessProposal/admin/TechnicalDocumentEditor.vue';
import ProposalAnalytics from '~/components/BusinessProposal/admin/ProposalAnalytics.vue';
import ContractParamsModal from '~/components/BusinessProposal/admin/ContractParamsModal.vue';
import ProposalActionsModal from '~/components/BusinessProposal/admin/ProposalActionsModal.vue';
import ProposalMultiSendModal from '~/components/BusinessProposal/admin/ProposalMultiSendModal.vue';
import ProposalDocumentsTab from '~/components/BusinessProposal/admin/ProposalDocumentsTab.vue';
import ProposalEmailsTab from '~/components/BusinessProposal/admin/ProposalEmailsTab.vue';
import ProjectScheduleEditor from '~/components/BusinessProposal/admin/ProjectScheduleEditor.vue';
import JsonStatsPanel from '~/components/BusinessProposal/admin/JsonStatsPanel.vue';
import TabSplitLayout from '~/components/panel/TabSplitLayout.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { buildProposalItemLinkOptions, buildProposalModuleLinkOptions } from '~/utils/proposalModuleLinkOptions';
import { getProposalNextAction } from '~/utils/proposalNextAction';
import { toSlug } from '~/utils/slugify';
import { JSON_TEXTAREA_ROWS, makeJsonStats } from '~/utils/proposalJsonStats';
import DevChecklistTab from '~/components/panel/proposal/DevChecklistTab.vue';
import ProposalActivityTab from '~/components/panel/proposal/ProposalActivityTab.vue';
import ProposalJsonTab from '~/components/panel/proposal/ProposalJsonTab.vue';
import ProposalPromptTab from '~/components/panel/proposal/ProposalPromptTab.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';

const localePath = useLocalePath();
const { proposalEdit: tt } = useTooltipTexts();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const proposalStore = useProposalStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();
// Fed by ProposalSectionsTab's dirty-state-change emit; drives the
// route-leave / beforeunload / refresh guards below.
const sectionsDirty = ref(false);

const proposal = computed(() => proposalStore.currentProposal);

const proposalModeLinks = [
  { label: 'Propuesta completa', labelUrl: 'URL propuesta completa', mode: 'detailed' },
  { label: 'Detalle técnico', labelUrl: 'URL detalle técnico', mode: 'technical' },
];

const publicIdentifier = computed(
  () => proposal.value?.slug || proposal.value?.uuid || ''
);

const copied = ref(false);
function copyUrl() {
  const url = `${window.location.origin}/proposal/${publicIdentifier.value}`;
  navigator.clipboard.writeText(url).then(() => {
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  });
}

const copiedMode = ref(null);
function copyModeUrl(mode) {
  const url = `${window.location.origin}/proposal/${publicIdentifier.value}?mode=${mode}`;
  navigator.clipboard.writeText(url).then(() => {
    copiedMode.value = mode;
    setTimeout(() => { copiedMode.value = null; }, 2000);
  });
}

// Editable slug UI state
const slugDraft = ref('');
const slugError = ref('');
const slugSaving = ref(false);
const slugSaved = ref(false);
const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

watch(
  () => proposal.value?.slug,
  (value) => { slugDraft.value = value || ''; },
  { immediate: true },
);

function regenerateSlugFromName() {
  slugDraft.value = toSlug(proposal.value?.client_name);
  slugError.value = '';
}

async function saveSlug() {
  const value = (slugDraft.value || '').trim();
  slugError.value = '';
  slugSaved.value = false;
  if (value === (proposal.value?.slug || '')) return;
  if (value && !slugRegex.test(value)) {
    slugError.value = 'Solo minúsculas, números y guiones (sin espacios ni acentos).';
    return;
  }
  if (value.length > 120) {
    slugError.value = 'La URL personalizada no puede superar 120 caracteres.';
    return;
  }
  slugSaving.value = true;
  try {
    const result = await proposalStore.updateProposal(proposal.value.id, { slug: value });
    if (result?.success) {
      slugDraft.value = proposal.value?.slug || value;
      slugSaved.value = true;
      setTimeout(() => { slugSaved.value = false; }, 2000);
    } else {
      slugError.value = result?.errors?.slug?.[0]
        || result?.error
        || 'No se pudo guardar la URL personalizada.';
    }
  } finally {
    slugSaving.value = false;
  }
}
const allSections = computed(() =>
  [...(proposal.value?.sections || [])].sort((a, b) => a.order - b.order)
);

const technicalSection = computed(() =>
  allSections.value.find(s => s.section_type === 'technical_document') || null
);

const investmentSection = computed(() =>
  allSections.value.find(s => s.section_type === 'investment') || null
);

// Multiplier derived from the loaded proposal: effective / base. The backend
// computes effective_total_investment as base + Σ(base * pct_module/100), so
// the ratio is constant for a given module selection. Reusing it here keeps
// the % logic in a single place (backend) while letting the live form base
// drive the displayed effective total.
const effectiveTotalsMultiplier = computed(() => {
  const base = Number(proposal.value?.total_investment || 0);
  const effective = Number(proposal.value?.effective_total_investment || 0);
  if (base <= 0 || effective <= 0) return 1;
  return effective / base;
});

const effectiveTotalInvestment = computed(() => {
  const liveBase = Number(form.total_investment) || 0;
  return Math.round(liveBase * effectiveTotalsMultiplier.value);
});

const hasCustomizedEffectiveTotal = computed(() => {
  const liveBase = Number(form.total_investment) || 0;
  const effective = effectiveTotalInvestment.value;
  return liveBase > 0 && effective > 0 && Math.round(effective) !== Math.round(liveBase);
});

const technicalModuleLinkOptions = computed(() =>
  buildProposalModuleLinkOptions(proposal.value?.sections || []),
);

const technicalItemLinkOptions = computed(() =>
  buildProposalItemLinkOptions(proposal.value?.sections || []),
);

const validTabs =['general', 'emails', 'documents', 'schedule', 'development', 'sections', 'technical', 'prompt', 'json', 'activity', 'analytics'];
const activeTab = ref(validTabs.includes(route.query.tab) ? route.query.tab : 'general');
const technicalSubTab = ref('editor');
const hasSendEmailTab = computed(() =>
  ['sent', 'viewed', 'negotiating', 'accepted', 'rejected'].includes(proposal.value?.status),
);
const hasDocumentsTab = computed(() =>
  ['sent', 'viewed', 'negotiating', 'accepted', 'rejected'].includes(proposal.value?.status),
);
const hasProposalDocuments = computed(() =>
  ['sent', 'viewed', 'negotiating', 'accepted', 'rejected'].includes(proposal.value?.status),
);
const hasScheduleTab = computed(() =>
  ['accepted', 'finished'].includes(proposal.value?.status),
);
const hasDevTab = computed(() => proposal.value?.status === 'accepted');

const tabs = computed(() => {
  const base = [
    { id: 'general', label: 'General' },
  ];
  if (hasSendEmailTab.value) {
    base.push({ id: 'emails', label: 'Correos' });
  }
  if (hasDocumentsTab.value) {
    base.push({ id: 'documents', label: 'Documentos' });
  }
  if (hasScheduleTab.value) {
    base.push({ id: 'schedule', label: 'Cronograma' });
  }
  if (hasDevTab.value) {
    base.push({ id: 'development', label: 'Desarrollo' });
  }
  base.push(
    { id: 'sections', label: 'Secciones' },
    { id: 'technical', label: 'Det. técnico' },
    { id: 'prompt', label: 'Prompt Proposal' },
    { id: 'json', label: 'JSON' },
    { id: 'activity', label: 'Actividad' },
    { id: 'analytics', label: 'Analytics' },
  );
  return base;
});

// ── Actions menu (modal) ──
const showActionsModal = ref(false);
const showMultiSendModal = ref(false);

async function handleMultiSendSent(payload) {
  if (payload?.error) {
    const errors = payload.error;
    notify.error({
      title: 'No se pudo enviar el correo conjunto.',
      detail: errors?.error
        || (errors ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ') : ''),
    });
    return;
  }
  await refreshData();
  notify.success({
    title: `Correo enviado al cliente con ${payload?.count ?? 0} propuestas.`,
  });
}
const nextAction = computed(() => {
  const base = getProposalNextAction(proposal.value);
  if (!base) return null;
  const launchPending = base.key === 'launch'
    && (isLaunching.value || proposal.value?.platform_onboarding_status === 'pending');
  return {
    ...base,
    disabled: launchPending,
    label: launchPending ? 'Lanzando...' : base.label,
  };
});
function handleNextAction() {
  if (!nextAction.value || nextAction.value.disabled) return;
  const handlers = {
    send: handleSend,
    negotiate: () => openContractModal(false),
    approve: () => handleStatusChange('accepted'),
    launch: handleLaunchToPlatform,
    finish: handleMarkAsFinished,
  };
  handlers[nextAction.value.key]?.();
}

// ── Contract modal state ──
const showContractModal = ref(false);
const contractModalEditing = ref(false);

function openContractModal(editing = false) {
  contractModalEditing.value = editing;
  showContractModal.value = true;
}

async function handleContractConfirm(params) {
  showContractModal.value = false;
  let result;
  if (contractModalEditing.value) {
    result = await proposalStore.updateContractParams(proposal.value.id, params);
  } else {
    result = await proposalStore.saveContractAndNegotiate(proposal.value.id, params);
  }
  if (result.success) {
    proposal.value = result.data;
  }
}

async function handleStatusChange(newStatus) {
  const result = await proposalStore.updateProposalStatus(proposal.value.id, newStatus);
  if (result.success) {
    proposal.value = result.data;
    const ed = result.email_delivery;
    if (ed && ed.ok === false) {
      notify.warning({
        title: 'Estado actualizado',
        detail: ed.detail || 'No se pudo enviar el correo al cliente.',
      });
    }
  } else {
    notifyProposalFailure(result, 'No se pudo actualizar el estado');
  }
}

async function handleMarkAsFinished() {
  const confirmed = await requestConfirm({
    title: 'Marcar como finalizada',
    message: 'El proyecto pasará al estado Finalizada y se notificará al cliente por correo. ¿Deseas continuar?',
    variant: 'primary',
    confirmText: 'Marcar como finalizada',
    cancelText: 'Cancelar',
  });
  if (!confirmed) return;
  await handleStatusChange('finished');
}

let cancelOnboardingPoll = null;

async function handleLaunchToPlatform() {
  const alreadyOnboarded = !!proposal.value.platform_onboarding_completed_at;

  if (alreadyOnboarded) {
    const confirmed = await requestConfirm({
      title: 'Re-lanzar a Plataforma',
      message: 'El proyecto, entregables, requerimientos y archivos existentes serán eliminados y recreados desde cero. ¿Deseas continuar?',
      variant: 'danger',
      confirmText: 'Re-lanzar',
      cancelText: 'Cancelar',
    });
    if (!confirmed) return;
  }

  isLaunching.value = true;
  const result = await proposalStore.launchToPlatform(proposal.value.id, alreadyOnboarded);
  if (!result.success) {
    isLaunching.value = false;
    notify.error({
      title: result.errors?.error || 'Error al lanzar a la plataforma.',
    });
    return;
  }

  proposal.value = result.data;

  if (result.data.platform_onboarding_status === 'pending') {
    notify.success({ title: 'Onboarding en progreso...' });
    cancelOnboardingPoll = proposalStore.pollOnboardingStatus(
      proposal.value.id,
      (updated) => {
        proposal.value = updated;
        isLaunching.value = false;
        cancelOnboardingPoll = null;
        if (updated.platform_onboarding_status === 'completed') {
          notify.success({
            title: alreadyOnboarded ? 'Plataforma re-lanzada exitosamente.' : 'Propuesta lanzada a la plataforma.',
          });
        } else {
          notify.error({
            title: 'El onboarding falló. Revisa los logs del servidor.',
          });
        }
      },
    );
  } else {
    isLaunching.value = false;
    const succeeded = result.data.platform_onboarding_status === 'completed';
    notify.push({
      type: succeeded ? 'success' : 'error',
      title: succeeded
        ? (alreadyOnboarded ? 'Plataforma re-lanzada exitosamente.' : 'Propuesta lanzada a la plataforma.')
        : 'El onboarding falló. Revisa los logs del servidor.',
    });
  }
}

const technicalJsonRaw = ref('');
const technicalJsonError = ref('');

function refreshTechnicalJsonFromProposal() {
  const s = technicalSection.value;
  if (!s?.content_json) {
    technicalJsonRaw.value = '{}';
    return;
  }
  try {
    technicalJsonRaw.value = JSON.stringify(s.content_json, null, 2);
  } catch {
    technicalJsonRaw.value = '{}';
  }
  technicalJsonError.value = '';
}

async function handleApplyTechnicalJson() {
  technicalJsonError.value = '';
  const sid = technicalSection.value?.id;
  if (!sid) {
    technicalJsonError.value = 'No hay sección técnica.';
    return;
  }
  let parsed;
  try {
    parsed = JSON.parse(technicalJsonRaw.value.trim());
  } catch (e) {
    technicalJsonError.value = `JSON inválido: ${e.message}`;
    return;
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    technicalJsonError.value = 'El contenido debe ser un objeto JSON.';
    return;
  }
  const result = await proposalStore.updateSection(sid, { content_json: parsed });
  if (result.success) {
    notify.success({ title: 'Detalle técnico actualizado.' });
    await proposalStore.fetchProposal(proposal.value.id);
    refreshTechnicalJsonFromProposal();
  } else {
    notify.error({ title: 'No se pudo guardar.' });
  }
}

const isRefreshing = ref(false);
const notify = usePanelNotify();

// Notify a failed proposal action using the store's normalized error fields.
function notifyProposalFailure(result, fallbackTitle) {
  notify.error({
    title: result?.message || fallbackTitle,
    detail: result?.hint || '',
  });
}
const isLaunching = ref(false);
const syncPreviewVisible = ref(false);
const syncPreviewData = ref(null);
const syncApplying = ref(false);
const pendingSyncPayload = ref(null);
const investmentPaymentPercentages = ref([]);

const form = reactive({
  title: '',
  client_id: null,
  client_name: '',
  client_email: '',
  client_phone: '',
  client_company: '',
  project_type: '',
  market_type: '',
  project_type_custom: '',
  market_type_custom: '',
  language: 'es',
  total_investment: 0,
  currency: 'COP',
  hosting_percent: DEFAULT_HOSTING_PERCENT,
  hosting_discount_annual: 40,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  expires_at: '',
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
  automations_paused: true,
  email_intro: '',
  email_features: [],
  email_method_phases: [],
  email_signed_by: 'gustavo',
});

const DEFAULT_METHOD_PHASES = [
  { number: '01', title: 'Diagnóstico', duration: '', description: 'Mapeo de procesos y alcance final.' },
  { number: '02', title: 'Construcción', duration: '', description: 'Sprints con demo cada viernes.' },
  { number: '03', title: 'Lanzamiento', duration: '', description: 'Deploy, capacitación y soporte.' },
];

const MAX_EMAIL_FEATURES = 8;
function addEmailFeature() {
  if (form.email_features.length >= MAX_EMAIL_FEATURES) return;
  form.email_features = [...form.email_features, ''];
}
function removeEmailFeature(idx) {
  form.email_features = form.email_features.filter((_, i) => i !== idx);
}
function ensureMethodPhases() {
  if (!form.email_method_phases || form.email_method_phases.length === 0) {
    form.email_method_phases = DEFAULT_METHOD_PHASES.map((p) => ({ ...p }));
  }
}

// Preview modal state — see openEmailPreview() trigger in the email config section.
const PREVIEWABLE_EMAIL_TEMPLATES = [
  { key: 'proposal_sent_client', label: 'Propuesta enviada (master)' },
  { key: 'proposal_reminder', label: 'Recordatorio' },
  { key: 'proposal_urgency', label: 'Urgencia con descuento' },
  { key: 'proposal_urgency_no_discount', label: 'Urgencia sin descuento' },
  { key: 'proposal_accepted_client', label: 'Aceptación' },
  { key: 'proposal_finished_client', label: 'Finalización' },
  { key: 'proposal_rejected_client', label: 'Rechazo (agradecimiento)' },
  { key: 'proposal_negotiation_confirmation', label: 'Negociación' },
  { key: 'proposal_reengagement', label: 'Re-engagement post-rechazo' },
  { key: 'proposal_abandonment_followup', label: 'Seguimiento por abandono' },
  { key: 'proposal_investment_interest_followup', label: 'Seguimiento por inversión' },
  { key: 'proposal_scheduled_followup', label: 'Seguimiento programado' },
  { key: 'proposal_documents_sent', label: 'Documentos enviados' },
  { key: 'branded_email', label: 'Correo libre branded' },
];

const isPreviewOpen = ref(false);
const previewLoading = ref(false);
const previewError = ref('');
const previewHtml = ref('');
const previewTemplateKey = ref('proposal_sent_client');

async function loadPreview() {
  if (!proposal.value?.id) return;
  previewLoading.value = true;
  previewError.value = '';
  previewHtml.value = '';
  const result = await proposalStore.previewProposalEmail(proposal.value.id, {
    template_key: previewTemplateKey.value,
    email_features: form.email_features
      .map((f) => (typeof f === 'string' ? f.trim() : ''))
      .filter(Boolean),
    email_method_phases: form.email_method_phases.map((p) => ({
      number: (p.number || '').trim(),
      title: (p.title || '').trim(),
      duration: (p.duration || '').trim(),
      description: (p.description || '').trim(),
    })),
    email_signed_by: form.email_signed_by,
  });
  previewLoading.value = false;
  if (result.success) {
    previewHtml.value = result.html;
  } else {
    previewError.value = result.error;
  }
}

async function openEmailPreview() {
  isPreviewOpen.value = true;
  await loadPreview();
}

watch(previewTemplateKey, () => {
  if (isPreviewOpen.value) loadPreview();
});

// ── Discount offer (manual send with preview) ──────────────────────
const showDiscountModal = ref(false);
const discountPreviewHtml = ref('');
const discountPreviewLoading = ref(false);
const discountPreviewError = ref('');
const discountSending = ref(false);

async function loadDiscountPreview() {
  if (!proposal.value?.id) return;
  discountPreviewLoading.value = true;
  discountPreviewError.value = '';
  discountPreviewHtml.value = '';
  const result = await proposalStore.previewProposalEmail(proposal.value.id, {
    template_key: 'proposal_urgency',
  });
  discountPreviewLoading.value = false;
  if (result.success) {
    discountPreviewHtml.value = result.html;
  } else {
    discountPreviewError.value = result.error;
  }
}

async function openDiscountOfferModal() {
  showDiscountModal.value = true;
  await loadDiscountPreview();
}

async function confirmSendDiscountOffer() {
  if (!proposal.value?.id) return;
  discountSending.value = true;
  const result = await proposalStore.sendDiscountOffer(proposal.value.id);
  discountSending.value = false;
  if (result.success) {
    showDiscountModal.value = false;
    notify.success({ title: 'Oferta de descuento enviada al cliente.' });
  } else {
    notify.error({ title: result.message || 'No se pudo enviar la oferta.' });
  }
}

// True when the admin chose "create a new client" from the autocomplete: the
// backend must build a fresh UserProfile from the inline fields instead of
// editing the currently linked one.
const creatingNewClient = ref(false);

const DEFAULT_EXPIRY_DAYS = 21;
const padDate = (n) => String(n).padStart(2, '0');
function getExpiryDaysFromStr(datetimeStr) {
  if (!datetimeStr) return DEFAULT_EXPIRY_DAYS;
  const diff = new Date(datetimeStr) - Date.now();
  return Math.max(1, Math.round(diff / (24 * 60 * 60 * 1000)));
}
const expiryDaysInput = ref(getExpiryDaysFromStr(form.expires_at));
watch(() => form.expires_at, (val) => {
  expiryDaysInput.value = getExpiryDaysFromStr(val);
});
watch(expiryDaysInput, (days) => {
  const safeDays = Number.isInteger(days) && days > 0 ? days : DEFAULT_EXPIRY_DAYS;
  const expiry = new Date(Date.now() + safeDays * 24 * 60 * 60 * 1000);
  const dateStr = `${expiry.getFullYear()}-${padDate(expiry.getMonth() + 1)}-${padDate(expiry.getDate())}`;
  const timeStr = form.expires_at ? form.expires_at.slice(11, 16) : `${padDate(expiry.getHours())}:${padDate(expiry.getMinutes())}`;
  form.expires_at = `${dateStr}T${timeStr}`;
});

function onClientSelected(client) {
  if (!client) return;
  creatingNewClient.value = false;
  form.client_id = client.id;
  form.client_name = client.name || form.client_name;
  // Empty input is friendlier than a fake placeholder address; the badge already signals it.
  form.client_email = client.is_email_placeholder ? '' : client.email || '';
  form.client_phone = client.phone || form.client_phone;
  form.client_company = client.company || form.client_company;
}

function onCreateInlineClient(typedName) {
  creatingNewClient.value = true;
  form.client_id = null;
  form.client_name = typedName || '';
  // Drop the previously selected client's contact details so the new profile
  // isn't matched (by email) to that existing client.
  form.client_email = '';
  form.client_phone = '';
  form.client_company = '';
}

function parseSectionContentJson(section) {
  if (!section?.content_json) return {};
  if (typeof section.content_json === 'string') {
    try {
      return JSON.parse(section.content_json);
    } catch {
      return {};
    }
  }
  return section.content_json;
}

function parsePercentFromLabel(label) {
  if (!label) return null;
  const match = String(label).match(/(\d+(?:[.,]\d+)?)\s*%/);
  if (!match) return null;
  const parsed = Number(match[1].replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  const clamped = Math.min(100, Math.max(0, numeric));
  return Math.round(clamped * 100) / 100;
}

function formatPercent(value) {
  const normalized = normalizePercent(value);
  if (Number.isInteger(normalized)) return String(normalized);
  return normalized.toFixed(2).replace(/\.?0+$/, '');
}

function extractInvestmentPercentages(contentJson) {
  const paymentOptions = Array.isArray(contentJson?.paymentOptions) ? contentJson.paymentOptions : [];
  return paymentOptions
    .map(opt => parsePercentFromLabel(opt?.label))
    .filter(percent => percent != null)
    .map(percent => normalizePercent(percent));
}

function replaceOrPrefixPercent(label, percent, index) {
  const percentText = `${formatPercent(percent)}%`;
  const base = String(label || '').trim();
  if (!base) return `${percentText} pago ${index + 1}`;
  if (/(\d+(?:[.,]\d+)?)\s*%/.test(base)) {
    return base.replace(/(\d+(?:[.,]\d+)?)\s*%/, percentText);
  }
  return `${percentText} ${base}`;
}

function buildPaymentDescription(percent) {
  const total = Number(effectiveTotalInvestment.value) || 0;
  const amount = Math.round(total * normalizePercent(percent) / 100);
  return `$${amount.toLocaleString('es-CO')} ${form.currency || 'COP'}`;
}

const paymentAmounts = computed(() =>
  investmentPaymentPercentages.value.map(pct => buildPaymentDescription(pct))
);

function normalizeGeneralPaymentPercentage(index) {
  const current = investmentPaymentPercentages.value[index];
  investmentPaymentPercentages.value[index] = normalizePercent(current);
}

watch(
  () => parseSectionContentJson(investmentSection.value)?.paymentOptions,
  (paymentOptions) => {
    investmentPaymentPercentages.value = extractInvestmentPercentages({ paymentOptions });
  },
  { immediate: true, deep: true },
);

async function syncInvestmentPercentagesFromGeneral() {
  const section = investmentSection.value;
  if (!section?.id) return { success: true, skipped: true };

  const contentJson = parseSectionContentJson(section);
  const paymentOptions = Array.isArray(contentJson.paymentOptions) ? contentJson.paymentOptions : [];
  if (!paymentOptions.length || !investmentPaymentPercentages.value.length) {
    return { success: true, skipped: true };
  }

  let editablePercentIdx = 0;
  const nextPaymentOptions = paymentOptions.map((option, idx) => {
    if (parsePercentFromLabel(option?.label) == null) return option;
    const percent = investmentPaymentPercentages.value[editablePercentIdx];
    editablePercentIdx += 1;
    if (percent == null) return option;
    const normalized = normalizePercent(percent);
    return {
      ...option,
      label: replaceOrPrefixPercent(option?.label, normalized, idx),
      description: buildPaymentDescription(normalized),
    };
  });

  const changed = JSON.stringify(paymentOptions) !== JSON.stringify(nextPaymentOptions);
  if (!changed) return { success: true, skipped: true };

  const result = await proposalStore.updateSection(section.id, {
    content_json: {
      ...contentJson,
      paymentOptions: nextPaymentOptions,
    },
  });
  return result.success ? { success: true } : { success: false };
}

function hydrateFormFromProposal() {
  if (!proposal.value) return;
  Object.assign(form, {
    title: proposal.value.title,
    client_id: proposal.value.client?.id ?? null,
    client_name: proposal.value.client_name,
    client_email: proposal.value.client_email || '',
    client_phone: proposal.value.client_phone || '',
    client_company: proposal.value.client?.company || '',
    project_type: proposal.value.project_type || '',
    market_type: proposal.value.market_type || '',
    project_type_custom: proposal.value.project_type_custom || '',
    market_type_custom: proposal.value.market_type_custom || '',
    language: proposal.value.language || 'es',
    total_investment: Number(proposal.value.total_investment),
    currency: proposal.value.currency,
    hosting_percent: proposal.value.hosting_percent ?? DEFAULT_HOSTING_PERCENT,
    hosting_discount_annual: proposal.value.hosting_discount_annual ?? 40,
    hosting_discount_semiannual: proposal.value.hosting_discount_semiannual ?? 20,
    hosting_discount_quarterly: proposal.value.hosting_discount_quarterly ?? 10,
    expires_at: proposal.value.expires_at
      ? proposal.value.expires_at.slice(0, 16)
      : '',
    reminder_days: proposal.value.reminder_days,
    urgency_reminder_days: proposal.value.urgency_reminder_days ?? 15,
    discount_percent: proposal.value.discount_percent ?? 0,
    automations_paused: proposal.value.automations_paused ?? true,
    email_intro: proposal.value.email_intro || '',
    email_features: Array.isArray(proposal.value.email_features) ? [...proposal.value.email_features] : [],
    email_method_phases: Array.isArray(proposal.value.email_method_phases) && proposal.value.email_method_phases.length
      ? proposal.value.email_method_phases.map((p) => ({ ...p }))
      : DEFAULT_METHOD_PHASES.map((p) => ({ ...p })),
    email_signed_by: proposal.value.email_signed_by || 'gustavo',
  });
  creatingNewClient.value = false;
}

onMounted(async () => {
  const id = route.params.id;
  await proposalStore.fetchProposal(id);
  hydrateFormFromProposal();
  window.addEventListener('beforeunload', warnUnsavedBeforeUnload);
});

const UNSAVED_CONFIRM = {
  title: 'Cambios sin guardar',
  message: 'Hay secciones con cambios sin guardar. Si continúas, se perderán.',
  variant: 'warning',
  confirmText: 'Continuar sin guardar',
  cancelText: 'Seguir editando',
};

function warnUnsavedBeforeUnload(e) {
  if (sectionsDirty.value) {
    e.preventDefault();
    e.returnValue = '';
  }
}

onBeforeRouteLeave(async () => {
  if (!sectionsDirty.value) return true;
  return await requestConfirm(UNSAVED_CONFIRM);
});

async function refreshData() {
  // fetchProposal re-hydrates every open SectionEditor via its deep watch,
  // silently clobbering unsaved edits — confirm before refreshing. The
  // refetch re-baselines the editors, which clears the flags organically.
  if (sectionsDirty.value) {
    const ok = await requestConfirm(UNSAVED_CONFIRM);
    if (!ok) return;
  }
  isRefreshing.value = true;
  try {
    await proposalStore.fetchProposal(route.params.id);
    hydrateFormFromProposal();
  } finally {
    isRefreshing.value = false;
  }
}

usePanelRefresh(refreshData);

onBeforeUnmount(() => {
  if (cancelOnboardingPoll) cancelOnboardingPoll();
  window.removeEventListener('beforeunload', warnUnsavedBeforeUnload);
});

async function toggleAutomationsPaused() {
  form.automations_paused = !form.automations_paused;
  const result = await proposalStore.updateProposal(proposal.value.id, {
    automations_paused: form.automations_paused,
  });
  if (result.success) {
    notify.success({ title: form.automations_paused ? 'Automatizaciones pausadas.' : 'Automatizaciones reactivadas.' });
  } else {
    form.automations_paused = !form.automations_paused;
    notify.error({ title: 'Error al cambiar automatizaciones.' });
  }
}

function sanitizeEmailMetadata(payload) {
  payload.email_features = (payload.email_features || [])
    .map((f) => (typeof f === 'string' ? f.trim() : ''))
    .filter(Boolean);
  payload.email_method_phases = (payload.email_method_phases || []).map((p) => ({
    number: (p.number || '').trim(),
    title: (p.title || '').trim(),
    duration: (p.duration || '').trim(),
    description: (p.description || '').trim(),
  }));
  return payload;
}

async function handleUpdate() {
  const payload = sanitizeEmailMetadata({ ...form });
  if (creatingNewClient.value) {
    payload.create_new_client = true;
    payload.propagate_client_updates = false;
    payload.client_id = null;
  } else {
    payload.propagate_client_updates = true;
  }
  if (payload.expires_at) {
    const d = new Date(payload.expires_at);
    payload.expires_at = isNaN(d.getTime()) ? null : d.toISOString();
  } else {
    payload.expires_at = null;
  }
  const result = await proposalStore.updateProposal(proposal.value.id, payload);
  if (result.success) {
    const syncResult = await syncInvestmentPercentagesFromGeneral();
    if (syncResult.success) {
      notify.success({ title: 'Propuesta actualizada.' });
    } else {
      notify.error({ title: 'Se actualizó la propuesta, pero falló la sincronización de porcentajes de inversión.' });
    }
  } else {
    const errors = result.errors;
    notify.error({
      title: 'Error al actualizar.',
      detail: errors
        ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
        : '',
    });
  }
}

const showSendChecklist = ref(false);
const scorecardData = ref(null);
const scorecardLoading = ref(false);

const sendChecklist = computed(() => {
  if (scorecardData.value?.checks) {
    return scorecardData.value.checks.map(c => ({
      label: c.label,
      pass: c.passed,
      blocker: c.blocker,
    }));
  }
  // Fallback to local checks if scorecard hasn't loaded
  return [
    { label: 'Email del cliente configurado', pass: !!form.client_email?.trim(), blocker: true },
    { label: 'Nombre del cliente', pass: !!form.client_name?.trim(), blocker: true },
    { label: 'Inversión > $0', pass: Number(form.total_investment) > 0, blocker: true },
    { label: 'Fecha de expiración futura', pass: !!form.expires_at && new Date(form.expires_at) > new Date(), blocker: true },
    { label: 'Al menos 1 sección habilitada', pass: allSections.value?.some(s => s.is_enabled), blocker: true },
  ];
});

const allChecksPassing = computed(() => {
  if (scorecardData.value) {
    return scorecardData.value.can_send !== false;
  }
  return sendChecklist.value.filter(c => c.blocker).every(c => c.pass);
});

async function handleSend() {
  showSendChecklist.value = true;
  scorecardLoading.value = true;
  try {
    const result = await proposalStore.fetchScorecard(proposal.value.id);
    if (result.success) {
      scorecardData.value = result.data;
    } else {
      notify.warning({
        title: 'No se pudo cargar el scorecard.',
        detail: 'Se muestran las verificaciones locales.',
      });
    }
  } catch (_e) { /* use local fallback */ }
  scorecardLoading.value = false;
}

async function confirmSend() {
  showSendChecklist.value = false;
  const result = await proposalStore.sendProposal(proposal.value.id);
  if (result.success) {
    const ed = result.email_delivery;
    if (ed && ed.ok === false) {
      notify.warning({
        title: 'Propuesta marcada como enviada',
        detail: ed.detail || 'No se pudo enviar el correo al cliente.',
        action: { label: 'Reenviar', handler: () => handleResend() },
      });
    } else {
      notify.success({ title: 'Propuesta enviada al cliente' });
    }
  } else {
    notifyProposalFailure(result, 'No se pudo enviar la propuesta');
  }
}

function handleResend() {
  requestConfirm({
    title: 'Re-enviar propuesta',
    message: '¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración.',
    variant: 'info',
    confirmText: 'Re-enviar',
    onConfirm: async () => {
      const result = await proposalStore.resendProposal(proposal.value.id);
      if (result.success) {
        const ed = result.email_delivery;
        if (ed && ed.ok === false) {
          notify.warning({
            title: 'Reenvío registrado',
            detail: ed.detail || 'No se pudo enviar el correo al cliente.',
          });
        } else {
          notify.success({ title: 'Propuesta re-enviada al cliente' });
        }
      } else {
        notifyProposalFailure(result, 'No se pudo re-enviar la propuesta');
      }
    },
  });
}

async function toggleTechnicalSectionEnabled() {
  const s = technicalSection.value;
  if (!s?.id) return;
  const willEnable = !s.is_enabled;
  const result = await proposalStore.updateSection(s.id, { is_enabled: willEnable });
  if (result.success) {
    notify.success({ title: willEnable ? 'Sección técnica habilitada.' : 'Sección técnica deshabilitada.' });
  } else {
    notify.error({ title: 'No se pudo actualizar la sección técnica.' });
  }
}

async function handleToggleActive() {
  const result = await proposalStore.toggleProposalActive(proposal.value.id);
  if (result.success) {
    const label = result.data.is_active ? 'activada' : 'desactivada';
    notify.success({ title: `Propuesta ${label}.` });
  } else {
    notify.error({ title: 'Error al cambiar el estado.' });
  }
}

// Save handler for the TECHNICAL tab only — commercial sections save inside
// ProposalSectionsTab. Accepted proposals route through the sync preview.
async function handleSaveSection({ sectionId, payload }) {
  const isAccepted = proposal.value?.status === 'accepted';

  if (isAccepted) {
    const previewResult = await proposalStore.previewSync(sectionId, payload.content_json);
    if (!previewResult.success) {
      notify.error({ title: 'No se pudo calcular la vista previa de sincronización.' });
      return;
    }
    if (!previewResult.data.has_project) {
      const r = await proposalStore.updateSection(sectionId, payload);
      notify.push(r.success
        ? { type: 'success', title: 'Sección técnica guardada.' }
        : { type: 'error', title: 'Error al guardar.' });
      return;
    }
    syncPreviewData.value = previewResult.data;
    pendingSyncPayload.value = { sectionId, payload };
    syncPreviewVisible.value = true;
    return;
  }

  const r = await proposalStore.updateSection(sectionId, payload);
  if (!r.success) {
    notifyProposalFailure(r, 'No se pudo guardar la sección');
  }
}

async function handleSyncConfirm() {
  syncApplying.value = true;
  const { sectionId, payload } = pendingSyncPayload.value;
  const result = await proposalStore.applySync(sectionId, payload.content_json);
  syncApplying.value = false;
  syncPreviewVisible.value = false;
  syncPreviewData.value = null;
  pendingSyncPayload.value = null;
  notify.push(result.success
    ? { type: 'success', title: 'Sección técnica guardada y proyecto sincronizado.' }
    : { type: 'error', title: 'Error al aplicar la sincronización.' });
}

function handleSyncCancel() {
  syncPreviewVisible.value = false;
  syncPreviewData.value = null;
  pendingSyncPayload.value = null;
}

async function handleSyncHostingPercent(percent) {
  if (form.hosting_percent !== percent) {
    form.hosting_percent = percent;
    await proposalStore.updateProposal(proposal.value.id, { hosting_percent: percent });
  }
}

// Must match Investment.vue's hostingAnnualAmount / computedBillingTiers so admin preview
// shows the exact same numbers the client will see (avoids rounding drift).
// Client-facing basis is the effective total (base + admin-default additional
// modules), same input the client's "Inversión Total" line uses.
const hostingAnnualAmount = computed(() => {
  const effective = Number(effectiveTotalInvestment.value);
  const basis = effective > 0 ? effective : Number(form.total_investment) || 0;
  const percent = Number(form.hosting_percent) || 0;
  return Math.round(basis * percent / 100);
});
const hostingMonthlyBase = computed(() =>
  Math.round(hostingAnnualAmount.value / 12)
);
function hostingMonthlyWithDiscount(discountPercent) {
  return Math.round(hostingMonthlyBase.value * (100 - (discountPercent || 0)) / 100);
}
function hostingPeriodTotal(discountPercent, months) {
  return hostingMonthlyWithDiscount(discountPercent) * months;
}

function formatInvestment(value, currency = 'COP') {
  if (!value) return '';
  const num = Number(value);
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' ' + currency;
}

function statusClass(status) {
  const map = {
    draft: 'bg-surface-raised text-text-muted',
    sent: 'bg-info-soft text-info-strong',
    viewed: 'bg-success-soft text-success-strong',
    accepted: 'bg-primary-soft text-text-brand',
    rejected: 'bg-danger-soft text-danger-strong',
    expired: 'bg-warning-soft text-warning-strong',
  };
  return map[status] || 'bg-surface-raised text-text-muted';
}

// --- JSON tab (export/import live in ProposalJsonTab) ---
const TECHNICAL_EXPECTED_KEYS = [
  'purpose', 'stack', 'architecture', 'dataModel', 'growthReadiness',
  'epics', 'apiSummary', 'apiDomains', 'integrations', 'environmentsNote',
  'environments', 'security', 'performanceQuality', 'backupsNote',
  'quality', 'decisions',
];

const technicalJsonParsed = computed(() => {
  const raw = technicalJsonRaw.value.trim();
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
});

const technicalJsonSource = computed(
  () => technicalJsonParsed.value || technicalSection.value?.content_json || null,
);

const technicalJsonStats = makeJsonStats({
  sourceRef: technicalJsonSource,
  rawStringRef: technicalJsonRaw,
  expectedKeys: TECHNICAL_EXPECTED_KEYS,
  updatedAtRef: computed(() => proposal.value?.updated_at),
});

function handleJsonApplied() {
  // The store already refreshed currentProposal; resync the General form.
  hydrateFormFromProposal();
}

watch(activeTab, (newTab) => {
  if (newTab === 'technical') {
    refreshTechnicalJsonFromProposal();
  }
});

watch(technicalSubTab, (sub) => {
  if (activeTab.value === 'technical' && sub === 'json') {
    refreshTechnicalJsonFromProposal();
  }
});

</script>
