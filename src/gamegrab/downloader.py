import asyncio
import aiohttp
import aiofiles
import os
from pathlib import Path
from typing import Dict, List, Optional
from rich.progress import Progress, TaskID, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.console import Console
import hashlib
import math
import time

console = Console()

class DownloadManager:
    def __init__(self, config: Dict):
        self.config = config
        self.download_dir = Path(config.get("download_dir"))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(config.get("concurrency", 3))
        self.user_agent = config.get("user_agent")
        self.retries = config.get("retries", 5)
        self.timeout = config.get("timeout_seconds", 30)

    async def _fetch_head(self, session: aiohttp.ClientSession, url: str) -> Dict:
        async with session.head(url, timeout=self.timeout) as resp:
            size = resp.headers.get("Content-Length")
            accept_ranges = resp.headers.get("Accept-Ranges", "")
            return {"size": int(size) if size else None, "accept_ranges": accept_ranges.lower() == "bytes"}

    async def _download_one(self, session: aiohttp.ClientSession, url: str, dest: Path, sha256: Optional[str], progress: Progress, task_id: TaskID):
        temp = dest.with_suffix(dest.suffix + ".part")
        existing = temp.stat().st_size if temp.exists() else 0

        headers = {"User-Agent": self.user_agent}
        total = None
        try:
            head = await self._fetch_head(session, url)
            total = head["size"]
            can_resume = head["accept_ranges"] and total is not None
        except Exception:
            can_resume = False
            total = None

        # If final file exists and size matches, skip
        if dest.exists() and total and dest.stat().st_size == total:
            progress.update(task_id, completed=total)
            console.log(f"Skipping, already downloaded: {dest.name}")
            return True

        # open stream request with Range if resuming
        range_header = {}
        if can_resume and existing:
            range_header["Range"] = f"bytes={existing}-"

        attempt = 0
        backoff = 1.0
        while attempt <= self.retries:
            try:
                async with session.get(url, headers={**headers, **range_header}, timeout=self.timeout) as resp:
                    resp.raise_for_status()
                    mode = "ab" if existing and resp.status == 206 else "wb"
                    # determine total for progress
                    content_length = resp.headers.get("Content-Length")
                    if content_length:
                        remaining = int(content_length)
                        expected_total = (existing + remaining) if mode == "ab" else remaining
                    else:
                        expected_total = total
                    if expected_total:
                        progress.update(task_id, total=expected_total)
                    # write to temp file
                    async with aiofiles.open(temp, mode) as f:
                        async for chunk in resp.content.iter_chunked(64 * 1024):
                            await f.write(chunk)
                            progress.advance(task_id, advance=len(chunk))
                    # rename to final
                    temp.replace(dest)
                    # verify checksum if provided
                    if sha256:
                        if not self._verify_sha256(dest, sha256):
                            console.log(f"[red]SHA256 mismatch for {dest.name}[/red]")
                            return False
                    return True
            except Exception as e:
                attempt += 1
                console.log(f"Download error ({attempt}/{self.retries}) for {url}: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                # next attempt should try without range header if server didn't support resume
                range_header = {}
        console.log(f"[red]Failed to download {url} after {self.retries} retries[/red]")
        return False

    def _verify_sha256(self, path: Path, expected: str) -> bool:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(64 * 1024), b""):
                h.update(chunk)
        return h.hexdigest().lower() == expected.lower()

    async def _download_task(self, session: aiohttp.ClientSession, entry: Dict, progress: Progress, task_id: TaskID):
        url = entry["url"]
        fname = entry.get("file_name") or os.path.basename(url.split("?")[0]) or f"{entry['id']}"
        dest = self.download_dir / fname
        async with self.semaphore:
            return await self._download_one(session, url, dest, entry.get("sha256"), progress, task_id)

    async def download_entries(self, entries: List[Dict]):
        timeout = aiohttp.ClientTimeout(total=None)
        connector = aiohttp.TCPConnector(limit_per_host=self.config.get("concurrency",3))
        headers = {"User-Agent": self.user_agent}
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                tasks = []
                for e in entries:
                    tid = progress.add_task(f"Downloading {e['title']}", total=None)
                    tasks.append(self._download_task(session, e, progress, tid))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success = sum(1 for r in results if r is True)
                console.print(f"Completed: {success}/{len(entries)}")
