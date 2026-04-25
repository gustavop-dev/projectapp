---
name: implement
description: "Implement a ProjectApp feature or fix using the repo's existing architecture and minimal targeted verification. Use when the user asks to build, code, or fix something."
argument-hint: "[feature, refactor, bugfix, or concrete implementation request]"
---

# Implement Workflow

## Before Editing
- Read the relevant scope instructions and touched code.
- Read only the memory files that materially affect the change.
- Identify the smallest useful verification commands before changing code.

## ProjectApp Rules
- Backend DRF views stay function-based unless the user explicitly asks otherwise.
- Keep business logic out of views when a service, serializer, helper, or model method is the better fit.
- Frontend stores use Pinia Options API.
- Keep content/admin requests on `stores/services/request_http.js`.
- Keep platform/auth requests on `usePlatformApi.js`.
- Preserve existing public response shapes unless the task explicitly changes them.

## Implementation Sequence
1. Confirm the affected files, contracts, and side effects.
2. Make the smallest coherent change that solves the request.
3. Update tests or add focused coverage for the changed behavior.
4. Run only the smallest relevant verification slice.
5. Update docs or memory files only if the user asked for it or the change materially alters runtime guidance, architecture, or workflows.

## Output Contract
When done, report:
- what changed
- why the change fits existing project patterns
- what verification ran
- what could not be verified

---

Before starting, ALWAYS do 2 things:
a. Read and understand the documentation in `docs/` and `tasks/`
b. Get required code context from `backend/` and `frontend/`

---

# Implementation Workflow

## Programming Principles

- **Algorithm efficiency**: Use the most efficient algorithms and data structures
- **Modularity**: Write modular code, break complex logic into smaller atomic parts
- **File management**: Break long files into smaller, more manageable files
- **Import statements**: Prefer importing functions from other files instead of modifying them directly
- **Reuse**: Prefer to reuse existing code instead of writing from scratch
- **Code preservation**: Don't modify working components without necessity
- **Systematic sequence**: Complete one step completely before starting another
- **Design patterns**: Apply appropriate patterns for maintainability and scalability
- **Proactive testing**: Functionality code should be accompanied with proper tests

## Systematic Code Protocol

### Step 1: Analyze Code

**Dependency Analysis:**
- Which components will be affected?
- What dependencies exist?
- Is this local or does it affect core logic?
- What cascading effects will this change have?

**Flow Analysis:**
- Conduct complete end-to-end flow analysis from entry point to execution of all affected code.
- Track data and logic flow throughout all components.
- Document dependencies thoroughly.

### Step 2: Plan Code

- Outline a detailed plan including component dependencies and architectural considerations.
- Provide a proposal specifying: (1) what files/functions/lines are changed; (2) why; (3) impacted modules; (4) potential side effects; (5) trade-offs.

### Step 3: Make Changes

1. Document current state in memory files
2. Plan single logical change at a time:
   - One logical feature at a time
   - Fully resolve by accommodating changes in other parts
   - Adjust all existing dependencies
   - Ensure new code integrates with existing architecture
3. Simulation testing: simulate user interactions, dry runs, trace calls before applying
4. If simulation passes, do the actual implementation

### Step 4: Test

- Create unit tests for new functionality
- Run tests to confirm existing behavior is preserved
- Write test logic in separate files
- Think of exhaustive test plans covering edge cases

### Step 5: Loop Steps 1-4

Incorporate all changes systematically, one by one. Verify and test each.

### Step 6: Optimize

Optimize the implemented code after all changes are tested and verified.

---

After every implementation, ALWAYS do 2 things:
a. Update other possibly affected codes in `backend/` and `frontend/`
b. Update the documentation in `docs/` and `tasks/`
