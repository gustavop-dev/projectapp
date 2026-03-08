import { defineEventHandler, setResponseHeader } from 'h3';

const BASE_URL = 'https://projectapp.co';

// Static pages — mirrors what was in public/sitemap.xml
const STATIC_PAGES = [
  { path: '/en-us', alt: '/es-co', changefreq: 'weekly', priority: '1.0' },
  { path: '/es-co', alt: '/en-us', changefreq: 'weekly', priority: '1.0' },
  { path: '/en-us/landing-web-design', alt: '/es-co/landing-web-design', changefreq: 'weekly', priority: '0.9' },
  { path: '/es-co/landing-web-design', alt: '/en-us/landing-web-design', changefreq: 'weekly', priority: '0.9' },
  { path: '/en-us/about-us', alt: '/es-co/about-us', changefreq: 'monthly', priority: '0.9' },
  { path: '/es-co/about-us', alt: '/en-us/about-us', changefreq: 'monthly', priority: '0.9' },
  { path: '/en-us/web-designs', alt: '/es-co/web-designs', changefreq: 'weekly', priority: '0.9' },
  { path: '/es-co/web-designs', alt: '/en-us/web-designs', changefreq: 'weekly', priority: '0.9' },
  { path: '/en-us/portfolio-works', alt: '/es-co/portfolio-works', changefreq: 'weekly', priority: '0.9' },
  { path: '/es-co/portfolio-works', alt: '/en-us/portfolio-works', changefreq: 'weekly', priority: '0.9' },
  { path: '/en-us/custom-software', alt: '/es-co/custom-software', changefreq: 'monthly', priority: '0.9' },
  { path: '/es-co/custom-software', alt: '/en-us/custom-software', changefreq: 'monthly', priority: '0.9' },
  { path: '/en-us/3d-animations', alt: '/es-co/3d-animations', changefreq: 'weekly', priority: '0.8' },
  { path: '/es-co/3d-animations', alt: '/en-us/3d-animations', changefreq: 'weekly', priority: '0.8' },
  { path: '/en-us/e-commerce-prices', alt: '/es-co/e-commerce-prices', changefreq: 'monthly', priority: '0.7' },
  { path: '/es-co/e-commerce-prices', alt: '/en-us/e-commerce-prices', changefreq: 'monthly', priority: '0.7' },
  { path: '/en-us/hosting', alt: '/es-co/hosting', changefreq: 'monthly', priority: '0.7' },
  { path: '/es-co/hosting', alt: '/en-us/hosting', changefreq: 'monthly', priority: '0.7' },
  { path: '/en-us/contact', alt: '/es-co/contact', changefreq: 'monthly', priority: '0.6' },
  { path: '/es-co/contact', alt: '/en-us/contact', changefreq: 'monthly', priority: '0.6' },
];

function escapeXml(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toISOString().split('T')[0];
  } catch {
    return new Date().toISOString().split('T')[0];
  }
}

export default defineEventHandler(async (event) => {
  setResponseHeader(event, 'Content-Type', 'application/xml; charset=utf-8');
  setResponseHeader(event, 'Cache-Control', 'public, max-age=3600, s-maxage=3600');

  // Fetch blog posts from backend API
  let blogPosts: Array<{ slug: string; updated_at: string }> = [];
  try {
    const apiBase = process.env.NUXT_API_BASE || 'http://127.0.0.1:8000';
    const res = await fetch(`${apiBase}/api/blog/sitemap-data/`);
    if (res.ok) {
      blogPosts = await res.json();
    }
  } catch (err) {
    console.error('[sitemap] Failed to fetch blog posts:', err);
  }

  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
  xml += `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n`;
  xml += `        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n\n`;

  // Static pages
  for (const page of STATIC_PAGES) {
    const loc = `${BASE_URL}${page.path}`;
    const altLoc = `${BASE_URL}${page.alt}`;
    const hreflangSelf = page.path.startsWith('/en-us') ? 'en-us' : 'es-co';
    const hreflangAlt = page.path.startsWith('/en-us') ? 'es-co' : 'en-us';

    xml += `  <url>\n`;
    xml += `    <loc>${escapeXml(loc)}</loc>\n`;
    xml += `    <xhtml:link rel="alternate" hreflang="${hreflangSelf}" href="${escapeXml(loc)}" />\n`;
    xml += `    <xhtml:link rel="alternate" hreflang="${hreflangAlt}" href="${escapeXml(altLoc)}" />\n`;
    xml += `    <changefreq>${page.changefreq}</changefreq>\n`;
    xml += `    <priority>${page.priority}</priority>\n`;
    xml += `  </url>\n`;
  }

  // Blog listing page
  xml += `\n  <!-- Blog -->\n`;
  xml += `  <url>\n`;
  xml += `    <loc>${BASE_URL}/blog</loc>\n`;
  xml += `    <changefreq>daily</changefreq>\n`;
  xml += `    <priority>0.8</priority>\n`;
  xml += `  </url>\n`;

  // Blog posts
  for (const post of blogPosts) {
    const lastmod = post.updated_at ? formatDate(post.updated_at) : formatDate(new Date().toISOString());
    xml += `  <url>\n`;
    xml += `    <loc>${BASE_URL}/blog/${escapeXml(post.slug)}</loc>\n`;
    xml += `    <lastmod>${lastmod}</lastmod>\n`;
    xml += `    <changefreq>weekly</changefreq>\n`;
    xml += `    <priority>0.7</priority>\n`;
    xml += `  </url>\n`;
  }

  xml += `\n</urlset>\n`;

  return xml;
});
