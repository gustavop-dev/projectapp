<template>
    <section class="p-3">
            <div class="py-32 bg-esmerald-dark rounded-xl">
                <h2 class="max-w-7xl mx-auto mb-12 px-3 text-start font-light text-4xl text-white lg:text-6xl lg:px-0">{{ messages.wordpress_component.our_products_are }}</h2>
                <Vue3Marquee :pause-on-hover="true">
                    <div class="w-72 h-full mx-auto px-4" v-for="(attribute, index) in qualityAttributes" :key="index">
                        <div class="bg-esmerald rounded-xl relative h-full">
                            <component :is="attribute.icon" class="w-16 h-16 text-lemon text-center p-4"></component>
                            <p class="text-white m-4 font-regular">{{ messages.wordpress_component.quality_attributes[index].text }}</p>
                        </div>
                    </div>
                </Vue3Marquee>
                <h2 class="max-w-7xl mx-center my-12 px-3 text-end font-light text-4xl text-white lg:text-6xl lg:px-0">{{ messages.wordpress_component.why_not_wordpress }}</h2>
                <Vue3Marquee :pause-on-hover="true" direction="reverse" duration="35">
                    <div class="w-72 h-full mx-auto px-4" v-for="(reason, index) in reasons" :key="index">
                        <div class="bg-esmerald rounded-xl relative h-full">
                            <component :is="reason.icon" class="w-16 h-16 text-lemon text-center p-4"></component>
                            <p class="text-white m-4 font-regular">{{ messages.wordpress_component.reasons[index].text }}</p>
                        </div>
                    </div>
                </Vue3Marquee>
            </div>
    </section>
</template>

<script setup>
import { Vue3Marquee } from 'vue3-marquee';
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
    CheckBadgeIcon
} from '@heroicons/vue/24/outline';
import { useMessages } from '@/composables/useMessages'; // Importar el composable de mensajes

// Obtener los mensajes traducidos para esta vista
const { messages } = useMessages();

// Array de atributos de calidad con sus iconos correspondientes
// Mantenemos los iconos pero el texto vendrá de las traducciones
const qualityAttributes = [
    { icon: CheckCircleIcon },
    { icon: ShieldCheckIcon },
    { icon: UserCircleIcon },
    { icon: LightBulbIcon },
    { icon: CogIcon },
    { icon: LockClosedIcon },
    { icon: ArrowTrendingUpIcon },
    { icon: BeakerIcon }
];

// Array de razones con sus iconos correspondientes
// Mantenemos los iconos pero el texto vendrá de las traducciones
const reasons = [
    { icon: ExclamationCircleIcon },
    { icon: ClockIcon },
    { icon: ShieldExclamationIcon },
    { icon: ComputerDesktopIcon },
    { icon: ShieldCheckIcon },
    { icon: BanknotesIcon },
    { icon: LightBulbIcon },
    { icon: AdjustmentsHorizontalIcon },
    { icon: BookOpenIcon },
    { icon: AcademicCapIcon },
    { icon: SwatchIcon },
    { icon: ArrowTrendingDownIcon },
    { icon: CheckBadgeIcon },
    { icon: ClockIcon }
];
</script>