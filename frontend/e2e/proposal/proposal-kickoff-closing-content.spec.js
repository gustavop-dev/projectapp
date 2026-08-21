/**
 * E2E coverage for the proposal kickoff disclosure and final contact panel.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PROPOSAL_CLOSING_CONTACT,
  PROPOSAL_KICKOFF_DISCLOSURE,
} from '../helpers/flow-tags.js';

const MOCK_UUID = 'e4111111-1111-1111-1111-111111111111';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Kickoff Proposal',
  client_name: 'Kickoff Client',
  status: 'sent',
  language: 'es',
  total_investment: '320000000',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: 'Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Kickoff Client', inspirationalQuote: '' },
    },
    {
      id: 2,
      section_type: 'final_note',
      title: 'Nuestro compromiso',
      order: 1,
      is_enabled: true,
      content_json: {
        message: 'Construiremos el proyecto con alcance verificable.',
        personalNote: 'Estamos listos para acompañar el proceso.',
        teamName: 'El equipo de Project App',
        teamRole: 'Tu socio en transformación digital',
        contactEmail: 'team@projectapp.co',
        commitmentBadges: [
          { icon: '🤝', title: 'Alcance claro', description: 'Revisión conjunta.' },
          { icon: '🔎', title: 'Transparencia', description: 'Seguimiento continuo.' },
          { icon: '✅', title: 'Entrega responsable', description: 'Validación verificable.' },
        ],
        kickoffPlan: [
          { day: 'D1', title: 'Revisión comercial', description: 'Alineamos el acuerdo.' },
          { day: 'D2', title: 'Kickoff', description: 'Iniciamos el trabajo.' },
        ],
        thankYouMessage: 'Gracias por confiar en Project App.',
      },
    },
    {
      id: 3,
      section_type: 'next_steps',
      title: 'Próximos pasos',
      order: 2,
      is_enabled: true,
      content_json: {
        introMessage: 'Necesitamos confirmar los insumos disponibles.',
        steps: [
          { title: 'Entrega de insumos', description: 'Aerocivil comparte las fuentes disponibles.' },
          { title: 'Validación técnica', description: 'Project App revisa formato y acceso.' },
        ],
        ctaMessage: 'Conversemos para activar el cronograma.',
        primaryCTA: { text: 'Escribir por WhatsApp', link: 'https://wa.me/573001112233' },
        secondaryCTA: { text: 'Agendar reunión' },
        contactMethods: [
          { icon: '✉️', title: 'Email', value: 'team@projectapp.co', link: 'mailto:team@projectapp.co' },
          { icon: '💬', title: 'WhatsApp', value: '+57 300 111 2233', link: 'https://wa.me/573001112233' },
          { icon: '🌐', title: 'Website', value: 'projectapp.co', link: 'https://projectapp.co' },
        ],
      },
    },
  ],
  requirement_groups: [],
};

async function openProposal(page) {
  await page.addInitScript(() => localStorage.setItem('proposal_onboarding_seen', 'true'));
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    return null;
  });
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
  await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });
}

test.describe('Proposal kickoff and closing content', () => {
  test('keeps both commitment columns readable at laptop width', {
    tag: [...PROPOSAL_KICKOFF_DISCLOSURE, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await openProposal(page);
    await page.getByTestId('nav-next').click();

    const commitment = page.getByTestId('commitment-column');
    const kickoff = page.getByTestId('kickoff-card');
    await expect(commitment).toBeVisible();
    await expect(kickoff).toBeVisible();
    const widths = await Promise.all([
      commitment.evaluate(element => element.getBoundingClientRect().width),
      kickoff.evaluate(element => element.getBoundingClientRect().width),
    ]);

    expect(widths[0]).toBeGreaterThan(520);
    expect(widths[1]).toBeGreaterThan(520);
  });

  test('expands the schedule prerequisites from the kickoff panel', {
    tag: [...PROPOSAL_KICKOFF_DISCLOSURE, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the shared proposal URL is the guest's real
    // entry point; the test reaches the target section through nav-next)
    await openProposal(page);
    await page.getByTestId('nav-next').click();

    const disclosure = page.getByTestId('next-steps-disclosure');
    await expect(disclosure).toBeVisible();
    await expect(disclosure).not.toHaveAttribute('open', '');
    await disclosure.locator('summary').click();

    await expect(disclosure).toHaveAttribute('open', '');
    await expect(disclosure.getByText('Entrega de insumos')).toBeVisible();
    await expect(disclosure.getByText('Validación técnica')).toBeVisible();
  });

  test('shows the commercial contact channels in the final panel', {
    tag: [...PROPOSAL_CLOSING_CONTACT, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the shared proposal URL is the guest's real
    // entry point; the test reaches the closing panel through nav-next)
    await openProposal(page);
    await page.getByTestId('nav-next').click();
    await page.getByTestId('nav-next').click();

    const contactPanel = page.getByTestId('proposal-ready-contact');
    await expect(contactPanel).toBeVisible();
    await expect(contactPanel.getByText('¿Listo para comenzar?')).toBeVisible();
    await expect(contactPanel.getByText('Email')).toBeVisible();
    await expect(contactPanel.getByText('WhatsApp', { exact: true })).toBeVisible();
    await expect(contactPanel.getByText('Website')).toBeVisible();
  });
});
