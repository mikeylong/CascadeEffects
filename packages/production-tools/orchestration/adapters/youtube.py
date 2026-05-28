from __future__ import annotations

import contextlib
import json
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class YouTubeAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class YouTubePublishResult:
    video_id: str
    video_url: str
    scheduled_for: str
    published_at: str
    raw_response: dict[str, Any]
    thumbnail_status: str = ""
    thumbnail_error: str = ""


@dataclass(frozen=True)
class YouTubeVideoStatus:
    video_id: str
    exists: bool
    video_url: str
    channel_id: str
    channel_title: str
    title: str
    privacy_status: str
    upload_status: str
    processing_status: str
    published_at: str
    raw_response: dict[str, Any]
    embeddable: bool = False


@dataclass(frozen=True)
class YouTubeDeleteResult:
    video_id: str
    deleted_at: str
    raw_response: dict[str, Any]


@dataclass(frozen=True)
class YouTubeTitleUpdateResult:
    video_id: str
    video_url: str
    old_title: str
    new_title: str
    raw_response: dict[str, Any]
    updated_at: str


@dataclass(frozen=True)
class YouTubeSnippetUpdateResult:
    video_id: str
    video_url: str
    old_title: str
    new_title: str
    old_description: str
    new_description: str
    raw_response: dict[str, Any]
    updated_at: str


