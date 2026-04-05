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
      :proposal="contractModalProposal || {}"
      @confirm="handleContractConfirmFromList"
      @cancel="showContractModal = false; contractModalProposal = null"
    />
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Propuestas</h1>
      <div class="flex items-center gap-3">
        <NuxtLink
          :to="localePath('/panel/proposals/defaults')"
          class="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-gray-600 border border-gray-200 rounded-xl
                 font-medium text-sm hover:bg-gray-50 hover:border-gray-300 transition-colors
                 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-500"
          title="Configurar valores por defecto de las propuestas"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Valores por Defecto
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/proposals/create')"
          class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
                 font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm
                 dark:bg-emerald-700 dark:hover:bg-emerald-600"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nueva Propuesta
        </NuxtLink>
      </div>
    </div>

    <!-- KPI Dashboard -->
    <ProposalDashboard />

    <!-- Floating metrics manual -->
    <MetricsManual />

    <!-- Zombie proposals segment -->
    <div v-if="zombieAlerts.length" class="mb-4 bg-gray-800 border border-gray-700 rounded-xl p-4">
      <div class="flex items-center justify-between mb-3 cursor-pointer" @click="zombieExpanded = !zombieExpanded">
        <div class="flex items-center gap-2">
          <span class="text-lg">🧟</span>
          <h3 class="text-sm font-semibold text-gray-200">Propuestas zombie ({{ zombieAlerts.length }})</h3>
        </div>
        <span class="text-xs text-gray-400">{{ zombieExpanded ? '▲' : '▼' }}</span>
      </div>
      <div v-if="zombieExpanded" class="space-y-2">
        <div
          v-for="alert in zombieAlerts"
          :key="`zombie-${alert.id}-${alert.alert_type}`"
          class="flex items-center justify-between bg-gray-700/50 rounded-lg px-4 py-2.5 border border-gray-600 cursor-pointer hover:border-gray-500 transition-colors"
          @click="router.push(localePath(`/panel/proposals/${alert.id}/edit`))"
        >
          <div class="flex items-center gap-3">
            <span class="text-sm">{{ alert.alert_type === 'zombie_draft' ? '📝💀' : alert.alert_type === 'zombie_sent_stale' ? '📤💀' : '💀' }}</span>
            <div>
              <span class="text-sm font-medium text-gray-200">{{ alert.client_name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ alert.title }}</span>
            </div>
          </div>
          <span class="text-xs text-gray-400 font-medium dark:text-gray-500">{{ alert.message }}</span>
        </div>
      </div>
    </div>

    <!-- Alerts panel -->
    <div v-if="activeAlerts.length || showAlertForm" class="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4 dark:bg-amber-900/20 dark:border-amber-700">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-lg">⚠️</span>
          <h3 class="text-sm font-semibold text-amber-800 dark:text-amber-300">Propuestas que necesitan atención ({{ activeAlerts.length }})</h3>
        </div>
        <button
          type="button"
          class="text-xs text-amber-700 font-medium hover:text-amber-900 transition-colors"
          @click="showAlertForm = !showAlertForm"
        >
          {{ showAlertForm ? 'Cancelar' : '+ Crear recordatorio' }}
        </button>
      </div>

      <!-- Create alert form -->
      <div v-if="showAlertForm" class="mb-4 bg-white rounded-lg border border-amber-100 p-4 space-y-3 dark:bg-gray-800 dark:border-gray-600">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Propuesta</label>
            <select v-model="newAlert.proposal" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white outline-none focus:ring-1 focus:ring-emerald-500">
              <option value="">Seleccionar...</option>
              <option v-for="p in proposalStore.proposals" :key="p.id" :value="p.id">{{ p.client_name }} — {{ p.title }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Tipo</label>
            <select v-model="newAlert.alert_type" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white outline-none focus:ring-1 focus:ring-emerald-500">
              <option value="reminder">Recordatorio</option>
              <option value="followup">Seguimiento</option>
              <option value="call">Llamada</option>
              <option value="meeting">Reunión</option>
              <option value="custom">Personalizado</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Fecha</label>
            <input v-model="newAlert.alert_date" type="datetime-local" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-emerald-500" />
          </div>
        </div>
        <div class="flex gap-3 items-end">
          <div class="flex-1">
            <label class="block text-xs text-gray-500 mb-1">Mensaje</label>
            <input v-model="newAlert.message" type="text" placeholder="Ej: Llamar al cliente para seguimiento..." class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-emerald-500" />
          </div>
          <button
            type="button"
            :disabled="!newAlert.proposal || !newAlert.message"
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
            @click="handleCreateAlert"
          >
            Crear
          </button>
        </div>
        <p v-if="alertError" class="text-xs text-red-500">{{ alertError }}</p>
      </div>

      <div class="space-y-2">
        <div
          v-for="alert in activeAlerts"
          :key="`${alert.id}-${alert.alert_type}-${alert.manual_alert_id || ''}`"
          class="flex items-center justify-between bg-white rounded-lg px-4 py-2.5 border cursor-pointer transition-colors dark:bg-gray-800"
          :class="alertBorderClass(alert.priority)"
          @click="router.push(localePath(`/panel/proposals/${alert.id}/edit`))"
        >
          <div class="flex items-center gap-3">
            <span class="text-sm">{{ alertIcon(alert.alert_type) }}</span>
            <div>
              <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ alert.client_name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ alert.title }}</span>
              <span v-if="alert.priority === 'critical'" class="ml-2 px-1.5 py-0.5 text-[10px] font-bold uppercase rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">urgente</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <span class="text-xs font-medium block" :class="alert.priority === 'critical' ? 'text-red-600 dark:text-red-400' : 'text-amber-700 dark:text-amber-400'">{{ alert.message }}</span>
              <span v-if="alert.ref_date || alert.alert_date" class="text-[10px] text-gray-400 dark:text-gray-500">
                {{ formatAlertDate(alert.ref_date || alert.alert_date) }}
              </span>
            </div>
            <button
              v-if="alert.manual_alert_id"
              type="button"
              class="text-xs text-gray-400 hover:text-red-500 transition-colors"
              title="Descartar"
              @click.stop="handleDismissAlert(alert.manual_alert_id)"
            >✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Filter Tabs -->
    <ProposalFilterTabs
      :tabs="savedTabs"
      :active-tab-id="activeTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectTab"
      @create="handleCreateTab"
      @rename="renameTab"
      @delete="deleteTab"
    />

    <!-- Search + Filter toggle -->
    <div class="flex flex-col sm:flex-row gap-3 mb-4">
      <div class="relative flex-1 max-w-sm">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por título o cliente..."
          class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
        />
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors border"
          :class="isFilterPanelOpen
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
          @click="isFilterPanelOpen = !isFilterPanelOpen"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros
          <span
            v-if="activeFilterCount > 0"
            class="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold"
            :class="isFilterPanelOpen ? 'bg-white text-emerald-600' : 'bg-emerald-600 text-white'"
          >
            {{ activeFilterCount }}
          </span>
        </button>
        <button
          v-if="activeTabId !== 'all' && hasActiveFilters"
          type="button"
          class="px-3 py-2 rounded-xl text-xs font-medium transition-colors border bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-700"
          @click="updateTab(activeTabId)"
        >
          Guardar cambios
        </button>
        <div class="w-px h-5 bg-gray-200 dark:bg-gray-600 self-center" />
        <button
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border flex items-center gap-1.5"
          :class="technicalFilter
            ? 'bg-teal-600 text-white border-teal-600'
            : 'bg-white text-teal-700 border-teal-200 hover:border-teal-300 dark:bg-gray-800 dark:text-teal-400 dark:border-teal-800 dark:hover:border-teal-600'"
          @click="toggleTechnicalFilter"
        >
          🔬 Det. técnico
          <span v-if="technicalFilterCount > 0" class="opacity-75">({{ technicalFilterCount }})</span>
        </button>
      </div>
    </div>

    <!-- Filter Panel -->
    <ProposalFilterPanel
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :filter-count="activeFilterCount"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
    />

    <!-- Loading -->
    <div v-if="proposalStore.isLoading" class="text-center py-12 text-gray-400 dark:text-gray-500 text-sm">
      Cargando...
    </div>

    <!-- Empty state -->
    <div v-else-if="proposals.length === 0" class="text-center py-16 dark:text-gray-400">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p class="text-gray-500 text-sm">No hay propuestas{{ hasActiveFilters ? ' con los filtros seleccionados' : '' }}.</p>
    </div>

    <!-- Batch action bar -->
    <Transition name="fade-modal">
      <div v-if="selectedIds.size > 0" class="sticky top-0 z-40 mb-3 bg-gray-900 text-white rounded-xl px-5 py-3 flex items-center justify-between shadow-lg">
        <span class="text-sm font-medium">{{ selectedIds.size }} seleccionada(s)</span>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1.5 bg-blue-600 rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            :disabled="isBulkActing"
            @click="handleBulkAction('resend')"
          >
            🔄 Re-enviar
          </button>
          <button
            class="px-3 py-1.5 bg-yellow-600 rounded-lg text-xs font-medium hover:bg-yellow-700 transition-colors disabled:opacity-50"
            :disabled="isBulkActing"
            @click="handleBulkAction('expire')"
          >
            ⏰ Expirar
          </button>
          <button
            class="px-3 py-1.5 bg-red-600 rounded-lg text-xs font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
            :disabled="isBulkActing"
            @click="handleBulkAction('delete')"
          >
            🗑️ Eliminar
          </button>
          <button
            class="px-3 py-1.5 bg-gray-700 rounded-lg text-xs font-medium hover:bg-gray-600 transition-colors"
            @click="selectedIds = new Set()"
          >
            Cancelar
          </button>
        </div>
      </div>
    </Transition>

    <!-- Table -->
    <div v-if="!proposalStore.isLoading && proposals.length > 0" class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto dark:bg-gray-800 dark:border-gray-700">
      <table class="w-full min-w-[800px]">
        <thead>
          <tr class="border-b border-gray-100 dark:border-gray-700 text-left">
            <th class="px-3 py-3 w-10">
              <input type="checkbox" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" :checked="selectedIds.size === paginatedProposals.length && paginatedProposals.length > 0" @change="toggleSelectAll" @click.stop />
            </th>
            <th class="px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-12">ID</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('client_name')">
              Cliente <span v-if="sortKey === 'client_name'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('total_investment')">
              Inversión <span v-if="sortKey === 'total_investment'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('last_activity_at')">
              Última actividad <span v-if="sortKey === 'last_activity_at'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Vistas</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-center">
              <UiTooltip position="bottom" backgroundColor="bg-gray-900" width="max-w-[220px]">
                <template #trigger><span class="cursor-help">🔥</span></template>
                <p class="text-xs">Heat Score (1-10): indicador rápido de "temperatura" de engagement del cliente con la propuesta.</p>
              </UiTooltip>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
          <tr v-for="(p, rowIdx) in paginatedProposals" :key="p.id" class="transition-colors cursor-pointer" :class="[p.is_active ? 'hover:bg-gray-50 dark:hover:bg-gray-700/50' : 'bg-gray-50 dark:bg-gray-700/30 opacity-60', selectedIds.has(p.id) ? 'bg-emerald-50/50 dark:bg-emerald-900/20' : '']" @click="navigateToProposal(p.id, $event)">
            <td class="px-3 py-4" @click.stop>
              <input type="checkbox" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" :checked="selectedIds.has(p.id)" @change="toggleSelect(p.id)" />
            </td>
            <td class="px-4 py-4 text-xs text-gray-400 tabular-nums">#{{ p.id }}</td>
            <td class="px-6 py-4">
              <div class="text-sm text-gray-600 dark:text-gray-300">{{ p.client_name }}</div>
              <div v-if="p.client_phone" class="text-[10px] text-gray-400">📱 {{ p.client_phone }}</div>
            </td>
            <td class="px-6 py-4">
              <template v-if="(p.available_transitions || []).length">
                <div class="relative inline-flex items-center">
                  <select
                    :value="p.status"
                    :disabled="updatingStatusId === p.id"
                    class="text-xs px-2.5 py-1 rounded-full font-medium border-0 cursor-pointer outline-none focus:ring-2 focus:ring-emerald-500 pr-6 disabled:opacity-60 disabled:cursor-not-allowed"
                    :class="statusClass(p.status)"
                    @change="handleInlineStatusChange(p, $event.target.value, $event)"
                    @click.stop
                  >
                    <option :value="p.status" disabled>{{ statusLabel(p.status) }}</option>
                    <option v-for="s in p.available_transitions" :key="s" :value="s">{{ statusLabel(s) }}</option>
                  </select>
                  <span v-if="updatingStatusId === p.id" class="absolute right-1.5 flex items-center pointer-events-none">
                    <svg class="animate-spin h-3 w-3 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  </span>
                </div>
              </template>
              <span v-else class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(p.status)">
                {{ statusLabel(p.status) }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-300 tabular-nums">
              ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
              <template v-if="isInactive(p)">
                <span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-red-100 text-red-700">
                  {{ inactiveDays(p) }}d sin actividad
                </span>
              </template>
              <template v-else-if="p.last_activity_at">
                {{ timeAgo(p.last_activity_at) }}
              </template>
              <template v-else-if="p.created_at">
                {{ timeAgo(p.created_at) }}
                <span class="text-[10px] text-gray-300 ml-1">(creada)</span>
              </template>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-300 tabular-nums">{{ p.view_count }}</td>
            <td class="px-6 py-4 text-center">
              <UiTooltip v-if="p.heat_score > 0 && p.engagement_summary" position="left" backgroundColor="bg-gray-900" width="max-w-[260px]">
                <template #trigger>
                  <span class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold text-white cursor-help" :class="heatScoreColor(p.heat_score)">
                    {{ p.heat_score }}
                  </span>
                </template>
                <div class="space-y-1.5 text-xs">
                  <div class="flex justify-between gap-3">
                    <span class="text-gray-400">Vistas</span>
                    <span class="font-medium">{{ p.engagement_summary.views }}</span>
                  </div>
                  <div v-if="p.engagement_summary.last_activity" class="flex justify-between gap-3">
                    <span class="text-gray-400">Última visita</span>
                    <span class="font-medium">{{ p.engagement_summary.last_activity }}</span>
                  </div>
                  <div class="flex justify-between gap-3">
                    <span class="text-gray-400">Inversión</span>
                    <span class="font-medium">{{ formatInvestmentTime(p.engagement_summary.investment_time_sec) }}</span>
                  </div>
                  <div v-if="p.engagement_summary.technical_viewed" class="flex justify-between gap-3">
                    <span class="text-teal-400">Det. técnico</span>
                    <span class="font-medium text-teal-300">{{ formatInvestmentTime(p.engagement_summary.technical_time_sec) }}</span>
                  </div>
                  <div v-if="p.engagement_summary.unique_devices > 1" class="flex justify-between gap-3">
                    <span class="text-gray-400">Dispositivos</span>
                    <span class="font-medium">{{ p.engagement_summary.unique_devices }}</span>
                  </div>
                  <div v-if="p.engagement_summary.skipped_sections && p.engagement_summary.skipped_sections.length" class="pt-1 border-t border-gray-700">
                    <span class="text-gray-400">No revisó:</span>
                    <span class="text-amber-400 ml-1">{{ p.engagement_summary.skipped_sections.map(s => sectionLabel(s)).join(', ') }}</span>
                  </div>
                </div>
              </UiTooltip>
              <span v-else-if="p.heat_score > 0" class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold text-white" :class="heatScoreColor(p.heat_score)">
                {{ p.heat_score }}
              </span>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>
            <td class="px-6 py-4">
              <div class="flex items-center gap-2">
                <button
                  class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
                  @click.stop="actionsModalProposal = p"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

    <!-- Actions modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="actionsModalProposal"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="actionsModalProposal = null"
        >
          <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full dark:bg-gray-800">
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
              <div>
                <h3 class="text-base font-bold text-gray-900 dark:text-gray-100 truncate">{{ actionsModalProposal.title }}</h3>
                <p class="text-xs text-gray-500 mt-0.5">{{ actionsModalProposal.client_name }}</p>
              </div>
              <button class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 transition-colors" @click="actionsModalProposal = null">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <!-- Actions list -->
            <div class="p-3 space-y-1 max-h-[60vh] overflow-y-auto">
              <template v-for="action in proposalActions" :key="action.key">
                <component
                  :is="action.href ? 'a' : action.to ? 'NuxtLink' : 'button'"
                  v-bind="action.href ? { href: action.href, target: '_blank', rel: 'noopener noreferrer' } : action.to ? { to: action.to } : {}"
                  class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors group"
                  :class="action.danger ? 'hover:bg-red-50' : 'hover:bg-gray-50'"
                  @click="action.onClick ? action.onClick() : null"
                >
                  <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
                    :class="action.danger ? 'bg-red-50 text-red-500' : action.bgClass || 'bg-gray-100'"
                  >
                    {{ action.icon }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <span class="text-sm font-medium block" :class="action.danger ? 'text-red-600' : action.textClass || 'text-gray-800'">{{ action.label }}</span>
                  </div>
                  <!-- Info tooltip -->
                  <div class="relative flex-shrink-0 group/info">
                    <span class="w-6 h-6 rounded-full bg-gray-100 group-hover/info:bg-emerald-50 flex items-center justify-center text-gray-400 group-hover/info:text-emerald-600 text-[11px] cursor-help transition-colors">?</span>
                    <div class="absolute right-full top-1/2 -translate-y-1/2 mr-2 w-52 bg-gray-900 text-white text-xs rounded-xl px-3 py-2 shadow-lg opacity-0 pointer-events-none group-hover/info:opacity-100 group-hover/info:pointer-events-auto transition-opacity z-10 leading-relaxed">
                      {{ action.info }}
                      <div class="absolute top-1/2 -translate-y-1/2 -right-1 w-2 h-2 bg-gray-900 rotate-45" />
                    </div>
                  </div>
                </component>
              </template>

            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Send confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="sendConfirmId"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="sendConfirmId = null"
        >
          <div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center dark:bg-gray-800">
            <div class="text-4xl mb-3">📤</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">¿Enviar esta propuesta?</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Se enviará un email al cliente con el enlace de la propuesta.</p>
            <div class="flex gap-3 justify-center">
              <button
                class="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors"
                :disabled="isSending"
                @click="confirmSend"
              >
                {{ isSending ? 'Enviando...' : 'Sí, enviar' }}
              </button>
              <button
                class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
                @click="sendConfirmId = null"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Quick-log activity modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="quickLogProposal"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="quickLogProposal = null"
        >
          <div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 dark:bg-gray-800">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-bold text-gray-900 dark:text-gray-100">Registrar actividad</h3>
              <button class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 transition-colors" @click="quickLogProposal = null">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <p class="text-xs text-gray-500 mb-4">{{ quickLogProposal.client_name }} — {{ quickLogProposal.title }}</p>
            <div class="space-y-3">
              <div>
                <label class="block text-xs text-gray-500 mb-1">Tipo de actividad</label>
                <select v-model="quickLogType" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white outline-none focus:ring-1 focus:ring-emerald-500">
                  <option value="call">📞 Llamada</option>
                  <option value="meeting">🤝 Reunión</option>
                  <option value="followup">📩 Seguimiento</option>
                  <option value="note">📝 Nota</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">Descripción</label>
                <input v-model="quickLogMessage" type="text" placeholder="Ej: Llamada de seguimiento, cliente interesado..." class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-emerald-500" @keyup.enter="confirmQuickLog" />
              </div>
            </div>
            <div class="flex gap-3 mt-5">
              <button
                class="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors disabled:opacity-50"
                :disabled="!quickLogMessage.trim() || isQuickLogging"
                @click="confirmQuickLog"
              >
                {{ isQuickLogging ? 'Guardando...' : 'Registrar' }}
              </button>
              <button
                class="px-4 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
                @click="quickLogProposal = null"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 dark:border-gray-700">
        <span class="text-xs text-gray-400">{{ filteredProposals.length }} propuestas</span>
        <div class="flex gap-1">
          <button
            v-for="page in totalPages"
            :key="page"
            class="w-8 h-8 rounded-lg text-xs font-medium transition-colors"
            :class="currentPage === page ? 'bg-emerald-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </div>

    <!-- Status change toast -->
    <Teleport to="body">
      <Transition name="toast-slide">
        <div
          v-if="statusToast"
          class="fixed bottom-6 right-6 z-[9999] flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-sm font-medium pointer-events-none"
          :class="statusToast.type === 'success'
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            : 'bg-red-50 text-red-700 border border-red-200'"
        >
          <svg v-if="statusToast.type === 'success'" class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          {{ statusToast.message }}
        </div>
      </Transition>
    </Teleport>

    <!-- Floating refresh button (above MetricsManual ? button) -->
    <button
      type="button"
      class="fixed bottom-[76px] right-6 z-50 w-12 h-12 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:opacity-50 flex items-center justify-center dark:bg-emerald-700 dark:hover:bg-emerald-600"
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
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import ProposalDashboard from '~/components/BusinessProposal/admin/ProposalDashboard.vue';
import MetricsManual from '~/components/BusinessProposal/admin/MetricsManual.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useProposalFilters } from '~/composables/useProposalFilters';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();
const proposals = computed(() => proposalStore.proposals);
const {
  currentFilters,
  savedTabs,
  activeTabId,
  isFilterPanelOpen,
  hasActiveFilters,
  activeFilterCount,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab,
  saveTab,
  updateTab,
  deleteTab,
  renameTab,
} = useProposalFilters();
const technicalFilter = ref(false);
const technicalFilterCount = computed(() =>
  proposals.value.filter(p => p.engagement_summary?.technical_viewed === true).length,
);
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();
const actionsModalProposal = ref(null);
const copiedId = ref(null);
const sendConfirmId = ref(null);
const isSending = ref(false);
const quickLogProposal = ref(null);
const quickLogType = ref('call');
const quickLogMessage = ref('');
const isQuickLogging = ref(false);
const searchQuery = ref('');
const showAlertForm = ref(false);
const alertError = ref('');
const newAlert = reactive({
  proposal: '',
  alert_type: 'reminder',
  message: '',
  alert_date: '',
});
const sortKey = ref('created_at');
const sortDir = ref('desc');
const currentPage = ref(1);
const pageSize = 15;
const zombieExpanded = ref(false);
const selectedIds = ref(new Set());
const isBulkActing = ref(false);
const isRefreshing = ref(false);

function toggleSelectAll() {
  if (selectedIds.value.size === paginatedProposals.value.length) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(paginatedProposals.value.map(p => p.id));
  }
}

function toggleSelect(id) {
  const s = new Set(selectedIds.value);
  if (s.has(id)) s.delete(id);
  else s.add(id);
  selectedIds.value = s;
}

function handleBulkAction(action) {
  const ids = [...selectedIds.value];
  const labels = { delete: 'eliminar', expire: 'expirar', resend: 're-enviar' };
  requestConfirm({
    title: `${(labels[action] || action).charAt(0).toUpperCase() + (labels[action] || action).slice(1)} propuestas`,
    message: `¿${labels[action] || action} ${ids.length} propuesta(s)?`,
    variant: action === 'delete' ? 'danger' : 'warning',
    confirmText: labels[action] || action,
    onConfirm: async () => {
      isBulkActing.value = true;
      const result = await proposalStore.bulkAction(ids, action);
      if (result.success) {
        selectedIds.value = new Set();
        proposalStore.fetchProposals();
      }
      isBulkActing.value = false;
    },
  });
}

const ZOMBIE_TYPES = ['zombie', 'zombie_draft', 'zombie_sent_stale'];
const zombieAlerts = computed(() =>
  alerts.value.filter(a => ZOMBIE_TYPES.includes(a.alert_type))
);
const activeAlerts = computed(() =>
  alerts.value.filter(a => !ZOMBIE_TYPES.includes(a.alert_type))
);

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortDir.value = 'desc';
  }
  currentPage.value = 1;
}

