<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-16">
    <!-- Left Column - Contact Form -->
    <div class="left-column">
      <h2 class="form-title mb-8">
        {{ messages?.contactForm?.title || 'Hi there!' }} <span ref="waveEmoji" class="inline-block">👋</span><br>
        {{ messages?.contactForm?.subtitle || 'tell us what you need' }}
      </h2>
      <form @submit.prevent="handleSubmit" class="space-y-8">
        <!-- Full Name -->
        <input
          v-model="form.fullName"
          type="text"
          :placeholder="(messages?.contactForm?.fullName || 'Full name') + '*'"
          class="minimal-input"
          required
        />

        <!-- Phone Number -->
        <input
          v-model="form.phone"
          type="tel"
          :placeholder="(messages?.contactForm?.phone || 'Phone number') + '*'"
          class="minimal-input"
          required
        />

        <!-- Email -->
        <input
          v-model="form.email"
          type="email"
          :placeholder="(messages?.contactForm?.email || 'Your email address') + '*'"
          class="minimal-input"
          required
        />

        <!-- Message -->
        <textarea
          v-model="form.message"
          :placeholder="messages?.contactForm?.message || 'Tell us about your project'"
          rows="4"
          class="minimal-textarea"
          required
        ></textarea>

        <!-- Budget Options -->
        <div class="budget-section">
          <label class="budget-label">{{ messages?.contactForm?.budgetLabel || 'Project budget (USD)' }}</label>
          <div class="flex flex-wrap gap-3 mt-4">
            <button
              v-for="option in budgetOptions"
              :key="option"
              type="button"
              @click="selectBudget(option)"
              :class="[
                'budget-pill',
                form.budget === option ? 'budget-pill-active' : ''
              ]"
            >
              {{ option }}
            </button>
          </div>
        </div>

        <!-- Privacy Policy -->
        <p class="text-xs text-gray-600 leading-relaxed">
          {{ messages?.contactForm?.privacy || 'By submitting this form, your information will be sent directly to the listed business. It will not be sold, shared, or disclosed by Chilliwack Connect.' }}
          <a href="/privacy-policy" class="text-esmerald underline">{{ messages?.contactForm?.privacyLink || 'Privacy Policy.' }}</a>
        </p>

        <!-- Buttons Row -->
        <div class="flex flex-wrap gap-4">
          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="isSubmitting"
            class="submit-button"
          >
            {{ isSubmitting ? (messages?.contactForm?.sending || 'Sending...') : (messages?.contactForm?.submit || 'Submit') }}
          </button>

          <!-- Book a Call Button -->
          <button
            type="button"
            class="book-call-button"
            data-cal-link="projectapp/discovery-call-projectapp"
            data-cal-namespace="discovery-call-projectapp"
            data-cal-config='{"layout":"week_view","theme":"dark"}'
          >
            {{ messages?.contactForm?.bookCall || 'Book a Call' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Right Column - Two cards stacked -->
    <div class="right-column flex flex-col gap-6">
      <!-- Card 2: Awesome UI Design -->
      <div class="service-card group">
        <div class="card-background card-bg-2"></div>
        <div class="card-content">
          <div class="mockup-container">
            <img 
              src="@/assets/images/home/services/mkups/design.webp" 
              alt="UI Design Mockup"
              class="mockup-image"
            />
          </div>
          <div class="card-text">
            <h3 class="text-2xl font-bold text-white mb-3">
              {{ messages?.services?.card2?.title || 'Awesome UI Design' }}
            </h3>
            <p class="text-white/90 text-sm leading-relaxed">
              {{ messages?.services?.card2?.description || 'Where stunning visuals meet effortless functionality for an experience users love.' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Card 3: Flawless Performance -->
      <div class="service-card group">
        <div class="card-background card-bg-3"></div>
        <div class="card-content">
          <div class="mockup-container">
            <img 
              src="@/assets/images/home/services/mkups/cards-info.webp" 
              alt="Performance Mockup"
              class="mockup-image"
            />
          </div>
          <div class="card-text">
            <h3 class="text-2xl font-bold text-white mb-3">
              {{ messages?.services?.card3?.title || 'Flawless Performance' }}
            </h3>
            <p class="text-white/90 text-sm leading-relaxed">
              {{ messages?.services?.card3?.description || 'A website that looks amazing and works perfectly on every device.' }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessages } from '@/composables/useMessages'
import gsap from 'gsap'

const { messages } = useMessages()

// Ref for wave emoji animation
const waveEmoji = ref(null)

// Form state
const form = ref({
  fullName: '',
  phone: '',
  email: '',
  message: '',
  budget: ''
})

const budgetOptions = ['500-5K', '5-10K', '10-20K', '20-30K', '>30K']

const isSubmitting = ref(false)

const selectBudget = (option) => {
  form.value.budget = option
}

// Handle form submission
const handleSubmit = async () => {
  isSubmitting.value = true
  
  try {
    // TODO: Integrate with your backend API
    console.log('Form submitted:', form.value)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Reset form
    form.value = {
      fullName: '',
      phone: '',
      email: '',
      message: '',
      budget: ''
    }
    
    alert('Form submitted successfully!')
  } catch (error) {
    console.error('Error submitting form:', error)
    alert('Error submitting form. Please try again.')
  } finally {
    isSubmitting.value = false
  }
}

// Animate wave emoji on mount (infinite loop)
onMounted(() => {
  if (waveEmoji.value) {
    gsap.to(waveEmoji.value, {
      rotation: 20,
      transformOrigin: 'bottom center',
      duration: 0.3,
      ease: 'power1.inOut',
      yoyo: true,
      repeat: -1,
      repeatDelay: 3,
      delay: 0.5
    })
  }
})
</script>

<style scoped>
/* Form Title */
.form-title {
  font-size: 28px;
  font-weight: 300;
  color: #002921;
  line-height: 1.4;
}

/* Minimal Form Styles */
.minimal-input,
.minimal-textarea {
  width: 100%;
  padding: 16px 0;
  font-size: 18px;
  font-weight: 300;
  color: #333;
  background: transparent;
  border: none;
  border-bottom: 1px solid #d1d5db;
  outline: none;
  transition: border-color 0.3s ease;
}

.minimal-input:focus,
.minimal-textarea:focus {
  border-bottom-color: #002921;
}

.minimal-input::placeholder,
.minimal-textarea::placeholder {
  color: #002921;
  font-weight: 300;
}

.minimal-textarea {
  resize: none;
  font-family: inherit;
}

.budget-section {
  padding-top: 8px;
}

.budget-label {
  display: block;
  font-size: 16px;
  font-weight: 400;
  color: #64748b;
  margin-bottom: 4px;
}

.budget-pill {
  padding: 10px 24px;
  font-size: 15px;
  font-weight: 400;
  color: #64748b;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.budget-pill:hover {
  border-color: #002921;
  color: #002921;
}

.budget-pill-active {
  background: #002921;
  color: #ffffff;
  border-color: #002921;
}

.submit-button {
  width: auto;
  padding: 14px 48px;
  font-size: 16px;
  font-weight: 600;
  color: #000;
  background: #F0FF3D;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-button:hover:not(:disabled) {
  background: #e0ef2d;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(240, 255, 61, 0.3);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.book-call-button {
  width: auto;
  padding: 14px 48px;
  font-size: 16px;
  font-weight: 600;
  color: #002921;
  background: transparent;
  border: 2px solid #E6EFEF;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.book-call-button:hover {
  background: rgba(230, 239, 239, 0.3);
  border-color: #002921;
  transform: translateY(-1px);
}

/* Service Cards */
.service-card {
  position: relative;
  height: 400px;
  border-radius: 24px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.service-card:hover {
  transform: translateY(-8px);
}

.card-background {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  transition: transform 0.3s ease;
}

.card-bg-1 {
  background-image: url('@/assets/images/home/services/bg/card-technologies-1.webp');
}

.card-bg-2 {
  background-image: url('@/assets/images/home/services/bg/card-technologies-2.webp');
}

.card-bg-3 {
  background-image: url('@/assets/images/home/services/bg/card-technologies-3.webp');
}

.service-card:hover .card-background {
  transform: scale(1.05);
}

.card-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 32px;
  z-index: 1;
}

.mockup-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70%;
  max-width: 280px;
  transition: transform 0.3s ease;
}

.service-card:hover .mockup-container {
  transform: translate(-50%, -50%) scale(1.05);
}

.mockup-image {
  width: 100%;
  height: auto;
  filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.3));
}

.card-text {
  position: relative;
  z-index: 2;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .service-card {
    height: 350px;
  }
  
  .mockup-container {
    width: 60%;
    max-width: 200px;
  }
  
  .card-content {
    padding: 24px;
  }
}
</style>
