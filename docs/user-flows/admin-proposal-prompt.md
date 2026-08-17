### FLOW: `admin-proposal-prompt`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/:id/edit` (Prompt tab)
- **Description:** Admin copies, edits, downloads and resets the commercial and technical proposal-generation prompts from the Prompt tab (`ProposalPromptTab.vue`, localStorage-persisted via `useSellerPrompt`/`useTechnicalPrompt`). Parallel of `admin-diagnostic-prompt`.
- **Steps:**
  1. Admin opens a proposal's edit page and switches to the Prompt tab.
  2. Admin copies, edits, downloads or resets either prompt.
- **Coverage:** ❌ Missing
- **E2E Spec:** — (suggested: `e2e/admin/admin-proposal-prompt.spec.js`)
