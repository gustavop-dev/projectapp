/**
 * Trigger a browser download of *url* under an explicit name (temporary
 * <a download>). Same-origin only: cross-origin responses ignore `download`.
 */
export function downloadUrl(url, filename) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Trigger a browser download for a Blob (same pattern as the PDF
 * download buttons: objectURL + temporary <a download>).
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  downloadUrl(url, filename);
  URL.revokeObjectURL(url);
}

/** Extract the filename from a Content-Disposition header, if present. */
export function filenameFromDisposition(disposition) {
  if (!disposition) return '';
  const match = /filename="?([^";]+)"?/.exec(disposition);
  return match ? match[1] : '';
}
