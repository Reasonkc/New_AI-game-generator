/**
 * Wrapper around fetch that adds a timeout.
 *
 * @param {string} url - The URL to fetch.
 * @param {RequestInit} options - Standard fetch options.
 * @param {number} [timeoutMs=60000] - Timeout in milliseconds (default 60s).
 * @returns {Promise<Response>} The fetch response.
 * @throws {Error} If the request exceeds the timeout.
 */
export async function fetchWithTimeout(url, options = {}, timeoutMs = 60000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(
        `Request timed out after ${Math.round(timeoutMs / 1000)} seconds. The server may be busy — please try again.`
      );
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
