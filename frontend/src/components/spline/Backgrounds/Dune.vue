  <template>
    <div ref="canvasContainer" class="canvas-container"></div>
  </template>
  
  <script setup>
  import { onMounted, ref } from 'vue'; // Import onMounted for lifecycle and ref for reactivity
  import { Application } from '@splinetool/runtime'; // Import Spline runtime for embedding 3D scenes
  
  /**
   * Props received by the component:
   * - spline (String, required): The URL of the Spline 3D model to be loaded into the scene.
   */
  const props = defineProps({
    spline: {
      type: String,
      required: true, // Ensure the spline URL is provided
    }
  });
  
  const canvasContainer = ref(null); // Reference for the container where the canvas will be added
  
  /**
   * Lifecycle hook that runs after the component is mounted.
   * 
   * This hook creates a new <canvas> element, appends it to the canvas container, and
   * uses Spline's Application class to load a 3D model from the provided URL.
   */
  onMounted(() => {
    const canvas = document.createElement('canvas'); // Create a new canvas element
    canvasContainer.value.appendChild(canvas); // Append the canvas to the container
  
    const app = new Application(canvas); // Initialize the Spline Application with the canvas
    app.load(props.spline); // Load the Spline model using the URL from props
  });
  </script>  
  
  <style scoped>
  .canvas-container {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  </style>
  