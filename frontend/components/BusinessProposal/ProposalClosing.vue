<template>
  <section ref="sectionRef" class="proposal-closing min-h-screen w-full bg-white flex flex-col items-center justify-center py-8 px-6 md:px-12 lg:px-24">
    <div class="max-w-4xl w-full mx-auto text-center flex flex-col items-center gap-6">
      <!-- Validity notice -->
      <div v-if="displayedValidity" ref="validityRef" data-animate="fade-up" class="validity-notice w-full bg-esmerald/5 border border-esmerald/15 p-4 md:p-6 rounded-xl text-left">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-esmerald/60 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
          </svg>
          <div>
            <h4 class="font-bold text-esmerald mb-1 text-sm md:text-base">{{ t.validityTitle }}</h4>
            <p class="text-xs md:text-sm text-esmerald/70">{{ displayedValidity }}</p>
          </div>
        </div>
      </div>

      <!-- Thank you message -->
      <div v-if="thankYouMessage" data-animate="fade-up">
        <h3 class="text-2xl md:text-3xl font-bold text-esmerald mb-2">{{ t.thankYouTitle }}</h3>
        <p class="text-base md:text-lg text-esmerald/70 font-light max-w-2xl mx-auto">{{ thankYouMessage }}</p>
      </div>

      <!-- Discount badge near accept button -->
      <div v-if="canRespond && !submitted && hasActiveDiscount" data-animate="fade-up" class="w-full max-w-md bg-lemon/20 border border-lemon/50 rounded-xl p-4 text-center">
        <p class="text-xs font-semibold text-esmerald uppercase tracking-wider mb-1">🔥 {{ t.specialPrice }}</p>
        <div class="flex items-baseline justify-center gap-2">
          <span class="text-2xl font-bold text-esmerald">{{ formatCurrency(proposal?.discounted_investment) }}</span>
          <span class="text-sm text-esmerald/40 line-through">{{ formatCurrency(effectiveTotal) }}</span>
          <span class="text-xs text-esmerald/60">{{ proposal?.currency }}</span>
        </div>
      </div>

      <!-- F12: Payment plan milestones -->
      <div v-if="canRespond && !submitted && paymentMilestones.length" data-animate="fade-up" class="w-full max-w-md bg-esmerald/5 border border-esmerald/15 rounded-xl p-4 text-left">
        <p class="text-xs font-semibold text-green-light uppercase tracking-wider mb-2">{{ t.paymentPlanTitle }}</p>
        <div class="space-y-2">
          <div v-for="(m, i) in paymentMilestones" :key="i" class="flex items-center gap-3">
            <span class="w-6 h-6 rounded-full bg-esmerald-light/60 text-esmerald text-xs font-bold flex items-center justify-center flex-shrink-0">{{ i + 1 }}</span>
            <div class="flex-1 min-w-0">
              <span class="text-sm font-medium text-esmerald/80">{{ m.label }}</span>
              <span class="text-sm text-esmerald font-bold ml-2">{{ m.amount }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Payment options breakdown — visible before accept -->
      <div v-if="canRespond && !submitted && closingPaymentOptions.length" data-animate="fade-up" class="w-full max-w-md bg-esmerald rounded-2xl p-5 text-left">
        <p class="text-xs font-semibold text-green-light uppercase tracking-wider mb-1">{{ t.paymentPlanTitle }}</p>
        <p class="text-lg font-bold text-lemon mb-3">{{ closingPaymentOptions.length }} {{ t.flexiblePayments }}</p>
        <div class="space-y-2">
          <div v-for="(opt, i) in closingPaymentOptions" :key="i" class="flex items-center justify-between gap-3 bg-white/10 rounded-xl px-4 py-3">
            <span class="text-sm text-white/80">{{ opt.label }}</span>
            <span class="text-sm font-bold text-lemon whitespace-nowrap">{{ opt.description }}</span>
          </div>
        </div>
        <div v-if="effectiveTotal" class="text-center mt-4 pt-3 border-t border-white/15">
          <span class="text-xs text-green-light/70">{{ t.scopeInvestment }}:</span>
          <span class="text-lg font-bold text-lemon ml-2">{{ formatCurrency(effectiveTotal) }}</span>
          <span class="text-xs text-green-light/70 ml-1">{{ proposal.currency }}</span>
        </div>
      </div>

      <!-- Action buttons — professional B2B hierarchy -->
      <div v-if="canRespond && !submitted" data-animate="fade-up" class="w-full max-w-md pt-2">
        <!-- Primary CTA -->
        <button
          class="w-full py-4 bg-esmerald text-lemon rounded-2xl font-bold text-lg
                 hover:bg-esmerald/90 transition-all shadow-[0_0_24px_rgba(16,185,129,0.18)]
                 hover:shadow-[0_0_32px_rgba(16,185,129,0.3)] flex items-center justify-center gap-2.5 accept-pulse"
          :disabled="isSubmitting"
          @click="showAcceptConfirm = true"
        >
          ✅ {{ t.acceptBtn }}
        </button>

        <!-- Secondary actions — side by side -->
        <div class="grid grid-cols-2 gap-3 mt-3">
          <button
            class="py-3 bg-esmerald/5 border border-esmerald/15 text-esmerald rounded-xl font-medium text-sm
                   hover:bg-esmerald/10 transition-colors flex items-center justify-center gap-1.5"
            :disabled="isSubmitting"
            @click="showNegotiateModal = true"
          >
            🤝 {{ t.negotiateBtn }}
          </button>
          <button
            class="py-3 bg-esmerald/5 border border-esmerald/15 text-esmerald rounded-xl font-medium text-sm
                   hover:bg-esmerald/10 transition-colors flex items-center justify-center gap-1.5"
            :disabled="isSubmitting"
            @click="showCommentModal = true"
          >
            💬 {{ t.commentBtn }}
          </button>
        </div>

        <!-- Tertiary links — inline, subtle -->
        <div class="flex items-center justify-center gap-4 mt-4">
          <button
            class="text-xs text-esmerald/40 hover:text-esmerald/60 transition-colors"
            :disabled="isSubmitting"
            @click="showRejectModal = true"
          >
            {{ t.rejectBtn }}
          </button>
          <span v-if="whatsappTalkUrl" class="text-esmerald/20">·</span>
          <a
            v-if="whatsappTalkUrl"
            :href="whatsappTalkUrl"
            target="_blank"
            class="text-xs text-esmerald/40 hover:text-esmerald/60 transition-colors flex items-center gap-1"
          >
            📞 {{ t.talkBtn }}
          </a>
        </div>
      </div>

      <!-- Comment submitted confirmation -->
      <div v-if="commentSubmitted && canRespond && !submitted" data-animate="fade-up" class="w-full max-w-md bg-esmerald/5 border border-esmerald/15 rounded-xl p-4 text-center">
        <p class="text-sm font-medium text-esmerald">✅ {{ t.commentSent }}</p>
      </div>

      <!-- F13: Post-acceptance welcome kit -->
      <div v-if="submitted || proposal?.status === 'accepted'" data-animate="fade-up" class="py-4 w-full max-w-lg">
        <div class="text-5xl mb-3 celebration-bounce">🎉</div>
        <p class="text-xl font-bold text-esmerald">{{ t.accepted }}</p>
        <p class="text-esmerald/70 mt-2 mb-6">{{ t.acceptedSub }}</p>

        <!-- Payment options breakdown -->
        <div v-if="closingPaymentOptions.length" class="w-full bg-esmerald p-5 rounded-2xl text-left mb-6">
          <p class="text-xs font-semibold text-green-light uppercase tracking-wider mb-1">{{ t.paymentPlanTitle }}</p>
          <p class="text-lg font-bold text-lemon mb-3">{{ closingPaymentOptions.length }} {{ t.flexiblePayments }}</p>
          <div class="space-y-2">
            <div v-for="(opt, i) in closingPaymentOptions" :key="i" class="flex items-center justify-between gap-3 bg-white/10 rounded-xl px-4 py-3">
              <span class="text-sm text-white/80">{{ opt.label }}</span>
              <span class="text-sm font-bold text-lemon whitespace-nowrap">{{ opt.description }}</span>
            </div>
          </div>
          <div v-if="effectiveTotal" class="text-center mt-4 pt-3 border-t border-white/15">
            <span class="text-xs text-green-light/70">{{ t.scopeInvestment }}:</span>
            <span class="text-lg font-bold text-lemon ml-2">{{ formatCurrency(effectiveTotal) }}</span>
            <span class="text-xs text-green-light/70 ml-1">{{ proposal.currency }}</span>
          </div>
        </div>

        <!-- PDF download -->
        <a
          v-if="proposal?.uuid"
          :href="pdfUrl"
          :download="pdfFilename"
          target="_blank"
          class="inline-flex items-center gap-2 px-6 py-3 bg-esmerald text-lemon rounded-xl font-bold text-sm hover:bg-esmerald/90 transition-colors shadow-sm mb-6"
        >
          📄 {{ t.downloadPdf }}
        </a>

        <!-- Onboarding timeline -->
        <div class="bg-esmerald/5 border border-esmerald/15 rounded-xl p-5 text-left space-y-4">
          <h4 class="font-bold text-esmerald text-sm">{{ t.onboardingTitle }}</h4>
          <div v-for="(step, i) in onboardingSteps" :key="i" class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-full bg-lemon text-esmerald text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{{ i + 1 }}</div>
            <div>
              <p class="text-sm font-medium text-esmerald">{{ step.title }}</p>
              <p class="text-xs text-esmerald/70">{{ step.desc }}</p>
            </div>
          </div>
        </div>

        <!-- PM WhatsApp contact -->
        <a
          v-if="whatsappTalkUrl"
          :href="whatsappTalkUrl"
          target="_blank"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-esmerald/5 border border-esmerald/15 text-esmerald rounded-xl text-sm font-medium hover:bg-esmerald/10 transition-colors mt-4"
        >
          💬 {{ t.contactPm }}
        </a>
      </div>

      <!-- Negotiating success -->
      <div v-else-if="negotiatingSubmitted || proposal?.status === 'negotiating'" data-animate="fade-up" class="py-4 w-full max-w-lg">
        <div class="text-5xl mb-3 celebration-bounce">🤝</div>
        <p class="text-xl font-bold text-amber-700">{{ t.negotiatingSuccess }}</p>
        <p class="text-gray-500 mt-2">{{ t.negotiatingSub }}</p>
      </div>

      <!-- Smart rejection recovery (Feature 12) -->
      <div v-else-if="rejectionSubmitted || proposal?.status === 'rejected'" data-animate="fade-up" class="py-4 w-full max-w-lg">
        <p class="text-lg text-gray-500 mb-6">{{ t.rejected }}</p>

        <!-- Budget too high -->
        <div v-if="submittedReason === t.reasons[0]" class="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-left">
          <h4 class="font-bold text-emerald-800 mb-2">💡 {{ t.recovery.budgetTitle }}</h4>
          <p class="text-sm text-emerald-700 mb-4">{{ t.recovery.budgetText }}</p>
          <a :href="whatsappRecoveryLink" target="_blank" class="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors">
            💬 {{ t.recovery.budgetCta }}
          </a>
        </div>

        <!-- Not the right time -->
        <div v-else-if="submittedReason === t.reasons[2]" class="bg-blue-50 border border-blue-200 rounded-xl p-5 text-left">
          <h4 class="font-bold text-blue-800 mb-2">⏰ {{ t.recovery.timeTitle }}</h4>
          <p class="text-sm text-blue-700 mb-4">{{ t.recovery.timeText }}</p>
          <button
            v-if="!followupScheduled"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors"
            :disabled="isScheduling"
            @click="scheduleReminder"
          >
            🔔 {{ isScheduling ? t.sending : t.recovery.timeCta }}
          </button>
          <p v-else class="text-sm font-medium text-blue-600">✅ {{ t.recovery.timeScheduled }}</p>
        </div>

        <!-- Found another option -->
        <div v-else-if="submittedReason === t.reasons[1]" class="bg-gray-50 border border-gray-200 rounded-xl p-5 text-left">
          <h4 class="font-bold text-gray-800 mb-2">🤝 {{ t.recovery.otherTitle }}</h4>
          <p class="text-sm text-gray-600">{{ t.recovery.otherText }}</p>
        </div>

        <!-- Does not meet expectations -->
        <div v-else-if="submittedReason === t.reasons[3]" class="bg-purple-50 border border-purple-200 rounded-xl p-5 text-left">
          <h4 class="font-bold text-purple-800 mb-2">🎯 {{ t.recovery.expectTitle }}</h4>
          <p class="text-sm text-purple-700 mb-4">{{ t.recovery.expectText }}</p>
          <a :href="whatsappRecoveryLink" target="_blank" class="inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-xl text-sm font-medium hover:bg-purple-700 transition-colors">
            💬 {{ t.recovery.expectCta }}
          </a>
        </div>

        <!-- Generic / Other -->
        <div v-else class="bg-gray-50 border border-gray-200 rounded-xl p-5 text-left">
          <h4 class="font-bold text-gray-800 mb-2">🙏 {{ t.recovery.genericTitle }}</h4>
          <p class="text-sm text-gray-600">{{ t.recovery.genericText }}</p>
        </div>
      </div>
    </div>
  </section>

  <!-- F16: Accept confirmation modal with optional condition note -->
  <teleport to="body">
    <div v-if="showAcceptConfirm" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showAcceptConfirm = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-5 sm:p-8 text-center">
        <div class="text-5xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-esmerald mb-2">{{ confirmTitleText }}</h3>
        <p class="text-esmerald/70 text-sm mb-4">{{ t.confirmText }}</p>
        <p v-if="scopeDisplay.length" class="text-xs text-green-light mb-4">
          {{ scopeDisplay.map(i => `${i.label}: ${i.value}`).join(' · ') }}
        </p>
        <div class="text-left mb-4">
          <label class="block text-xs text-esmerald/50 mb-1">{{ t.conditionLabel }}</label>
          <textarea
            v-model="conditionNote"
            rows="2"
            :placeholder="t.conditionPlaceholder"
            class="w-full px-3 py-2 border border-esmerald/15 rounded-xl text-sm focus:ring-2 focus:ring-esmerald/30 outline-none resize-none"
          />
        </div>
        <div class="flex gap-3 justify-center">
          <button class="px-6 py-2.5 bg-esmerald text-lemon rounded-xl font-medium text-sm hover:bg-esmerald/90 transition-colors" :disabled="isSubmitting" @click="confirmAccept">
            {{ isSubmitting ? t.sending : t.confirmYes }}
          </button>
          <button class="px-6 py-2.5 bg-esmerald/5 text-esmerald rounded-xl text-sm font-medium hover:bg-esmerald/10 transition-colors" @click="showAcceptConfirm = false">{{ t.cancel }}</button>
        </div>
      </div>
    </div>
  </teleport>

  <!-- Negotiate modal — adjustments only -->
  <teleport to="body">
    <div v-if="showNegotiateModal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showNegotiateModal = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-5 sm:p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ t.negotiateTitle }}</h3>
        <p class="text-gray-600 text-sm mb-4">{{ t.negotiateText }}</p>

        <!-- Structured adjustment reasons -->
        <div class="space-y-2 mb-4">
          <label
            v-for="reason in t.adjustmentReasons"
            :key="reason"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg border cursor-pointer transition-colors"
            :class="selectedAdjustments.includes(reason) ? 'bg-amber-50 border-amber-300' : 'border-gray-200 hover:border-amber-200'"
          >
            <input type="checkbox" :value="reason" v-model="selectedAdjustments" class="w-4 h-4 accent-amber-600 rounded" />
            <span class="text-sm text-gray-700">{{ reason }}</span>
          </label>
        </div>

        <textarea
          v-model="negotiateComment"
          rows="3"
          :placeholder="t.negotiatePlaceholder"
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 outline-none resize-none"
        />

        <div class="flex gap-3 justify-end mt-4">
          <button class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showNegotiateModal = false">{{ t.cancel }}</button>
          <button
            class="px-5 py-2 bg-amber-600 text-white rounded-xl text-sm font-medium hover:bg-amber-700 transition-colors"
            :disabled="isSubmitting || (!negotiateComment.trim() && !selectedAdjustments.length)"
            @click="confirmNegotiate"
          >
            {{ negotiateCtaText }}
          </button>
        </div>
      </div>
    </div>
  </teleport>

  <!-- Comment modal — lightweight, separate from negotiate -->
  <teleport to="body">
    <div v-if="showCommentModal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showCommentModal = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-5 sm:p-8">
        <h3 class="text-lg font-bold text-gray-900 mb-2">💬 {{ t.commentBtn }}</h3>
        <p class="text-gray-500 text-sm mb-4">{{ t.commentPlaceholder2 }}</p>

        <textarea
          v-model="negotiationComment"
          rows="3"
          :placeholder="t.commentPlaceholder2"
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none resize-none"
        />

        <div class="flex gap-3 justify-end mt-4">
          <button class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showCommentModal = false">{{ t.cancel }}</button>
          <button
            class="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors"
            :disabled="isCommenting || !negotiationComment.trim()"
            @click="submitComment"
          >
            {{ isCommenting ? t.sending : t.commentSend }}
          </button>
        </div>
      </div>
    </div>
  </teleport>

  <!-- Reject modal -->
  <teleport to="body">
    <div v-if="showRejectModal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showRejectModal = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-5 sm:p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ t.rejectTitle }}</h3>
        <p class="text-gray-600 text-sm mb-6">{{ t.rejectText }}</p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t.reasonLabel }}</label>
            <p class="text-xs text-gray-400 italic mb-2">{{ t.reasonNudge }}</p>
            <select v-model="rejectReason" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none bg-white">
              <option value="">{{ t.selectReason }}</option>
              <option v-for="reason in t.reasons" :key="reason" :value="reason">{{ reason }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ isOtherReason ? t.otherLabel : t.commentLabel }}</label>
            <textarea v-model="rejectComment" rows="3" :placeholder="isOtherReason ? t.otherPlaceholder : t.commentPlaceholder"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none resize-none" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-6">
          <button class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showRejectModal = false">{{ t.cancel }}</button>
          <button class="px-5 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition-colors" :disabled="isSubmitting" @click="confirmReject">
            {{ isSubmitting ? t.sending : t.confirmReject }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted, toRef, nextTick } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';
