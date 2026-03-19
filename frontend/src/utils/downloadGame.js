/**
 * Download game HTML as a standalone file.
 *
 * @param {string} html - The game HTML content to download.
 * @param {string} [title="ai-game"] - The filename (without extension).
 * @returns {boolean} True if the download was triggered, false otherwise.
 */
export function downloadGame(html, title = "ai-game") {
  if (!html || typeof html !== "string") {
    console.error("downloadGame: invalid or empty HTML content");
    return false;
  }

  const blob = new Blob([html], { type: "text/html" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${title}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
  return true;
}
