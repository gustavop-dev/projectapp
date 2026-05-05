<template>
  <div>
    <PanelToast />

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
          class="text-xs px-2 py-0.5 rounded-full font-medium bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200 whitespace-nowrap"
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
            <div class="flex-1 min-w-[260px] flex items-stretch rounded-lg border border-border-default dark:border-white/[0.08] bg-surface-raised focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-focus-ring/30">
              <span class="px-3 flex items-center text-xs text-text-subtle border-r border-border-default dark:border-white/[0.08] select-none">/proposal/</span>
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
              class="px-3 py-2 text-xs font-medium rounded-lg border border-border-default dark:border-white/[0.08] text-text-muted hover:border-border-default"
              :title="'Regenerar desde el nombre del cliente'"
              @click="regenerateSlugFromName"
            >
              Regenerar
            </button>
          </div>
          <p v-if="slugError" class="text-xs text-rose-500 mt-2">{{ slugError }}</p>
          <p v-else class="text-xs text-text-subtle mt-2">
            Solo minúsculas, números y guiones. El cliente verá esta URL en el enlace.
          </p>
        </div>

        <div
          class="mb-4 rounded-xl border border-emerald-200/70 dark:border-emerald-500/20 bg-primary-soft dark:bg-primary/[0.06] px-4 py-3 sm:px-5 sm:py-4 text-sm"
          aria-label="Identificación y estado de la propuesta"
        >
          <span class="inline-flex items-center gap-1 mb-3 px-2 py-0.5 rounded-full bg-primary-soft dark:bg-primary/15 text-[10px] font-medium uppercase tracking-wider text-text-brand">
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
                  <CheckIcon v-else class="w-3.5 h-3.5 text-emerald-500" />
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
                    <CheckIcon v-else class="w-3.5 h-3.5 text-emerald-500" />
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
                class="text-xs text-amber-700 dark:text-amber-300 mt-1.5"
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
          <div v-if="investmentSection" class="bg-primary-soft border border-emerald-200 dark:border-emerald-700/30 rounded-xl px-4 py-3">
            <label class="block text-sm font-medium text-emerald-900 dark:text-emerald-200 mb-2">Porcentajes de pago (sección Inversión)</label>
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
            <div v-if="form.hosting_percent > 0 && form.total_investment > 0" class="mt-3 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-700/30 rounded-xl overflow-hidden">
              <div class="px-4 py-2 text-[11px] uppercase tracking-wider text-blue-600 dark:text-blue-300/70 border-b border-blue-100 dark:border-blue-900/30">
                Precio que verá el cliente (por mes)
              </div>
              <div class="grid grid-cols-[1fr_auto_auto] gap-x-4 text-sm divide-y divide-blue-100 dark:divide-blue-900/30">
                <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">Mensual</div>
                <div class="px-4 py-2 text-blue-800 dark:text-blue-200 font-semibold text-right whitespace-nowrap">
                  ${{ hostingMonthlyBase.toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-blue-500 dark:text-blue-300/60 text-right whitespace-nowrap">facturado mensual</div>

                <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">
                  Trimestral
                  <span v-if="form.hosting_discount_quarterly" class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_quarterly }}% dcto)</span>
                </div>
                <div class="px-4 py-2 font-semibold text-right whitespace-nowrap"
                     :class="form.hosting_discount_quarterly ? 'text-text-brand' : 'text-blue-800 dark:text-blue-200'">
                  ${{ hostingMonthlyWithDiscount(form.hosting_discount_quarterly).toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-blue-500 dark:text-blue-300/60 text-right whitespace-nowrap">
                  total ${{ hostingPeriodTotal(form.hosting_discount_quarterly, 3).toLocaleString() }} / 3 meses
                </div>

                <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">
                  Semestral
                  <span v-if="form.hosting_discount_semiannual" class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_semiannual }}% dcto)</span>
                </div>
                <div class="px-4 py-2 font-semibold text-right whitespace-nowrap"
                     :class="form.hosting_discount_semiannual ? 'text-text-brand' : 'text-blue-800 dark:text-blue-200'">
                  ${{ hostingMonthlyWithDiscount(form.hosting_discount_semiannual).toLocaleString() }} {{ form.currency }}/mes
                </div>
                <div class="px-4 py-2 text-[11px] text-blue-500 dark:text-blue-300/60 text-right whitespace-nowrap">
                  total ${{ hostingPeriodTotal(form.hosting_discount_semiannual, 6).toLocaleString() }} / 6 meses
                </div>

                <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">☁️ Anual (referencia)</div>
                <div class="px-4 py-2 text-blue-800 dark:text-blue-200 font-semibold text-right whitespace-nowrap">
                  ${{ hostingAnnualAmount.toLocaleString() }} {{ form.currency }}
                </div>
                <div class="px-4 py-2 text-[11px] text-blue-500 dark:text-blue-300/60 text-right whitespace-nowrap">sin descuento</div>
              </div>
            </div>
            <p class="text-xs text-text-subtle mt-1">Sincronizado automáticamente con el Plan de Hosting que ve el cliente en "Tu inversión y cómo pagar".</p>
          </div>
          <div data-testid="general-finance-discounts-card" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
              class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-100 dark:border-amber-500/20"
            >
              <span class="text-amber-700 dark:text-amber-300 text-xs font-medium">
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
        <PromptSubTabsPanel v-model="promptSubTab">
          <template #commercial>
          <p class="text-sm text-text-muted mb-6">
            Este prompt se usa con IA (ChatGPT, Claude, etc.) para generar propuestas comerciales personalizadas a partir del JSON plantilla.
          </p>

          <!-- Action bar -->
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <template v-if="!promptIsEditing">
              <BaseButton variant="secondary" size="md" @click="startEditPrompt">
                <PencilIcon class="w-4 h-4" />
                Editar
              </BaseButton>
              <BaseButton variant="secondary" size="md" @click="handleCopyPrompt">
                <DocumentDuplicateIcon class="w-4 h-4" />
                {{ promptCopied ? '¡Copiado!' : 'Copiar' }}
              </BaseButton>
              <BaseButton variant="secondary" size="md" @click="promptDownload">
                <ArrowDownTrayIcon class="w-4 h-4" />
                Descargar .md
              </BaseButton>
              <BaseButton
                v-if="promptText !== promptDefault"
                variant="secondary"
                size="md"
                class="!text-danger-strong"
                @click="handleResetPrompt"
              >
                Restaurar original
              </BaseButton>
            </template>
            <template v-else>
              <BaseButton variant="primary" size="md" @click="saveEditPrompt">
                Guardar cambios
              </BaseButton>
              <BaseButton variant="ghost" size="md" @click="cancelEditPrompt">
                Cancelar
              </BaseButton>
            </template>
          </div>

          <div v-if="promptIsEditing" class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
            <textarea
              v-model="promptEditBuffer"
              rows="30"
              class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-text-default bg-transparent border-0 outline-none resize-y focus:ring-0"
            />
          </div>

          <div v-else class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
            <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
              <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ promptText }}</pre>
            </div>
          </div>

          <p v-if="promptText !== promptDefault" class="text-xs text-amber-600 mt-3">
            Este prompt ha sido personalizado. Usa "Restaurar original" para volver al valor por defecto.
          </p>
          </template>

          <template #technical>
          <p class="text-sm text-text-muted mb-6">
            Prompt para generar solo la clave <code class="text-xs bg-surface-raised px-1 rounded">technicalDocument</code> del JSON (arquitectura, módulos del producto, requerimientos, integraciones, etc.). Sin narrativa comercial ni precios.
          </p>
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <template v-if="!technicalPromptIsEditing">
              <BaseButton variant="secondary" size="md" @click="startEditTechnicalPrompt">
                <PencilIcon class="w-4 h-4" />
                Editar
              </BaseButton>
              <BaseButton variant="secondary" size="md" @click="handleCopyTechnicalPrompt">
                <DocumentDuplicateIcon class="w-4 h-4" />
                {{ technicalPromptCopied ? '¡Copiado!' : 'Copiar' }}
              </BaseButton>
              <BaseButton variant="secondary" size="md" @click="technicalPromptDownload">
                <ArrowDownTrayIcon class="w-4 h-4" />
                Descargar .md
              </BaseButton>
              <BaseButton
                v-if="technicalPromptText !== technicalPromptDefault"
                variant="secondary"
                size="md"
                class="!text-danger-strong"
                @click="handleResetTechnicalPrompt"
              >
                Restaurar original
              </BaseButton>
            </template>
            <template v-else>
              <BaseButton variant="primary" size="md" @click="saveEditTechnicalPrompt">
                Guardar cambios
              </BaseButton>
              <BaseButton variant="ghost" size="md" @click="cancelEditTechnicalPrompt">
                Cancelar
              </BaseButton>
            </template>
          </div>
          <div v-if="technicalPromptIsEditing" class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
            <textarea
              v-model="technicalPromptEditBuffer"
              rows="28"
              class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-text-default bg-transparent border-0 outline-none resize-y focus:ring-0"
            />
          </div>
          <div v-else class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
            <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
              <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ technicalPromptText }}</pre>
            </div>
          </div>
          <p v-if="technicalPromptText !== technicalPromptDefault" class="text-xs text-amber-600 mt-3">
            Prompt técnico personalizado. «Restaurar original» vuelve al texto por defecto.
          </p>
          </template>
        </PromptSubTabsPanel>
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
        <TabSplitLayout>
          <template #main>
        <!-- Current JSON (read-only) -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h3 class="text-sm font-medium text-text-default">JSON de la propuesta</h3>
              <p class="text-xs text-text-subtle dark:text-green-light/40 mt-0.5">Representación JSON completa — se actualiza al guardar cambios en otras pestañas.</p>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <BaseButton variant="secondary" size="sm" :disabled="jsonExportLoading" @click="refreshExportJson">
                <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': jsonExportLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Actualizar
              </BaseButton>
              <BaseButton variant="secondary" size="sm" @click="copyExportJson">
                <DocumentDuplicateIcon class="w-3.5 h-3.5" />
                {{ jsonCopied ? '¡Copiado!' : 'Copiar' }}
              </BaseButton>
              <BaseButton variant="secondary" size="sm" @click="downloadExportJson">
                <ArrowDownTrayIcon class="w-3.5 h-3.5" />
                Descargar
              </BaseButton>
            </div>
          </div>

          <div v-if="jsonExportLoading" class="text-center py-8 text-text-subtle text-sm">
            Cargando JSON...
          </div>
          <template v-else>
            <JsonStatsPanel class="mb-4" :stats="proposalJsonStats" test-id="proposal-json-stats" />
            <textarea
              :value="exportJsonString"
              readonly
              data-testid="proposal-export-json-textarea"
              :rows="JSON_TEXTAREA_ROWS"
              class="w-full px-4 py-3 border border-border-default dark:border-white/[0.08] rounded-xl text-xs font-mono leading-relaxed
                     bg-surface-raised text-text-default outline-none resize-y cursor-text select-all"
            />
          </template>
        </div>

          </template>

          <template #aside>
        <!-- Import JSON -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
          <h3 class="text-sm font-medium text-text-default mb-1">Importar JSON</h3>
          <p class="text-xs text-text-subtle mb-4">Pega o sube un JSON para reemplazar el contenido de la propuesta (metadata + secciones).</p>

          <div class="flex items-center gap-3 mb-3">
            <label
              class="inline-flex items-center gap-2 px-3 py-1.5 border border-border-default dark:border-white/[0.08] rounded-lg text-xs
                     text-text-default hover:bg-surface-raised cursor-pointer transition-colors"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Subir .json
              <input type="file" accept=".json" class="hidden" @change="handleJsonFileUpload" />
            </label>
            <span v-if="jsonImportFileName" class="text-xs text-text-muted">{{ jsonImportFileName }}</span>
          </div>

          <textarea
            v-model="jsonImportRaw"
            data-testid="proposal-import-json-textarea"
            :rows="JSON_TEXTAREA_ROWS"
            placeholder='Pega aquí el JSON completo de la propuesta...'
            class="bg-input-bg w-full px-4 py-3 border border-border-default dark:border-white/[0.08]  rounded-xl text-xs font-mono leading-relaxed
                   focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none resize-y"
            @input="parseImportJson"
          />

          <!-- Parse error -->
          <div v-if="jsonImportError" class="mt-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
            {{ jsonImportError }}
          </div>

          <!-- Preview -->
          <div v-if="jsonImportParsed && !jsonImportError" class="mt-3 bg-primary-soft border border-emerald-200 dark:border-emerald-700/30 rounded-lg px-4 py-3">
            <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <span><span class="text-text-muted">Cliente:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.clientName }}</span></span>
              <span><span class="text-text-muted">Secciones:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.sectionCount }}</span></span>
              <span v-if="jsonImportPreview.epicCount != null"><span class="text-text-muted">Módulos (téc.):</span> <span class="font-medium text-text-default">{{ jsonImportPreview.epicCount }}</span></span>
              <span v-if="jsonImportPreview.investment"><span class="text-text-muted">Inversión:</span> <span class="font-medium text-text-default">{{ jsonImportPreview.investment }}</span></span>
            </div>
          </div>

          <!-- Legacy format warning -->
          <LegacyFormatWarning
            v-if="jsonImportParsed && !jsonImportError"
            :issues="jsonImportLegacyIssues"
            :field-labels="LEGACY_FIELD_LABELS"
            action-label="Descarga la versión corregida y úsala para actualizar la propuesta:"
            @download="downloadMigratedProposalJson(jsonImportParsed)"
          />

          <!-- Apply button -->
          <div v-if="jsonImportParsed && !jsonImportError && !jsonImportLegacyIssues.length" class="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              :disabled="proposalStore.isUpdating"
              class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl font-medium text-sm
                     hover:bg-primary transition-colors shadow-sm disabled:opacity-50 disabled:cursor-wait"
              @click="handleApplyImportJson"
            >
              <svg v-if="proposalStore.isUpdating" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ proposalStore.isUpdating ? 'Aplicando...' : 'Aplicar JSON' }}
            </button>
            <p class="text-xs text-text-subtle dark:text-green-light/40">Esto reemplazará la metadata y todas las secciones de la propuesta.</p>
          </div>

        </div>
          </template>
        </TabSplitLayout>
      </div>

      <!-- Tab: Activity -->
      <div v-show="activeTab === 'activity'" class="max-w-5xl mx-auto">
        <!-- Log activity form -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 mb-6">
          <div class="flex items-center gap-1.5 mb-3">
            <h3 class="text-sm font-semibold text-text-default">Registrar actividad</h3>
            <BaseTooltip position="right">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-text-subtle hover:text-text-muted transition-colors" />
              </template>
              {{ tt.logActivity }}
            </BaseTooltip>
          </div>
          <div class="flex flex-col sm:flex-row gap-3">
            <BaseSelect v-model="activityForm.change_type" size="sm" class="sm:w-40">
              <option value="call">📞 Llamada</option>
              <option value="meeting">🤝 Reunión</option>
              <option value="followup">📩 Seguimiento</option>
              <option value="note">📝 Nota</option>
            </BaseSelect>
            <BaseInput
              v-model="activityForm.description"
              type="text"
              size="sm"
              placeholder="Descripción de la actividad..."
              class="flex-1"
              @keydown.enter.prevent="submitActivity"
            />
            <button type="button" :disabled="!activityForm.description.trim() || isSubmittingActivity" class="px-4 py-2 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary transition-colors disabled:opacity-50 whitespace-nowrap" @click="submitActivity">
              {{ isSubmittingActivity ? 'Guardando...' : 'Agregar' }}
            </button>
          </div>
        </div>

        <!-- Timeline -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-5">
          <div class="flex items-center gap-1.5 mb-4">
            <h3 class="text-sm font-semibold text-text-default">Historial de actividad</h3>
            <BaseTooltip position="right">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-text-subtle hover:text-text-muted transition-colors" />
              </template>
              {{ tt.activityHistory }}
            </BaseTooltip>
          </div>
          <div v-if="!changeLogs.length" class="text-center py-8 text-sm text-text-subtle dark:text-green-light/40">Sin actividad registrada.</div>
          <div v-else class="relative pl-6 space-y-0">
            <div class="absolute left-[9px] top-2 bottom-2 w-px bg-surface-raised" />
            <div v-for="log in changeLogs" :key="log.id" class="relative pb-5 last:pb-0">
              <div class="absolute -left-6 top-1 w-[18px] h-[18px] rounded-full border-2 border-border-default shadow-sm flex items-center justify-center text-[10px]" :class="activityDotClass(log.change_type)">
                {{ activityIcon(log.change_type) }}
              </div>
              <div class="ml-2">
                <div class="flex items-baseline gap-2">
                  <span class="text-xs font-semibold" :class="activityLabelClass(log.change_type)">{{ activityLabel(log.change_type) }}</span>
                  <span class="text-[10px] text-text-subtle dark:text-green-light/40">{{ formatLogDate(log.created_at) }}</span>
                </div>
                <!-- eslint-disable-next-line vue/no-v-html -->
                <p class="text-sm text-text-muted/60 mt-0.5" v-html="formatActivityDescription(log)"></p>
              </div>
            </div>
          </div>
        </div>
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
          <p v-if="!technicalSection" class="text-sm text-amber-600 dark:text-amber-300 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-700/30 rounded-lg px-4 py-3">
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
        <!-- F10: Section completeness indicator -->
        <div v-if="allSections.length" class="mb-4 bg-surface rounded-xl shadow-sm border border-border-muted px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-1">
              <span class="text-xs font-semibold text-text-muted uppercase tracking-wider">Completitud de secciones</span>
              <BaseTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-text-subtle hover:text-text-muted transition-colors" />
                </template>
                {{ tt.sectionCompleteness }}
              </BaseTooltip>
            </div>
            <span class="text-sm font-bold" :class="sectionCompleteness >= 80 ? 'text-text-brand' : sectionCompleteness >= 50 ? 'text-amber-600' : 'text-red-500'">
              {{ sectionCompleteness }}%
            </span>
          </div>
          <div class="w-full h-2 bg-surface-raised rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="sectionCompleteness >= 80 ? 'bg-primary' : sectionCompleteness >= 50 ? 'bg-amber-500' : 'bg-red-400'"
              :style="{ width: sectionCompleteness + '%' }"
            />
          </div>
          <p class="text-[11px] text-text-subtle mt-1.5">
            {{ sectionsWithContent }}/{{ enabledSectionsCount }} secciones comerciales habilitadas tienen contenido (sin contar «Det. técnico» — pestaña dedicada).
          </p>
        </div>

        <div class="space-y-3">
          <div
            v-for="section in commercialSections"
            :key="section.id"
            class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden"
          >
            <!-- Section header -->
            <div
              :data-testid="`section-header-${section.section_type}`"
              class="px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-2 cursor-pointer hover:bg-surface-raised transition-colors"
              @click="toggleSection(section.id)"
            >
              <div class="flex items-center gap-4">
                <span class="text-xs text-text-subtle font-mono w-6">{{ section.order + 1 }}</span>
                <span class="text-sm font-medium text-text-default">{{ section.title }}</span>
                <span class="text-xs text-text-subtle">({{ section.section_type }})</span>
              </div>
              <div class="flex items-center gap-3">
                <label class="flex items-center gap-2 text-xs" @click.stop>
                  <input
                    type="checkbox"
                    :checked="section.is_enabled"
                    class="rounded border-gray-300 text-text-brand focus:ring-focus-ring/30"
                    @change="toggleEnabled(section)"
                  />
                  <span class="text-text-muted">Visible</span>
                </label>
                <svg
                  class="w-4 h-4 text-text-subtle transition-transform"
                  :class="{ 'rotate-180': expandedSections.has(section.id) }"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <!-- Section content editor (expanded) -->
            <div v-if="expandedSections.has(section.id)" class="border-t border-border-muted px-3 sm:px-6 py-4 sm:py-6">
              <SectionEditor
                :section="section"
                :proposalData="proposal"
                :module-link-options="technicalModuleLinkOptions"
                :all-sections="allSections"
                @save="handleSaveSection"
                @syncHostingPercent="handleSyncHostingPercent"
              />
            </div>
          </div>
        </div>

        <!-- Sticky send bar for sections tab -->
        <div v-if="proposal.client_email" class="sticky bottom-0 mt-4 bg-surface/95 backdrop-blur-sm border border-border-muted rounded-xl shadow-lg px-5 py-3 flex items-center justify-between gap-3 z-10">
          <div class="flex items-center gap-2 text-xs text-text-muted">
            <a :href="'/proposal/' + proposal.uuid + '?preview=1'" target="_blank" class="text-text-brand hover:underline">Preview →</a>
          </div>
          <div class="flex items-center gap-3">
            <BaseButton
              v-if="proposal.status === 'draft'"
              variant="primary"
              size="md"
              class="!bg-blue-600 hover:!bg-blue-700"
              @click="handleSend"
            >
              📤 Enviar al Cliente
            </BaseButton>
            <BaseButton
              v-else-if="['sent', 'viewed'].includes(proposal.status)"
              variant="primary"
              size="md"
              class="!bg-blue-600 hover:!bg-blue-700"
              @click="handleResend"
            >
              🔄 Re-enviar al Cliente
            </BaseButton>
          </div>
        </div>
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
          class="!bg-blue-600 hover:!bg-blue-700"
          :disabled="!allChecksPassing || scorecardLoading"
          @click="confirmSend"
        >
          Enviar al Cliente
        </BaseButton>
      </div>
    </BaseModal>

    <!-- Floating refresh button -->
    <button
      type="button"
      class="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-primary hover:bg-primary text-white shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:opacity-50 flex items-center justify-center"
      :disabled="isRefreshing"
      :title="isRefreshing ? 'Actualizando...' : 'Actualizar datos'"
      @click="refreshData"
    >
      <svg class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import {
  QuestionMarkCircleIcon,
  PencilIcon,
  DocumentDuplicateIcon,
  ArrowDownTrayIcon,
  CheckIcon,
} from '@heroicons/vue/24/outline';
import SectionEditor from '~/components/BusinessProposal/admin/SectionEditor.vue';
import TechnicalDocumentEditor from '~/components/BusinessProposal/admin/TechnicalDocumentEditor.vue';
import ProposalAnalytics from '~/components/BusinessProposal/admin/ProposalAnalytics.vue';
import ContractParamsModal from '~/components/BusinessProposal/admin/ContractParamsModal.vue';
import ProposalActionsModal from '~/components/BusinessProposal/admin/ProposalActionsModal.vue';
import ProposalMultiSendModal from '~/components/BusinessProposal/admin/ProposalMultiSendModal.vue';
import ProposalDocumentsTab from '~/components/BusinessProposal/admin/ProposalDocumentsTab.vue';
import ProposalEmailsTab from '~/components/BusinessProposal/admin/ProposalEmailsTab.vue';
import ProjectScheduleEditor from '~/components/BusinessProposal/admin/ProjectScheduleEditor.vue';
import JsonStatsPanel from '~/components/BusinessProposal/admin/JsonStatsPanel.vue';
import PromptSubTabsPanel from '~/components/panel/PromptSubTabsPanel.vue';
import TabSplitLayout from '~/components/panel/TabSplitLayout.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useSellerPrompt } from '~/composables/useSellerPrompt';
import { useTechnicalPrompt } from '~/composables/useTechnicalPrompt';
import { buildProposalModuleLinkOptions } from '~/utils/proposalModuleLinkOptions';
import { getProposalNextAction } from '~/utils/proposalNextAction';
import { toSlug } from '~/utils/slugify';
import { detectLegacyTechnicalFormat, downloadMigratedProposalJson, LEGACY_FIELD_LABELS } from '~/utils/proposalJsonMigration';
import LegacyFormatWarning from '~/components/panel/LegacyFormatWarning.vue';
import PanelToast from '~/components/panel/PanelToast.vue';
import { usePanelToast } from '~/composables/usePanelToast';

