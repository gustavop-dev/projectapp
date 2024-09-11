import axios from "axios";
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

const route = "http://127.0.0.1:8000/";

/**
 * Makes an HTTP request to the specified endpoint.
 * 
 * This function sends either a GET or POST request to the backend API and returns the response.
 * 
 * @param {string} method - The type of HTTP request ('GET' or 'POST').
 * @param {string} url - The endpoint to send the request to (relative to the base route).
 * @param {object} params - Optional parameters to include in the request body (for POST requests).
 * @returns {object|null} - The response data and status from the endpoint, or null if an error occurs.
 */
async function makeRequest(method, url, params = {}) {
    const headers = {
      "Content-Type": "application/json",
    };
  
    try {
      let response;
  
      // Handle GET and POST methods
      switch (method) {
        case "GET":
          response = await axios.get(`${route}${url}`, { headers });
          break;
        case "POST":
          response = await axios.post(`${route}${url}`, params, { headers });
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
  
      return response;
    } catch (error) {
      console.error(error);
      return null; // Return null in case of error
    }
}

/**
 * Sends a GET request to the specified endpoint.
 * 
 * This function uses the `makeRequest` function to send a GET request to the backend API.
 * 
 * @param {string} url - The endpoint to send the request to (relative to the base route).
 * @returns {object|null} - The response data and status from the endpoint, or null if an error occurs.
 */
export async function get_request(url) {
    return await makeRequest("GET", url);
}

/**
 * Sends a POST request to the specified endpoint with the provided parameters.
 * 
 * This function uses the `makeRequest` function to send a POST request to the backend API.
 * 
 * @param {string} url - The endpoint to send the request to (relative to the base route).
 * @param {object} params - The data to include in the request body.
 * @returns {object|null} - The response data and status from the endpoint, or null if an error occurs.
 */
export async function create_request(url, params) {
    return await makeRequest("POST", url, params);
}
