"""
Zernio API Client for WooPlans.
Handles media uploads, Facebook Reels publishing, comment-to-DM automations,
inbox interaction, and analytics via Zernio API (v1).
"""
import mimetypes
import os
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests

# Ensure socket prioritizes IPv4 to avoid hanging on networks without IPv6 routes
try:
    _orig_getaddrinfo = socket.getaddrinfo
    def _getaddrinfo_v4(*args, **kwargs):
        res = _orig_getaddrinfo(*args, **kwargs)
        v4 = [r for r in res if r[0] == socket.AF_INET]
        return v4 if v4 else res
    socket.getaddrinfo = _getaddrinfo_v4
except Exception:
    pass

from wooplans.settings import (
    ZERNIO_ACCOUNT_ID,
    ZERNIO_API_KEY,
    ZERNIO_API_URL,
    ZERNIO_PROFILE_ID,
)



class ZernioClient:
    """Client for interacting with Zernio Omnichannel API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        profile_id: Optional[str] = None,
        account_id: Optional[str] = None,
    ):
        self.api_key = api_key or ZERNIO_API_KEY or os.environ.get("ZERNIO_API_KEY", "")
        self.api_url = (api_url or ZERNIO_API_URL or os.environ.get("ZERNIO_API_URL", "https://zernio.com/api/v1")).rstrip("/")
        self.profile_id = profile_id or ZERNIO_PROFILE_ID or os.environ.get("ZERNIO_PROFILE_ID", "")
        self.account_id = account_id or ZERNIO_ACCOUNT_ID or os.environ.get("ZERNIO_ACCOUNT_ID", "")

        if not self.api_key:
            raise ValueError("ZERNIO_API_KEY is not defined. Please set it in .env or pass it to ZernioClient.")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # Core Profiles & Accounts
    # -------------------------------------------------------------------------
    def get_profiles(self) -> List[Dict[str, Any]]:
        """List profiles under the current team/user."""
        url = f"{self.api_url}/profiles"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("profiles", [])

    def get_accounts(self) -> List[Dict[str, Any]]:
        """List connected accounts (e.g., Secrets D'ébène Studios Facebook Page)."""
        url = f"{self.api_url}/accounts"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("accounts", [])

    # -------------------------------------------------------------------------
    # Media Upload (Presigned S3 flow)
    # -------------------------------------------------------------------------
    def upload_media(self, file_path: Union[str, Path], content_type: Optional[str] = None) -> str:
        """
        Request a presigned URL, upload binary file, and return the permanent publicUrl.
        Supported formats: video/mp4, image/jpeg, image/png, etc.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {path}")

        if not content_type:
            mime, _ = mimetypes.guess_type(str(path))
            content_type = mime or ("video/mp4" if path.suffix.lower() in [".mp4", ".mov"] else "application/octet-stream")

        # 1. Request presigned URL
        presign_url = f"{self.api_url}/media/presign"
        payload = {
            "filename": path.name,
            "contentType": content_type,
        }
        res_presign = requests.post(presign_url, json=payload, headers=self.headers, timeout=30)
        res_presign.raise_for_status()
        data = res_presign.json()

        upload_url = data.get("uploadUrl")
        public_url = data.get("publicUrl")

        if not upload_url or not public_url:
            raise RuntimeError(f"Invalid response from media/presign: {data}")

        # 2. Upload file binary via PUT
        file_size = path.stat().st_size
        with open(path, "rb") as f:
            put_headers = {
                "Content-Type": content_type,
                "Content-Length": str(file_size),
            }
            res_upload = requests.put(upload_url, data=f, headers=put_headers, timeout=300)
            res_upload.raise_for_status()

        return public_url

    # -------------------------------------------------------------------------
    # Post & Reel Publishing
    # -------------------------------------------------------------------------
    def publish_reel(
        self,
        video_url: str,
        caption: str,
        title: Optional[str] = None,
        first_comment: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        publish_now: bool = True,
        scheduled_for: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish or schedule a Facebook 9:16 Reel on the connected Page.
        """
        acc_id = account_id or self.account_id
        if not acc_id:
            raise ValueError("No account_id specified for Reel publication.")

        platform_entry: Dict[str, Any] = {
            "platform": "facebook",
            "accountId": acc_id,
            "platformSpecificData": {
                "contentType": "reel",
            },
        }

        if title:
            platform_entry["platformSpecificData"]["title"] = title

        if first_comment:
            platform_entry["platformSpecificData"]["firstComment"] = first_comment

        media_item: Dict[str, Any] = {"type": "video", "url": video_url}
        if thumbnail_url:
            media_item["thumbnail"] = thumbnail_url
            media_item["thumbnailUrl"] = thumbnail_url

        body: Dict[str, Any] = {
            "content": caption,
            "mediaItems": [media_item],
            "platforms": [platform_entry],
        }

        if scheduled_for:
            body["scheduledFor"] = scheduled_for
        elif publish_now:
            body["publishNow"] = True

        url = f"{self.api_url}/posts"
        resp = requests.post(url, json=body, headers=self.headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def schedule_reel(
        self,
        video_url: str,
        caption: str,
        scheduled_for: str,
        timezone: Optional[str] = "Africa/Abidjan",
        title: Optional[str] = None,
        first_comment: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a Facebook 9:16 Reel for a future date/time.
        scheduled_for can be ISO 8601 (e.g. '2026-10-01T18:00:00' or with offset '2026-10-01T18:00:00+02:00').
        """
        acc_id = account_id or self.account_id
        if not acc_id:
            raise ValueError("No account_id specified for Reel publication.")

        platform_entry: Dict[str, Any] = {
            "platform": "facebook",
            "accountId": acc_id,
            "platformSpecificData": {
                "contentType": "reel",
            },
        }

        if title:
            platform_entry["platformSpecificData"]["title"] = title
        if first_comment:
            platform_entry["platformSpecificData"]["firstComment"] = first_comment

        media_item: Dict[str, Any] = {"type": "video", "url": video_url}
        if thumbnail_url:
            media_item["thumbnail"] = thumbnail_url
            media_item["thumbnailUrl"] = thumbnail_url

        body: Dict[str, Any] = {
            "content": caption,
            "mediaItems": [media_item],
            "platforms": [platform_entry],
            "scheduledFor": scheduled_for,
        }
        if timezone:
            body["timezone"] = timezone

        url = f"{self.api_url}/posts"
        resp = requests.post(url, json=body, headers=self.headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[Dict[str, str]]] = None,
        publish_now: bool = True,
        scheduled_for: Optional[str] = None,
        timezone: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish or schedule a standard feed post (text, image, or video).
        """
        acc_id = account_id or self.account_id
        if not acc_id:
            raise ValueError("No account_id specified for post publication.")

        body: Dict[str, Any] = {
            "content": content,
            "platforms": [
                {
                    "platform": "facebook",
                    "accountId": acc_id,
                }
            ],
        }

        if media_urls:
            body["mediaItems"] = media_urls

        if scheduled_for:
            body["scheduledFor"] = scheduled_for
            if timezone:
                body["timezone"] = timezone
        elif publish_now:
            body["publishNow"] = True

        url = f"{self.api_url}/posts"
        resp = requests.post(url, json=body, headers=self.headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def schedule_post(
        self,
        content: str,
        scheduled_for: str,
        timezone: Optional[str] = "Africa/Abidjan",
        media_urls: Optional[List[Dict[str, str]]] = None,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience method to schedule a standard feed post."""
        return self.publish_post(
            content=content,
            media_urls=media_urls,
            publish_now=False,
            scheduled_for=scheduled_for,
            timezone=timezone,
            account_id=account_id,
        )

    def list_posts(
        self,
        status: Optional[str] = None,
        limit: int = 10,
        page: int = 1,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List posts (filter by status: 'scheduled', 'published', 'draft', etc.)."""
        params: Dict[str, Any] = {"limit": limit, "page": page}
        acc_id = account_id or self.account_id
        if acc_id:
            params["accountId"] = acc_id
        if status:
            params["status"] = status

        url = f"{self.api_url}/posts"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def list_scheduled_posts(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all upcoming scheduled posts."""
        data = self.list_posts(status="scheduled", limit=50, account_id=account_id)
        return data.get("posts", [])

    def reschedule_post(
        self,
        post_id: str,
        new_scheduled_for: str,
        timezone: Optional[str] = "Africa/Abidjan",
    ) -> Dict[str, Any]:
        """Change the scheduled time of a pending post."""
        url = f"{self.api_url}/posts/{post_id}"
        body: Dict[str, Any] = {
            "scheduledFor": new_scheduled_for,
            "isDraft": False,
        }
        if timezone:
            body["timezone"] = timezone
        resp = requests.put(url, json=body, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def cancel_scheduled_post(self, post_id: str) -> Dict[str, Any]:
        """Cancel and delete a scheduled post before it publishes."""
        url = f"{self.api_url}/posts/{post_id}"
        resp = requests.delete(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def unpublish_post(self, post_id: str, platform: str = "facebook") -> Dict[str, Any]:
        """Take down / delete a published post directly from Facebook."""
        url = f"{self.api_url}/posts/{post_id}/unpublish"
        resp = requests.post(url, json={"platform": platform}, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a post record from Zernio (works on cancelled, scheduled, draft)."""
        url = f"{self.api_url}/posts/{post_id}"
        resp = requests.delete(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # -------------------------------------------------------------------------
    # Comment-to-DM Automations (Funnel)
    # -------------------------------------------------------------------------
    def create_comment_automation(
        self,
        name: str,
        keywords: List[str],
        dm_message: str,
        comment_reply: Optional[str] = None,
        buttons: Optional[List[Dict[str, Any]]] = None,
        match_mode: str = "contains",
        also_match_in_dms: bool = True,
        account_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        platform_post_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Configure a keyword-triggered Comment-to-DM growth automation on Facebook.
        When someone comments a trigger keyword (e.g. 'GUIDE', 'SECRET', 'EPISODE'),
        they automatically receive a private DM and optional public comment reply.
        """
        acc_id = account_id or self.account_id
        prof_id = profile_id or self.profile_id

        if not acc_id or not prof_id:
            raise ValueError("account_id and profile_id are required for comment automations.")

        body: Dict[str, Any] = {
            "name": name,
            "accountId": acc_id,
            "profileId": prof_id,
            "trigger": "comment",
            "keywords": keywords,
            "matchMode": match_mode,
            "dmMessage": dm_message,
            "alsoMatchInDms": also_match_in_dms,
        }

        if comment_reply:
            body["commentReply"] = comment_reply

        if buttons:
            body["buttons"] = buttons

        if platform_post_id:
            body["platformPostId"] = platform_post_id

        url = f"{self.api_url}/comment-automations"
        resp = requests.post(url, json=body, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def list_comment_automations(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all active comment automations for the account."""
        acc_id = account_id or self.account_id
        params = {}
        if acc_id:
            params["accountId"] = acc_id

        url = f"{self.api_url}/comment-automations"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("automations", [])

    def delete_comment_automation(self, automation_id: str) -> Dict[str, Any]:
        """Delete a comment automation by ID."""
        url = f"{self.api_url}/comment-automations/{automation_id}"
        resp = requests.delete(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # -------------------------------------------------------------------------
    # Analytics & Insights
    # -------------------------------------------------------------------------
    def get_analytics(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch general analytics for the account."""
        acc_id = account_id or self.account_id
        params = {}
        if acc_id:
            params["accountId"] = acc_id

        url = f"{self.api_url}/analytics"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # -------------------------------------------------------------------------
    # Inbox Management
    # -------------------------------------------------------------------------
    def get_inbox_conversations(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch Messenger conversations in the inbox."""
        acc_id = account_id or self.account_id
        params = {}
        if acc_id:
            params["accountId"] = acc_id

        url = f"{self.api_url}/inbox/conversations"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_inbox_comments(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch comments across posts."""
        acc_id = account_id or self.account_id
        params = {}
        if acc_id:
            params["accountId"] = acc_id

        url = f"{self.api_url}/inbox/comments"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
