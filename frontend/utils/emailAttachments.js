export const ALLOWED_EXTENSIONS = new Set(['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg']);
export const MAX_FILE_SIZE = 15 * 1024 * 1024;

export function validateEmailAttachments(files) {
  const validFiles = [];
  const errors = [];
  for (const file of files) {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      errors.push(`${file.name}: tipo no permitido`);
      continue;
    }
    if (file.size > MAX_FILE_SIZE) {
      errors.push(`${file.name}: excede 15 MB`);
      continue;
    }
    validFiles.push(file);
  }
  return { validFiles, errors };
}
