from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class BuzzsproutAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class BuzzsproutPublishResult:
    external_id: str
    episode_url: str
    scheduled_for: str
    published_at: str
    raw_response: dict[str, Any]


class BuzzsproutPublisher:
    API_ROOT = "https://www.buzzsprout.com/api"
    USER_AGENT = "CascadeEffectsPublish/1.0 (+https://cascadeeffects.tv)"

    def __init__(
        self,
        *,
        api_token: str,
        podcast_id: str,
        opener: Any = None,
    ) -> None:
        self.api_token = api_token
        self.podcast_id = podcast_id
        self._opener = opener or urllib_request.urlopen

    @property
    def base_url(self) -> str:
        return f"{self.API_ROOT}/{self.podcast_id}"

    def _open(self, request: urllib_request.Request) -> Any:
        try:
            return self._opener(request)
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise BuzzsproutAPIError(f"Buzzsprout API request failed: {exc.code} {details}") from exc
        except urllib_error.URLError as exc:
            raise BuzzsproutAPIError(f"Buzzsprout API connection failed: {exc}") from exc

    def _headers(self, *, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Token token={self.api_token}",
            "User-Agent": self.USER_AGENT,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _json_request(
        self,
        *,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        body = None
        headers = self._headers(content_type="application/json; charset=utf-8" if payload is not None else None)
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = urllib_request.Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        with self._open(request) as response:
            raw = response.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw else {}

    @staticmethod
    def _multipart_body(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[str, bytes]:
        boundary = f"----CascadeEffects{uuid.uuid4().hex}"
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                    value.encode("utf-8"),
                    b"\r\n",
                ]
            )
        for field_name, file_path in files:
            filename = file_path.name
            content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    (
                        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                        f"Content-Type: {content_type}\r\n\r\n"
                    ).encode("utf-8"),
                    file_path.read_bytes(),
                    b"\r\n",
                ]
            )
        chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
        return (f"multipart/form-data; boundary={boundary}", b"".join(chunks))

    def validate_credentials(self) -> dict[str, Any]:
        payload = self._json_request(path="/episodes.json")
        if not isinstance(payload, list):
            raise BuzzsproutAPIError("Buzzsprout credentials are valid, but the response shape was unexpected.")
        return {"podcast_id": self.podcast_id, "validated_at": _utc_now_iso()}

    def publish_episode(self, payload: dict[str, Any]) -> BuzzsproutPublishResult:
        audio_path = Path(str(payload.get("audio_path", "")).strip())
        if not audio_path.exists():
            raise BuzzsproutAPIError(f"Buzzsprout audio path is missing: {audio_path}")
        fields = {
            "title": str(payload.get("title", "")).strip(),
            "description": str(payload.get("description_text", "")).strip(),
            "summary": str(payload.get("summary", "")).strip(),
            "artist": str(payload.get("artist", "Cascade Effects")).strip() or "Cascade Effects",
            "tags": str(payload.get("tags_csv", "")).strip(),
            "private": "false",
            "email_user_after_audio_processed": "false",
        }
        scheduled_for = str(payload.get("scheduled_for", "")).strip()
        if scheduled_for:
            fields["published_at"] = scheduled_for
        content_type, body = self._multipart_body(fields, [("audio_file", audio_path)])
        request = urllib_request.Request(
            f"{self.base_url}/episodes.json",
            data=body,
            headers=self._headers(content_type=content_type),
            method="POST",
        )
        with self._open(request) as response:
            raw = response.read().decode("utf-8", errors="replace")
        response_payload = json.loads(raw) if raw else {}
        external_id = str(response_payload.get("id", "")).strip()
        if not external_id:
            raise BuzzsproutAPIError("Buzzsprout create episode response did not include an id.")
        published_at = str(response_payload.get("published_at", "")).strip() or ("" if scheduled_for else _utc_now_iso())
        return BuzzsproutPublishResult(
            external_id=external_id,
            episode_url=f"https://www.buzzsprout.com/{self.podcast_id}/{external_id}",
            scheduled_for=scheduled_for,
            published_at=published_at,
            raw_response=response_payload,
        )
