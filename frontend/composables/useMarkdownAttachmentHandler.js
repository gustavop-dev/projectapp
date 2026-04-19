import { usePanelToast } from '~/composables/usePanelToast';

export function useMarkdownAttachmentHandler(attachments) {
  const { showToast } = usePanelToast();

  function handleMarkdownAttach(file) {
    attachments.value.push(file);
    showToast({
      type: 'success',
      text: `Adjunto "${file.name}" agregado al correo.`,
    });
  }

  return { handleMarkdownAttach };
}