import { useExpirationTimer } from '~/composables/useExpirationTimer';
import confetti from 'canvas-confetti';

const sectionRef = ref(null);
const validityRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  proposal: { type: Object, default: null },
  validityMessage: { type: String, default: '' },
  thankYouMessage: { type: String, default: '' },
  expiresAt: { type: String, default: '' },
  language: { type: String, default: 'es' },
  whatsappLink: { type: String, default: '' },
  paymentOptions: { type: Array, default: () => [] },
  customizedTotal: { type: Number, default: null },
  selectedModuleIds: { type: Array, default: () => [] },
});

// Use customizedTotal from calculator when available, otherwise fall back to proposal.total_investment
const effectiveTotal = computed(() => props.customizedTotal ?? props.proposal?.total_investment);

const whatsappTalkUrl = computed(() => {
  if (props.whatsappLink) return props.whatsappLink;
  const title = props.proposal?.title || '';
  if (!title) return '';
  const msg = props.language === 'en'
    ? encodeURIComponent(`Hi, I'm reviewing the proposal "${title}" and I'd like to talk before making a decision.`)
    : encodeURIComponent(`Hola, estoy revisando la propuesta "${title}" y me gustaría hablar antes de tomar una decisión.`);
  return `https://wa.me/573238122373?text=${msg}`;
});