const localePath = useLocalePath();
const { proposalEdit: tt } = useTooltipTexts();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const proposalStore = useProposalStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

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

const commercialSections = computed(() =>
  allSections.value.filter(s => s.section_type !== 'technical_document')
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

const enabledSectionsCount = computed(() =>
  commercialSections.value.filter(s => s.is_enabled).length
);

const sectionsWithContent = computed(() => {
  return commercialSections.value.filter(s => {
    if (!s.is_enabled) return false;
    let cj = s.content_json;
    if (typeof cj === 'string') {
      try { cj = JSON.parse(cj); } catch { cj = null; }
    }
    return cj && typeof cj === 'object' && Object.keys(cj).length > 0;
  }).length;
});

const sectionCompleteness = computed(() => {
  if (enabledSectionsCount.value === 0) return 0;
  return Math.round(sectionsWithContent.value / enabledSectionsCount.value * 100);
});

const validTabs = ['general', 'emails', 'documents', 'schedule', 'sections', 'technical', 'prompt', 'json', 'activity', 'analytics'];
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
    showToast({
      type: 'error',
      text: errors?.error
        || (errors ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ') : 'No se pudo enviar el correo conjunto.'),
    });
    return;
  }
  await refreshData();
  showToast({
    type: 'success',
    text: `Correo enviado al cliente con ${payload?.count ?? 0} propuestas.`,
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
    showToast({
      type: 'error',
      text: result.errors?.error || 'Error al lanzar a la plataforma.',
    });
    return;
  }

  proposal.value = result.data;

  if (result.data.platform_onboarding_status === 'pending') {
    showToast({ type: 'success', text: 'Onboarding en progreso...' });
    cancelOnboardingPoll = proposalStore.pollOnboardingStatus(
      proposal.value.id,
      (updated) => {
        proposal.value = updated;
        isLaunching.value = false;
        cancelOnboardingPoll = null;
        if (updated.platform_onboarding_status === 'completed') {
          showToast({
            type: 'success',
            text: alreadyOnboarded ? 'Plataforma re-lanzada exitosamente.' : 'Propuesta lanzada a la plataforma.',
          });
        } else {
          showToast({
            type: 'error',
            text: 'El onboarding falló. Revisa los logs del servidor.',
          });
        }
      },
    );
  } else {
    isLaunching.value = false;
    const succeeded = result.data.platform_onboarding_status === 'completed';
    showToast({
      type: succeeded ? 'success' : 'error',
      text: succeeded
        ? (alreadyOnboarded ? 'Plataforma re-lanzada exitosamente.' : 'Propuesta lanzada a la plataforma.')
        : 'El onboarding falló. Revisa los logs del servidor.',
    });
  }
}

// ── Prompt Proposal ──
const {
  promptText,
  isEditing: promptIsEditing,
  DEFAULT_PROMPT: promptDefault,
  loadSavedPrompt,
  savePrompt: promptSave,
  resetPrompt: promptReset,
  copyPrompt: promptCopy,
  downloadPrompt: promptDownload,
} = useSellerPrompt();

const promptEditBuffer = ref('');
const promptCopied = ref(false);

function startEditPrompt() {
  promptEditBuffer.value = promptText.value;
  promptIsEditing.value = true;
}
function cancelEditPrompt() {
  promptIsEditing.value = false;
}
function saveEditPrompt() {
  promptSave(promptEditBuffer.value);
  promptIsEditing.value = false;
  showToast({ type: 'success', text: 'Prompt comercial guardado.' });
}
async function handleCopyPrompt() {
  await promptCopy();
  promptCopied.value = true;
  setTimeout(() => { promptCopied.value = false; }, 2000);
}
function handleResetPrompt() {
  promptReset();
}

const promptSubTab = ref('commercial');

const {
  promptText: technicalPromptText,
  isEditing: technicalPromptIsEditing,
  DEFAULT_PROMPT: technicalPromptDefault,
  loadSavedPrompt: loadTechnicalPrompt,
  savePrompt: technicalPromptSave,
  resetPrompt: technicalPromptReset,
  copyPrompt: technicalPromptCopy,
  downloadPrompt: technicalPromptDownload,
} = useTechnicalPrompt();

const technicalPromptEditBuffer = ref('');
const technicalPromptCopied = ref(false);

function startEditTechnicalPrompt() {
  technicalPromptEditBuffer.value = technicalPromptText.value;
  technicalPromptIsEditing.value = true;
}
function cancelEditTechnicalPrompt() {
  technicalPromptIsEditing.value = false;
}
function saveEditTechnicalPrompt() {
  technicalPromptSave(technicalPromptEditBuffer.value);
  technicalPromptIsEditing.value = false;
  showToast({ type: 'success', text: 'Prompt técnico guardado.' });
}
async function handleCopyTechnicalPrompt() {
  await technicalPromptCopy();
  technicalPromptCopied.value = true;
  setTimeout(() => { technicalPromptCopied.value = false; }, 2000);
}
function handleResetTechnicalPrompt() {
  technicalPromptReset();
  technicalPromptIsEditing.value = false;
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
    showToast({ type: 'success', text: 'Detalle técnico actualizado.' });
    await proposalStore.fetchProposal(proposal.value.id);
    refreshTechnicalJsonFromProposal();
  } else {
    showToast({ type: 'error', text: 'No se pudo guardar.' });
  }
}

