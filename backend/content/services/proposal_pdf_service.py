"""
Service for generating PDF snapshots of business proposals
using Playwright headless Chromium.
"""

import logging
import tempfile
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


class ProposalPdfService:
    """
    Generate a PDF of a proposal's public page using Playwright.

    Usage:
        pdf_bytes = ProposalPdfService.generate(proposal)
    """

    @classmethod
    def _get_proposal_url(cls, proposal):
        """Build the full URL for the proposal's public page."""
        base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
        return f'{base}/proposal/{proposal.uuid}'

    @classmethod
    def generate(cls, proposal, timeout_ms=60000):
        """
        Render the proposal page in headless Chromium and return PDF bytes.

        Args:
            proposal: BusinessProposal instance.
            timeout_ms: Max time to wait for page load (default 60s).

        Returns:
            bytes: The PDF content, or None on failure.
        """
        url = cls._get_proposal_url(proposal)

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1280, 'height': 900})

                page.goto(url, wait_until='networkidle', timeout=timeout_ms)

                # Wait for the preloader animation to finish and content to render
                page.wait_for_selector(
                    '.horizontal-scroll-wrapper',
                    state='visible',
                    timeout=timeout_ms,
                )

                # Hide interactive UI elements that shouldn't appear in PDF
                page.evaluate("""
                    () => {
                        const selectors = [
                            '.proposal-index',
                            '.section-counter',
                            '.expiration-badge',
                            '.pdf-download-button',
                            '.proposal-closing',
                        ];
                        selectors.forEach(sel => {
                            document.querySelectorAll(sel).forEach(el => {
                                el.style.display = 'none';
                            });
                        });

                        // Unpin the scroll container and lay out panels vertically
                        const wrapper = document.querySelector('.panels-wrapper');
                        if (wrapper) {
                            wrapper.style.display = 'block';
                            wrapper.style.width = '100%';
                            wrapper.style.height = 'auto';
                            wrapper.style.transform = 'none';
                        }
                        const container = document.querySelector('.scroll-container');
                        if (container) {
                            container.style.height = 'auto';
                            container.style.overflow = 'visible';
                        }
                        document.querySelectorAll('.panel').forEach(panel => {
                            panel.style.width = '100%';
                            panel.style.height = 'auto';
                            panel.style.minHeight = '100vh';
                            panel.style.flexShrink = '1';
                            panel.style.overflow = 'visible';
                            panel.style.pageBreakAfter = 'always';
                        });
                    }
                """)

                # Let the layout settle
                page.wait_for_timeout(1000)

                pdf_bytes = page.pdf(
                    format='A4',
                    print_background=True,
                    margin={
                        'top': '0.5in',
                        'bottom': '0.5in',
                        'left': '0.4in',
                        'right': '0.4in',
                    },
                )

                browser.close()

                logger.info(
                    'Generated PDF for proposal %s (%d bytes)',
                    proposal.uuid, len(pdf_bytes),
                )
                return pdf_bytes

        except Exception:
            logger.exception(
                'Failed to generate PDF for proposal %s', proposal.uuid,
            )
            return None

    @classmethod
    def generate_to_file(cls, proposal, output_path=None, timeout_ms=60000):
        """
        Generate PDF and save to a file. Returns the file path or None.

        Args:
            proposal: BusinessProposal instance.
            output_path: Optional path. If None, uses a temp file.
            timeout_ms: Max time to wait for page load.

        Returns:
            str: Path to the generated PDF file, or None on failure.
        """
        pdf_bytes = cls.generate(proposal, timeout_ms=timeout_ms)
        if not pdf_bytes:
            return None

        if output_path is None:
            media_temp = Path(settings.MEDIA_ROOT) / 'temp'
            media_temp.mkdir(parents=True, exist_ok=True)
            fd, output_path = tempfile.mkstemp(
                suffix='.pdf',
                prefix=f'proposal_{proposal.uuid}_',
                dir=str(media_temp),
            )
            import os
            os.close(fd)

        output_path = str(output_path)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        logger.info('Saved PDF to %s', output_path)
        return output_path
