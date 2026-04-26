export const PREVIEWABLE_PDF_RE = /\.pdf(?:\?|#|$)/i;
export const PREVIEWABLE_IMG_RE = /\.(png|jpe?g|gif|webp|svg)(?:\?|#|$)/i;

export function isPdfUrl(url) {
  return PREVIEWABLE_PDF_RE.test(url || '');
}

export function isImageUrl(url) {
  return PREVIEWABLE_IMG_RE.test(url || '');
}

export function canPreviewFile(url) {
  return isPdfUrl(url) || isImageUrl(url);
}
