<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Clientes</h1>
        <p class="text-sm text-text-subtle mt-1">
          Perfiles de clientes para propuestas y plataforma. Los huérfanos pueden eliminarse.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="clients-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo cliente</span>
      </BaseButton>
    </div>

    <!-- Level 1: business module. It groups the subfilters below; the cut
         itself happens at level 2. -->
    <ClientModuleTabs
      :model-value="activeModule"
      @update:model-value="selectModule"
    >
      <template #trailing>
        <!-- design-tokens: allow-raw-button -->
        <button
          data-testid="clients-tab-config"
          :class="[
            'ml-auto px-4 py-2 rounded-xl text-sm font-medium transition-colors',
            isConfigOpen
              ? 'bg-primary text-white'
              : 'bg-surface-raised text-text-muted hover:bg-border-muted',
          ]"
          @click="isConfigOpen = !isConfigOpen"
        >
          Configuraciones
        </button>
      </template>
    </ClientModuleTabs>

    <!-- Settings tab replaces the list area -->
    <ViewSettingsPanel
      v-if="isConfigOpen"
      :filter-views="[{ value: 'client', label: 'Clientes' }]"
      @reset="reloadFilterTabs"
    >
      <section class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6">
        <h2 class="text-lg font-bold text-text-default mb-1">Defaults del panel</h2>
        <p class="text-sm text-text-muted mb-4">
          Los valores por defecto de propuestas y diagnósticos (que afectan a
          los clientes) se administran en el panel de defaults.
        </p>
        <BaseButton as="NuxtLink" variant="secondary" size="sm" :to="localePath('/panel/defaults')">
          Abrir defaults
        </BaseButton>
      </section>
    </ViewSettingsPanel>

    <template v-if="!isConfigOpen">
    <!-- Level 2: the subfilters of the selected module, plus its saved tabs -->
    <ProposalFilterTabs
      :tabs="displayTabs"
      :active-tab-id="filterTabId"
      :counts="subfilterCounts"
      :is-tab-limit-reached="isTabLimitReached"
      count-title="Clientes que cumplen este filtro"
      :max-visible="7"
      @select="onSelectFilterTab"
      @create="handleCreateFilterTab"
      @rename="renameFilterTab"
      @delete="deleteFilterTab"
      @restore="restoreFilterTab"
      @rebase="rebaseFilterTab"
    />

    <!-- Search + client status + Filter toggle. Status sits here, next to the
         search box, because it qualifies the register itself and combines with
         any module rather than competing with them for the row above. -->
    <div class="flex flex-wrap items-center gap-2 mb-5">
      <BaseInput
        v-model="search"
        type="text"
        placeholder="Buscar por nombre, email o empresa..."
        data-testid="clients-search-input"
        class="w-full sm:max-w-xs"
        @input="onSearchInput"
      />
      <BaseSegmented
        :model-value="clientStatus"
        :options="clientStatusOptions"
        size="sm"
        data-testid="clients-status-selector"
        @update:model-value="setClientStatus"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        data-testid="clients-filter-toggle"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
    </div>

    <!-- Filter panel -->
    <ClientFilterPanel
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :filter-count="activeFilterCount"
      @update:model-value="onFiltersUpdate"
      @reset="handleResetFilters"
    />

    <!-- Loading -->
    <div v-if="clientsStore.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando clientes...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredClients.length === 0"
      class="text-center py-16 text-text-subtle text-sm"
    >
      {{ search || hasActiveFilters ? 'No se encontraron clientes con ese criterio.' : 'No hay clientes aún.' }}
    </div>

    <!-- Client list -->
    <div v-else class="space-y-3">
      <div
        v-for="client in pagedClients"
        :key="client.id"
        :data-testid="`client-row-${client.id}`"
        class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden"
      >
        <!-- Client row header (drop target for proposal/diagnostic reassignment) -->
        <div
          :data-testid="`client-header-${client.id}`"
          class="px-5 py-4 flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-between gap-3 cursor-pointer hover:bg-surface-raised transition-colors"
          :class="{ 'ring-2 ring-inset ring-focus-ring bg-primary-soft': dragOverClientId === client.id }"
          @click="toggleClient(client)"
          @dragover="onClientDragOver($event, client)"
          @dragleave="onClientDragLeave(client)"
          @drop.prevent="onClientDrop(client)"
        >
          <div class="flex items-center gap-4 flex-1 min-w-0 w-full sm:w-auto">
            <!-- Avatar -->
            <div
              class="w-10 h-10 rounded-full bg-primary-soft flex items-center justify-center flex-shrink-0"
            >
              <span class="text-text-brand font-bold text-sm">{{ initials(client.name) }}</span>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="text-sm font-semibold text-text-default truncate">{{ client.name }}</p>
                <span class="text-xs text-text-subtle tabular-nums">#{{ client.id }}</span>
                <span
                  v-if="client.is_email_placeholder"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong font-medium uppercase tracking-wide"
                  title="Email pendiente — automatizaciones de correo pausadas para este cliente"
                >
                  📧 placeholder
                </span>
                <span
                  v-if="client.is_orphan"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-raised text-text-muted font-medium uppercase tracking-wide"
                  title="Sin propuestas, proyectos, diagnósticos, ingresos ni hostings — puede eliminarse"
                >
                  Huérfano
                </span>
                <span
                  v-if="client.is_inactive"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong font-medium uppercase tracking-wide"
                  title="Cliente marcado como inactivo — oculto de los demás tabs"
                >
                  Inactivo
                </span>
              </div>
              <p class="text-xs text-text-subtle mt-0.5 truncate">
                {{ client.is_email_placeholder ? 'Email pendiente' : client.email }}
                <span v-if="client.company" class="text-text-subtle">· {{ client.company }}</span>
              </p>
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 flex-shrink-0 w-full sm:w-auto">
            <!-- Stats pills -->
            <span
              class="text-xs px-2.5 py-1 rounded-full bg-surface-raised text-text-muted font-medium"
            >
              {{ client.total_proposals }} propuesta{{ client.total_proposals !== 1 ? 's' : '' }}
            </span>

            <!-- Hosting count, only while a hosting preset is applied. Doubles
                 as the jump into Hostings already filtered by this client. -->
            <!-- design-tokens: allow-raw-button -->
            <button
              v-if="showsHostingCount(client) && canOpenHostings"
              type="button"
              :data-testid="`client-hostings-${client.id}`"
              class="text-xs px-2.5 py-1 rounded-full bg-info-soft text-info-strong font-medium hover:bg-primary-soft transition-colors"
              :title="`Ver los hostings de ${client.name} en Contabilidad`"
              @click.stop="goToClientHostings(client)"
            >
              {{ client.hostings_count }} hosting{{ client.hostings_count !== 1 ? 's' : '' }}
            </button>
            <span
              v-else-if="showsHostingCount(client)"
              :data-testid="`client-hostings-${client.id}`"
              class="text-xs px-2.5 py-1 rounded-full bg-info-soft text-info-strong font-medium"
            >
              {{ client.hostings_count }} hosting{{ client.hostings_count !== 1 ? 's' : '' }}
            </span>

            <!-- Documentos: cuántos tiene + fecha del último, sólo con el
                 módulo activo. Salta al gestor ya filtrado por el cliente.
                 Sin gate de superuser: documentos comparte el gate admin de
                 esta misma página. -->
            <!-- design-tokens: allow-raw-button -->
            <button
              v-if="showsDocumentsCount(client)"
              type="button"
              :data-testid="`client-documents-${client.id}`"
              class="text-xs px-2.5 py-1 rounded-full bg-info-soft text-info-strong font-medium hover:bg-primary-soft transition-colors"
              :title="`Ver los documentos de ${client.name}`"
              @click.stop="goToClientDocuments(client)"
            >
              {{ client.documents_count }} doc{{ client.documents_count !== 1 ? 's' : '' }}<span v-if="client.last_document_at"> · {{ formatDate(client.last_document_at) }}</span>
            </button>

            <!-- Emails: the count plus when we last wrote, which is what turns
                 the list into a reading of contact and not just a filter.
                 Opens the same modal the ficha does. -->
            <!-- design-tokens: allow-raw-button -->
            <button
              v-if="showsEmailCount(client)"
              type="button"
              :data-testid="`client-emails-${client.id}`"
              class="text-xs px-2.5 py-1 rounded-full bg-info-soft text-info-strong font-medium hover:bg-primary-soft transition-colors"
              :title="`Ver los correos de ${client.name}`"
              @click.stop="openEmails(client)"
            >
              {{ client.emails_sent_count }} correo{{ client.emails_sent_count !== 1 ? 's' : '' }}
              <template v-if="client.last_email_at"> · {{ formatDate(client.last_email_at) }}</template>
            </button>

            <button
              v-if="client.accepted_count > 0"
              type="button"
              :data-testid="`client-platform-${client.id}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              :disabled="isBridging"
              title="Ver en plataforma"
              @click.stop="goToPlatform('/platform/clients/' + client.user_id)"
            >
              <SidebarIcon name="external" class="w-4 h-4" />
            </button>

            <!-- Edit button -->
            <button
              type="button"
              :data-testid="`client-edit-${client.id}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              title="Editar cliente"
              @click.stop="openEditModal(client)"
            >
              <PencilSquareIcon class="w-4 h-4" />
            </button>

            <!-- Inactive toggle button -->
            <button
              type="button"
              :data-testid="`client-toggle-inactive-${client.id}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-warning-strong hover:bg-warning-soft transition-colors"
              :title="client.is_inactive ? 'Reactivar cliente' : 'Marcar como inactivo'"
              @click.stop="toggleInactive(client)"
            >
              <PlayCircleIcon v-if="client.is_inactive" class="w-4 h-4" />
              <PauseCircleIcon v-else class="w-4 h-4" />
            </button>

            <!-- Trash button -->
            <BaseButton variant="danger-ghost" size="sm" :data-testid="`client-delete-${client.id}`" :title="'Eliminar cliente'" @click.stop="confirmDelete(client)">
              <TrashIcon class="w-4 h-4" />
            </BaseButton>

            <!-- Expand chevron -->
            <svg
              class="w-4 h-4 text-text-subtle transition-transform flex-shrink-0"
              :class="{ 'rotate-180': expandedClients.has(client.id) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>

        <!-- Expanded: proposals, projects, and diagnostics -->
        <div
          v-if="expandedClients.has(client.id)"
          class="border-t border-border-muted bg-surface-raised"
        >
          <div v-if="loadingDetails.has(client.id)" class="px-5 py-4 text-sm text-text-subtle">
            Cargando...
          </div>
          <template v-else>
            <!-- Reachable without going through the filter: filtering is for
                 finding who, the ficha is where you already are when the
                 question "what did we send them?" comes up. -->
            <div class="px-5 pt-4 flex justify-end">
              <BaseButton
                variant="secondary"
                size="sm"
                :data-testid="`client-view-emails-${client.id}`"
                @click.stop="openEmails(client)"
              >
                Ver correos
              </BaseButton>
            </div>

            <!-- Proposals (drop target for proposal reassignment) -->
            <div
              :data-testid="`client-proposals-zone-${client.id}`"
              :class="{ 'ring-2 ring-inset ring-focus-ring bg-primary-soft': dragOverZoneKey === `${client.id}:proposal` }"
              @dragover="onZoneDragOver($event, client, 'proposal')"
              @dragleave="onZoneDragLeave($event, client, 'proposal')"
              @drop.prevent="onZoneDrop(client, 'proposal')"
            >
              <div class="px-5 pt-4 pb-1">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Propuestas</p>
              </div>
              <div
                v-if="(detailCache[client.id]?.proposals || []).length === 0"
                class="px-5 pb-4 text-sm text-text-subtle"
              >
                Sin propuestas.
              </div>
              <div v-else class="overflow-x-auto">
                <table class="w-full min-w-[600px] text-sm">
                  <thead>
                    <tr
                      class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider"
                    >
                      <th class="px-5 py-3">Propuesta</th>
                      <th class="px-4 py-3">Estado</th>
                      <th class="px-4 py-3">Inversión</th>
                      <th class="px-4 py-3 text-center">Vistas</th>
                      <th class="px-4 py-3">Enviada</th>
                      <th class="px-4 py-3 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border-muted">
                    <tr
                      v-for="p in detailCache[client.id].proposals"
                      :key="p.id"
                      draggable="true"
                      :data-testid="`client-proposal-row-${p.id}`"
                      class="hover:bg-surface-raised transition-colors bg-surface cursor-grab active:cursor-grabbing select-none"
                      :class="{ 'opacity-50': draggingItem?.type === 'proposal' && draggingItem?.id === p.id }"
                      @dragstart="onRowDragStart($event, client, 'proposal', p)"
                      @dragend="onRowDragEnd"
                    >
                      <td class="px-5 py-3">
                        <NuxtLink
                          :to="localePath(`/panel/proposals/${p.id}/edit`)"
                          draggable="false"
                          class="font-medium text-text-default hover:text-text-brand transition-colors"
                        >
                          {{ p.title }}
                        </NuxtLink>
                      </td>
                      <td class="px-4 py-3">
                        <ProposalStatusSelect
                          :proposal="p"
                          :updating="updatingProposalStatusId === p.id"
                          @change="(s) => onProposalStatusSelect(client, p, s)"
                        />
                      </td>
                      <td class="px-4 py-3 text-text-muted/60 tabular-nums">
                        ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
                      </td>
                      <td class="px-4 py-3 text-center text-text-muted/60">{{ p.view_count }}</td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ p.sent_at ? formatDate(p.sent_at) : '—' }}
                      </td>
                      <td class="px-4 py-3 text-right">
                        <BaseButton variant="danger-ghost" size="sm" :data-testid="`client-proposal-delete-${p.id}`" title="Eliminar propuesta" @click.stop="confirmDeleteProposal(client, p)">
                          <TrashIcon class="w-4 h-4" />
                        </BaseButton>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Platform projects -->
            <template v-if="(detailCache[client.id]?.projects || []).length > 0">
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Proyectos de plataforma</p>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Proyecto</th>
                      <th class="px-4 py-3">Estado</th>
                      <th class="px-4 py-3 text-center">Progreso</th>
                      <th class="px-4 py-3">Inicio</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border-muted">
                    <tr
                      v-for="proj in detailCache[client.id].projects"
                      :key="proj.id"
                      class="hover:bg-surface-raised transition-colors bg-surface"
                    >
                      <td class="px-5 py-3 font-medium text-text-default">{{ proj.name }}</td>
                      <td class="px-4 py-3">
                        <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(proj.status)">
                          {{ proj.status }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-center text-text-muted/60">{{ proj.progress }}%</td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ proj.start_date ? formatDate(proj.start_date) : '—' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <!-- Web diagnostics (drop target for diagnostic reassignment) -->
            <div
              v-if="(detailCache[client.id]?.diagnostics || []).length > 0"
              :data-testid="`client-diagnostics-zone-${client.id}`"
              :class="{ 'ring-2 ring-inset ring-focus-ring bg-primary-soft': dragOverZoneKey === `${client.id}:diagnostic` }"
              @dragover="onZoneDragOver($event, client, 'diagnostic')"
              @dragleave="onZoneDragLeave($event, client, 'diagnostic')"
              @drop.prevent="onZoneDrop(client, 'diagnostic')"
            >
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Diagnósticos web</p>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Diagnóstico</th>
                      <th class="px-4 py-3">Estado</th>
                      <th class="px-4 py-3">Creado</th>
                      <th class="px-4 py-3 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border-muted">
                    <tr
                      v-for="diag in detailCache[client.id].diagnostics"
                      :key="diag.id"
                      draggable="true"
                      :data-testid="`client-diagnostic-row-${diag.id}`"
                      class="hover:bg-surface-raised transition-colors bg-surface cursor-grab active:cursor-grabbing select-none"
                      :class="{ 'opacity-50': draggingItem?.type === 'diagnostic' && draggingItem?.id === diag.id }"
                      @dragstart="onRowDragStart($event, client, 'diagnostic', diag)"
                      @dragend="onRowDragEnd"
                    >
                      <td class="px-5 py-3 font-medium text-text-default">{{ diag.title }}</td>
                      <td class="px-4 py-3">
                        <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(diag.status)">
                          {{ diag.status }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ diag.created_at ? formatDate(diag.created_at) : '—' }}
                      </td>
                      <td class="px-4 py-3 text-right">
                        <BaseButton variant="danger-ghost" size="sm" :data-testid="`client-diagnostic-delete-${diag.id}`" title="Eliminar diagnóstico" @click.stop="confirmDeleteDiagnostic(client, diag)">
                          <TrashIcon class="w-4 h-4" />
                        </BaseButton>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Accounting: what this client costs and pays -->
            <div v-if="detailCache[client.id]?.hostings?.length">
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2 flex items-center justify-between gap-3">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider">Hostings</p>
                <p class="text-xs text-text-muted tabular-nums">
                  {{ formatMoney(detailCache[client.id].hostings_monthly_total) }} /mes activos
                </p>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Hosting</th>
                      <th class="px-4 py-3">Proyecto</th>
                      <th class="px-4 py-3">Valor/mes</th>
                      <th class="px-4 py-3">Vence</th>
                      <th class="px-4 py-3">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="hosting in detailCache[client.id].hostings"
                      :key="hosting.id"
                      class="border-t border-border-muted"
                      :data-testid="`client-hosting-${hosting.id}`"
                    >
                      <td class="px-5 py-3 text-text-default">
                        {{ hosting.domain_url || hosting.client_name }}
                      </td>
                      <td
                        class="px-4 py-3 text-text-muted text-xs"
                        :data-testid="`client-hosting-project-${hosting.id}`"
                      >
                        {{ hosting.project_name || '—' }}
                      </td>
                      <td class="px-4 py-3 tabular-nums text-text-muted">
                        {{ formatMoney(hosting.monthly_value) }}
                      </td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ hosting.valid_to ? formatDate(hosting.valid_to) : '—' }}
                      </td>
                      <td class="px-4 py-3">
                        <span
                          class="text-xs px-2.5 py-1 rounded-full font-medium"
                          :class="hosting.is_active
                            ? 'bg-success-soft text-success-strong'
                            : 'bg-surface-raised text-text-muted'"
                        >
                          {{ hosting.is_active ? 'Vigente' : 'Inactivo' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="detailCache[client.id]?.incomes?.length">
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider">Ingresos</p>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Concepto</th>
                      <th class="px-4 py-3">Proyecto</th>
                      <th class="px-4 py-3">Mes</th>
                      <th class="px-4 py-3">Total</th>
                      <th class="px-4 py-3">Cobro</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="income in detailCache[client.id].incomes"
                      :key="income.id"
                      class="border-t border-border-muted"
                      :data-testid="`client-income-${income.id}`"
                    >
                      <td class="px-5 py-3 text-text-default">{{ income.concept }}</td>
                      <td
                        class="px-4 py-3 text-text-muted text-xs"
                        :data-testid="`client-income-project-${income.id}`"
                      >
                        {{ income.project_name || '—' }}
                      </td>
                      <td class="px-4 py-3 text-text-muted text-xs">{{ income.period_label }}</td>
                      <td class="px-4 py-3 tabular-nums text-text-muted">
                        {{ formatMoney(income.total_amount) }}
                      </td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ income.payment_status_label || income.kind_label }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Los últimos 5 documentos del cliente; "Ver todos" entra al
                 módulo ya filtrado — la relación sirve en las dos direcciones. -->
            <div v-if="detailCache[client.id]?.documents?.length">
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2 flex items-center justify-between gap-3">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider">Documentos</p>
                <!-- design-tokens: allow-raw-button -->
                <button
                  type="button"
                  :data-testid="`client-documents-all-${client.id}`"
                  class="text-xs text-text-brand hover:underline"
                  @click.stop="goToClientDocuments(client)"
                >
                  Ver todos ({{ detailCache[client.id].documents_total }})
                </button>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Documento</th>
                      <th class="px-4 py-3">Proyecto</th>
                      <th class="px-4 py-3">Estado</th>
                      <th class="px-4 py-3">Creado</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="doc in detailCache[client.id].documents"
                      :key="doc.id"
                      class="border-t border-border-muted"
                      :data-testid="`client-document-row-${doc.id}`"
                    >
                      <td class="px-5 py-3">
                        <NuxtLink
                          :to="localePath(`/panel/documents/${doc.id}/edit`)"
                          class="text-text-default hover:text-text-brand hover:underline"
                          @click.stop
                        >
                          {{ doc.title }}
                        </NuxtLink>
                      </td>
                      <td class="px-4 py-3 text-text-muted text-xs">{{ doc.project_name || '—' }}</td>
                      <td class="px-4 py-3 text-text-muted text-xs">{{ documentStatusLabel(doc.status) }}</td>
                      <td class="px-4 py-3 text-text-muted text-xs">{{ formatDate(doc.created_at) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <BasePagination
      v-if="!clientsStore.isLoading && filteredClients.length > 0"
      :current-page="clientsPage"
      :total-pages="clientsTotalPages"
      :total-items="clientsTotalItems"
      :range-from="clientsRangeFrom"
      :range-to="clientsRangeTo"
      class="mt-4"
      @prev="clientsPrev"
      @next="clientsNext"
      @go="clientsGoTo"
    />
    </template>

    <!-- New client modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="closeCreateModal"
    >
      <div class="bg-surface border border-border-muted rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div class="px-6 pt-6 pb-2">
          <h3 class="text-lg font-bold text-text-default">Nuevo cliente</h3>
          <p class="mt-1 text-sm text-text-muted">
            Crea un perfil sin propuesta. Si no agregas email, generaremos uno temporal y las
            automatizaciones quedarán pausadas para este cliente.
          </p>
        </div>
        <form @submit.prevent="submitCreate" class="px-6 py-4 space-y-4">
          <ClientFormFields
            :model-value="createForm"
            testid-prefix="clients-new"
            @update:model-value="Object.assign(createForm, $event)"
          />
          <p v-if="createError" class="text-xs text-danger-strong">{{ createError }}</p>
          <div class="flex items-center justify-end gap-3 pt-2">
            <BaseButton variant="ghost" size="md" @click="closeCreateModal">
              Cancelar
            </BaseButton>
            <BaseButton variant="primary" size="md" type="submit" :disabled="clientsStore.isUpdating" data-testid="clients-new-submit">
              Crear cliente
            </BaseButton>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit client modal -->
    <div
      v-if="editingClient"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="closeEditModal"
    >
      <div class="bg-surface border border-border-muted rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div class="px-6 pt-6 pb-2">
          <h3 class="text-lg font-bold text-text-default">Editar cliente</h3>
          <p class="mt-1 text-sm text-text-muted">
            Los cambios se propagarán a todas las propuestas vinculadas a este cliente.
          </p>
        </div>
        <form @submit.prevent="submitEdit" class="px-6 py-4 space-y-4">
          <ClientFormFields
            :model-value="editForm"
            testid-prefix="clients-edit"
            @update:model-value="Object.assign(editForm, $event)"
          />
          <p v-if="editError" class="text-xs text-danger-strong">{{ editError }}</p>
          <div class="flex items-center justify-end gap-3 pt-2">
            <BaseButton variant="ghost" size="md" @click="closeEditModal">
              Cancelar
            </BaseButton>
            <BaseButton variant="primary" size="md" type="submit" :disabled="clientsStore.isUpdating" data-testid="clients-edit-submit">
              Guardar cambios
            </BaseButton>
          </div>
        </form>
      </div>
    </div>

    <!-- The client's emails, and the viewer for one of them. Siblings rather
         than nested: BaseModal has no stacking manager, so DOM order is what
         decides which one paints on top. -->
    <ClientEmailsModal
      :open="emailsModalOpen"
      :client="emailsClient"
      :preview-open="emailBodyOpen"
      @close="closeEmails"
      @view-body="openEmailBody"
    />
    <EmailBodyModal
      :open="emailBodyOpen"
      :entry="emailBodyEntry"
      :fetcher="fetchEmailBody"
      @close="emailBodyOpen = false"
    />

    <!-- Confirm modal for delete -->
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      :require-type-text="confirmState.requireTypeText"
      :hide-cancel="confirmState.hideCancel"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { PlusIcon, TrashIcon, PencilSquareIcon, PauseCircleIcon, PlayCircleIcon } from '@heroicons/vue/24/outline';
import { formatDate } from '~/utils/formatDate';
import { statusLabel as documentStatusLabel } from '~/utils/documentStatus';
import { formatMoney as formatMoneyRaw } from '~/utils/formatMoney';
import { clientFormPayload, emptyClientForm } from '~/utils/billingCode';
import SidebarIcon from '~/components/platform/SidebarIcon.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ClientFilterPanel from '~/components/clients/ClientFilterPanel.vue';
import ClientFormFields from '~/components/clients/ClientFormFields.vue';
import ClientModuleTabs from '~/components/clients/ClientModuleTabs.vue';
import ClientEmailsModal from '~/components/clients/ClientEmailsModal.vue';
import EmailBodyModal from '~/components/accounting/EmailBodyModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import ViewSettingsPanel from '~/components/panel/ViewSettingsPanel.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import ProposalStatusSelect from '~/components/panel/proposal/ProposalStatusSelect.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useProposalStatusChange } from '~/composables/useProposalStatusChange';
import { useAccountingFilters } from '~/composables/useAccountingFilters';
import {
  CLIENT_FILTERS_CONFIG,
  clientSubfiltersFor,
  findClientSubfilter,
  matchesSubfilter,
} from '~/constants/clientFilters';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelToPlatformBridge } from '~/composables/usePanelToPlatformBridge';
import { usePagination } from '~/composables/usePagination';
import { useProposalClientsStore } from '~/stores/proposal_clients';
import { useProposalStore } from '~/stores/proposals';
import { useDiagnosticsStore } from '~/stores/diagnostics';

const localePath = useLocalePath();
const { goToPlatform, isBridging } = usePanelToPlatformBridge();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const clientsStore = useProposalClientsStore();

/** COP money from the API's string amounts. */
function formatMoney(value) {
  return formatMoneyRaw(Number(value ?? 0), 'COP');
}
const proposalStore = useProposalStore();
const diagnosticsStore = useDiagnosticsStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } =
  useConfirmModal();
const notify = usePanelNotify();

// Inline status change for the nested proposal rows. No onNegotiate here:
// natural negotiating PATCHes directly; the contract flow lives in the
// proposal edit view.
const { updatingId: updatingProposalStatusId, changeStatus: changeProposalStatus } =
  useProposalStatusChange({ requestConfirm });

async function onProposalStatusSelect(client, proposal, newStatus) {
  const result = await changeProposalStatus(proposal, newStatus);
  // Refresh on success AND failure: the nested row may be stale either way.
  if (result) await refreshClientDetail(client.id);
}

// Migrated off the old useClientFilters (its pre-generalization ancestor) so
// the predefined filters ride the same `builtinTabs` mechanism the accounting
// subviews already use. The configuration itself lives in ~/constants/
// clientFilters so this page and its tests never drift apart.
const {
  currentFilters,
  displayTabs,
  activeTabId: filterTabId,
  activeModule,
  selectModule,
  isFilterPanelOpen,
  hasActiveFilters,
  activeFilterCount,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab: selectFilterTab,
  saveTab,
  deleteTab: deleteFilterTab,
  renameTab: renameFilterTab,
  restoreTab: restoreFilterTab,
  rebaseTab: rebaseFilterTab,
  reloadTabs: reloadFilterTabs,
} = useAccountingFilters(CLIENT_FILTERS_CONFIG);

const filteredClients = computed(() => applyFilters(clientsStore.clients));

/**
 * The per-row hosting count only earns its space while the Hosting module is
 * the one being read — that is the moment the question "cuántos" is being
 * asked, whichever of its subfilters is applied.
 */
function showsHostingCount(client) {
  return activeModule.value === 'hosting' && Number(client.hostings_count || 0) > 0;
}

function showsEmailCount(client) {
  return activeModule.value === 'emails' && Number(client.emails_sent_count || 0) > 0;
}

// The emails modal, reachable two ways: the row pill while the Emails module
// is being read, and the "Ver correos" button on the expanded card — filtering
// is for finding who, the ficha is where you already are when the question
// comes up. One modal serves both.
const emailsClient = ref(null);
const emailsModalOpen = ref(false);
const emailBodyEntry = ref(null);
const emailBodyOpen = ref(false);

function openEmails(client) {
  emailsClient.value = client;
  emailsModalOpen.value = true;
}

function closeEmails() {
  emailsModalOpen.value = false;
  emailsClient.value = null;
}

function openEmailBody(entry) {
  emailBodyEntry.value = entry;
  emailBodyOpen.value = true;
}

function fetchEmailBody(logId) {
  return clientsStore.fetchClientEmailBody(emailsClient.value?.id, logId);
}

/**
 * /panel/clients only requires admin, but /panel/accounting/* is behind the
 * superuser-only middleware. Without this guard a staff non-superuser would
 * click the pill straight into a redirect.
 */
const canOpenHostings = computed(() => proposalStore.isSuperuser);

function goToClientHostings(client) {
  navigateTo({
    path: '/panel/accounting/hostings',
    query: { client: String(client.id) },
  });
}

/**
 * A diferencia del pill de hostings, sin guard de superuser: /panel/documents
 * comparte el gate admin de esta misma página.
 */
function showsDocumentsCount(client) {
  return activeModule.value === 'documents' && Number(client.documents_count || 0) > 0;
}

function goToClientDocuments(client) {
  navigateTo({
    path: '/panel/documents',
    query: { client: String(client.id) },
  });
}

/**
 * Matches per subfilter of the active module, read straight off the loaded
 * rows so the number is visible without applying the filter. Counted before
 * the panel's advanced filters — a badge should not move as you tweak
 * unrelated controls — but after the status selector and search, which is what
 * "lo que obtendrías si lo presionas ahora" means here.
 *
 * Always a number, never absent: an empty set is information, and hiding the
 * zero would force the user to press the filter to find out.
 */
const subfilterCounts = computed(() => {
  const counts = {};
  for (const sub of clientSubfiltersFor(activeModule.value)) {
    counts[sub.id] = clientsStore.clients.filter((c) => matchesSubfilter(sub, c)).length;
  }
  return counts;
});

/**
 * Presses on the active subfilter turn it off (requisito: "al presionarlo de
 * nuevo, la lista vuelve a todos los clientes"). Gated to subfilter ids on
 * purpose: re-clicking a saved tab has always been an idempotent reload of
 * its filters, and toggling those off would be a silent behavior change.
 */
function onSelectFilterTab(tabId) {
  const key = String(tabId);
  if (findClientSubfilter(key) && key === String(filterTabId.value)) {
    selectFilterTab('all');
    return;
  }
  selectFilterTab(tabId);
}

/**
 * Tab, chip and panel are three views of one state, so they have to move
 * together: the panel owns the whole filter object, and once an edit from it
 * (typically removing a chip) leaves the highlighted subfilter's own values no
 * longer set, that highlight is a lie and has to go.
 *
 * Only the highlight is dropped, not the filters: the user may well have other
 * cuts applied, and clearing one chip must not take them down with it. Saved
 * tabs are left alone — editing one is how you modify it, and the composable
 * already tracks that as "modificada" with its own restore.
 */
function onFiltersUpdate(next) {
  Object.assign(currentFilters, next);

  const active = findClientSubfilter(filterTabId.value);
  if (active && !subfilterStillApplied(active)) {
    filterTabId.value = 'all';
  }
}

/** Whether every value the subfilter stands for is still set in the panel. */
function subfilterStillApplied(subfilter) {
  return Object.entries(subfilter.filters).every(([key, value]) => {
    const current = currentFilters[key];
    if (Array.isArray(value)) {
      return Array.isArray(current)
        && current.length === value.length
        && value.every((v) => current.includes(v));
    }
    return current === value;
  });
}

const {
  currentPage: clientsPage,
  totalPages: clientsTotalPages,
  totalItems: clientsTotalItems,
  rangeFrom: clientsRangeFrom,
  rangeTo: clientsRangeTo,
  paginatedItems: pagedClients,
  goTo: clientsGoTo,
  next: clientsNext,
  prev: clientsPrev,
  reset: clientsResetPage,
} = usePagination(filteredClients, { pageSize: 10 });

watch(filteredClients, () => clientsResetPage(), { deep: false });

/**
 * Client status: the state of the register itself, orthogonal to every module,
 * so it lives next to the search box and combines with any of them. Applied
 * server-side, which is why its counts come from their own endpoint.
 */
const CLIENT_STATUSES = [
  { id: 'all', label: 'Todos' },
  { id: 'active', label: 'Activos' },
  { id: 'orphans', label: 'Huérfanos' },
  { id: 'inactive', label: 'Inactivos' },
];
const route = useRoute();
const router = useRouter();
const VALID_STATUSES = CLIENT_STATUSES.map((s) => s.id);
const initialStatus = String(route.query.status || 'all');
const clientStatus = ref(VALID_STATUSES.includes(initialStatus) ? initialStatus : 'all');
const isConfigOpen = ref(false);

const clientStatusOptions = computed(() =>
  CLIENT_STATUSES.map(({ id, label }) => {
    const count = clientsStore.statusCounts?.[id];
    return {
      value: id,
      // Same treatment as the subfilter counts: in parentheses, always shown,
      // zero included.
      label: count == null ? label : `${label} (${count})`,
      testId: `clients-status-${id}`,
    };
  }),
);

const search = ref('');
const expandedClients = ref(new Set());
const loadingDetails = ref(new Set());
const detailCache = reactive({});

let searchTimer = null;

// -------------------------------------------------------------------
// Data loading
// -------------------------------------------------------------------

async function loadClients({ silent = false } = {}) {
  let orphans = null;
  if (clientStatus.value === 'orphans') orphans = true;
  else if (clientStatus.value === 'active') orphans = false;
  const search_ = search.value.trim();
  await Promise.all([
    clientsStore.fetchClients({
      search: search_,
      orphans,
      // The endpoint does not paginate and every filter on this page — the
      // subfilters and their counts included — runs over whatever was loaded,
      // so ask for the endpoint's hard cap instead of the default 100. Past 500
      // clients this needs real server-side pagination.
      limit: 500,
      inactive: clientStatus.value === 'inactive',
      silent,
    }),
    // Same search, so the numbers in the selector describe the same table the
    // list is showing.
    clientsStore.fetchStatusCounts({ search: search_ }),
  ]);
}

/**
 * Full refresh bound to the global panel refresh button.
 *
 * Besides reloading the top-level rows, it invalidates the per-client
 * detail cache and refetches the rows that are still expanded. Without
 * this, renaming a proposal or reassigning it to another client would
 * not show up after refresh because the nested proposals are served from
 * `detailCache`, which is only populated once on expand.
 */
async function refreshAll() {
  await loadClients();
  const expandedIds = Array.from(expandedClients.value);
  Object.keys(detailCache).forEach((key) => { delete detailCache[key]; });
  await Promise.all(
    expandedIds.map(async (id) => {
      const result = await clientsStore.fetchClient(id);
      if (result.success) detailCache[id] = result.data;
    }),
  );
}

/**
 * The applied status travels in the URL so the link can be saved and survives
 * a reload, and is dropped again when it goes back to the default instead of
 * staying glued there.
 */
function setClientStatus(status) {
  if (status === clientStatus.value) return;
  clientStatus.value = status;
  const query = { ...route.query };
  if (status === 'all') delete query.status;
  else query.status = status;
  router.replace({ query });
  clientsResetPage();
  loadClients();
}

async function toggleInactive(client) {
  const makeInactive = !client.is_inactive;
  const result = await clientsStore.updateClient(client.id, { is_inactive: makeInactive });
  if (result.success) {
    notify.success(makeInactive
      ? `"${client.name}" marcado como inactivo.`
      : `"${client.name}" reactivado.`);
    await loadClients();
  } else {
    notify.error('No se pudo actualizar el estado del cliente.');
  }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(loadClients, 250);
}

function handleCreateFilterTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

function handleResetFilters() {
  resetFilters();
  isFilterPanelOpen.value = false;
}

function handleEditEscape(e) {
  if (e.key === 'Escape' && editingClient.value) closeEditModal();
}

onMounted(async () => {
  document.addEventListener('keydown', handleEditEscape);
  await loadClients();
  applyHighlightFromQuery();
});

/**
 * ?highlight=<profileId>: llega desde el enlace "Ver cliente" de un documento
 * — expande la ficha y hace scroll a la fila. Param de un solo uso (espejo de
 * ?highlight= en /panel/projects): se limpia de la URL y degrada sin ruido si
 * el cliente no está entre las filas cargadas o quedó en otra página.
 */
function applyHighlightFromQuery() {
  const targetId = Number.parseInt(route.query.highlight, 10);
  if (!Number.isFinite(targetId)) return;
  const query = { ...route.query };
  delete query.highlight;
  router.replace({ query });
  const target = clientsStore.clients.find((c) => c.id === targetId);
  if (!target) return;
  toggleClient(target);
  nextTick(() => {
    document.querySelector(`[data-testid="client-row-${targetId}"]`)
      ?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  });
}

usePanelRefresh(refreshAll);
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
  document.removeEventListener('keydown', handleEditEscape);
});