const filteredProposals = computed(() => {
  // Single filter pass: advanced filters + technical + search
  const isTechnical = technicalFilter.value;
  const q = searchQuery.value.trim().toLowerCase();
  let list = applyFilters(proposals.value).filter((p) => {
    if (isTechnical && p.engagement_summary?.technical_viewed !== true) return false;
    if (q && !(
      (p.title || '').toLowerCase().includes(q) ||
      (p.client_name || '').toLowerCase().includes(q) ||
      (p.client_email || '').toLowerCase().includes(q)
    )) return false;
    return true;
  });
  // Sort
  const sk = sortKey.value;
  const isNumericSort = sk === 'total_investment';
  const asc = sortDir.value === 'asc';
  list.sort((a, b) => {
    let va = a[sk];
    let vb = b[sk];
    if (isNumericSort) { va = Number(va) || 0; vb = Number(vb) || 0; }
    else { va = va || ''; vb = vb || ''; }
    if (va < vb) return asc ? -1 : 1;
    if (va > vb) return asc ? 1 : -1;
    return 0;
  });
  return list;
});

const totalPages = computed(() => Math.ceil(filteredProposals.value.length / pageSize));
const paginatedProposals = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredProposals.value.slice(start, start + pageSize);
});

function formatAlertDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es', { day: 'numeric', month: 'short', year: d.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined });
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const d = new Date(dateStr);
  const diffMs = now - d;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'ahora';
  if (mins < 60) return `hace ${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `hace ${days}d`;
  return d.toLocaleDateString();
}


const proposalActions = computed(() => {
  const p = actionsModalProposal.value;
  if (!p) return [];
  const actions = [];

  actions.push({
    key: 'edit',
    icon: '✏️',
    label: 'Editar propuesta',
    info: 'Abre el editor para modificar secciones, precios y contenido de la propuesta.',
    to: `/panel/proposals/${p.id}/edit`,
    bgClass: 'bg-gray-100',
    textClass: 'text-gray-800',
    onClick: () => { actionsModalProposal.value = null; },
  });

  actions.push({
    key: 'preview',
    icon: '👁️',
    label: 'Ver preview',
    info: 'Abre la propuesta tal como la ve el cliente, sin registrar vistas.',
    href: `/proposal/${p.uuid}?preview=1`,
    bgClass: 'bg-purple-50 text-purple-600',
    textClass: 'text-purple-700',
  });

  if (p.status === 'draft') {
    actions.push({
      key: 'send',
      icon: '📤',
      label: 'Enviar al cliente',
      info: 'Envía un email al cliente con el enlace de la propuesta. Cambia el estado a "enviada".',
      bgClass: 'bg-blue-50 text-blue-600',
      textClass: 'text-blue-700',
      onClick: () => { actionsModalProposal.value = null; handleSend(p.id); },
    });
  }

  if (['sent', 'viewed'].includes(p.status)) {
    actions.push({
      key: 'resend',
      icon: '🔄',
      label: 'Re-enviar email',
      info: 'Envía nuevamente el email al cliente. Mantiene la misma fecha de expiración.',
      bgClass: 'bg-blue-50 text-blue-600',
      textClass: 'text-blue-700',
      onClick: () => { actionsModalProposal.value = null; handleResend(p.id); },
    });
  }

  actions.push({
    key: 'copy',
    icon: copiedId.value === p.id ? '✅' : '🔗',
    label: copiedId.value === p.id ? '¡Enlace copiado!' : 'Copiar enlace',
    info: 'Copia el enlace público de la propuesta al portapapeles para compartir manualmente.',
    bgClass: copiedId.value === p.id ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100',
    textClass: copiedId.value === p.id ? 'text-emerald-600' : 'text-gray-800',
    onClick: () => { handleCopyLink(p); },
  });

  actions.push({
    key: 'whatsapp',
    icon: '💬',
    label: 'Enviar por WhatsApp',
    info: 'Abre WhatsApp con un mensaje pre-escrito incluyendo el enlace de la propuesta.',
    href: buildWhatsAppUrl(p),
    bgClass: 'bg-green-50 text-green-600',
    textClass: 'text-green-700',
  });

  actions.push({
    key: 'quick-log',
    icon: '📝',
    label: 'Registrar actividad',
    info: 'Registra rápidamente una llamada, reunión o nota sin entrar a la propuesta.',
    bgClass: 'bg-teal-50 text-teal-600',
    textClass: 'text-teal-700',
    onClick: () => { actionsModalProposal.value = null; openQuickLog(p); },
  });

  actions.push({
    key: 'duplicate',
    icon: '📋',
    label: 'Duplicar propuesta',
    info: 'Crea una copia exacta de esta propuesta para reutilizar con otro cliente.',
    bgClass: 'bg-indigo-50 text-indigo-600',
    textClass: 'text-indigo-700',
    onClick: () => { actionsModalProposal.value = null; handleDuplicate(p.id); },
  });

  actions.push({
    key: 'toggle',
    icon: p.is_active ? '⏸️' : '▶️',
    label: p.is_active ? 'Desactivar' : 'Activar',
    info: p.is_active
      ? 'Desactiva la propuesta. El cliente no podrá acceder al enlace.'
      : 'Reactiva la propuesta para que el cliente pueda verla nuevamente.',
    bgClass: p.is_active ? 'bg-yellow-50 text-yellow-600' : 'bg-emerald-50 text-emerald-600',
    textClass: p.is_active ? 'text-yellow-700' : 'text-emerald-700',
    onClick: () => { actionsModalProposal.value = null; handleToggleActive(p.id, p.is_active); },
  });

  actions.push({
    key: 'delete',
    icon: '🗑️',
    label: 'Eliminar',
    info: 'Elimina permanentemente la propuesta. Esta acción no se puede deshacer.',
    danger: true,
    onClick: () => { actionsModalProposal.value = null; handleDelete(p.id); },
  });

  return actions;
});

const router = useRouter();
function navigateToProposal(id, event) {
  const path = localePath(`/panel/proposals/${id}/edit`);
  if (event?.ctrlKey || event?.metaKey) {
    window.open(path, '_blank');
  } else {
    router.push(path);
  }
}

const statusLabelMap = {
  draft: 'Borrador',
  sent: 'Enviadas',
  viewed: 'Vistas',
  accepted: 'Aceptadas',
  rejected: 'Rechazadas',
  negotiating: 'Negociando',
  expired: 'Expiradas',
};
function statusLabel(s) { return statusLabelMap[s] || s; }

// Contract modal for inline negotiation
const showContractModal = ref(false);
const contractModalProposal = ref(null);

// Status change feedback
const updatingStatusId = ref(null);
const statusToast = ref(null);
let toastTimer = null;

function showStatusToast(message, type) {
  if (toastTimer) clearTimeout(toastTimer);
  statusToast.value = { message, type };
  toastTimer = setTimeout(() => { statusToast.value = null; }, 3500);
}

async function handleInlineStatusChange(proposal, newStatus, event) {
  if (newStatus === 'negotiating') {
    contractModalProposal.value = proposal;
    showContractModal.value = true;
    // Revert the select visually
    if (event?.target) event.target.value = proposal.status;
    return;
  }
  updatingStatusId.value = proposal.id;
  try {
    const result = await proposalStore.updateProposalStatus(proposal.id, newStatus);
    if (result.success) {
      showStatusToast('Estado actualizado correctamente', 'success');
    } else {
      showStatusToast('Error al actualizar el estado', 'error');
      proposalStore.fetchProposals();
    }
  } finally {
    updatingStatusId.value = null;
  }
}

async function handleContractConfirmFromList(params) {
  showContractModal.value = false;
  if (!contractModalProposal.value) return;
  const result = await proposalStore.saveContractAndNegotiate(contractModalProposal.value.id, params);
  if (result.success) {
    proposalStore.fetchProposals();
  }
  contractModalProposal.value = null;
}

const alerts = ref([]);

async function refreshData() {
  isRefreshing.value = true;
  try {
    await proposalStore.fetchProposals();
    const alertResult = await proposalStore.fetchAlerts();
    if (alertResult.success) alerts.value = alertResult.data || [];
  } finally {
    isRefreshing.value = false;
  }
}

onMounted(async () => {
  proposalStore.fetchProposals();
  const alertResult = await proposalStore.fetchAlerts();
  if (alertResult.success) alerts.value = alertResult.data || [];
});

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});

function alertIcon(type) {
  const map = {
    not_viewed: '👁️‍🗨️', not_responded: '⏳', expiring_soon: '🔥',
    manual_reminder: '🔔', manual_followup: '📩', manual_call: '📞',
    manual_meeting: '🤝', manual_custom: '📝',
    seller_inactive: '🏷️', zombie: '💀', late_return: '🔄',
    manual_discount_suggestion: '💰', discount_suggestion: '💰',
    manual_post_expiration_visit: '🔥🕰️', post_expiration_visit: '🔥🕰️',
    manual_engagement_decay: '📉', engagement_decay: '📉',
  };
  return map[type] || '⚠️';
}

function alertBorderClass(priority) {
  if (priority === 'critical') return 'border-red-300 hover:border-red-400 dark:border-red-700 dark:hover:border-red-500';
  if (priority === 'high') return 'border-amber-200 hover:border-amber-300 dark:border-amber-700 dark:hover:border-amber-500';
  return 'border-gray-200 hover:border-gray-300 dark:border-gray-600 dark:hover:border-gray-500';
}

async function handleCreateAlert() {
  alertError.value = '';
  const payload = {
    proposal: newAlert.proposal,
    alert_type: newAlert.alert_type,
    message: newAlert.message,
    alert_date: newAlert.alert_date
      ? new Date(newAlert.alert_date).toISOString()
      : new Date().toISOString(),
  };
  const result = await proposalStore.createAlert(payload);
  if (result.success) {
    showAlertForm.value = false;
    newAlert.proposal = '';
    newAlert.alert_type = 'reminder';
    newAlert.message = '';
    newAlert.alert_date = '';
    const alertResult = await proposalStore.fetchAlerts();
    if (alertResult.success) alerts.value = alertResult.data || [];
  } else {
    alertError.value = 'Error al crear el recordatorio.';
  }
}

async function handleDismissAlert(alertId) {
  const result = await proposalStore.dismissAlert(alertId);
  if (result.success) {
    alerts.value = alerts.value.filter(a => a.manual_alert_id !== alertId);
  }
}

function handleCreateTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

function handleResetFilters() {
  resetFilters();
  isFilterPanelOpen.value = false;
}

function toggleTechnicalFilter() {
  technicalFilter.value = !technicalFilter.value;
  currentPage.value = 1;
}

function handleSend(id) {
  sendConfirmId.value = id;
}

async function confirmSend() {
  if (!sendConfirmId.value) return;
  isSending.value = true;
  try {
    await proposalStore.sendProposal(sendConfirmId.value);
    sendConfirmId.value = null;
    proposalStore.fetchProposals();
  } finally {
    isSending.value = false;
  }
}

function handleResend(id) {
  requestConfirm({
    title: 'Re-enviar propuesta',
    message: '¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración.',
    variant: 'info',
    confirmText: 'Re-enviar',
    onConfirm: async () => {
      await proposalStore.resendProposal(id);
      proposalStore.fetchProposals();
    },
  });
}

function handleToggleActive(id, currentlyActive) {
  const label = currentlyActive ? 'desactivar' : 'activar';
  requestConfirm({
    title: `${label.charAt(0).toUpperCase() + label.slice(1)} propuesta`,
    message: `¿${label.charAt(0).toUpperCase() + label.slice(1)} esta propuesta?`,
    variant: 'warning',
    confirmText: label.charAt(0).toUpperCase() + label.slice(1),
    onConfirm: () => proposalStore.toggleProposalActive(id),
  });
}

async function handleDuplicate(id) {
  const result = await proposalStore.duplicateProposal(id);
  if (result.success) {
    router.push(localePath(`/panel/proposals/${result.data.id}/edit`));
  }
}

function handleCopyLink(p) {
  const url = `${window.location.origin}/proposal/${p.uuid}`;
  navigator.clipboard.writeText(url).then(() => {
    copiedId.value = p.id;
    setTimeout(() => { copiedId.value = null; }, 1500);
  });
}

function handleDelete(id) {
  requestConfirm({
    title: 'Eliminar propuesta',
    message: '¿Eliminar esta propuesta? Esta acción no se puede deshacer.',
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: () => proposalStore.deleteProposal(id),
  });
}

function statusClass(status) {
  const map = {
    draft: 'bg-gray-100 text-gray-600',
    sent: 'bg-blue-50 text-blue-700',
    viewed: 'bg-green-50 text-green-700',
    accepted: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-700',
    negotiating: 'bg-amber-50 text-amber-700',
    expired: 'bg-yellow-50 text-yellow-700',
  };
  return map[status] || 'bg-gray-100 text-gray-600';
}

function isInactive(p) {
  if (!['sent', 'viewed'].includes(p.status)) return false;
  const ref = p.last_activity_at || p.sent_at || p.created_at;
  if (!ref) return false;
  return (Date.now() - new Date(ref).getTime()) / 86400000 >= 3;
}

function inactiveDays(p) {
  const ref = p.last_activity_at || p.sent_at || p.created_at;
  if (!ref) return 0;
  return Math.floor((Date.now() - new Date(ref).getTime()) / 86400000);
}

function heatScoreColor(score) {
  if (score >= 8) return 'bg-red-500';
  if (score >= 5) return 'bg-orange-400';
  if (score >= 2) return 'bg-yellow-400 text-gray-800';
  return 'bg-gray-300 text-gray-700';
}

function formatInvestmentTime(seconds) {
  if (!seconds || seconds === 0) return '0s';
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

function sectionLabel(sectionType) {
  const labels = {
    investment: 'Inversión',
    timeline: 'Timeline',
    functional_requirements: 'Requerimientos',
    final_note: 'Nota final',
  };
  return labels[sectionType] || sectionType;
}

function openQuickLog(p) {
  quickLogProposal.value = p;
  quickLogType.value = 'call';
  quickLogMessage.value = '';
}

async function confirmQuickLog() {
  if (!quickLogProposal.value || !quickLogMessage.value.trim()) return;
  isQuickLogging.value = true;
  try {
    await proposalStore.logActivity(quickLogProposal.value.id, {
      change_type: quickLogType.value,
      description: quickLogMessage.value.trim(),
    });
    quickLogProposal.value = null;
    proposalStore.fetchProposals();
  } finally {
    isQuickLogging.value = false;
  }
}

function buildWhatsAppUrl(p) {
  const url = `${window.location.origin}/proposal/${p.uuid}`;
  const phone = (p.client_phone || '').replace(/\D/g, '');
  const msg = encodeURIComponent(
    `Hola ${p.client_name}, te comparto la propuesta "${p.title}": ${url}\n\n¿Tienes alguna pregunta?`
  );
  return phone
    ? `https://wa.me/${phone}?text=${msg}`
    : `https://wa.me/?text=${msg}`;
}
</script>

<style scoped>
.fade-modal-enter-active,
.fade-modal-leave-active {
  transition: opacity 0.2s ease;
}
.fade-modal-enter-from,
.fade-modal-leave-to {
  opacity: 0;
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
