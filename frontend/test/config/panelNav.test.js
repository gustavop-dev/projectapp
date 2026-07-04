/**
 * Tests for the panel navigation config.
 *
 * Covers: the "ProjectApp content" section (renamed from "Website content")
 * and its LinkedIn module entry.
 */
import { getPanelNavSections } from '../../config/panelNav';

const identityLocalePath = (path) => path;

describe('getPanelNavSections', () => {
  it('names the site section ProjectApp content', () => {
    const sections = getPanelNavSections(identityLocalePath);
    const site = sections.find((s) => s.id === 'site');

    expect(site).toBeDefined();
    expect(site.label).toBe('ProjectApp content');
  });

  it('includes the LinkedIn module in the site section', () => {
    const sections = getPanelNavSections(identityLocalePath);
    const site = sections.find((s) => s.id === 'site');
    const linkedin = site.items.find((i) => i.label === 'LinkedIn');

    expect(linkedin).toBeDefined();
    expect(linkedin.href).toBe('/panel/linkedin');
    expect(linkedin.icon).toBe('linkedin');
  });

  it('no section uses the old Website content label', () => {
    const sections = getPanelNavSections(identityLocalePath);

    expect(sections.map((s) => s.label)).not.toContain('Website content');
  });
});
