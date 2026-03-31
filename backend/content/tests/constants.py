"""
Central expectations shared across content tests.

When the number of hardcoded default proposal sections changes (see
``ProposalService.get_default_sections`` / ``DEFAULT_SECTIONS``), update
``EXPECTED_DEFAULT_SECTION_COUNT`` here and run tests that assert section counts.
"""

# Must match len(ProposalService.get_hardcoded_defaults('es')) when no DB override exists.
EXPECTED_DEFAULT_SECTION_COUNT = 15
