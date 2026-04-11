from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from django.utils import timezone

from projectapp.tasks import (
    scheduled_backup,
    silk_garbage_collection,
    silk_reports_cleanup,
    weekly_slow_queries_report,
)


class FakeQuerySet:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, **kwargs):
        if 'query_count__gte' in kwargs:
            threshold = kwargs['query_count__gte']
            return FakeQuerySet([
                item for item in self.items
                if getattr(item, 'query_count', 0) >= threshold
            ])
        return self

    def annotate(self, **kwargs):
        return self

    def select_related(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def __getitem__(self, item):
        if isinstance(item, slice):
            return FakeQuerySet(self.items[item])
        return self.items[item]

    def __iter__(self):
        return iter(self.items)

    def __bool__(self):
        return bool(self.items)

    def count(self):
        return len(self.items)


@pytest.mark.django_db
class TestScheduledBackup:
    @patch('projectapp.tasks.logger')
    @patch('django.core.management.call_command')
    def test_runs_db_and_media_backup_and_returns_true(self, mock_call_command, mock_logger):
        result = scheduled_backup.call_local()

        assert result is True
        assert mock_call_command.call_count == 2
        first_call = mock_call_command.call_args_list[0]
        second_call = mock_call_command.call_args_list[1]
        assert first_call.args[:3] == ('dbbackup', '--compress', '--clean')
        assert second_call.args[:3] == ('mediabackup', '--compress', '--clean')
        assert mock_logger.info.call_count >= 4

    @patch('projectapp.tasks.logger')
    @patch('django.core.management.call_command', side_effect=RuntimeError('boom'))
    def test_logs_and_reraises_when_backup_fails(self, mock_call_command, mock_logger):
        with pytest.raises(RuntimeError, match='boom'):
            scheduled_backup.call_local()

        mock_call_command.assert_called_once()
        mock_logger.error.assert_called_once()


@pytest.mark.django_db
class TestSilkGarbageCollection:
    @override_settings(ENABLE_SILK=False)
    @patch('django.core.management.call_command')
    def test_returns_early_when_silk_disabled(self, mock_call_command):
        result = silk_garbage_collection.call_local()

        assert result is None
        mock_call_command.assert_not_called()

    @override_settings(ENABLE_SILK=True)
    @patch('projectapp.tasks.logger')
    @patch('django.core.management.call_command')
    def test_runs_cleanup_when_silk_enabled(self, mock_call_command, mock_logger):
        silk_garbage_collection.call_local()

        mock_call_command.assert_called_once()
        assert mock_call_command.call_args.args[:2] == ('silk_garbage_collect', '--days=7')
        mock_logger.info.assert_called()


@pytest.mark.django_db
class TestWeeklySlowQueriesReport:
    @override_settings(ENABLE_SILK=False)
    def test_returns_none_when_silk_disabled(self):
        result = weekly_slow_queries_report.call_local()

        assert result is None

    @override_settings(ENABLE_SILK=True, SLOW_QUERY_THRESHOLD_MS=500, N_PLUS_ONE_THRESHOLD=10)
    @patch('projectapp.tasks.logger')
    @patch('projectapp.tasks.timezone.now')
    def test_generates_report_with_slow_queries_and_n_plus_one(
        self,
        mock_now,
        mock_logger,
        tmp_path,
        settings,
    ):
        fixed_now = timezone.now()
        mock_now.return_value = fixed_now
        settings.BASE_DIR = tmp_path

        slow_queries = FakeQuerySet([
            SimpleNamespace(
                time_taken=640,
                request=SimpleNamespace(path='/api/projects'),
                query='SELECT * FROM projects WHERE id = 1',
            ),
        ])
        n_plus_one = FakeQuerySet([
            SimpleNamespace(path='/platform/projects', query_count=12),
        ])
        fake_module = SimpleNamespace(
            SQLQuery=SimpleNamespace(objects=slow_queries),
            Request=SimpleNamespace(objects=n_plus_one),
        )

        with patch.dict('sys.modules', {'silk.models': fake_module}):
            report = weekly_slow_queries_report.call_local()

        report_path = tmp_path / 'logs' / 'silk-reports' / f'silk-report-{fixed_now.strftime("%Y-%m-%d")}.log'
        assert 'SLOW QUERIES (>500ms)' in report
        assert '/api/projects' in report
        assert 'POTENTIAL N+1 (>10 queries/request)' in report
        assert '/platform/projects' in report
        assert report_path.exists()
        assert 'Slow queries: 1' in mock_logger.info.call_args.args[0]

    @override_settings(ENABLE_SILK=True)
    @patch('projectapp.tasks.logger')
    @patch('projectapp.tasks.timezone.now')
    def test_generates_report_when_no_findings(
        self,
        mock_now,
        mock_logger,
        tmp_path,
        settings,
    ):
        fixed_now = timezone.now()
        mock_now.return_value = fixed_now
        settings.BASE_DIR = tmp_path

        fake_module = SimpleNamespace(
            SQLQuery=SimpleNamespace(objects=FakeQuerySet([])),
            Request=SimpleNamespace(objects=FakeQuerySet([])),
        )

        with patch.dict('sys.modules', {'silk.models': fake_module}):
            report = weekly_slow_queries_report.call_local()

        assert 'No slow queries found this week' in report
        assert 'No N+1 patterns detected this week' in report
        mock_logger.info.assert_called_once()


@pytest.mark.django_db
class TestSilkReportsCleanup:
    @override_settings(ENABLE_SILK=False)
    def test_returns_early_when_silk_disabled(self):
        result = silk_reports_cleanup.call_local()

        assert result is None

    @override_settings(ENABLE_SILK=True)
    def test_returns_when_reports_dir_missing(self, tmp_path, settings):
        settings.BASE_DIR = tmp_path

        result = silk_reports_cleanup.call_local()

        assert result is None

    @override_settings(ENABLE_SILK=True)
    @patch('projectapp.tasks.logger')
    def test_deletes_only_old_report_files(self, mock_logger, tmp_path, settings):
        settings.BASE_DIR = tmp_path
        reports_dir = tmp_path / 'logs' / 'silk-reports'
        reports_dir.mkdir(parents=True, exist_ok=True)

        old_file = reports_dir / 'silk-report-old.log'
        old_file.write_text('old')
        recent_file = reports_dir / 'silk-report-recent.log'
        recent_file.write_text('recent')

        now = timezone.now()
        old_ts = (now - timedelta(days=181)).timestamp()
        recent_ts = (now - timedelta(days=10)).timestamp()

        import os
        os.utime(old_file, (old_ts, old_ts))
        os.utime(recent_file, (recent_ts, recent_ts))

        silk_reports_cleanup.call_local()

        assert not old_file.exists()
        assert recent_file.exists()
        mock_logger.info.assert_called_once()
