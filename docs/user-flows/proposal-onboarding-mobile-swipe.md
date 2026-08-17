### FLOW: `proposal-onboarding-mobile-swipe`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** On mobile devices, the onboarding tutorial replaces positioned tooltips with a fullscreen swipe carousel overlay. Users navigate steps by swiping left/right or tapping next/back buttons. Desktop retains tooltip-based onboarding.
- **Steps:**
  1. First-time visitor opens a proposal on a mobile device.
  2. ProposalOnboarding detects `isMobile` and renders fullscreen overlay.
  3. User swipes left/right or taps navigation buttons to progress through steps.
  4. On completion, onboarding emits `@complete` and sets localStorage flag.
  5. Reading time popup appears.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-onboarding-mobile-swipe.spec.js`
