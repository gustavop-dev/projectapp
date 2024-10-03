import axios from "axios";

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Request endpoint
 * @param {string} method - Type request.
 * @param {string} url - Endpoint
 * @param {object} params - Params.
 * @returns {object} - Data and status from endpoint.
 */
async function makeRequest(method, url, params = {}) {
  const csrfToken = getCookie('csrftoken');
  const headers = {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken
  };

  try {
    let response;

    switch (method) {
      case "GET":
        response = await axios.get(`/api/${url}`, { headers });
        break;
      case "POST":
        response = await axios.post(`/api/${url}`, params, { headers });
        break;
      default:
        throw new Error(`Unsupported method: ${method}`);
    }

    return response;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

/**
 * Get request.
 * @param {string} url - Endpoint.
 * @returns {object} - Data and status from endpoint.
 */
export async function get_request(url) {
  return await makeRequest("GET", url);
}

/**
 * Create request.
 * @param {string} url - Endpoint.
 * @param {object} params - Params.
 * @returns {object} - Data and status from endpoint.
 */
export async function create_request(url, params) {
  return await makeRequest("POST", url, params);
}