const isRefreshing = ref(false);
const expandedSections = ref(new Set());
const { showToast } = usePanelToast();
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
  hosting_percent: 40,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  expires_at: '',
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
  automations_paused: true,
  email_intro: '',
});

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
  form.client_id = client.id;
  form.client_name = client.name || form.client_name;
  // Empty input is friendlier than a fake placeholder address; the badge already signals it.
  form.client_email = client.is_email_placeholder ? '' : client.email || '';
  form.client_phone = client.phone || form.client_phone;
  form.client_company = client.company || form.client_company;
}

function onCreateInlineClient(typedName) {
  form.client_id = null;
  if (typedName) {
    form.client_name = typedName;
  }
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
    hosting_percent: proposal.value.hosting_percent ?? 40,
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
  });
}

onMounted(async () => {
  const id = route.params.id;
  await proposalStore.fetchProposal(id);
  loadSavedPrompt();
  loadTechnicalPrompt();
  hydrateFormFromProposal();
});

async function refreshData() {
  isRefreshing.value = true;
  try {
    await proposalStore.fetchProposal(route.params.id);
    hydrateFormFromProposal();
  } finally {
    isRefreshing.value = false;
  }
}

onBeforeUnmount(() => {
  if (cancelOnboardingPoll) cancelOnboardingPoll();
});

