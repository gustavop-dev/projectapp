<template>
  <div class="bg-esmerald-light">
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <div class="h-32"></div>
    <section>
      <h1 class="text-center font-light text-6xl text-esmerald lg:text-8xl">
        We don't use WordPress
        <br />
        We are real programmers
      </h1>
    </section>
    <Wordpress></Wordpress>
    <section class="mt-32 w-full px-3">
      <h2 class="text-esmerald text-4xl font-light lg:text-6xl">
        E-Commerce Landing Page V1.0
      </h2>
      <div class="grid mt-6 lg:grid-cols-3">
        <div
          class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-r-none lg:rounded-l-xl lg:col-span-2 lg:order-1"
        >
          <div class="grid gap-3 mt-6 order-2 lg:mt-0 lg:order-1">
            <div>
              <h3 class="text-xl text-white font-light">Views</h3>
              <ul class="font-regular text-lg text-green-light ps-6">
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Home (Landing Page)
                </li>
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >About Us
                </li>
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Contact
                </li>
              </ul>
            </div>
            <div>
              <h3 class="text-xl text-white font-light">Components</h3>
              <ul class="font-regular text-lg text-green-light ps-6">
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Header
                </li>
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Footer
                </li>
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Advertising Banners
                </li>
              </ul>
            </div>
            <div>
              <h3 class="text-xl text-white font-light">Functionalities</h3>
              <ul class="font-regular text-lg text-green-light ps-6">
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Responsive Design
                </li>
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Integration, with social networks
                </li>
                <li class="flex items-center gap-2">
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                  >Advertising Banners
                </li>
              </ul>
            </div>
          </div>
          <div class="border-l border-l-green-light ps-4 order-1 lg:order-2">
            <p class="text-lg text-green-light font-regular">
              <span class="text-white">Our E-commerce Landing Page</span> is
              designed to focus on your business goals, ensuring a strong and
              scalable online presence. With a responsive design, seamless
              integration with social media, and advanced security measures, our
              solution provides a professional and efficient platform for your
              business. <br /><br />This page is built to grow with your
              business, allowing easy addition of new features. Customizable
              components ensure your brand stands out, and our team offers
              comprehensive support to keep your site running smoothly.
              <br /><br />Invest in a modern, reliable, and business-focused
              website today!
            </p>
            <br />
            <p class="text-md font-regular text-white flex gap-2">
              <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> $
              900,000 COP
            </p>
            <p class="text-md font-regular text-white flex gap-2 mt-2">
              <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon> 2 Weeks
            </p>
          </div>
        </div>
        <div class="flex justify-center items-center order-1 lg:order-2">
          <img
            src="@/assets/images/prices/1.webp"
            class="w-full h-full object-cover rounded-t-xl lg:rounded-l-none lg:rounded-r-xl"
          />
        </div>
      </div>
    </section>

    <section class="mt-32 w-full px-3">
      <h2 class="text-esmerald text-end text-4xl font-light lg:text-6xl">
        E-Commerce Standard V2.0
      </h2>
      <div class="grid mt-6 lg:grid-cols-3">
        <div class="flex justify-center items-center">
          <img
            src="@/assets/images/prices/2.webp"
            class="w-full h-full object-cover rounded-t-xl lg:rounded-r-none lg:rounded-l-xl"
          />
        </div>
        <div
          class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-l-none lg:rounded-r-xl lg:col-span-2 lg:order-2"
        >
          <div class="border-r border-r-green-light pe-4">
            <p class="text-lg text-green-light font-regular text-end">
              <span class="text-white">Our E-commerce Standard + V1.0</span> is
              designed to elevate your business, providing a comprehensive
              online platform. With features like category and product
              management, advanced product zoom, and seamless integration, this
              solution is tailored to your needs. <br /><br />This version
              includes a product carousel, FAQs, and terms & conditions to
              enhance user experience. It's built to grow with your business,
              offering scalable solutions and customizable components that make
              your brand shine. <br /><br />Invest in a versatile, efficient,
              and business-centric e-commerce platform today!
            </p>
            <br />
            <p class="text-md font-regular text-white flex gap-2 justify-end">
                $ 1,900,000 COP
                <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
            </p>
            <p
              class="text-md font-regular text-white flex gap-2 mt-2 justify-end"
            >
            3 Weeks <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon>
            </p>
          </div>
          <div class="grid text-end mt-6 lg:mt-0">
            <div>
              <h3 class="text-xl text-white font-light">Views</h3>
              <ul class="font-regular text-lg text-green-light ps-6">
                <li class="flex items-center gap-2 justify-end">
                    Catalog by Categories
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
                <li class="flex items-center gap-2 justify-end">
                    Product/Services
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
              </ul>
            </div>
            <div>
              <h3 class="text-xl text-white font-light">Components</h3>
              <ul class="font-regular text-lg text-green-light ps-6">
                <li class="flex items-center gap-2 justify-end">
                    Terms and Conditions
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
                <li class="flex items-center gap-2 justify-end">
                    Product Carousel (featured, related, seasonal)
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
                <li class="flex items-center gap-2 justify-end">
                    FAQs
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
              </ul>
            </div>
            <div>
              <h3 class="text-xl text-white font-light">Functionalities</h3>
              <ul class="font-regular text-lg text-green-light ps-6">
                <li class="flex items-center gap-2 justify-end">
                    Category Manager (create, edit, delete)
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
                <li class="flex items-center gap-2 justify-end">
                    Product Manager (create, edit, delete)
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
                <li class="flex items-center gap-2 justify-end">
                    Product Image Zoom
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
                <li class="flex items-center gap-2 justify-end">
                    Pagination by number of products
                  <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mt-32 w-full px-3">
      <h2 class="text-esmerald text-4xl font-light lg:text-6xl">
        E-Commerce Premium V3.0
      </h2>
      <div class="grid mt-6 lg:grid-cols-3">
        <div class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-l-none lg:rounded-r-xl lg:col-span-2 lg:order-1">
            <div class="grid gap-3 mt-6 order-2 lg:mt-0 lg:order-1">
                <div>
                <h3 class="text-xl text-white font-light">Views</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >User Registration
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >User Login
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Favorite Products
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >User Profile
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Blog/Articles/Podcast List
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Blog/Articles/Podcast
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Blog/Articles/Podcast Editor
                    </li>
                </ul>
                </div>
                <div>
                <h3 class="text-xl text-white font-light">Components</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >User Reviews
                    </li>
                </ul>
                </div>
                <div>
                <h3 class="text-xl text-white font-light">Functionalities</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Product Filter by Category
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Interactive Search Bar
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Blog/Article/Podcast Manager
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Review Manager
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >User Manager
                    </li>
                    <li class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >Favorite Product Button
                    </li>
                </ul>
                </div>
            </div>
            <div class="border-l border-l-green-light ps-4">
                <p class="text-lg text-green-light font-regular">
                <span class="text-white">Our E-commerce Premium + Standard</span> package
                offers a comprehensive solution for your online business. With user
                registration and login, favorite products, and an advanced blog system,
                this package is designed to enhance user engagement and streamline your
                operations.
                <br /><br />This package includes advanced search and filtering
                functionalities, as well as user and review management systems to ensure a
                seamless and efficient user experience. Our solution is built to grow
                with your business, providing scalable and customizable components to
                keep your site running smoothly.
                <br /><br />Invest in a feature-rich, client-focused e-commerce platform
                today!
                </p>
                <br />
                <p class="text-md font-regular text-white flex gap-2">
                <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> $2,900,000 COP
                </p>
                <p class="text-md font-regular text-white flex gap-2 mt-2">
                <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon> 4 Weeks
                </p>
            </div>
            </div>

        <div class="flex justify-center items-center">
          <img
            src="@/assets/images/prices/3.webp"
            class="w-full h-full object-cover rounded-t-xl lg:rounded-r-none lg:rounded-l-xl"
          />
        </div>
      </div>
    </section>

    <section class="mt-32 w-full px-3">
      <h2 class="text-esmerald text-end text-4xl font-light lg:text-6xl">
        E-Commerce Gold V4.0
      </h2>
      <div class="grid mt-6 lg:grid-cols-3">
        <div class="flex justify-center items-center">
          <img
            src="@/assets/images/prices/4.webp"
            class="w-full h-full object-cover rounded-t-xl lg:rounded-r-none lg:rounded-l-xl"
          />
        </div>
        <div class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-l-none lg:rounded-r-xl lg:col-span-2 lg:order-2">
            <div class="border-r border-r-green-light pe-4">
                <p class="text-lg text-green-light font-regular text-end">
                <span class="text-white">Our E-commerce Gold + Premium</span> package
                offers a complete solution for your online business. With features like
                payment gateway integration, newsletters, and email notifications, this
                package is designed to boost your marketing and sales efforts.
                <br /><br />This version includes an advanced email marketing editor and
                campaign management tools to engage your customers effectively. It's built
                to grow with your business, providing scalable solutions and customizable
                components that make your brand shine.
                <br /><br />Invest in a comprehensive, sales-driven e-commerce platform
                today!
                </p>
                <br />
                <p class="text-md font-regular text-white flex gap-2 justify-end">
                $ 3,900,000 COP
                <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
                </p>
                <p
                class="text-md font-regular text-white flex gap-2 mt-2 justify-end"
                >
                6 Weeks <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon>
                </p>
            </div>
            <div class="grid text-end">
                <div>
                <h3 class="text-xl text-white font-light">Views</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                    <li class="flex items-center gap-2 justify-end">
                    Shopping Cart
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                    <li class="flex items-center gap-2 justify-end">
                    Purchase History
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                    <li class="flex items-center gap-2 justify-end">
                    Email Marketing Editor
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                    <li class="flex items-center gap-2 justify-end">
                    Campaign Management
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                </ul>
                </div>
                <div>
                <h3 class="text-xl text-white font-light">Functionalities</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                    <li class="flex items-center gap-2 justify-end">
                    Payment Gateway Integration
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                    <li class="flex items-center gap-2 justify-end">
                    Newsletters and Subscription
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                    <li class="flex items-center gap-2 justify-end">
                    Email Purchase Notifications
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                    <li class="flex items-center gap-2 justify-end">
                    Email Campaign Scheduling
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                    </li>
                </ul>
                </div>
            </div>
            </div>

      </div>
    </section>
    
    <Contact></Contact>

    <div class="mt-16">
        <Footer></Footer>
    </div>
  </div>
</template>

<script setup>
import Navbar from "@/components/layouts/Navbar.vue";
import Footer from "@/components/layouts/Footer.vue";
import Contact from "@/components/layouts/Contact.vue";
import Wordpress from "@/components/utils/Wordpress.vue";
import {
  BanknotesIcon,
  CheckBadgeIcon,
  ClockIcon,
} from "@heroicons/vue/24/outline";
</script>
