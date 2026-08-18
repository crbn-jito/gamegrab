import pytest
from pathlib import Path
from gamegrab.downloader import DownloadManager
import asyncio
import tempfile
import os

@pytest.mark.asyncio
async def test_download_small_http_file(tmp_path):
    # This is a placeholder test that expects you to run a small HTTP server locally
    # For CI, replace with a local file server or mock
    conf = {"download_dir": str(tmp_path), "concurrency": 1, "user_agent": "test", "retries": 1, "timeout_seconds": 5}
    mgr = DownloadManager(conf)
    # We won't actually perform a network test here; ensure object builds
    assert mgr.download_dir.exists()
