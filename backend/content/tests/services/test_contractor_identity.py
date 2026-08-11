"""The contractor is named by whichever document is on file, NIT first."""

from content.services.contractor_identity import (
    CEDULA_LABEL,
    NIT_LABEL,
    UNKNOWN_LABEL,
    resolve_contractor_identity,
)


class TestResolveContractorIdentity:
    def test_nit_wins_when_both_documents_are_present(self):
        assert resolve_contractor_identity('900.123.456-7', '1037635428') == (
            NIT_LABEL, '900.123.456-7',
        )

    def test_falls_back_to_cedula_when_there_is_no_nit(self):
        assert resolve_contractor_identity('', '1037635428') == (
            CEDULA_LABEL, '1037635428',
        )

    def test_whitespace_only_nit_does_not_shadow_the_cedula(self):
        """A form that posts a spaces-only NIT must not win over a real cédula."""
        assert resolve_contractor_identity('   ', '1037635428') == (
            CEDULA_LABEL, '1037635428',
        )

    def test_values_are_stripped(self):
        assert resolve_contractor_identity(' 900.123.456-7 ', '') == (
            NIT_LABEL, '900.123.456-7',
        )

    def test_keeps_the_dual_label_when_neither_document_is_on_file(self):
        """The blank document is meant to be completed by hand, so it hedges."""
        assert resolve_contractor_identity('', '') == (UNKNOWN_LABEL, '')

    def test_blank_filler_is_used_as_the_number_when_nothing_is_on_file(self):
        assert resolve_contractor_identity(None, None, blank='___') == (
            UNKNOWN_LABEL, '___',
        )