async function toggleAutomationsPaused() {
  form.automations_paused = !form.automations_paused;
  const result = await proposalStore.updateProposal(proposal.value.id, {
    automations_paused: form.automations_paused,
  });
  if (result.success) {
    showToast({ type: 'success', text: form.automations_paused ? 'Automatizaciones pausadas.' : 'Automatizaciones reactivadas.' });
  } else {
    form.automations_paused = !form.automations_paused;
    showToast({ type: 'error', text: 'Error al cambiar automatizaciones.' });
  }
}

async function handleUpdate() {
  const payload = { ...form, propagate_client_updates: true };
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
      showToast({ type: 'success', text: 'Propuesta actualizada.' });
    } else {
      showToast({ type: 'error', text: 'Se actualizó la propuesta, pero falló la sincronización de porcentajes de inversión.' });
    }
  } else {
    const errors = result.errors;
    showToast({
      type: 'error',
      text: errors
        ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
        : 'Error al actualizar.',
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
    }
  } catch (_e) { /* use local fallback */ }
  scorecardLoading.value = false;
}

async function confirmSend() {
  showSendChecklist.value = false;
  const result = await proposalStore.sendProposal(proposal.value.id);
  if (result.success) {
    showToast({ type: 'success', text: 'Propuesta enviada al cliente.' });
  } else {
    showToast({ type: 'error', text: result.errors?.error || 'Error al enviar.' });
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
        showToast({ type: 'success', text: 'Propuesta re-enviada al cliente.' });
      } else {
        showToast({ type: 'error', text: result.errors?.error || 'Error al re-enviar.' });
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
    showToast({ type: 'success', text: willEnable ? 'Sección técnica habilitada.' : 'Sección técnica deshabilitada.' });
  } else {
    showToast({ type: 'error', text: 'No se pudo actualizar la sección técnica.' });
  }
}