// -------------------------------------------------------------------
// Row expand → fetch nested proposals on demand
// -------------------------------------------------------------------

async function toggleClient(client) {
  const id = client.id;
  if (expandedClients.value.has(id)) {
    expandedClients.value.delete(id);
    expandedClients.value = new Set(expandedClients.value);
    return;
  }
  expandedClients.value.add(id);
  expandedClients.value = new Set(expandedClients.value);

  if (!detailCache[id]) {
    loadingDetails.value.add(id);
    loadingDetails.value = new Set(loadingDetails.value);
    const result = await clientsStore.fetchClient(id);
    if (result.success) {
      detailCache[id] = result.data;
    }
    loadingDetails.value.delete(id);
    loadingDetails.value = new Set(loadingDetails.value);
  }
}

// -------------------------------------------------------------------
// Create modal
// -------------------------------------------------------------------

const showCreateModal = ref(false);
const createForm = reactive(emptyClientForm());
const createError = ref('');

function openCreateModal() {
  Object.assign(createForm, emptyClientForm());
  createError.value = '';
  showCreateModal.value = true;
}

function closeCreateModal() {
  showCreateModal.value = false;
}

async function submitCreate() {
  createError.value = '';
  const result = await clientsStore.createClient(clientFormPayload(createForm));
  if (result.success) {
    closeCreateModal();
    await loadClients();
  } else {
    createError.value =
      result.errors?.message ||
      result.errors?.error ||
      'No se pudo crear el cliente. Verifica los datos e intenta nuevamente.';
  }
}