const i18nStrings = {
  es: {
    validityTitle: 'Validez de la Propuesta',
    thankYouTitle: '¡Gracias por tu Tiempo!',
    acceptBtn: 'Acepto la propuesta',
    negotiateBtn: 'Necesito ajustes',
    negotiateTitle: 'Me interesa, pero negociemos alcance',
    negotiateText: 'Cuéntanos qué ajustes necesitas. Nuestro equipo te contactará para conversar opciones sin compromiso.',
    negotiatePlaceholder: 'Ej: Me gustaría reducir el número de módulos, ajustar el timeline, explorar un precio diferente...',
    negotiateConfirm: 'Enviar solicitud de ajustes',
    negotiatingSuccess: '¡Solicitud recibida!',
    negotiatingSub: 'Nuestro equipo revisará tus notas y te contactará pronto para conversar opciones.',
    talkBtn: 'Prefiero hablar antes de decidir',
    commentBtn: 'Tengo comentarios por escrito',
    commentTitle: 'Tus comentarios nos ayudan',
    commentText: 'Sin compromiso — cuéntanos qué dudas tienes o qué ajustes necesitarías para avanzar.',
    commentPlaceholder2: 'Ej: El precio está un poco fuera de mi presupuesto, ¿podemos explorar opciones?',
    commentSend: 'Enviar mensaje',
    commentSent: 'Mensaje enviado. Te contactaremos pronto.',
    rejectBtn: 'No es el momento',
    confirmTitle: '¡Perfecto{clientName}!',
    confirmText: 'Te escribiremos en menos de 2 horas. Mientras, puedes descargar un resumen de lo acordado.',
    confirmYes: '¡Confirmar!',
    cancel: 'Cancelar',
    sending: 'Enviando...',
    accepted: '¡Propuesta aceptada!',
    acceptedSub: 'Te enviaremos un email de confirmación.',
    rejected: 'Propuesta rechazada. Gracias por tu tiempo.',
    rejectTitle: 'Lamentamos que no sea el momento',
    rejectText: 'Tu opinión es muy importante para nosotros. ¿Podrías indicarnos el motivo?',
    reasonLabel: 'Motivo (opcional)',
    reasonNudge: 'Nos ayudaría mucho saber por qué — tu respuesta es opcional y confidencial.',
    selectReason: 'Selecciona un motivo...',
    reasons: ['Presupuesto muy alto', 'Encontré otra opción', 'No es el momento', 'No cumple mis expectativas', 'Otros'],
    otherReason: 'Otros',
    otherLabel: 'Cuéntanos más',
    commentLabel: 'Comentario adicional (opcional)',
    otherPlaceholder: 'Escribe tu motivo aquí...',
    commentPlaceholder: 'Algún comentario adicional...',
    confirmReject: 'Confirmar rechazo',
    specialPrice: 'Precio especial disponible',
    paymentPlanTitle: 'Formas de pago',
    flexiblePayments: 'pagos flexibles',
    downloadPdf: 'Descargar resumen PDF',
    onboardingTitle: '¿Qué sigue?',
    contactPm: 'Contactar a tu Project Manager',
    conditionLabel: '¿Aceptas con alguna condición? (opcional)',
    conditionPlaceholder: 'Ej: Acepto, pero necesito que se incluya X...',
    adjustmentReasons: [
      'El presupuesto es alto para este momento',
      'Necesito ajustar el alcance o quitar módulos',
      'Los tiempos de entrega no me funcionan',
      'Quiero agregar o cambiar funcionalidades',
      'Necesito aprobación de otro decisor',
      'Otro ajuste',
    ],
    negotiateConfirmOne: 'Enviar solicitud de ajuste',
    negotiateConfirmMultiple: 'Enviar {count} ajustes',
    scopeSummaryTitle: 'Estás aprobando:',
    scopeProject: 'Proyecto',
    scopeInvestment: 'Inversión',
    scopeModules: 'Módulos',
    scopeStart: 'Inicio estimado',
    recovery: {
      budgetTitle: '¿Qué tal una versión más enfocada?',
      budgetText: 'Entendemos. Podemos ajustar el alcance del proyecto para adaptarnos a tu presupuesto. ¿Te gustaría explorar opciones?',
      budgetCta: 'Explorar opciones',
      timeTitle: '¿Te recordamos más adelante?',
      timeText: 'Sin problema. Podemos recordarte en 3 meses para retomar la conversación cuando sea más oportuno.',
      timeCta: 'Recordármelo en 3 meses',
      timeScheduled: 'Listo, te recordaremos en 3 meses.',
      otherTitle: 'Gracias por tu honestidad',
      otherText: 'Apreciamos tu transparencia. Si algo cambia o necesitas una segunda opinión, estaremos aquí.',
      expectTitle: 'Queremos entender mejor',
      expectText: '¿Te gustaría agendar 15 minutos para contarnos qué esperabas? Podemos ajustar la propuesta.',
      expectCta: 'Conversemos',
      genericTitle: 'Gracias por tu tiempo',
      genericText: 'Valoramos tu opinión. Si en el futuro necesitas algo, no dudes en contactarnos.',
    },
  },
  en: {
    validityTitle: 'Proposal Validity',
    thankYouTitle: 'Thank You for Your Time!',
    acceptBtn: 'I accept the proposal',
    negotiateBtn: 'I need adjustments',
    negotiateTitle: 'I\'m interested, but let\'s adjust the scope',
    negotiateText: 'Tell us what adjustments you need. Our team will reach out to discuss options with no commitment.',
    negotiatePlaceholder: 'E.g.: I\'d like to reduce the number of modules, adjust the timeline, explore a different price...',
    negotiateConfirm: 'Send adjustment request',
    negotiatingSuccess: 'Request received!',
    negotiatingSub: 'Our team will review your notes and contact you soon to discuss options.',
    talkBtn: 'I prefer to talk before deciding',
    commentBtn: 'I have written comments',
    commentTitle: 'Your feedback helps us',
    commentText: 'No commitment — tell us what questions you have or what adjustments you would need to move forward.',
    commentPlaceholder2: 'E.g.: The price is a bit over my budget, can we explore options?',
    commentSend: 'Send message',
    commentSent: 'Message sent. We will be in touch soon.',
    rejectBtn: 'Not the right time',
    confirmTitle: 'Awesome{clientName}!',
    confirmText: 'We\'ll reach out within 2 hours. Meanwhile, you can download a summary of what was agreed.',
    confirmYes: 'Confirm!',
    cancel: 'Cancel',
    sending: 'Sending...',
    accepted: 'Proposal accepted!',
    acceptedSub: 'We will send you a confirmation email.',
    rejected: 'Proposal declined. Thank you for your time.',
    rejectTitle: 'We\'re sorry it\'s not the right time',
    rejectText: 'Your feedback is very important to us. Could you let us know why?',
    reasonLabel: 'Reason (optional)',
    reasonNudge: 'It would really help us to know why — your answer is optional and confidential.',
    selectReason: 'Select a reason...',
    reasons: ['Budget too high', 'Found another option', 'Not the right time', 'Does not meet my expectations', 'Other'],
    otherReason: 'Other',
    otherLabel: 'Tell us more',
    commentLabel: 'Additional comment (optional)',
    otherPlaceholder: 'Write your reason here...',
    commentPlaceholder: 'Any additional comments...',
    confirmReject: 'Confirm rejection',
    specialPrice: 'Special price available',
    paymentPlanTitle: 'Payment options',
    flexiblePayments: 'flexible payments',
    downloadPdf: 'Download PDF summary',
    onboardingTitle: 'What\'s next?',
    contactPm: 'Contact your Project Manager',
    conditionLabel: 'Accept with a condition? (optional)',
    conditionPlaceholder: 'E.g.: I accept, but I need X to be included...',
    adjustmentReasons: [
      'The budget is high for right now',
      'I need to adjust the scope or remove modules',
      'The delivery timeline doesn\'t work for me',
      'I want to add or change features',
      'I need approval from another decision-maker',
      'Other adjustment',
    ],
    negotiateConfirmOne: 'Send adjustment request',
    negotiateConfirmMultiple: 'Send {count} adjustments',
    scopeSummaryTitle: 'You are approving:',
    scopeProject: 'Project',
    scopeInvestment: 'Investment',
    scopeModules: 'Modules',
    scopeStart: 'Estimated start',
    recovery: {
      budgetTitle: 'How about a more focused version?',
      budgetText: 'We understand. We can adjust the project scope to fit your budget. Would you like to explore options?',
      budgetCta: 'Explore options',
      timeTitle: 'Should we remind you later?',
      timeText: 'No problem. We can remind you in 3 months to revisit the conversation when the timing is better.',
      timeCta: 'Remind me in 3 months',
      timeScheduled: 'Done! We\'ll remind you in 3 months.',
      otherTitle: 'Thank you for your honesty',
      otherText: 'We appreciate your transparency. If anything changes or you need a second opinion, we\'re here.',
      expectTitle: 'We want to understand better',
      expectText: 'Would you like to schedule 15 minutes to tell us what you expected? We can adjust the proposal.',
      expectCta: 'Let\'s talk',
      genericTitle: 'Thank you for your time',
      genericText: 'We value your feedback. If you need anything in the future, don\'t hesitate to reach out.',
    },
  },
};

