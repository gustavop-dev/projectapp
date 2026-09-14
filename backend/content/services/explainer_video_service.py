"""Visibility rule for the explainer videos shown in the client-facing views."""

from content.models import ExplainerVideoSettings

# Explainer ids match frontend/composables/useExplainerVideos.js.
MODULE_SWITCHES = {
    'additional-modules': 'show_additional_modules_video',
    'financing': 'show_financing_video',
}


def explainer_video_visible(module, *, share_link=None):
    """Return whether the public view of ``module`` may show its explainer.

    The panel switch of the module governs. A shared catalog link can only hide
    the video for its recipient: it shows when both switches are on. Whether a
    render exists for the visitor's language is decided by the frontend.
    """

    if module not in MODULE_SWITCHES:
        raise ValueError(f'Unknown explainer module: {module}')
    visible = getattr(ExplainerVideoSettings.load(), MODULE_SWITCHES[module])
    if share_link is not None:
        visible = visible and share_link.show_explainer_video
    return visible
