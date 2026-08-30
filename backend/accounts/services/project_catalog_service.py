"""Shared catalog classification for project-facing panel modules."""


ACTIVE_PROJECT_EFFECTS = frozenset({'development', 'operating'})


def project_catalog_bucket(project):
    """Classify a project without hiding it from any module catalog."""
    state = getattr(project, 'current_state', None)
    if state is not None:
        return (
            'active'
            if state.operational_effect in ACTIVE_PROJECT_EFFECTS
            else 'archived'
        )
    return (
        'active'
        if project.status in {project.STATUS_DEVELOPMENT, project.STATUS_ACTIVE}
        else 'archived'
    )
