<template>
  <ContactPage />
</template>

<script setup>
import ContactPage from '~/components/pages/ContactPage.vue'
import { useWebPageJsonLd } from '~/composables/useSeoJsonLd'

useSeoHead('contact')

const { locale } = useI18n()
const isEn = computed(() => locale.value.startsWith('en'))

useWebPageJsonLd({
  name: isEn.value ? 'Contact Us' : 'Contáctanos',
  description: isEn.value
    ? 'Get in touch with Project App. for a free consultation on custom software development, web design, mobile apps, and digital solutions.'
    : 'Ponte en contacto con Project App. para una consultoría gratuita sobre desarrollo de software a medida, diseño web, apps móviles y soluciones digitales.',
  url: `/${locale.value}/contact`,
  pageType: 'ContactPage',
})
</script>
