"""Unit tests for Updater and Admin Announcement Engine."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.config.updater import (
    get_local_version,
    save_local_version,
    bump_version_on_push,
    check_remote_update,
    publish_admin_announcement,
    get_local_announcement,
    check_remote_announcement,
    VERSION_FILE,
    ANNOUNCEMENT_FILE,
)


def test_get_and_save_local_version(tmp_path, monkeypatch):
    test_version_file = tmp_path / "version.json"
    monkeypatch.setattr("src.config.updater.VERSION_FILE", test_version_file)

    v = get_local_version()
    assert "version" in v
    assert "build" in v

    v["build"] = 999
    save_local_version(v)
    v_new = get_local_version()
    assert v_new["build"] == 999


def test_bump_version_on_push(tmp_path, monkeypatch):
    test_version_file = tmp_path / "version.json"
    monkeypatch.setattr("src.config.updater.VERSION_FILE", test_version_file)

    initial = get_local_version()
    initial_build = initial["build"]

    bumped = bump_version_on_push("Test Release")
    assert bumped["build"] == initial_build + 1
    assert bumped["description"] == "Test Release"


def test_check_remote_update(tmp_path, monkeypatch):
    test_version_file = tmp_path / "version.json"
    monkeypatch.setattr("src.config.updater.VERSION_FILE", test_version_file)
    save_local_version({"version": "4.2.0", "build": 100})

    # Mock remote higher build
    remote_data = json.dumps({"version": "4.2.1", "build": 101}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = remote_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        has_update, info = check_remote_update()
        assert has_update is True
        assert info["build"] == 101

    # Mock remote same build
    remote_data_same = json.dumps({"version": "4.2.0", "build": 100}).encode("utf-8")
    mock_resp.read.return_value = remote_data_same
    with patch("urllib.request.urlopen", return_value=mock_resp):
        has_update, info = check_remote_update()
        assert has_update is False


def test_publish_and_get_announcement(tmp_path, monkeypatch):
    test_ann_file = tmp_path / "announcements.json"
    monkeypatch.setattr("src.config.updater.ANNOUNCEMENT_FILE", test_ann_file)

    assert get_local_announcement() is None

    payload = publish_admin_announcement("Thong bao test tu Admin", sender="LilBoiXAU")
    assert payload["message"] == "Thong bao test tu Admin"
    assert payload["sender"] == "LilBoiXAU"

    local = get_local_announcement()
    assert local is not None
    assert local["message"] == "Thong bao test tu Admin"
