import Swal from "sweetalert2";
import { create_request } from "@/stores/services/request_http.js";

/**
 * Handles form submission and displays a SweetAlert notification based on the response.
 * 
 * This function sends the form data to the backend API, handles the response,
 * and provides feedback to the user through SweetAlert notifications.
 * 
 * @param {object} formData - The form data to be sent in the request body.
 * @returns {object|null} - The API response if successful, or null if an error occurs.
 */
export async function submitHandler(formData) {
  try {
    // Send form data to the backend as a POST request
    const response = await create_request('api/contact/', JSON.stringify(formData));
    
    // If the request is successful and the status is 201 (created)
    if (response && response.status === 201) {
      Swal.fire({
        icon: 'success',
        title: 'Success',
        html: '<a class="text-lg font-regular text-white">Your message has been sent successfully!</a>',
        confirmButtonText: 'Ok',
        customClass: {
          popup: 'bg-window-black bg-opacity-40 backdrop-blur-md p-4 rounded-lg shadow-lg',
          title: 'text-4xl font-light text-white',
          confirmButton: 'bg-lemon text-esmerald font-regular py-2 px-4 rounded-xl',
        },
        buttonsStyling: false,
      });
    } else {
      // If the request fails (non-201 status), display an error alert
      Swal.fire({
        icon: 'error',
        title: 'Error',
        html: '<a class="text-lg font-regular text-white">There was an error sending your message.</a>',
        customClass: {
          popup: 'bg-window-black bg-opacity-40 backdrop-blur-md p-4 rounded-lg shadow-lg',
          title: 'text-4xl font-light text-white',
          confirmButton: 'bg-lemon text-black font-regular py-2 px-4 rounded-xl',
        },
        buttonsStyling: false,
      });
    }
    return response;
  } catch (error) {
    // In case of an error during the request, display a SweetAlert error
    Swal.fire({
      icon: 'error',
      title: 'Error',
      html: '<a class="text-lg font-regular text-white">There was an error sending your message.</a>',
      customClass: {
        popup: 'bg-window-black bg-opacity-40 backdrop-blur-md p-4 rounded-lg shadow-lg',
        title: 'text-4xl font-light text-white',
        confirmButton: 'bg-lemon text-black font-regular py-2 px-4 rounded-xl',
      },
      buttonsStyling: false,
    });
    return null; // Return null in case of an error
  }
}