const t = computed(() => i18nStrings[props.language] || i18nStrings.es);

const { daysRemaining } = useExpirationTimer(toRef(props, 'expiresAt'));

const displayedValidity = computed(() => {
  if (!props.validityMessage) return '';
  if (daysRemaining.value === null) return props.validityMessage;
  const dayWord = props.language === 'en' ? 'days' : 'días';
  return props.validityMessage.replace(/\d+\s*(días|days)/, `${daysRemaining.value} ${dayWord}`);
});

onMounted(() => {
  setTimeout(() => {
    if (validityRef.value) {
      validityRef.value.classList.add('validity-blink');
      setTimeout(() => {
        validityRef.value?.classList.remove('validity-blink');
      }, 1400);
    }
  }, 600);
});

const proposalStore = useProposalStore();

const pdfUrl = computed(() => {
  const base = `/api/proposals/${props.proposal?.uuid}/pdf/`;
  if (props.selectedModuleIds.length) {
    return `${base}?selected_modules=${encodeURIComponent(props.selectedModuleIds.join(','))}`;
  }
  return base;
});

const pdfFilename = computed(() => {
  const title = props.proposal?.title || props.proposal?.client_name || 'Propuesta';
  const safe = title.replace(/[^\w\sáéíóúñÁÉÍÓÚÑ-]/g, '').trim().replace(/\s+/g, '_').slice(0, 100);
  const created = props.proposal?.created_at;
  const date = created ? new Date(created).toISOString().slice(0, 10) : new Date().toISOString().slice(0, 10);
  return `${safe}_${date}.pdf`;
});

