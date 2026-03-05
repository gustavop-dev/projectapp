<template>
  <main>
    <slot />
  </main>
</template>

<script setup>
// Global Organization JSON-LD structured data
useHead({
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'Organization',
        name: 'Project App.',
        url: 'https://projectapp.co',
        logo: 'https://projectapp.co/img/icons/icon-logo-512x512.png',
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
        description: 'Professional web design and development company specializing in custom software solutions, 3D animations, and e-commerce platforms.',
      }),
    },
  ],
})
</script>
