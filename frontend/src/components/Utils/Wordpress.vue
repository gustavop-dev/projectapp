<template>
    <section class="p-3">
            <div class="py-32 bg-esmerald-dark rounded-xl">
                <h2 class="ps-52 mb-12 text-start font-light text-6xl text-white">Our products are</h2>
                <Vue3Marquee :pause-on-hover="true">
                    <div class="w-72 h-full mx-auto px-4" v-for="attribute in qualityAttributes">
                        <div class="bg-esmerald rounded-xl relative h-full">
                            <component :is="attribute.icon" class="w-16 h-16 text-lemon text-center p-4"></component>
                            <p class="text-white m-4 font-regular">{{ attribute.text }}</p>
                        </div>
                    </div>
                </Vue3Marquee>
                <h2 class="pe-52 my-12 text-end font-light text-6xl text-white">Why not WordPress?</h2>
                <Vue3Marquee :pause-on-hover="true" direction="reverse" duration="35">
                    <div class="w-72 h-full mx-auto px-4" v-for="reason in reasons">
                        <div class="bg-esmerald rounded-xl relative h-full">
                            <component :is="reason.icon" class="w-16 h-16 text-lemon text-center p-4"></component>
                            <p class="text-white m-4 font-regular">{{ reason.text }}</p>
                        </div>
                    </div>
                </Vue3Marquee>
            </div>
    </section>
</template>
<script setup>
import { Vue3Marquee } from 'vue3-marquee'
import { 
    CheckCircleIcon,
    ShieldCheckIcon,
    UserCircleIcon,
    LightBulbIcon,
    CogIcon,
    LockClosedIcon,
    ArrowTrendingUpIcon,
    ArrowTrendingDownIcon,
    BeakerIcon,
    ExclamationCircleIcon,
    ClockIcon,
    ShieldExclamationIcon,
    ComputerDesktopIcon,
    BanknotesIcon,
    AdjustmentsHorizontalIcon,
    BookOpenIcon,
    AcademicCapIcon,
    SwatchIcon,
CheckBadgeIcon,
 } from '@heroicons/vue/24/outline';

const qualityAttributes = [
    {
        icon: CheckCircleIcon,
        text: "The software's ability to meet specified requirements, including accuracy and interoperability."
    },
    {
        icon: ShieldCheckIcon,
        text: "The software's ability to perform correctly and predictably under various conditions over a specified period."
    },
    {
        icon: UserCircleIcon,
        text: "The ease with which users can learn to use the software, as well as its effectiveness, efficiency, and user satisfaction."
    },
    {
        icon: LightBulbIcon,
        text: "The software's performance in terms of response time, memory usage, and processor utilization.",
    },
    {
        icon: CogIcon,
        text: "The ease with which the software can be modified or corrected, including the ability to locate and fix defects, and the clarity and modularity of the code."
    },
    {
        icon: LockClosedIcon,
        text: "The software's ability to protect data and system resources from unauthorized access and its resistance to attacks and vulnerabilities."
    },
    {
        icon: ArrowTrendingUpIcon,
        text: "The software's ability to adapt and grow in terms of capacity and performance in response to increased workload or user numbers. A scalable architecture ensures optimal performance even with higher demands, either by adding additional resources or optimizing existing ones."
    },
    {
        icon: BeakerIcon,
        text: "Implementation of unit and integration tests within the codebase to facilitate updates and ensure that existing functionality is not broken, making it easier for new software providers to implement their solutions without issues."
    }
]

const reasons = [
    {
        icon: ExclamationCircleIcon,
        text: "Plugins developed by random people can become unstable with new updates."
    },
    {
        icon: ClockIcon,
        text: "Updating plugins can turn into a nightmare of time, money, and resources."
    },
    {
        icon: ShieldExclamationIcon,
        text: "Over time, WordPress becomes heavy and less secure."
    },
    {
        icon: ComputerDesktopIcon,
        text: "Incompatibility with Chrome can affect your website's performance."
    },
    {
        icon: ShieldCheckIcon,
        text: "Plugins can pose risks to your website and clients' security."
    },
    {
        icon: BanknotesIcon,
        text: "Additional functionalities may have hidden costs and integration issues."
    },
    {
        icon: LightBulbIcon,
        text: "Lack of innovation and outdated plugins don't help keep your website up to date."
    },
    {
        icon: AdjustmentsHorizontalIcon,
        text: "WordPress doesn't specialize in anything; opt for specific and better tools."
    },
    {
        icon: BookOpenIcon,
        text: "Lack of clear guides for plugins and the system in general."
    },
    {
        icon: AcademicCapIcon,
        text: "Creating websites without knowing how to program can compromise professionalism and quality."
    },
    {
        icon: SwatchIcon,
        text: "Limited to templates and difficult to integrate modern libraries like Tailwind CSS."
    },
    {
        icon: ArrowTrendingDownIcon,
        text: "WordPress may not support future growth and complex systems."
    },
    {
        icon: CheckBadgeIcon,
        text: "Availability, accessibility, performance, and scalability are essential."
    },
    {
        icon: ClockIcon,
        text: "Update your website with modern technologies like Django, Vue.js, MySQL, Tailwind CSS."
    }
]
</script>