const canRespond = computed(() => {
  const s = props.proposal?.status;
  return s === 'sent' || s === 'viewed';
});

const confirmTitleText = computed(() => {
  const name = props.proposal?.client_name;
  const suffix = name ? `, ${name}` : '';
  return t.value.confirmTitle.replace('{clientName}', suffix);
});

const hasActiveDiscount = computed(() => {
  return props.proposal?.discount_percent > 0 && props.proposal?.discounted_investment;
});

function formatCurrency(value) {
  if (!value) return '';
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

const isSubmitting = ref(false);
const submitted = ref(false);
const rejectionSubmitted = ref(false);
const submittedReason = ref('');
const showAcceptConfirm = ref(false);
const showRejectModal = ref(false);
const showNegotiateModal = ref(false);
const negotiateComment = ref('');
const negotiatingSubmitted = ref(false);
const showCommentModal = ref(false);
const negotiationComment = ref('');
const isCommenting = ref(false);
const commentSubmitted = ref(false);
const rejectReason = ref('');
const rejectComment = ref('');
const isOtherReason = computed(() => rejectReason.value === t.value.otherReason);
const followupScheduled = ref(false);
const isScheduling = ref(false);
const conditionNote = ref('');
const selectedAdjustments = ref([]);

const negotiateCtaText = computed(() => {
  const count = selectedAdjustments.value.length;
  if (isSubmitting.value) return t.value.sending;
  if (count <= 1) return t.value.negotiateConfirmOne || t.value.negotiateConfirm;
  return (t.value.negotiateConfirmMultiple || t.value.negotiateConfirm).replace('{count}', count);
});

const scopeSummary = computed(() => {
  const p = props.proposal;
  if (!p) return [];
  const items = [];
  if (p.title) items.push({ label: t.value.scopeProject, value: p.title });
  const inv = effectiveTotal.value || p.investment;
  if (inv) {
    const numVal = parseFloat(String(inv).replace(/[^\d.]/g, ''));
    const formatted = !isNaN(numVal) && numVal > 0 ? formatCurrency(numVal) : inv;
    items.push({ label: t.value.scopeInvestment, value: formatted + ' ' + (p.currency || '') });
  }
  const mods = p.selected_modules || p.modules;
  if (Array.isArray(mods) && mods.length) items.push({ label: t.value.scopeModules, value: String(mods.length) });
  const start = p.estimated_start || p.start_date;
  if (start) items.push({ label: t.value.scopeStart, value: start });
  return items;
});

// scopeDisplay: like scopeSummary but replaces raw price with payment plan reference
const scopeDisplay = computed(() => {
  const p = props.proposal;
  if (!p) return [];
  const items = [];
  if (p.title) items.push({ label: t.value.scopeProject, value: p.title });
  // If payment milestones exist, show payment count instead of raw total
  const milestones = paymentMilestones.value;
  if (milestones.length) {
    const countLabel = props.language === 'en'
      ? `${milestones.length} payments`
      : `${milestones.length} pagos`;
    items.push({ label: t.value.scopeInvestment, value: countLabel });
  } else {
    const inv = effectiveTotal.value || p.investment;
    if (inv) {
      const numVal = parseFloat(String(inv).replace(/[^\d.]/g, ''));
      const formatted = !isNaN(numVal) && numVal > 0 ? formatCurrency(numVal) : inv;
      items.push({ label: t.value.scopeInvestment, value: formatted + ' ' + (p.currency || '') });
    }
  }
  const mods = p.selected_modules || p.modules;
  if (Array.isArray(mods) && mods.length) items.push({ label: t.value.scopeModules, value: String(mods.length) });
  const start = p.estimated_start || p.start_date;
  if (start) items.push({ label: t.value.scopeStart, value: start });
  return items;
});

const paymentMilestones = computed(() => {
  const opts = props.proposal?.payment_options;
  if (!opts || typeof opts !== 'object') return [];
  if (Array.isArray(opts)) return opts.map(o => ({ label: o.label || o.name || '', amount: o.amount || '' }));
  if (opts.milestones && Array.isArray(opts.milestones)) return opts.milestones;
  return [];
});

const closingPaymentOptions = computed(() => {
  if (!props.paymentOptions || !Array.isArray(props.paymentOptions)) return [];
  return props.paymentOptions.filter(o => o.label && o.description);
});

const onboardingSteps = computed(() => {
  const lang = props.language;
  if (lang === 'en') {
    return [
      { title: 'Confirmation email', desc: 'You will receive an email with the summary and next steps.' },
      { title: 'Kickoff call', desc: 'Within 48h, your Project Manager will contact you.' },
      { title: 'Project setup', desc: 'We set up the environment and start the first sprint.' },
    ];
  }
  return [
    { title: 'Email de confirmación', desc: 'Recibirás un email con el resumen y próximos pasos.' },
    { title: 'Llamada de kickoff', desc: 'En menos de 48h, tu Project Manager te contactará.' },
    { title: 'Setup del proyecto', desc: 'Configuramos el entorno e iniciamos el primer sprint.' },
  ];
});

const whatsappRecoveryLink = computed(() => {
  const title = props.proposal?.title || '';
  const msg = props.language === 'en'
    ? encodeURIComponent(`Hi, I'm reviewing the proposal "${title}" and I'd like to discuss options.`)
    : encodeURIComponent(`Hola, estoy revisando la propuesta "${title}" y me gustaría conversar sobre opciones.`);
  return `https://wa.me/573238122373?text=${msg}`;
});

function fireConfetti() {
  const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 10000 };
  confetti({ ...defaults, particleCount: 80, origin: { x: 0.5, y: 0.5 } });
  setTimeout(() => confetti({ ...defaults, particleCount: 50, origin: { x: 0.3, y: 0.6 } }), 250);
  setTimeout(() => confetti({ ...defaults, particleCount: 50, origin: { x: 0.7, y: 0.6 } }), 400);
}

