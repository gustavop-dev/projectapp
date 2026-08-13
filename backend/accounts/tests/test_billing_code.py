"""The billing-code charset shared by every path that writes the field.

The charset is not a matter of taste: the code becomes the middle segment of
``PA-{CODE}-{NNN}``, which becomes the PDF filename, the email subject and the
last segment of the preview URL. These tests pin what a trade name may carry
through that chain and what is kept out of it.
"""
import pytest

from accounts.services.billing_code import (
    BILLING_CODE_MAX_LENGTH,
    billing_code_error,
    normalize_billing_code,
)


class TestNormalizeBillingCode:
    @pytest.mark.parametrize('raw,expected', [
        ('g&m', 'G&M'),
        ('  G&M  ', 'G&M'),
        ('G  &  M', 'G & M'),
        ('acme', 'ACME'),
    ])
    def test_uppercases_trims_and_collapses_inner_spaces(self, raw, expected):
        assert normalize_billing_code(raw) == expected

    @pytest.mark.parametrize('blank', ['', '   ', None])
    def test_blank_becomes_none_never_empty_string(self, blank):
        # The column is unique: a second client stored with '' would collide.
        assert normalize_billing_code(blank) is None


class TestBillingCodeError:
    @pytest.mark.parametrize('code', [
        'G&M',        # the case that motivated the charset
        'ACME',
        'CAFE & D',
        'A.B-C',
        'AB',                       # shortest allowed
        'A' + 'B' * 11,             # exactly 12
    ])
    def test_accepts_trade_names(self, code):
        assert billing_code_error(code) is None

    @pytest.mark.parametrize('code', [
        'G/M',        # `/` fits in no single URL path segment
        'G"M',        # would end the Content-Disposition filename early
        'G;M',        # the frontend's filename parser stops at `;`
        'G#M', 'G%M', 'G?M',        # would cut the URL short
    ])
    def test_rejects_what_would_break_the_chain(self, code):
        assert billing_code_error(code) is not None

    @pytest.mark.parametrize('code', ['-AB', 'AB-', '.AB', 'AB.', '..'])
    def test_rejects_a_separator_at_either_end(self, code):
        # Otherwise the code contributes a stray separator to PA-{CODE}-{NNN}.
        assert billing_code_error(code) is not None

    @pytest.mark.parametrize('code', ['A', 'B' * (BILLING_CODE_MAX_LENGTH + 1)])
    def test_rejects_out_of_range_lengths(self, code):
        assert billing_code_error(code) is not None

    @pytest.mark.parametrize('code', ['2026', '1-2', '20 26'])
    def test_rejects_codes_without_a_letter(self, code):
        # PA-2026-001 would read as the legacy PA-{year}-{NNNN} series.
        assert billing_code_error(code) is not None

    def test_every_code_valid_under_the_old_alphanumeric_rule_still_is(self):
        # The charset only widened; it never took anything away.
        for code in ('ACME', 'A1', 'ZZ9', 'ACMESOLU', 'C123456'):
            assert billing_code_error(code) is None