// -------------------------------------------------------------------
// Edit modal
// -------------------------------------------------------------------

const editingClient = ref(null);
const editForm = reactive(emptyClientForm());
const editError = ref('');

function openEditModal(client) {
  editingClient.value = client;
  editForm.name = client.name || '';
  editForm.email = client.is_email_placeholder ? '' : (client.email || '');
  editForm.phone = client.phone || '';
  editForm.company = client.company || '';
  editForm.nit = client.nit || '';
  editForm.billing_code = client.billing_code || '';
  editError.value = '';
}

function closeEditModal() {
  editingClient.value = null;
  editError.value = '';
}

async function submitEdit() {
  editError.value = '';
  const result = await clientsStore.updateClient(
    editingClient.value.id, clientFormPayload(editForm),
  );
  if (result.success) {
    closeEditModal();
  } else {
    editError.value =
      result.errors?.message ||
      result.errors?.error ||
      result.errors?.name?.[0] ||
      result.errors?.email?.[0] ||
      result.errors?.phone?.[0] ||
      result.errors?.company?.[0] ||
      'Error al actualizar el cliente.';
  }
}

// -------------------------------------------------------------------
// Delete
// -------------------------------------------------------------------

function buildBlockedMessage(client) {
  const parts = [];
  const proposals = client.total_proposals || 0;
  const projects = client.projects_count || 0;
  const diagnostics = client.diagnostics_count || 0;
  const incomes = client.incomes_count || 0;
  const hostings = client.hostings_count || 0;
  if (proposals > 0) parts.push(`${proposals} propuesta${proposals === 1 ? '' : 's'}`);
  if (projects > 0) parts.push(`${projects} proyecto${projects === 1 ? '' : 's'} de plataforma`);
  if (diagnostics > 0) parts.push(`${diagnostics} diagnóstico${diagnostics === 1 ? '' : 's'} web`);
  if (incomes > 0) parts.push(`${incomes} ingreso${incomes === 1 ? '' : 's'} contable${incomes === 1 ? '' : 's'}`);
  if (hostings > 0) parts.push(`${hostings} hosting${hostings === 1 ? '' : 's'}`);
  const reason = parts.length > 0 ? parts.join(', ') : 'elementos asociados';
  return `No se puede eliminar a "${client.name}" porque tiene ${reason}. Elimina o archiva esos elementos antes de borrar el cliente.`;
}

