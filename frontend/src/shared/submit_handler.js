import Swal from "sweetalert2";
import { create_request } from "@/stores/services/request_http.js";

export async function submitHandler(formData) {
  try {
    const response = await create_request('api/contact/', JSON.stringify(formData));
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
      Swal.fire({
        icon: 'error',
        title: 'Error',
        html: '<a class="text-lg font-regular text-white">There was a error sending your message.</a>',
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
    Swal.fire({
      icon: 'error',
      title: 'Error',
      html: '<a class="text-lg font-regular text-white">There was a error sending your message.</a>',
      customClass: {
        popup: 'bg-window-black bg-opacity-40 backdrop-blur-md p-4 rounded-lg shadow-lg',
          title: 'text-4xl font-light text-white',
          confirmButton: 'bg-lemon text-black font-regular py-2 px-4 rounded-xl',
      },
      buttonsStyling: false,
    });
    return response;
  }
}
