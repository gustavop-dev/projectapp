<template>
  <div class="lt-card" data-testid="linktree-card">
    <!-- Header: wordmark (personal) + event badge -->
    <div class="lt-header">
      <div v-if="tree.kind === 'personal' && tree.show_brand_header" class="lt-wordmark">
        <span>Project</span>
        <span>App.</span>
      </div>
      <span v-if="tree.badge_text" class="lt-badge" data-testid="linktree-badge">{{ tree.badge_text }}</span>
    </div>

    <!-- Identity block -->
    <div v-if="tree.kind === 'personal'" class="lt-identity">
      <div v-if="tree.avatar || initials" class="lt-avatar">
        <img v-if="tree.avatar" :src="tree.avatar" :alt="tree.display_name" class="lt-avatar__photo" />
        <span v-else>{{ initials }}</span>
      </div>
      <div class="lt-identity__names">
        <h1 class="lt-name">{{ tree.display_name }}</h1>
        <span v-if="tree.role" class="lt-role">{{ tree.role }}</span>
      </div>
      <p v-if="tree.bio" class="lt-bio">{{ tree.bio }}</p>
    </div>

    <div v-else class="lt-identity lt-identity--company">
      <div v-if="tree.show_brand_header" class="lt-wordmark lt-wordmark--big">
        <span>Project</span>
        <span>App.</span>
      </div>
      <div v-if="tree.claim_line_1 || tree.claim_line_2" class="lt-claim">
        <span>{{ tree.claim_line_1 }}</span>
        <span class="lt-claim__accent">{{ tree.claim_line_2 }}</span>
      </div>
      <p v-if="tree.bio" class="lt-bio lt-bio--company">{{ tree.bio }}</p>
    </div>

    <!-- Buttons -->
    <div class="lt-buttons" data-testid="linktree-buttons">
      <template v-for="(group, gi) in buttonGroups" :key="gi">
        <div v-if="group.length > 1" class="lt-pair-row">
          <LinktreeButtonPill
            v-for="button in group"
            :key="button.id"
            :button="button"
            @action="$emit('action', $event)"
          />
        </div>
        <LinktreeButtonPill
          v-else
          :button="group[0]"
          @action="$emit('action', $event)"
        />
      </template>
    </div>

    <!-- PWA / save-to-phone block -->
    <LinktreePwaBlock
      v-if="tree.pwa_enabled"
      :title="tree.pwa_title"
      :description="tree.pwa_description"
      @install="$emit('install')"
    />

    <!-- Footer -->
    <div class="lt-footer">
      <div class="lt-footer__divider">
        <div class="lt-footer__line"></div>
        <div class="lt-footer__dot"></div>
        <div class="lt-footer__line"></div>
      </div>
      <span v-if="tree.footer_tagline" class="lt-footer__tagline">{{ tree.footer_tagline }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import LinktreeButtonPill from './LinktreeButtonPill.vue';
import LinktreePwaBlock from './LinktreePwaBlock.vue';

const props = defineProps({
  tree: { type: Object, required: true },
});
defineEmits(['action', 'install']);

// Fallback for the avatar circle when there is no photo: initials of the
// first two words of the display name ("Gustavo Pérez" → "GP").
const initials = computed(() =>
  (props.tree.display_name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join('')
);

// Consecutive `pair` buttons render side by side in one row.
const buttonGroups = computed(() => {
  const groups = [];
  for (const button of props.tree.buttons || []) {
    const last = groups[groups.length - 1];
    if (button.tier === 'pair' && last && last[0].tier === 'pair' && last.length < 2) {
      last.push(button);
    } else {
      groups.push([button]);
    }
  }
  return groups;
});
</script>

<style scoped>
/* Fixed brand palette by design (Linktree.dc.html) — not theme tokens. */
.lt-card {
  width: 100%;
  max-width: 390px;
  background: #001713;
  display: flex;
  flex-direction: column;
  /* Extra bottom padding so the footer tagline doesn't sit flush with the edge */
  padding: 32px 28px 44px;
  box-sizing: border-box;
  gap: 24px;
  font-family: 'Ubuntu', system-ui, sans-serif;
}

.lt-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.lt-wordmark {
  display: flex;
  flex-direction: column;
  font-size: 15px;
  line-height: 1.14;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
}
.lt-wordmark--big {
  font-size: 38px;
  line-height: 1.08;
  letter-spacing: -0.02em;
}
.lt-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border: 1px solid #f0ff3d;
  border-radius: 999px;
  background: rgba(240, 255, 61, 0.12);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1.4px;
  color: #f0ff3d;
  margin-left: auto;
}

.lt-identity { display: flex; flex-direction: column; gap: 16px; }
.lt-identity--company { gap: 18px; }
.lt-avatar {
  width: 84px;
  height: 84px;
  border-radius: 999px;
  border: 1px solid #f0ff3d;
  background: rgba(240, 255, 61, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.lt-avatar span {
  font-size: 30px;
  font-weight: 700;
  color: #f0ff3d;
  letter-spacing: -0.02em;
}
.lt-avatar__photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.lt-identity__names { display: flex; flex-direction: column; gap: 4px; }
.lt-name { margin: 0; font-size: 27px; line-height: 1.15; font-weight: 500; color: #ffffff; }
.lt-role { font-size: 14px; font-weight: 400; color: #f0ff3d; }
.lt-claim {
  display: flex;
  flex-direction: column;
  font-size: 19px;
  line-height: 1.28;
  font-weight: 300;
  color: #ffffff;
}
.lt-claim__accent { font-weight: 700; color: #f0ff3d; }
.lt-bio {
  margin: 0;
  font-size: 14px;
  line-height: 21px;
  font-weight: 300;
  color: #e6efef;
  max-width: 30ch;
  text-wrap: pretty;
}
.lt-bio--company { max-width: 32ch; }

.lt-buttons { display: flex; flex-direction: column; gap: 10px; }
.lt-pair-row { display: flex; gap: 10px; }

.lt-footer { display: flex; flex-direction: column; gap: 10px; }
.lt-footer__divider { display: flex; align-items: center; gap: 14px; }
.lt-footer__line { flex: 1; height: 1px; background: rgba(128, 148, 144, 0.2); }
.lt-footer__dot { width: 6px; height: 6px; border-radius: 999px; background: #f0ff3d; }
.lt-footer__tagline {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1.6px;
  color: #809490;
  text-align: center;
}

@media (max-width: 360px) {
  .lt-card { padding-inline: 20px; }
  .lt-pair-row { flex-direction: column; }
}
</style>
