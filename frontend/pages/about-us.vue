<template>
  <AboutUs />
</template>

<script setup>
import AboutUs from '~/components/pages/AboutUs.vue'
import { useWebPageJsonLd } from '~/composables/useSeoJsonLd'

useSeoHead('aboutUs')

const { locale } = useI18n()
const isEn = computed(() => locale.value.startsWith('en'))

useWebPageJsonLd({
  name: isEn.value ? 'About Project App.' : 'Sobre Project App.',
  description: isEn.value
    ? 'Project App. is a team of expert web developers, designers, and 3D artists dedicated to creating exceptional websites and software solutions.'
    : 'Project App. es un equipo de desarrolladores web expertos, diseñadores y artistas 3D dedicados a crear sitios web y soluciones de software excepcionales.',
  url: `/${locale.value}/about-us`,
  pageType: 'AboutPage',
})
</script>
