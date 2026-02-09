"""Tests for Slack notification module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from market_pipeline.config.settings import SlackSettings
from market_pipeline.utils.slack_notifier import JobContext, JobResult, SlackNotifier


class TestSlackSettings:
    """Tests for SlackSettings.is_configured property."""

    def test_is_configured_with_url_and_enabled(self):
        s = SlackSettings(webhook_url="https://hooks.slack.com/test", enabled=True)
        assert s.is_configured is True

    def test_is_configured_without_url(self):
        s = SlackSettings(webhook_url="", enabled=True)
        assert s.is_configured is False

    def test_is_configured_when_disabled(self):
        s = SlackSettings(webhook_url="https://hooks.slack.com/test", enabled=False)
        assert s.is_configured is False

    def test_is_configured_without_url_and_disabled(self):
        s = SlackSettings(webhook_url="", enabled=False)
        assert s.is_configured is False


class TestJobResult:
    """Tests for JobResult dataclass."""

    def test_duration_formatted_minutes_and_seconds(self):
        result = JobResult(
            job_name="test",
            start_time=datetime(2025, 1, 1, 10, 0, 0),
            end_time=datetime(2025, 1, 1, 10, 2, 30),
        )
        assert result.duration_formatted == "2分30秒"

    def test_duration_formatted_seconds_only(self):
        result = JobResult(
            job_name="test",
            start_time=datetime(2025, 1, 1, 10, 0, 0),
            end_time=datetime(2025, 1, 1, 10, 0, 45),
        )
        assert result.duration_formatted == "45秒"

    def test_duration_formatted_zero_seconds(self):
        result = JobResult(
            job_name="test",
            start_time=datetime(2025, 1, 1, 10, 0, 0),
            end_time=datetime(2025, 1, 1, 10, 0, 0),
        )
        assert result.duration_formatted == "0秒"

    def test_duration_formatted_no_times(self):
        result = JobResult(job_name="test")
        assert result.duration_formatted == "不明"

    def test_duration_formatted_no_start_time(self):
        result = JobResult(job_name="test", end_time=datetime(2025, 1, 1, 10, 0, 0))
        assert result.duration_formatted == "不明"

    def test_default_values(self):
        result = JobResult(job_name="test")
        assert result.success is True
        assert result.metrics == {}
        assert result.errors == []
        assert result.warnings == []


class TestSlackNotifier:
    """Tests for SlackNotifier class."""

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    def test_is_available_when_configured(self, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        notifier = SlackNotifier()
        assert notifier.is_available is True

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    def test_is_available_when_not_configured(self, mock_settings):
        mock_settings.return_value.slack = SlackSettings(webhook_url="", enabled=True)
        notifier = SlackNotifier()
        assert notifier.is_available is False

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_send_success(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = SlackNotifier()
        job_result = JobResult(
            job_name="テストジョブ",
            start_time=datetime(2025, 1, 1, 10, 0, 0),
            end_time=datetime(2025, 1, 1, 10, 1, 0),
            metrics={"レコード数": "1,000"},
        )
        notifier.send_success(job_result)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "テストジョブ" in payload["text"]
        assert "完了" in payload["text"]
        assert "レコード数" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_send_error(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = SlackNotifier()
        job_result = JobResult(
            job_name="テストジョブ",
            success=False,
            start_time=datetime(2025, 1, 1, 10, 0, 0),
            end_time=datetime(2025, 1, 1, 10, 1, 0),
            errors=["Connection timeout"],
        )
        notifier.send_error(job_result)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "テストジョブ" in payload["text"]
        assert "失敗" in payload["text"]
        assert "Connection timeout" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_send_error_uses_error_webhook_url(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/normal",
            error_webhook_url="https://hooks.slack.com/errors",
            enabled=True,
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = SlackNotifier()
        job_result = JobResult(job_name="test", success=False, errors=["error"])
        notifier.send_error(job_result)

        call_args = mock_post.call_args
        assert call_args[0][0] == "https://hooks.slack.com/errors"

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_send_warning(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = SlackNotifier()
        notifier.send_warning("テストジョブ", "データが少ないです", "詳細情報")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "警告" in payload["text"]
        assert "データが少ないです" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    def test_send_success_skips_when_not_configured(self, mock_settings):
        mock_settings.return_value.slack = SlackSettings(webhook_url="", enabled=True)
        notifier = SlackNotifier()
        job_result = JobResult(job_name="test")
        # Should not raise
        notifier.send_success(job_result)

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    @patch("market_pipeline.utils.slack_notifier.time.sleep")
    def test_retry_on_failure(self, mock_sleep, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test",
            enabled=True,
            max_retries=3,
        )
        mock_post.side_effect = ConnectionError("Network error")

        notifier = SlackNotifier()
        job_result = JobResult(
            job_name="test",
            start_time=datetime(2025, 1, 1),
            end_time=datetime(2025, 1, 1),
        )
        # Should not raise, just log warning
        notifier.send_success(job_result)

        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries, not after last


class TestJobContext:
    """Tests for JobContext context manager."""

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_success_path(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        with JobContext("テストジョブ") as job:
            job.add_metric("レコード数", "100")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "完了" in payload["text"]
        assert "レコード数" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_error_path(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        with pytest.raises(ValueError, match="テストエラー"):
            with JobContext("テストジョブ"):
                raise ValueError("テストエラー")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "失敗" in payload["text"]
        assert "テストエラー" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_add_metric(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        with JobContext("テストジョブ") as job:
            job.add_metric("銘柄数", "500")
            job.add_metric("期間", "2025-01-01 ~ 2025-01-31")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "銘柄数" in payload["text"]
        assert "期間" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_add_warning(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        with JobContext("テストジョブ") as job:
            job.add_warning("一部銘柄でデータ欠損")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "一部銘柄でデータ欠損" in payload["text"]

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_notification_failure_does_not_affect_job(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test",
            enabled=True,
            max_retries=1,
        )
        mock_post.side_effect = ConnectionError("Network error")

        # Should complete without raising
        with JobContext("テストジョブ") as job:
            job.add_metric("結果", "OK")

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    def test_skips_when_webhook_not_set(self, mock_settings):
        mock_settings.return_value.slack = SlackSettings(webhook_url="", enabled=True)

        with JobContext("テストジョブ") as job:
            job.add_metric("結果", "OK")
        # No exception should be raised

    @patch("market_pipeline.utils.slack_notifier.get_settings")
    @patch("market_pipeline.utils.slack_notifier.requests.post")
    def test_records_start_and_end_time(self, mock_post, mock_settings):
        mock_settings.return_value.slack = SlackSettings(
            webhook_url="https://hooks.slack.com/test", enabled=True
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()

        with JobContext("テストジョブ"):
            pass

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        # Duration should be present in the message
        assert "実行時間" in payload["text"]