async function handleToggleActive() {
  const result = await proposalStore.toggleProposalActive(proposal.value.id);
  if (result.success) {
    const label = result.data.is_active ? 'activada' : 'desactivada';
    showToast({ type: 'success', text: `Propuesta ${label}.` });
  } else {
    showToast({ type: 'error', text: 'Error al cambiar el estado.' });
  }
}

function toggleSection(id) {
  if (expandedSections.value.has(id)) {
    expandedSections.value.delete(id);
  } else {
    expandedSections.value.add(id);
  }
  expandedSections.value = new Set(expandedSections.value);
}

function collapseSection(id) {
  expandedSections.value.delete(id);
  expandedSections.value = new Set(expandedSections.value);
}

async function toggleEnabled(section) {
  await proposalStore.updateSection(section.id, { is_enabled: !section.is_enabled });
}

async function handleSaveSection({ sectionId, payload }) {
  const section = proposal.value?.sections?.find((s) => s.id === sectionId);
  const isAccepted = proposal.value?.status === 'accepted';
  const isTechDoc = section?.section_type === 'technical_document';

  if (isTechDoc && isAccepted) {
    const previewResult = await proposalStore.previewSync(sectionId, payload.content_json);
    if (!previewResult.success) {
      showToast({ type: 'error', text: 'No se pudo calcular la vista previa de sincronización.' });
      return;
    }
    if (!previewResult.data.has_project) {
      const r = await proposalStore.updateSection(sectionId, payload);
      showToast(r.success
        ? { type: 'success', text: 'Sección técnica guardada.' }
        : { type: 'error', text: 'Error al guardar.' });
      if (r.success) collapseSection(sectionId);
      return;
    }
    syncPreviewData.value = previewResult.data;
    pendingSyncPayload.value = { sectionId, payload };
    syncPreviewVisible.value = true;
    return;
  }

  const r = await proposalStore.updateSection(sectionId, payload);
  if (r.success) collapseSection(sectionId);
}

