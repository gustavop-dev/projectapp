import axios from "axios";
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

const route = "http://127.0.0.1:8000/";

/**
 * Request endpoint
 * @param {string} method - Type request.
 * @param {string} url - Endpoint
 * @param {object} params - Params.
 * @returns {object} - Data and status from endpoint.
 */
async function makeRequest(method, url, params = {}) {
    const headers = {
      "Content-Type": "application/json",
    };
  
    try {
      let response;
  
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