"""Bounded HTTP retries and request-addressed cache for preflight evidence."""
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)


class WeatherCache:
    def __init__(self, root, settings, offline=False):
        self.root = Path(root)
        self.settings = settings
        self.offline = offline

    def get(self, provider, endpoint, params):
        url = endpoint + "?" + urlencode(sorted(params.items()))
        key = hashlib.sha256(url.encode()).hexdigest()
        directory = self.root / provider
        path = directory / f"{key}.json"
        if path.exists():
            entry = json.loads(path.read_text(encoding="utf-8"))
            # Cache errors too, but allow a later invocation to retry transient failures.
            if self.offline or entry["status"] not in [0, 429, 500, 502, 503, 504]:
                LOG.info("Cache hit %s %s", provider, key)
                return entry
        if self.offline:
            raise FileNotFoundError(f"No cached response for {url}")
        directory.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, self.settings["max_attempts"] + 1):
            retry_after = None
            time.sleep(self.settings["interval_seconds"])
            request = Request(url, headers={"User-Agent": "HackAlemArchivePreflight/0.1"})
            try:
                with urlopen(request, timeout=self.settings["timeout_seconds"]) as response:
                    status = response.status
                    body = response.read().decode("utf-8")
                    headers = dict(response.headers)
            except HTTPError as exc:
                status = exc.code
                body = exc.read().decode("utf-8", errors="replace")
                headers = dict(exc.headers)
                retry_after = exc.headers.get("Retry-After")
            except (URLError, TimeoutError, OSError) as exc:
                status, body, headers = 0, str(exc), {}
            entry = {"url": url, "status": status, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                     "attempt": attempt, "headers": headers, "body": body, "cache_key": key}
            # Cache retrieval time is NEVER historical publication time.
            payload = json.dumps(entry, ensure_ascii=False, indent=2)
            temporary = directory / f"{key}.tmp"
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(path)
            (directory / f"{key}.attempt-{attempt}.json").write_text(payload, encoding="utf-8")
            LOG.info("HTTP %s provider=%s attempt=%s key=%s", status, provider, attempt, key)
            transient = status in [0, 429, 500, 502, 503, 504]
            if not transient or attempt == self.settings["max_attempts"]:
                return entry
            try:
                delay = float(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            if delay > self.settings["max_retry_wait_seconds"]:
                LOG.warning("Retry-After exceeds bounded wait; resume in a later invocation")
                return entry
            time.sleep(max(0, delay))
        raise RuntimeError("Invalid retry settings")
