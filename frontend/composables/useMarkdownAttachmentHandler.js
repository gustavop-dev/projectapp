import { usePanelNotify } from '~/composables/usePanelNotify';

export function useMarkdownAttachmentHandler(attachments) {
  const notify = usePanelNotify();

  function handleMarkdownAttach(file) {
    attachments.value.push(file);
    notify.push({
      type: 'success',
      title: `Adjunto "${file.name}" agregado al correo.`,
    });
  }

  return { handleMarkdownAttach };
}
