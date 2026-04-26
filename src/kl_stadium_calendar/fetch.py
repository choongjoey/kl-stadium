from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from requests.utils import get_encoding_from_headers

from .models import FetchResult


@dataclass(frozen=True)
class Fetcher:
    timeout_seconds: int = 20
    user_agent: str = "kl-stadium-calendar/0.1 (+https://github.com/)"

    def get(self, url: str) -> FetchResult:
        response = requests.get(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "application/rss+xml;q=0.9,application/atom+xml;q=0.9,"
                "text/calendar;q=0.9,application/json;q=0.8,*/*;q=0.7",
                "User-Agent": self.user_agent,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        if get_encoding_from_headers(response.headers) is None:
            response.encoding = response.apparent_encoding
        return FetchResult(
            url=url,
            final_url=response.url,
            status_code=response.status_code,
            content_type=response.headers.get("content-type", ""),
            text=response.text,
            headers={key.lower(): value for key, value in response.headers.items()},
        )

    def post_json(self, url: str, payload: dict[str, Any]) -> FetchResult:
        response = requests.post(
            url,
            headers={
                "Accept": "application/json,text/plain;q=0.9,*/*;q=0.7",
                "Content-Type": "application/json",
                "User-Agent": self.user_agent,
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        if get_encoding_from_headers(response.headers) is None:
            response.encoding = response.apparent_encoding
        return FetchResult(
            url=url,
            final_url=response.url,
            status_code=response.status_code,
            content_type=response.headers.get("content-type", ""),
            text=response.text,
            headers={key.lower(): value for key, value in response.headers.items()},
        )
