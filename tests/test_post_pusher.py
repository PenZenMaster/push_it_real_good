"""
Module/Script Name: test_post_pusher.py
Path: E:/projects/push_it_real_good/tests/test_post_pusher.py

Description:
TDD test suite for post_pusher.py. Covers scheduling logic, config loading,
image upload, and post publishing without hitting the live WordPress API.

Author(s):
Rank Rocket Co (C) Copyright 2026 - All Rights Reserved

Created Date: 2026-05-17
Last Modified Date: 2026-05-17

Comments:
- v1.00 Initial TDD scaffold
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

from post_pusher import (
    get_schedule_timestamp,
    load_config,
    publish_file,
    upload_featured_image,
)


# ---------------------------------------------------------------------------
# get_schedule_timestamp
# ---------------------------------------------------------------------------


def test_get_schedule_timestamp_returns_future_timestamp() -> None:
    ts = get_schedule_timestamp("Monday", "09:00")
    assert ts > datetime.now().timestamp()


def test_get_schedule_timestamp_correct_day_of_week() -> None:
    day_name = "Friday"
    ts = get_schedule_timestamp(day_name, "10:00")
    result_dt = datetime.fromtimestamp(ts)
    assert result_dt.strftime("%A") == day_name


def test_get_schedule_timestamp_advances_a_week_when_same_day_past_time() -> None:
    today = datetime.now()
    day_name = today.strftime("%A")
    past_time = (today - timedelta(hours=1)).strftime("%H:%M")
    ts = get_schedule_timestamp(day_name, past_time)
    result_dt = datetime.fromtimestamp(ts)
    assert result_dt > today + timedelta(days=6)


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


def test_load_config_returns_dict(tmp_path: Path) -> None:
    cfg = {"wp_url": "https://example.com", "username": "admin", "app_password": "secret"}
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(cfg))
    result = load_config(str(cfg_file))
    assert result == cfg


def test_load_config_raises_on_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.json")


def test_load_config_raises_on_invalid_json(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json {{{")
    with pytest.raises(json.JSONDecodeError):
        load_config(str(bad_file))


# ---------------------------------------------------------------------------
# upload_featured_image
# ---------------------------------------------------------------------------


def test_upload_featured_image_returns_media_id(mocker: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 42}
    mock_response.raise_for_status.return_value = None
    mocker.patch("post_pusher.requests.post", return_value=mock_response)
    mocker.patch("builtins.open", mock_open(read_data=b"fake image bytes"))

    config = {"wp_url": "https://example.com", "username": "u", "app_password": "p"}
    result = upload_featured_image("fake_image.jpg", config)
    assert result == 42


def test_upload_featured_image_returns_none_on_http_error(mocker: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403")
    mocker.patch("post_pusher.requests.post", return_value=mock_response)
    mocker.patch("builtins.open", mock_open(read_data=b"fake image bytes"))

    config = {"wp_url": "https://example.com", "username": "u", "app_password": "p"}
    result = upload_featured_image("fake_image.jpg", config)
    assert result is None


def test_upload_featured_image_returns_none_on_io_error(mocker: MagicMock) -> None:
    mocker.patch("builtins.open", side_effect=OSError("disk error"))
    config = {"wp_url": "https://example.com", "username": "u", "app_password": "p"}
    result = upload_featured_image("missing.jpg", config)
    assert result is None


# ---------------------------------------------------------------------------
# publish_file
# ---------------------------------------------------------------------------


def test_publish_file_posts_to_wordpress(mocker: MagicMock, tmp_path: Path) -> None:
    html_file = tmp_path / "my-great-post.html"
    html_file.write_text("<p>Hello world</p>", encoding="utf-8")

    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 99}
    mock_response.raise_for_status.return_value = None
    mock_post = mocker.patch("post_pusher.requests.post", return_value=mock_response)

    (tmp_path / "posted").mkdir()
    config = {
        "wp_url": "https://example.com",
        "username": "u",
        "app_password": "p",
        "post_status": "draft",
    }
    publish_file(html_file, config)
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "my great post".lower() in call_kwargs.kwargs["json"]["title"].lower()


def test_publish_file_moves_file_after_post(mocker: MagicMock, tmp_path: Path) -> None:
    pre_post_dir = tmp_path / "pre-post"
    pre_post_dir.mkdir()
    html_file = pre_post_dir / "moved-post.html"
    html_file.write_text("<p>Content</p>", encoding="utf-8")
    posted_dir = tmp_path / "posted"
    posted_dir.mkdir()

    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 7}
    mock_response.raise_for_status.return_value = None
    mocker.patch("post_pusher.requests.post", return_value=mock_response)

    config = {
        "wp_url": "https://example.com",
        "username": "u",
        "app_password": "p",
        "post_status": "draft",
    }
    publish_file(html_file, config)
    assert not html_file.exists()
    assert (posted_dir / "moved-post.html").exists()


def test_publish_file_logs_error_on_unreadable_file(
    mocker: MagicMock, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    missing = tmp_path / "ghost.html"
    config = {"wp_url": "https://example.com", "username": "u", "app_password": "p"}
    import logging

    with caplog.at_level(logging.ERROR, logger="post_pusher"):
        publish_file(missing, config)
    assert any("I/O error" in r.message for r in caplog.records)
