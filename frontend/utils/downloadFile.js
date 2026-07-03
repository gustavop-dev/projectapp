/**
 * Trigger a browser download for a Blob (same pattern as the PDF
 * download buttons: objectURL + temporary <a download>).
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/** Extract the filename from a Content-Disposition header, if present. */
export function filenameFromDisposition(disposition) {
  if (!disposition) return '';
  const match = /filename="?([^";]+)"?/.exec(disposition);
  return match ? match[1] : '';
}