async function handleSyncConfirm() {
  syncApplying.value = true;
  const { sectionId, payload } = pendingSyncPayload.value;
  const result = await proposalStore.applySync(sectionId, payload.content_json);
  syncApplying.value = false;
  syncPreviewVisible.value = false;
  syncPreviewData.value = null;
  pendingSyncPayload.value = null;
  showToast(result.success
    ? { type: 'success', text: 'Sección técnica guardada y proyecto sincronizado.' }
    : { type: 'error', text: 'Error al aplicar la sincronización.' });
  if (result.success) collapseSection(sectionId);
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
    sent: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300',
    viewed: 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-300',
    accepted: 'bg-primary-soft text-text-brand',
    rejected: 'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300',
    expired: 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-300',
  };
  return map[status] || 'bg-surface-raised text-text-muted';
}

// --- JSON tab ---
const EXPECTED_SECTION_KEYS = [
  'general', 'executiveSummary', 'contextDiagnostic', 'conversionStrategy',
  'designUX', 'creativeSupport', 'developmentStages', 'processMethodology',
  'valueAddedModules', 'functionalRequirements', 'timeline', 'investment',
  'proposalSummary', 'finalNote', 'nextSteps', 'technicalDocument',
];

const TECHNICAL_EXPECTED_KEYS = [
  'purpose', 'stack', 'architecture', 'dataModel', 'growthReadiness',
  'epics', 'apiSummary', 'apiDomains', 'integrations', 'environmentsNote',
  'environments', 'security', 'performanceQuality', 'backupsNote',
  'quality', 'decisions',
];

const JSON_TEXTAREA_ROWS = 18;

const jsonExportLoading = ref(false);
const exportJsonData = ref(null);
const jsonCopied = ref(false);

const jsonImportRaw = ref('');
const jsonImportParsed = ref(null);
const jsonImportError = ref('');
const jsonImportFileName = ref('');
const jsonImportLegacyIssues = ref([]);

const exportJsonString = computed(() => {
  if (!exportJsonData.value) return '';
  return JSON.stringify(exportJsonData.value, null, 2);
});

function countPresentKeys(source, expectedKeys) {
  if (!source || typeof source !== 'object' || Array.isArray(source)) return 0;
  return expectedKeys.filter((key) => key in source).length;
}

function calculateProgress(completed, total) {
  if (!total) return 0;
  return Math.round((completed / total) * 100);
}

function formatJsonSize(raw) {
  const normalized = typeof raw === 'string' ? raw : JSON.stringify(raw || {}, null, 2);
  const bytes = new Blob([normalized]).size;
  if (bytes < 1024) return `${bytes} B`;
  const kilobytes = bytes / 1024;
  return `${kilobytes >= 10 ? kilobytes.toFixed(0) : kilobytes.toFixed(1)} KB`;
}

function formatDateTime(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function makeJsonStats({ sourceRef, rawStringRef, expectedKeys }) {
  return computed(() => {
    const source = sourceRef.value;
    const sectionCount = countPresentKeys(source, expectedKeys);
    const rawString = rawStringRef?.value || (source ? JSON.stringify(source, null, 2) : '');
    return {
      sectionCount,
      progress: calculateProgress(sectionCount, expectedKeys.length),
      size: formatJsonSize(rawString),
      updatedAt: formatDateTime(proposal.value?.updated_at),
    };
  });
}

const proposalJsonStats = makeJsonStats({
  sourceRef: exportJsonData,
  rawStringRef: exportJsonString,
  expectedKeys: EXPECTED_SECTION_KEYS,
});

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
});

const jsonImportPreview = computed(() => {
  if (!jsonImportParsed.value) return {};
  const p = jsonImportParsed.value;
  const clientName = p.general?.clientName || '';
  const sectionCount = EXPECTED_SECTION_KEYS.filter((k) => k in p).length;
  const investment = p.investment?.totalInvestment || '';
  const epics = p.technicalDocument?.epics;
  const epicCount = Array.isArray(epics) ? epics.length : null;
  return { clientName, sectionCount, investment, epicCount };
});

async function refreshExportJson() {
  if (!proposal.value?.id) return;
  jsonExportLoading.value = true;
  try {
    const result = await proposalStore.exportProposalJSON(proposal.value.id);
    if (result.success) {
      exportJsonData.value = result.data;
    }
  } finally {
    jsonExportLoading.value = false;
  }
}

async function copyExportJson() {
  if (!exportJsonString.value) return;
  try {
    await navigator.clipboard.writeText(exportJsonString.value);
    jsonCopied.value = true;
    setTimeout(() => { jsonCopied.value = false; }, 2000);
  } catch (e) {
    console.error('Copy failed:', e);
  }
}

