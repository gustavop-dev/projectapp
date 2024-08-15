<template>
  <div>
    <div>
      <div class="fixed top-0 left-0 w-full z-50">
        <Navbar></Navbar>
      </div>
      <InitialVideo></InitialVideo>
      <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
        <h2 class="block font-light text-4xl text-esmerald lg:pe-60 lg:text-6xl">
          Being visible is just no longer enough. It’s all about leveraging attention. And then moving forward together. Synced.
        </h2>
      </section>
      <section class="grid grid-cols-3">
        <div class="col-span-1">
          <h1 class="hidden font-light text-sm ms-32 text-esmerald lg:inline">[SOFTWARE HOUSE]</h1>
        </div>
        <div class="col-span-3 lg:col-span-2">
          <div class="grid grid-cols-3 gap-12 lg:grid-cols-2">
            <div class="col-span-1 lg:hidden"></div>
            <div class="col-span-2 lg:col-span-1">
              <h1 class="bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">Our motto</h1>
              <h2 class="mt-20"><span class="text-esmerald font-regular text-lg">We make developments for brand with hight objectives,</span><span class="text-green-light text-lg font-regular"> we specialize in web development, creating unique and efficient experiences that drive our clients' growth.<br><br>Our commitment is to excellence and innovation. We work closely with our clients to understand their needs and deliver solutions that not only solve problems but also enhance their success in the digital world.</span></h2>
            </div>
            <div class="col-span-3 lg:pe-4 lg:col-span-1">
              <Suspense>
                <template #default>
                  <Dune spline="/spline/cube/scene.splinecode"></Dune>
                </template>
                <template #fallback>
                  <div class="loader">Loading 3D content...</div>
                </template>
  
              </Suspense>
            </div>
          </div>
        </div>
      </section>
      <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
        <h2 class="block font-light text-5xl mb-24 text-esmerald lg:mb-40 lg:text-6xl lg:text-end">Our Services</h2>
        <div class="grid lg:grid-cols-2">
          <div class="h-80 order-2 mt-24 lg:mt-0 lg:order-1 lg:h-auto">
            <Dune spline="/spline/gradientColor/scene.splinecode"></Dune>
          </div>
          <div class="order-1 lg:order-2 lg:ps-32">
            <h3 class="text-end text-4xl font-light text-esmerald">Web Development</h3>
            <p class="text-end text-lg font-regular mt-8 text-green-light">We transform your vision into a digital reality with our web development services. Unlike others, we don't use Wordpress; every project is built from scratch with custom code because we are passionate programmers. We have developed a set of functionalities and components tailored to each business.</p>
            <h3 class="text-end text-4xl font-light text-esmerald mt-24 lg:mt-32">Custom Software Development</h3>
            <p class="text-end text-lg font-regular mt-8 text-green-light">We offer custom software development for companies seeking personalized and efficient solutions. We understand your unique needs and create applications that optimize your processes and enhance your productivity. Our approach focuses on quality, innovation, and customer satisfaction.</p>
          </div>
        </div>
      </section>
      <section class="mt-16">
        <Contact></Contact>
      </section>
      <section class="mt-16 relative">
        <Footer></Footer>
      </section>
    </div>
  </div>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue';
import InitialVideo from '@/components/home/InitialVideo.vue';
import Footer from '@/components/layouts/Footer.vue';
import Contact from '@/components/layouts/Contact.vue';
import { defineAsyncComponent } from 'vue';


const Dune = defineAsyncComponent(() =>
  import('@/components/spline/Backgrounds/Dune.vue')
);

</script>