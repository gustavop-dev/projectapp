"""Shared querysets for document threads.

The panel views and the Documents MCP connector need the same shapes: the fully
prefetched detail queryset and the paginated listing. Keeping them here means a
change to the chronology ordering or to the prefetch reaches both callers at
once, instead of drifting between `views/document_thread.py` and
`mcp/document_thread_tools.py`.
"""
from django.db.models import Count, Max, Min, Prefetch, Q
from django.db.models.functions import Lower

from content.models import DocumentThread, DocumentThreadItem


THREAD_LIST_ORDERS = ('recent', 'milestone', 'title')


def _item_queryset():
    return (
        DocumentThreadItem.objects.select_related(
            'document__document_type',
            'document__folder',
            'document__project',
            'document__client_user__profile',
            'linked_by',
            'updated_by',
        )
        .order_by('occurred_on', 'position', 'id')
    )


def thread_detail_queryset():
    """Threads with their chronology prefetched in display order."""
    return (
        DocumentThread.objects.select_related('created_by', 'updated_by')
        .annotate(document_count=Count('items', distinct=True))
        .prefetch_related(Prefetch('items', queryset=_item_queryset()))
    )


def thread_for_document(document_id):
    """The thread a document belongs to, or None when it is standalone."""
    membership = DocumentThreadItem.objects.filter(document_id=document_id).first()
    if membership is None:
        return None
    return thread_detail_queryset().filter(pk=membership.thread_id).first()


def thread_list_queryset(*, search='', client_id=None, project_id=None, order='recent'):
    """Paginable thread listing with its date span annotated.

    Filters go through subqueries on the membership table instead of joining it:
    a join would multiply the rows and contaminate the Min/Max annotations.
    """
    queryset = (
        DocumentThread.objects.select_related('created_by', 'updated_by')
        .annotate(
            document_count=Count('items', distinct=True),
            first_occurred_on=Min('items__occurred_on'),
            last_occurred_on=Max('items__occurred_on'),
        )
        .prefetch_related(Prefetch('items', queryset=_item_queryset()))
    )

    search = str(search or '').strip()[:200]
    if search:
        by_document = DocumentThreadItem.objects.filter(
            document__title__icontains=search,
        ).values('thread_id')
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(pk__in=by_document),
        )

    for value, lookup in (
        (client_id, 'document__client_user__profile__id'),
        (project_id, 'document__project_id'),
    ):
        if value is None:
            continue
        members = DocumentThreadItem.objects.filter(
            **{lookup: value},
        ).values('thread_id')
        queryset = queryset.filter(pk__in=members)

    if order == 'milestone':
        return queryset.order_by('-last_occurred_on', '-id')
    if order == 'title':
        return queryset.order_by(Lower('title'), 'id')
    return queryset.order_by('-updated_at', '-id')
