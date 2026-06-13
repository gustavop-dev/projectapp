"""Tests for the frontend prerender rebuild service (blog SEO)."""
import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from content.models import BlogPost
from content.services import frontend_build


@pytest.fixture
def marker_path(tmp_path, monkeypatch):
    """Point the build marker at a temp file."""
    path = tmp_path / 'frontend-build-marker.json'
    monkeypatch.setattr(frontend_build, 'MARKER_PATH', path)
    return path


@pytest.fixture
def published_post(db):
    return BlogPost.objects.create(
        title_es='Post publicado', title_en='Published post',
        excerpt_es='E', excerpt_en='E',
        is_published=True,
    )


def write_marker_now(marker_path):
    marker_path.write_text(json.dumps({'started_at': timezone.now().isoformat()}))


class TestRebuildNeeded:
    def test_false_without_published_posts(self, db, marker_path):
        assert frontend_build.rebuild_needed() is False

    def test_true_when_never_built(self, published_post, marker_path):
        assert frontend_build.rebuild_needed() is True

    def test_false_when_marker_is_newer_than_content(self, published_post, marker_path):
        write_marker_now(marker_path)
        assert frontend_build.rebuild_needed() is False

    def test_true_again_after_post_update(self, published_post, marker_path):
        write_marker_now(marker_path)
        published_post.title_es = 'Editado'
        published_post.save()  # bumps updated_at past the marker
        assert frontend_build.rebuild_needed() is True

    def test_corrupt_marker_counts_as_never_built(self, published_post, marker_path):
        marker_path.write_text('not json{')
        assert frontend_build.rebuild_needed() is True


class TestRunFrontendRebuild:
    def test_skips_when_disabled(self, settings, marker_path):
        settings.FRONTEND_REBUILD_ENABLED = False
        result = frontend_build.run_frontend_rebuild(force=True)
        assert result['status'] == 'skipped'

    def test_skips_when_no_changes(self, db, settings, marker_path):
        settings.FRONTEND_REBUILD_ENABLED = True
        result = frontend_build.run_frontend_rebuild()
        assert result['status'] == 'skipped'

    @patch.object(frontend_build, 'call_command')
    @patch.object(frontend_build.subprocess, 'run')
    def test_success_runs_build_and_writes_marker(
        self, mock_run, mock_collectstatic, published_post, settings, marker_path,
    ):
        settings.FRONTEND_REBUILD_ENABLED = True
        settings.DEBUG = False
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        result = frontend_build.run_frontend_rebuild()

        assert result['status'] == 'success'
        assert marker_path.exists()
        assert mock_run.call_args.kwargs['cwd'] == frontend_build.FRONTEND_DIR
        env = mock_run.call_args.kwargs['env']
        assert env['PRERENDER_REQUIRE_BLOG'] == '1'
        assert env['PRERENDER_API_ORIGIN'] == settings.PRERENDER_API_ORIGIN
        mock_collectstatic.assert_called_once()
        assert frontend_build.rebuild_needed() is False

    @patch.object(frontend_build, 'call_command')
    @patch.object(frontend_build.subprocess, 'run')
    def test_collectstatic_skipped_in_debug(
        self, mock_run, mock_collectstatic, published_post, settings, marker_path,
    ):
        settings.FRONTEND_REBUILD_ENABLED = True
        settings.DEBUG = True
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        result = frontend_build.run_frontend_rebuild()

        assert result['status'] == 'success'
        mock_collectstatic.assert_not_called()

    @patch.object(frontend_build.subprocess, 'run')
    def test_build_failure_reports_and_keeps_marker_untouched(
        self, mock_run, published_post, settings, marker_path,
    ):
        settings.FRONTEND_REBUILD_ENABLED = True
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='boom')

        result = frontend_build.run_frontend_rebuild()

        assert result['status'] == 'failed'
        assert 'boom' in result['detail']
        assert not marker_path.exists()

    @patch.object(frontend_build.subprocess, 'run')
    def test_build_timeout_reports_failure(
        self, mock_run, published_post, settings, marker_path,
    ):
        settings.FRONTEND_REBUILD_ENABLED = True
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='npm', timeout=1)

        result = frontend_build.run_frontend_rebuild()

        assert result['status'] == 'failed'
        assert not marker_path.exists()


class TestScheduleRebuildAfterPublish:
    def test_enqueues_task_with_delay(self, settings):
        settings.FRONTEND_REBUILD_ENABLED = True
        with patch('content.tasks.rebuild_frontend_prerender') as mock_task:
            frontend_build.schedule_rebuild_after_publish()
        mock_task.schedule.assert_called_once_with(delay=120)

    def test_noop_when_disabled(self, settings):
        settings.FRONTEND_REBUILD_ENABLED = False
        with patch('content.tasks.rebuild_frontend_prerender') as mock_task:
            frontend_build.schedule_rebuild_after_publish()
        mock_task.schedule.assert_not_called()

    def test_enqueue_failure_does_not_raise(self, settings):
        settings.FRONTEND_REBUILD_ENABLED = True
        with patch('content.tasks.rebuild_frontend_prerender') as mock_task:
            mock_task.schedule.side_effect = RuntimeError('redis down')
            frontend_build.schedule_rebuild_after_publish()  # must not raise
