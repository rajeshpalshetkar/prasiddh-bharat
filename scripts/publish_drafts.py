import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "drafts" / "queue"
ARCHIVE = ROOT / "drafts" / "submitted"
SCOPES = ["https://www.googleapis.com/auth/blogger"]


def load_credentials():
    raw = os.environ.get("BLOGGER_TOKEN_JSON")
    if not raw:
        raise RuntimeError("Missing BLOGGER_TOKEN_JSON GitHub Actions secret.")
    info = json.loads(raw)
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds.valid and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    return creds


def main():
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    if not blog_id:
        raise RuntimeError("Missing BLOGGER_BLOG_ID secret.")
    requested = os.environ.get("DRAFT_FILE", "").strip()

    files = [ROOT / requested] if requested else sorted(QUEUE.glob("*.json"))
    ready = []
    for path in files:
        if not path.exists():
            raise FileNotFoundError(f"Draft file not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status", "queued") == "queued":
            ready.append((path, payload))

    if not ready:
        print("No queued drafts found.")
        return

    service = build("blogger", "v3", credentials=load_credentials(), cache_discovery=False)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    for path, payload in ready:
        title = (payload.get("title") or "").strip()
        content = (payload.get("content") or "").strip()
        if not title or not content:
            raise ValueError(f"Draft must include non-empty title and content: {path}")

        body = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "labels": payload.get("labels", ["Prasiddh Bharat"]),
        }
        result = service.posts().insert(
            blogId=blog_id,
            body=body,
            isDraft=True
        ).execute()

        payload["status"] = "submitted_as_draft"
        payload["blogger_post_id"] = result.get("id")
        payload["blogger_url"] = result.get("url")
        payload["submitted_at"] = datetime.now(timezone.utc).isoformat()

        archive_path = ARCHIVE / path.name
        archive_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        path.unlink()
        print(f"Saved Blogger Draft: {title} (ID: {result.get('id')})")


if __name__ == "__main__":
    main()
