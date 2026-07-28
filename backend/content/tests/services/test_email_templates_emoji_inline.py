"""Guards the email templates against the Gmail emoji line-break bug.

Gmail web swaps some Unicode emoji in the body for its own ``<img>`` element.
A global ``img{display:block}`` reset therefore turns those emoji into block
boxes and drops them onto their own line, e.g. the payment plan rows of
``proposal_sent_client.html``. Block styling belongs on the ``.img-block``
helper class instead, applied to real images only.
"""
import re
from pathlib import Path

from django.conf import settings

EMAIL_TEMPLATE_DIRS = ('content', 'accounts')

# Declaration blocks of any rule whose selector list mentions a bare `img`
# element selector (`img`, `img,td`, `body,img` ...), not `.img-block`.
GLOBAL_IMG_RULE_RE = re.compile(
    r'(?<![\w.#-])img\s*(?:,[^{}]*)?\{([^{}]*)\}'
)


def _email_templates():
    backend_root = Path(settings.BASE_DIR)
    for app in EMAIL_TEMPLATE_DIRS:
        yield from sorted(
            (backend_root / app / 'templates' / 'emails').glob('*.html')
        )


def test_no_email_template_forces_images_to_display_block():
    offenders = []
    for template in _email_templates():
        source = template.read_text(encoding='utf-8')
        for declarations in GLOBAL_IMG_RULE_RE.findall(source):
            if re.search(r'display\s*:\s*block', declarations):
                offenders.append(template.name)

    assert offenders == [], (
        'Global img{display:block} breaks Gmail emoji rendering; use the '
        f'.img-block class instead. Offending templates: {sorted(set(offenders))}'
    )


def test_scan_actually_covers_the_branded_templates():
    names = [template.name for template in _email_templates()]

    assert 'proposal_sent_client.html' in names
    assert 'invitation.html' in names
    assert len(names) > 20