function confirmDelete(client) {
  if (!client.is_orphan) {
    requestConfirm({
      title: 'No se puede eliminar',
      message: buildBlockedMessage(client),
      variant: 'info',
      hideCancel: true,
      confirmText: 'Entendido',
    });
    return;
  }

  requestConfirm({
    title: 'Eliminar cliente',
    message: `Esto eliminará a "${client.name}" y su cuenta de plataforma de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    requireTypeText: 'DELETE',
    onConfirm: async () => {
      const result = await clientsStore.deleteClient(client.id);
      if (!result.success) {
        // Refresh in case the orphan flag was stale.
        await loadClients();
      }
    },
  });
}

async function refreshClientDetail(clientId) {
  const result = await clientsStore.fetchClient(clientId);
  if (result.success) detailCache[clientId] = result.data;
  // Counts and the orphan badge live on the list rows, not the detail payload.
  await loadClients();
}

// -------------------------------------------------------------------
// Drag & drop: reassign proposals/diagnostics between clients
// -------------------------------------------------------------------

const draggingItem = ref(null); // { type, id, title, sourceClientId, sourceClientName }
const dragOverClientId = ref(null);
const dragOverZoneKey = ref(null); // `${clientId}:${type}` for the proposals/diagnostics zones

function onRowDragStart(event, client, type, item) {
  draggingItem.value = {
    type,
    id: item.id,
    title: item.title,
    sourceClientId: client.id,
    sourceClientName: client.name,
  };
  // Sin setData, Firefox no inicia el drag nativo (no dispara dragover/drop).
  event.dataTransfer.setData('text/plain', `${type}:${item.id}`);
  event.dataTransfer.effectAllowed = 'move';
}

function onRowDragEnd() {
  draggingItem.value = null;
  dragOverClientId.value = null;
  dragOverZoneKey.value = null;
}

function onClientDragOver(event, client) {
  if (!draggingItem.value || client.id === draggingItem.value.sourceClientId) return;
  event.preventDefault(); // required so the browser allows the drop
  event.dataTransfer.dropEffect = 'move';
  dragOverClientId.value = client.id;
}

function onClientDragLeave(client) {
  if (dragOverClientId.value === client.id) dragOverClientId.value = null;
}

async function onClientDrop(targetClient) {
  dragOverClientId.value = null;
  dragOverZoneKey.value = null;
  const dragged = draggingItem.value;
  draggingItem.value = null;
  if (!dragged || dragged.sourceClientId === targetClient.id) return;
  await reassignItem(dragged, { targetClientId: targetClient.id, targetName: targetClient.name });
}

// Zone variants: the proposals/diagnostics areas of an expanded client accept
// only items of their own type; the client header keeps accepting both.
function onZoneDragOver(event, client, zoneType) {
  if (!draggingItem.value || draggingItem.value.type !== zoneType) return;
  if (client.id === draggingItem.value.sourceClientId) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = 'move';
  dragOverZoneKey.value = `${client.id}:${zoneType}`;
}

function onZoneDragLeave(event, client, zoneType) {
  // dragleave also fires when moving between the zone's own children.
  if (event.relatedTarget && event.currentTarget.contains(event.relatedTarget)) return;
  if (dragOverZoneKey.value === `${client.id}:${zoneType}`) dragOverZoneKey.value = null;
}

async function onZoneDrop(client, zoneType) {
  if (draggingItem.value?.type !== zoneType) {
    dragOverZoneKey.value = null;
    return;
  }
  await onClientDrop(client);
}

async function reassignItem(dragged, { targetClientId, targetName }) {
  const result = dragged.type === 'proposal'
    ? await proposalStore.updateProposal(dragged.id, { client_id: targetClientId })
    : await diagnosticsStore.update(dragged.id, { client_id: targetClientId });
  if (!result.success) {
    notify.error(`No se pudo mover ${dragged.type === 'proposal' ? 'la propuesta' : 'el diagnóstico'} "${dragged.title}".`);
    return;
  }
  await refreshAfterReassign(dragged.sourceClientId, targetClientId);
  notify.success({
    title: `"${dragged.title}" movido a ${targetName}.`,
    action: {
      label: 'Deshacer',
      handler: () => reassignItem(
        { ...dragged, sourceClientId: targetClientId, sourceClientName: targetName },
        { targetClientId: dragged.sourceClientId, targetName: dragged.sourceClientName },
      ),
    },
  });
}

// Unlike refreshClientDetail, this refreshes BOTH affected clients and the
// list once (the source/target orphan state may flip tabs). Everything runs
// silently and in-place: expanded details are overwritten only when the fresh
// payload arrives, and the list skips the loading skeleton, so the page does
// not visually "reload" after a drop.
async function refreshAfterReassign(...clientIds) {
  await Promise.all([
    ...clientIds.map(async (id) => {
      if (!expandedClients.value.has(id)) {
        delete detailCache[id]; // refetched on next expand
        return;
      }
      const result = await clientsStore.fetchClient(id);
      if (result.success) detailCache[id] = result.data;
    }),
    loadClients({ silent: true }),
  ]);
}

function confirmDeleteProposal(client, proposal) {
  requestConfirm({
    title: 'Eliminar propuesta',
    message: `Esto eliminará la propuesta "${proposal.title}" de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    requireTypeText: 'DELETE',
    onConfirm: async () => {
      const result = await proposalStore.deleteProposal(proposal.id);
      if (result.success) {
        await refreshClientDetail(client.id);
        notify.success('Propuesta eliminada.');
      } else {
        notify.error(result.error || 'No se pudo eliminar la propuesta.');
      }
    },
  });
}

function confirmDeleteDiagnostic(client, diagnostic) {
  requestConfirm({
    title: 'Eliminar diagnóstico',
    message: `Esto eliminará el diagnóstico "${diagnostic.title}" de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    requireTypeText: 'DELETE',
    onConfirm: async () => {
      const result = await diagnosticsStore.remove(diagnostic.id);
      if (result.success) await refreshClientDetail(client.id);
    },
  });
}

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

function initials(name) {
  return (name || '?')
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('');
}

function statusClass(s) {
  const map = {
    draft: 'bg-surface-raised text-text-muted',
    sent: 'bg-info-soft text-info-strong',
    viewed: 'bg-success-soft text-success-strong',
    accepted: 'bg-primary-soft text-text-brand',
    finished: 'bg-primary-soft text-text-brand',
    rejected: 'bg-danger-soft text-danger-strong',
    expired: 'bg-warning-soft text-warning-strong',
    negotiating: 'bg-primary-soft text-text-brand',
    active: 'bg-success-soft text-success-strong',
    paused: 'bg-warning-soft text-warning-strong',
    completed: 'bg-primary-soft text-text-brand',
    archived: 'bg-surface-raised text-text-muted',
  };
  return map[s] || 'bg-surface-raised text-text-muted';
}
</script>