class YouTubePublisher:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
    VIDEOS_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    THUMBNAILS_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
    USER_AGENT = "CascadeEffectsPublish/1.0"

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        channel_id: str,
        opener: Any = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.channel_id = channel_id
        self._opener = opener or urllib_request.urlopen

    def _open(self, request: urllib_request.Request) -> Any:
        try:
            return self._opener(request)
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            with contextlib.suppress(Exception):
                exc.close()
            raise YouTubeAPIError(f"YouTube API request failed: {exc.code} {details}") from exc
        except urllib_error.URLError as exc:
            raise YouTubeAPIError(f"YouTube API connection failed: {exc}") from exc

    def _json_request(
        self,
        *,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], Any]:
        body = None
        merged_headers = {"User-Agent": self.USER_AGENT}
        if headers:
            merged_headers.update(headers)
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            merged_headers.setdefault("Content-Type", "application/json; charset=utf-8")
        request = urllib_request.Request(url, data=body, headers=merged_headers, method=method)
        with self._open(request) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return (json.loads(raw) if raw else {}, response)

    def _binary_request(
        self,
        *,
        url: str,
        method: str,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, Any], Any]:
        request = urllib_request.Request(url, data=body, headers=headers, method=method)
        with self._open(request) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return (json.loads(raw) if raw else {}, response)

    def refresh_access_token(self) -> str:
        body = urllib_parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        request = urllib_request.Request(
            self.TOKEN_URL,
            data=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self.USER_AGENT,
            },
            method="POST",
        )
        with self._open(request) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
        token = str(payload.get("access_token", "")).strip()
        if not token:
            raise YouTubeAPIError("YouTube OAuth refresh did not return an access token.")
        return token

    def validate_credentials(self) -> dict[str, Any]:
        token = self.refresh_access_token()
        params = urllib_parse.urlencode({"part": "id", "id": self.channel_id})
        payload, _ = self._json_request(
            url=f"{self.CHANNELS_URL}?{params}",
            headers={"Authorization": f"Bearer {token}"},
        )
        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            raise YouTubeAPIError(f"YouTube channel `{self.channel_id}` is not accessible with the supplied credentials.")
        return {"channel_id": self.channel_id, "validated_at": _utc_now_iso()}

    def get_authenticated_channel(self) -> dict[str, Any]:
        token = self.refresh_access_token()
        params = urllib_parse.urlencode({"part": "id,snippet", "mine": "true"})
        payload, _ = self._json_request(
            url=f"{self.CHANNELS_URL}?{params}",
            headers={"Authorization": f"Bearer {token}"},
        )
        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            raise YouTubeAPIError("YouTube credentials did not return an authenticated channel.")
        item = items[0] if isinstance(items[0], dict) else {}
        snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}
        channel_id = str(item.get("id", "")).strip()
        if not channel_id:
            raise YouTubeAPIError("YouTube authenticated channel response did not include a channel id.")
        return {
            "channel_id": channel_id,
            "title": str(snippet.get("title", "")).strip(),
            "custom_url": str(snippet.get("customUrl", "")).strip(),
            "raw_response": payload,
        }

    def get_video_status(self, video_id: str) -> YouTubeVideoStatus:
        normalized_video_id = str(video_id or "").strip()
        if not normalized_video_id:
            raise YouTubeAPIError("YouTube status lookup requires a video id.")
        token = self.refresh_access_token()
        params = urllib_parse.urlencode(
            {
                "part": "id,snippet,status,processingDetails",
                "id": normalized_video_id,
            }
        )
        payload, _ = self._json_request(
            url=f"{self.VIDEOS_URL}?{params}",
            headers={"Authorization": f"Bearer {token}"},
        )
        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            return YouTubeVideoStatus(
                video_id=normalized_video_id,
                exists=False,
                video_url=f"https://www.youtube.com/watch?v={normalized_video_id}",
                channel_id="",
                channel_title="",
                title="",
                privacy_status="",
                upload_status="",
                processing_status="",
                published_at="",
                raw_response=payload,
            )
        item = items[0] if isinstance(items[0], dict) else {}
        snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}
        status = item.get("status", {}) if isinstance(item.get("status"), dict) else {}
        processing = item.get("processingDetails", {}) if isinstance(item.get("processingDetails"), dict) else {}
        return YouTubeVideoStatus(
            video_id=normalized_video_id,
            exists=True,
            video_url=f"https://www.youtube.com/watch?v={normalized_video_id}",
            channel_id=str(snippet.get("channelId", "")).strip(),
            channel_title=str(snippet.get("channelTitle", "")).strip(),
            title=str(snippet.get("title", "")).strip(),
            privacy_status=str(status.get("privacyStatus", "")).strip(),
            upload_status=str(status.get("uploadStatus", "")).strip(),
            processing_status=str(processing.get("processingStatus", "")).strip(),
            published_at=str(snippet.get("publishedAt", "")).strip(),
            raw_response=payload,
            embeddable=bool(status.get("embeddable", False)),
        )

    def delete_video(self, video_id: str) -> YouTubeDeleteResult:
        normalized_video_id = str(video_id or "").strip()
        if not normalized_video_id:
            raise YouTubeAPIError("YouTube delete requires a video id.")
        token = self.refresh_access_token()
        params = urllib_parse.urlencode({"id": normalized_video_id})
        payload, _ = self._json_request(
            url=f"{self.VIDEOS_URL}?{params}",
            method="DELETE",
            headers={"Authorization": f"Bearer {token}"},
        )
        return YouTubeDeleteResult(
            video_id=normalized_video_id,
            deleted_at=_utc_now_iso(),
            raw_response=payload,
        )

    @staticmethod
    def _snippet_update_payload(
        existing: dict[str, Any],
        *,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        category_id = str(existing.get("categoryId", "")).strip()
        if not category_id:
            raise YouTubeAPIError("YouTube video snippet is missing categoryId; refusing partial snippet update.")
        snippet: dict[str, Any] = {
            "title": str(title if title is not None else existing.get("title", "")).strip(),
            "description": str(description if description is not None else existing.get("description", "")),
            "categoryId": category_id,
        }
        next_tags: Any = tags if tags is not None else existing.get("tags")
        if isinstance(next_tags, list):
            snippet["tags"] = [str(tag) for tag in next_tags]
        for key in ("defaultLanguage", "defaultAudioLanguage"):
            value = str(existing.get(key, "")).strip()
            if value:
                snippet[key] = value
        return snippet

    @staticmethod
    def _title_update_snippet(existing: dict[str, Any], new_title: str) -> dict[str, Any]:
        return YouTubePublisher._snippet_update_payload(existing, title=new_title)

    def update_video_title(self, video_id: str, title: str) -> YouTubeTitleUpdateResult:
        normalized_video_id = str(video_id or "").strip()
        new_title = str(title or "").strip()
        if not normalized_video_id:
            raise YouTubeAPIError("YouTube title update requires a video id.")
        if not new_title:
            raise YouTubeAPIError("YouTube title update requires a non-empty title.")
        token = self.refresh_access_token()
        list_params = urllib_parse.urlencode({"part": "id,snippet", "id": normalized_video_id})
        current_payload, _ = self._json_request(
            url=f"{self.VIDEOS_URL}?{list_params}",
            headers={"Authorization": f"Bearer {token}"},
        )
        items = current_payload.get("items", [])
        if not isinstance(items, list) or not items:
            raise YouTubeAPIError(f"YouTube video `{normalized_video_id}` was not found.")
        item = items[0] if isinstance(items[0], dict) else {}
        existing_snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}
        old_title = str(existing_snippet.get("title", "")).strip()
        update_payload = {
            "id": normalized_video_id,
            "snippet": self._title_update_snippet(existing_snippet, new_title),
        }
        update_params = urllib_parse.urlencode({"part": "snippet"})
        response_payload, _ = self._json_request(
            url=f"{self.VIDEOS_URL}?{update_params}",
            method="PUT",
            headers={"Authorization": f"Bearer {token}"},
            payload=update_payload,
        )
        return YouTubeTitleUpdateResult(
            video_id=normalized_video_id,
            video_url=f"https://www.youtube.com/watch?v={normalized_video_id}",
            old_title=old_title,
            new_title=new_title,
            raw_response=response_payload,
            updated_at=_utc_now_iso(),
        )

    def update_video_snippet(
        self,
        video_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> YouTubeSnippetUpdateResult:
        normalized_video_id = str(video_id or "").strip()
        if not normalized_video_id:
            raise YouTubeAPIError("YouTube snippet update requires a video id.")
        token = self.refresh_access_token()
        list_params = urllib_parse.urlencode({"part": "id,snippet", "id": normalized_video_id})
        current_payload, _ = self._json_request(
            url=f"{self.VIDEOS_URL}?{list_params}",
            headers={"Authorization": f"Bearer {token}"},
        )
        items = current_payload.get("items", [])
        if not isinstance(items, list) or not items:
            raise YouTubeAPIError(f"YouTube video `{normalized_video_id}` was not found.")
        item = items[0] if isinstance(items[0], dict) else {}
        existing_snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}
        old_title = str(existing_snippet.get("title", "")).strip()
        old_description = str(existing_snippet.get("description", ""))
        update_payload = {
            "id": normalized_video_id,
            "snippet": self._snippet_update_payload(existing_snippet, title=title, description=description, tags=tags),
        }
        update_params = urllib_parse.urlencode({"part": "snippet"})
        response_payload, _ = self._json_request(
            url=f"{self.VIDEOS_URL}?{update_params}",
            method="PUT",
            headers={"Authorization": f"Bearer {token}"},
            payload=update_payload,
        )
        response_snippet = response_payload.get("snippet", {}) if isinstance(response_payload.get("snippet"), dict) else {}
        return YouTubeSnippetUpdateResult(
            video_id=normalized_video_id,
            video_url=f"https://www.youtube.com/watch?v={normalized_video_id}",
            old_title=old_title,
            new_title=str(response_snippet.get("title", title if title is not None else old_title)).strip(),
            old_description=old_description,
            new_description=str(response_snippet.get("description", description if description is not None else old_description)),
            raw_response=response_payload,
            updated_at=_utc_now_iso(),
        )

    @staticmethod
    def _status_payload(*, privacy: str, scheduled_for: str) -> dict[str, Any]:
        if scheduled_for:
            return {"privacyStatus": "private", "publishAt": scheduled_for, "embeddable": True}
        return {"privacyStatus": privacy, "embeddable": True}

    def publish_video(self, payload: dict[str, Any]) -> YouTubePublishResult:
        token = self.refresh_access_token()
        video_path = str(payload.get("video_path", "")).strip()
        if not video_path:
            raise YouTubeAPIError("YouTube publish payload is missing video_path.")
        with open(video_path, "rb") as handle:
            video_bytes = handle.read()
        content_type = mimetypes.guess_type(video_path)[0] or "video/mp4"
        snippet = {
            "title": str(payload.get("title", "")).strip(),
            "description": str(payload.get("description_text", "")).strip(),
            "tags": payload.get("tags", []),
        }
        category_id = str(payload.get("category_id", payload.get("categoryId", ""))).strip()
        if category_id:
            snippet["categoryId"] = category_id
        for source_key, youtube_key in (
            ("default_language", "defaultLanguage"),
            ("default_audio_language", "defaultAudioLanguage"),
        ):
            value = str(payload.get(source_key, "")).strip()
            if value:
                snippet[youtube_key] = value
        status = self._status_payload(
            privacy=str(payload.get("privacy", "public")).strip() or "public",
            scheduled_for=str(payload.get("scheduled_for", "")).strip(),
        )
        if "embeddable" in payload:
            status["embeddable"] = bool(payload.get("embeddable"))
        if "self_declared_made_for_kids" in payload:
            status["selfDeclaredMadeForKids"] = bool(payload.get("self_declared_made_for_kids"))
        metadata = {"snippet": snippet, "status": status}
        params_payload = {"uploadType": "resumable", "part": "snippet,status"}
        if payload.get("notify_subscribers") is False:
            params_payload["notifySubscribers"] = "false"
        params = urllib_parse.urlencode(params_payload)
        _, response = self._json_request(
            url=f"{self.VIDEOS_UPLOAD_URL}?{params}",
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Upload-Content-Length": str(len(video_bytes)),
                "X-Upload-Content-Type": content_type,
            },
            payload=metadata,
        )
        upload_url = response.headers.get("Location") or response.headers.get("location")
        if not upload_url:
            raise YouTubeAPIError("YouTube resumable upload did not return a Location header.")
        upload_response, _ = self._binary_request(
            url=upload_url,
            method="PUT",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": content_type,
                "Content-Length": str(len(video_bytes)),
                "User-Agent": self.USER_AGENT,
            },
            body=video_bytes,
        )
        video_id = str(upload_response.get("id", "")).strip()
        if not video_id:
            raise YouTubeAPIError("YouTube upload response did not include a video id.")
        thumbnail_path = str(payload.get("thumbnail_path", "")).strip()
        thumbnail_status = "not_declared"
        thumbnail_error = ""
        if thumbnail_path:
            thumbnail_status = "attempted"
            try:
                with open(thumbnail_path, "rb") as handle:
                    thumbnail_bytes = handle.read()
                thumbnail_type = mimetypes.guess_type(thumbnail_path)[0] or "image/png"
                thumbnail_params = urllib_parse.urlencode({"uploadType": "media", "videoId": video_id})
                self._binary_request(
                    url=f"{self.THUMBNAILS_UPLOAD_URL}?{thumbnail_params}",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": thumbnail_type,
                        "Content-Length": str(len(thumbnail_bytes)),
                        "User-Agent": self.USER_AGENT,
                    },
                    body=thumbnail_bytes,
                )
                thumbnail_status = "uploaded"
            except YouTubeAPIError as exc:
                if payload.get("ignore_thumbnail_errors") is True:
                    thumbnail_status = "failed_nonfatal"
                    thumbnail_error = str(exc)
                else:
                    raise
        scheduled_for = str(payload.get("scheduled_for", "")).strip()
        published_at = (
            str(upload_response.get("snippet", {}).get("publishedAt", "")).strip()
            or ("" if scheduled_for else _utc_now_iso())
        )
        return YouTubePublishResult(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            scheduled_for=scheduled_for,
            published_at=published_at,
            raw_response=upload_response,
            thumbnail_status=thumbnail_status,
            thumbnail_error=thumbnail_error,
        )
