"""
Billing-code charset, shared by every path that writes ``UserProfile.billing_code``.

The code becomes the middle segment of a collection account's consecutivo
(``PA-{CODE}-{NNN}``), which in turn becomes the PDF filename, the email
subject and the last segment of the preview URL. So the charset is defined by
what survives that chain rather than by taste:

* ``&``, ``.``, ``-`` and spaces are allowed because real company names use
  them (G&M). They travel intact through ``re.escape``-d consecutivo parsing,
  Django's ``content_disposition_header`` and the ``<str:filename>`` route.
* ``/`` is excluded: it is the one character ``<str:filename>`` will not match.
  ``#``, ``%`` and ``?`` are excluded because they would cut the URL short, and
  ``"``/``;`` because they terminate a Content-Disposition filename.

Living in ``accounts`` keeps the import direction ``content -> accounts``, the
one already established; the reverse would close a cycle.
"""
import re

BILLING_CODE_MAX_LENGTH = 12

# 2-12 chars, alphanumeric at both ends so a code can never contribute a
# leading/trailing separator to `PA-{CODE}-{NNN}` or to a filename.
BILLING_CODE_RE = re.compile(r'[A-Z0-9][A-Z0-9&.\- ]{0,10}[A-Z0-9]')

BILLING_CODE_ERROR = (
    'El código debe tener entre 2 y 12 caracteres, empezar y terminar en letra '
    'o número, y entremedio solo admite & . - o espacios.'
)
BILLING_CODE_NO_LETTER_ERROR = (
    'El código debe contener al menos una letra (uno solo de dígitos '
    'colisionaría con la numeración PA-{año}-{NNNN}).'
)


def normalize_billing_code(value):
    """Uppercase and trim, collapsing inner whitespace runs. Blank -> ``None``.

    ``None`` rather than ``''`` on purpose: the column is unique, so a second
    client stored with ``''`` would collide with the first.
    """
    code = re.sub(r'\s+', ' ', (value or '').strip()).upper()
    return code or None


def billing_code_error(code):
    """Spanish error message for an already-normalized code, or None if valid."""
    if not BILLING_CODE_RE.fullmatch(code):
        return BILLING_CODE_ERROR
    if not any(char.isalpha() for char in code):
        return BILLING_CODE_NO_LETTER_ERROR
    return None