function downloadExportJson() {
  if (!exportJsonString.value || !proposal.value) return;
  const blob = new Blob([exportJsonString.value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proposal-${proposal.value.uuid || proposal.value.id}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function parseImportJson() {
  jsonImportError.value = '';
  jsonImportParsed.value = null;
  jsonImportLegacyIssues.value = [];

  const raw = jsonImportRaw.value.trim();
  if (!raw) return;

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    jsonImportError.value = 'JSON inválido. Revisa la sintaxis.';
    return;
  }

  if (typeof parsed !== 'object' || Array.isArray(parsed)) {
    jsonImportError.value = 'El JSON debe ser un objeto, no un array.';
    return;
  }

  if (!parsed.general || !parsed.general.clientName) {
    jsonImportError.value = 'El JSON debe incluir "general" con "clientName".';
    return;
  }

  jsonImportLegacyIssues.value = detectLegacyTechnicalFormat(parsed).issues;

  jsonImportParsed.value = parsed;
}

function handleJsonFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  jsonImportFileName.value = file.name;

  const reader = new FileReader();
  reader.onload = (e) => {
    jsonImportRaw.value = e.target.result;
    parseImportJson();
  };
  reader.readAsText(file);
}

function parseInvestmentString(str) {
  if (!str) return 0;
  if (typeof str === 'number') return str;
  const cleaned = String(str).replace(/[^0-9]/g, '');
  return cleaned ? Number(cleaned) : 0;
}

function handleApplyImportJson() {
  if (!jsonImportParsed.value || !proposal.value?.id) return;

  requestConfirm({
    title: 'Aplicar JSON',
    message: 'Esto reemplazará la metadata y todas las secciones de la propuesta. ¿Continuar?',
    variant: 'warning',
    confirmText: 'Aplicar',
    cancelText: 'Cancelar',
    onConfirm: async () => {
      const sections = { ...jsonImportParsed.value };
      delete sections._meta;
      delete sections._seller_prompt;

      const meta = jsonImportParsed.value._meta || {};
      const payload = {
        title: meta.title || proposal.value.title,
        client_name: jsonImportParsed.value.general?.clientName || proposal.value.client_name,
        client_email: meta.client_email || proposal.value.client_email || '',
        client_phone: meta.client_phone || proposal.value.client_phone || '',
        project_type: meta.project_type || proposal.value.project_type || '',
        market_type: meta.market_type || proposal.value.market_type || '',
        project_type_custom: meta.project_type_custom || proposal.value.project_type_custom || '',
        market_type_custom: meta.market_type_custom || proposal.value.market_type_custom || '',
        language: meta.language || proposal.value.language || 'es',
        total_investment: parseInvestmentString(meta.total_investment || jsonImportParsed.value.investment?.totalInvestment) || Number(proposal.value.total_investment) || 0,
        currency: meta.currency || jsonImportParsed.value.investment?.currency || proposal.value.currency || 'COP',
        expires_at: meta.expires_at || (proposal.value.expires_at ? proposal.value.expires_at : null),
        reminder_days: meta.reminder_days || proposal.value.reminder_days || 10,
        urgency_reminder_days: meta.urgency_reminder_days || proposal.value.urgency_reminder_days || 15,
        discount_percent: meta.discount_percent ?? proposal.value.discount_percent ?? 0,
        sections,
      };

      const result = await proposalStore.updateProposalFromJSON(proposal.value.id, payload);
      if (result.success) {
        showToast({ type: 'success', text: 'Propuesta actualizada desde JSON.' });
        jsonImportRaw.value = '';
        jsonImportParsed.value = null;
        jsonImportFileName.value = '';
        jsonImportLegacyIssues.value = [];

        // Sync local form with updated proposal
        if (proposal.value) {
          Object.assign(form, {
            title: proposal.value.title,
            client_name: proposal.value.client_name,
            client_email: proposal.value.client_email || '',
            client_phone: proposal.value.client_phone || '',
            project_type: proposal.value.project_type || '',
            market_type: proposal.value.market_type || '',
            project_type_custom: proposal.value.project_type_custom || '',
            market_type_custom: proposal.value.market_type_custom || '',
            language: proposal.value.language || 'es',
            total_investment: Number(proposal.value.total_investment),
            currency: proposal.value.currency,
            hosting_percent: proposal.value.hosting_percent ?? 40,
            hosting_discount_semiannual: proposal.value.hosting_discount_semiannual ?? 20,
            hosting_discount_quarterly: proposal.value.hosting_discount_quarterly ?? 10,
            expires_at: proposal.value.expires_at ? proposal.value.expires_at.slice(0, 16) : '',
            reminder_days: proposal.value.reminder_days,
            urgency_reminder_days: proposal.value.urgency_reminder_days ?? 15,
            discount_percent: proposal.value.discount_percent ?? 0,
            automations_paused: proposal.value.automations_paused ?? true,
          });
        }

        // Refresh the export JSON view
        await refreshExportJson();
      } else {
        const errors = result.errors;
        showToast({
          type: 'error',
          text: errors
            ? (typeof errors === 'object'
              ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
              : String(errors))
            : 'Error al aplicar el JSON.',
        });
      }
    },
  });
}

// Auto-load JSON export when switching to json tab
watch(activeTab, (newTab) => {
  if (newTab === 'json' && proposal.value?.id) {
    refreshExportJson();
  }
  if (newTab === 'technical') {
    refreshTechnicalJsonFromProposal();
  }
});

watch(technicalSubTab, (sub) => {
  if (activeTab.value === 'technical' && sub === 'json') {
    refreshTechnicalJsonFromProposal();
  }
});

// --- Activity timeline ---
const activityForm = reactive({ change_type: 'note', description: '' });
const isSubmittingActivity = ref(false);
const changeLogs = computed(() => proposal.value?.change_logs || []);

async function submitActivity() {
  if (!activityForm.description.trim() || isSubmittingActivity.value) return;
  isSubmittingActivity.value = true;
  try {
    const result = await proposalStore.logActivity(proposal.value.id, {
      change_type: activityForm.change_type,
      description: activityForm.description.trim(),
    });
    if (result.success) {
      activityForm.description = '';
      await proposalStore.fetchProposal(proposal.value.id);
      showToast({ type: 'success', text: 'Actividad registrada.' });
    } else {
      showToast({ type: 'error', text: 'No se pudo registrar la actividad.' });
    }
  } finally {
    isSubmittingActivity.value = false;
  }
}

const AC = {
  gray:    { dot: 'bg-surface-raised',    text: 'text-text-muted' },
  grayMd:  { dot: 'bg-surface-raised',    text: 'text-text-muted' },
  blue:    { dot: 'bg-blue-100 dark:bg-blue-900/30',    text: 'text-blue-600 dark:text-blue-400' },
  green:   { dot: 'bg-green-100 dark:bg-green-900/30',   text: 'text-green-600 dark:text-green-400' },
  emerald: { dot: 'bg-primary-soft', text: 'text-text-brand' },
  red:     { dot: 'bg-red-100 dark:bg-red-900/30',     text: 'text-red-600 dark:text-red-400' },
  yellow:  { dot: 'bg-yellow-100 dark:bg-yellow-900/30',  text: 'text-yellow-600 dark:text-yellow-400' },
  purple:  { dot: 'bg-purple-100 dark:bg-purple-900/30',  text: 'text-purple-600 dark:text-purple-400' },
  indigo:  { dot: 'bg-indigo-100 dark:bg-indigo-900/30',  text: 'text-indigo-600 dark:text-indigo-400' },
  orange:  { dot: 'bg-orange-100 dark:bg-orange-900/30',  text: 'text-orange-600 dark:text-orange-400' },
  sky:     { dot: 'bg-sky-100 dark:bg-sky-900/30',     text: 'text-sky-600 dark:text-sky-400' },
  amber:   { dot: 'bg-amber-100 dark:bg-amber-900/30',   text: 'text-amber-600 dark:text-amber-400' },
};
const activityMeta = {
  created:       { icon: '✨', label: 'Creada',                   ...AC.gray },
  updated:       { icon: '✏️', label: 'Editada',                  ...AC.gray },
  sent:          { icon: '📤', label: 'Enviada',                  ...AC.blue },
  viewed:        { icon: '👁',  label: 'Vista',                    ...AC.green },
  accepted:      { icon: '✅', label: 'Aceptada',                 ...AC.emerald },
  rejected:      { icon: '❌', label: 'Rechazada',                ...AC.red },
  resent:        { icon: '🔁', label: 'Re-enviada',               ...AC.blue },
  expired:       { icon: '⏰', label: 'Expirada',                 ...AC.yellow },
  duplicated:    { icon: '📋', label: 'Duplicada',                ...AC.gray },
  commented:     { icon: '💬', label: 'Comentario',               ...AC.purple },
  negotiating:   { icon: '🤝', label: 'Negociando',               ...AC.indigo },
  reengagement:  { icon: '🔔', label: 'Reengagement',             ...AC.orange },
  call:          { icon: '📞', label: 'Llamada',                  ...AC.sky },
  meeting:       { icon: '🤝', label: 'Reunión',                  ...AC.indigo },
  followup:      { icon: '📩', label: 'Seguimiento',              ...AC.amber },
  note:          { icon: '📝', label: 'Nota',                     ...AC.grayMd },
  calc_confirmed:{ icon: '🧮', label: 'Calculadora confirmada',   ...AC.emerald },
  calc_abandoned:{ icon: '🧮', label: 'Calculadora abandonada',   ...AC.red },
  calc_followup: { icon: '🧮', label: 'Seguimiento calculadora',  ...AC.orange },
  auto_archived: { icon: '📦', label: 'Auto-archivada',           ...AC.gray },
  status_change: { icon: '🔄', label: 'Cambio de estado',         ...AC.blue },
  cond_accepted: { icon: '⚠️', label: 'Aceptación condicional',   ...AC.amber },
  req_clicked:   { icon: '🔗', label: 'Requerimiento consultado', ...AC.sky },
  email_sent:    { icon: '📧', label: 'Correo enviado',           ...AC.emerald },
};
function activityIcon(type) { return activityMeta[type]?.icon || '•'; }
function activityLabel(type) { return activityMeta[type]?.label || type; }
function activityDotClass(type) { return activityMeta[type]?.dot || AC.gray.dot; }
function activityLabelClass(type) { return activityMeta[type]?.text || AC.gray.text; }

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function fmtDate(val) {
  if (!val) return '(vacío)';
  const d = new Date(val);
  if (isNaN(d.getTime())) return escapeHtml(val);
  return escapeHtml(d.toLocaleString('es-CO', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }));
}

