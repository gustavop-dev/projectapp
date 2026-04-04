<template>
  <main>
    <slot />
  </main>
</template>

<script setup>
// Global Organization + WebSite JSON-LD structured data
useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'Organization',
            '@id': 'https://projectapp.co/#organization',
            name: 'Project App.',
            url: 'https://projectapp.co',
            logo: {
              '@type': 'ImageObject',
              url: 'https://projectapp.co/img/icons/icon-logo-512x512.png',
              width: 512,
              height: 512,
            },
            sameAs: [
              'https://www.instagram.com/projectapp.co/',
              'https://www.facebook.com/projectapp.co',
            ],
            contactPoint: {
              '@type': 'ContactPoint',
              email: 'team@projectapp.co',
              contactType: 'customer service',
              availableLanguage: ['English', 'Spanish'],
            },
            address: {
              '@type': 'PostalAddress',
              addressCountry: 'CO',
            },
            description: 'Professional web design and development company specializing in custom software solutions, 3D animations, and e-commerce platforms.',
          },
          {
            '@type': 'WebSite',
            '@id': 'https://projectapp.co/#website',
            url: 'https://projectapp.co',
            name: 'Project App.',
            publisher: { '@id': 'https://projectapp.co/#organization' },
            inLanguage: ['en-US', 'es-CO'],
          },
        ],
      }),
    },
  ],
})
</script>