async function confirmAccept() {
  if (!props.proposal?.uuid) return;
  isSubmitting.value = true;
  try {
    const extra = {};
    if (conditionNote.value.trim()) {
      extra.condition = conditionNote.value.trim();
    }
    const result = await proposalStore.respondToProposal(props.proposal.uuid, 'accepted', extra);
    if (result.success) {
      submitted.value = true;
      showAcceptConfirm.value = false;
      setTimeout(() => fireConfetti(), 500);
    }
  } finally {
    isSubmitting.value = false;
  }
}

async function confirmNegotiate() {
  if (!props.proposal?.uuid) return;
  isSubmitting.value = true;
  try {
    const parts = [];
    if (selectedAdjustments.value.length) {
      parts.push('[' + selectedAdjustments.value.join(', ') + ']');
    }
    if (negotiateComment.value.trim()) {
      parts.push(negotiateComment.value.trim());
    }
    const result = await proposalStore.respondToProposal(
      props.proposal.uuid, 'negotiating',
      { comment: parts.join(' — ') },
    );
    if (result.success) {
      negotiatingSubmitted.value = true;
      showNegotiateModal.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}

async function confirmReject() {
  if (!props.proposal?.uuid) return;
  isSubmitting.value = true;
  try {
    const result = await proposalStore.respondToProposal(
      props.proposal.uuid, 'rejected',
      { reason: rejectReason.value, comment: rejectComment.value },
    );
    if (result.success) {
      submittedReason.value = rejectReason.value;
      rejectionSubmitted.value = true;
      showRejectModal.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}

async function submitComment() {
  if (!props.proposal?.uuid || !negotiationComment.value.trim()) return;
  isCommenting.value = true;
  try {
    await proposalStore.commentOnProposal(props.proposal.uuid, negotiationComment.value.trim());
    commentSubmitted.value = true;
    showCommentModal.value = false;
    negotiationComment.value = '';
  } finally {
    isCommenting.value = false;
  }
}

async function scheduleReminder() {
  if (!props.proposal?.uuid) return;
  isScheduling.value = true;
  try {
    await proposalStore.scheduleFollowup(props.proposal.uuid, 3);
    followupScheduled.value = true;
  } finally {
    isScheduling.value = false;
  }
}
</script>

<style scoped>
.validity-blink {
  animation: validityDoublePulse 3.8s ease-in-out;
}

@keyframes validityDoublePulse {
  0%   { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.25); }
  10%  { box-shadow: 0 0 14px 5px rgba(234, 179, 8, 0.22); }
  24%  { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0); }
  38%  { box-shadow: 0 0 14px 5px rgba(234, 179, 8, 0.22); }
  54%  { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0); }
  100% { box-shadow: none; }
}

.accept-pulse {
  animation: acceptPulse 2.5s ease-in-out infinite;
}

@keyframes acceptPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

.celebration-bounce {
  animation: celebrationBounce 0.8s ease-out;
}

@keyframes celebrationBounce {
  0%   { transform: scale(0.3); opacity: 0; }
  50%  { transform: scale(1.2); }
  70%  { transform: scale(0.9); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