function formatActivityDescription(log) {
  const desc = log.description || '';

  // Calculator events — plain text (no v-html needed for counts)
  if (log.change_type === 'calc_abandoned' || log.change_type === 'calc_confirmed') {
    try {
      const data = JSON.parse(desc);
      const selected = data.selected || [];
      const deselected = data.deselected || [];
      const total = data.total;
      const elapsed = data.elapsed_seconds || 0;
      const mins = Math.floor(elapsed / 60);
      const secs = Math.round(elapsed % 60);
      const timeStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
      const totalStr = total != null ? `<strong>$${Number(total).toLocaleString('es-CO')}</strong>` : '';
      if (log.change_type === 'calc_confirmed') {
        return `Confirmó <strong>${selected.length}</strong> módulo${selected.length !== 1 ? 's' : ''}`
          + (totalStr ? ` — Total: ${totalStr}` : '')
          + (elapsed ? ` — Tiempo en calculadora: <strong>${timeStr}</strong>` : '');
      }
      return `Abandonó calculadora con <strong>${selected.length}</strong> módulo${selected.length !== 1 ? 's' : ''} seleccionado${selected.length !== 1 ? 's' : ''}`
        + (deselected.length ? `, <strong>${deselected.length}</strong> desmarcado${deselected.length !== 1 ? 's' : ''}` : '')
        + (totalStr ? ` — Total: ${totalStr}` : '')
        + (elapsed ? ` — Tiempo: <strong>${timeStr}</strong>` : '');
    } catch (_e) {
      return escapeHtml(desc);
    }
  }

  // Requirement clicked
  if (log.change_type === 'req_clicked') {
    try {
      const data = JSON.parse(desc);
      return `Cliente consultó <strong>${escapeHtml(data.group_title || 'módulo')}</strong>`;
    } catch (_e) { return escapeHtml(desc); }
  }

  // Field updates with old/new values
  const FIELD_LABELS_MAP = {
    title: 'Título', total_investment: 'Inversión total', currency: 'Moneda',
    client_name: 'Nombre del cliente', client_email: 'Email del cliente',
    status: 'Estado', expires_at: 'Fecha de expiración',
    followup_scheduled_at: 'Seguimiento programado',
  };
  if (log.change_type === 'updated' && log.field_name) {
    const fieldLabel = FIELD_LABELS_MAP[log.field_name] || log.field_name;
    const isCurrency = log.field_name === 'total_investment';
    const isDate = ['expires_at', 'followup_scheduled_at'].includes(log.field_name);
    const fmtCurrency = (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return escapeHtml(val || '(vacío)');
      return `<strong>$${num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</strong>`;
    };
    const oldDisplay = isCurrency ? fmtCurrency(log.old_value) : isDate ? fmtDate(log.old_value) : escapeHtml(log.old_value || '(vacío)');
    const newDisplay = isCurrency ? fmtCurrency(log.new_value) : isDate ? `<strong>${fmtDate(log.new_value)}</strong>` : `<strong>${escapeHtml(log.new_value || '(vacío)')}</strong>`;
    return `<strong>${escapeHtml(fieldLabel)}</strong>: ${oldDisplay} → ${newDisplay}`;
  }

  // Status change
  if (log.change_type === 'status_change' && log.old_value && log.new_value) {
    return `<strong>Estado</strong>: ${escapeHtml(log.old_value)} → <strong>${escapeHtml(log.new_value)}</strong>`;
  }

  // Client comment — bold the comment body
  if (log.change_type === 'commented') {
    const prefix = 'Client left a comment: ';
    if (desc.startsWith(prefix)) {
      return `Client left a comment: <strong>${escapeHtml(desc.slice(prefix.length))}</strong>`;
    }
    return escapeHtml(desc);
  }

  // Negotiating — bold the comment when present
  if (log.change_type === 'negotiating') {
    const key = ' Comment: ';
    const idx = desc.indexOf(key);
    if (idx !== -1) {
      return `${escapeHtml(desc.slice(0, idx))} Comment: <strong>${escapeHtml(desc.slice(idx + key.length))}</strong>`;
    }
    return escapeHtml(desc);
  }

  // Rejected — bold the rejection reason when present
  if (log.change_type === 'rejected') {
    const key = ' Reason: ';
    const idx = desc.indexOf(key);
    if (idx !== -1) {
      return `${escapeHtml(desc.slice(0, idx))} Reason: <strong>${escapeHtml(desc.slice(idx + key.length))}</strong>`;
    }
    return escapeHtml(desc);
  }

  // Conditional acceptance — bold the condition text
  if (log.change_type === 'cond_accepted') {
    const prefix = 'Conditional acceptance: ';
    if (desc.startsWith(prefix)) {
      return `Conditional acceptance: <strong>${escapeHtml(desc.slice(prefix.length))}</strong>`;
    }
    return escapeHtml(desc);
  }

  // Accepted — bold condition when present
  if (log.change_type === 'accepted') {
    const key = ' Condition: ';
    const idx = desc.indexOf(key);
    if (idx !== -1) {
      return `${escapeHtml(desc.slice(0, idx))} Condition: <strong>${escapeHtml(desc.slice(idx + key.length))}</strong>`;
    }
    return escapeHtml(desc);
  }

  // Sent / resent — bold the recipient email
  if (log.change_type === 'sent' || log.change_type === 'resent') {
    const key = ' to ';
    const idx = desc.indexOf(key);
    if (idx !== -1) {
      const afterTo = desc.slice(idx + key.length);
      const email = afterTo.endsWith('.') ? afterTo.slice(0, -1) : afterTo;
      return `${escapeHtml(desc.slice(0, idx))} to <strong>${escapeHtml(email)}</strong>.`;
    }
    return escapeHtml(desc);
  }

  // Created / duplicated — bold the proposal title between quotes
  if (log.change_type === 'created' || log.change_type === 'duplicated') {
    return escapeHtml(desc).replace(/&quot;(.+?)&quot;/, '<strong>&quot;$1&quot;</strong>');
  }

  return escapeHtml(desc);
}

function formatLogDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
</script>
