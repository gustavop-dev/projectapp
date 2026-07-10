/**
 * Prepare a markdown excerpt for the gallery mini-preview.
 * Cuts at the last complete line and closes a dangling ``` fence so an
 * excerpt that lands mid-code-block doesn't swallow the rest of the render.
 */
export function makeSafeExcerpt(markdown, maxChars = 500) {
  if (!markdown) return '';
  let text = String(markdown);
  if (text.length > maxChars) {
    const cut = text.slice(0, maxChars);
    const lastNewline = cut.lastIndexOf('\n');
    text = lastNewline > 0 ? cut.slice(0, lastNewline) : cut;
  }
  const fenceCount = (text.match(/```/g) || []).length;
  if (fenceCount % 2 !== 0) {
    text += '\n```';
  }
  return text;
}
