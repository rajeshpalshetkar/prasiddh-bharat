import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "pages" / "queue"
ARCHIVE = ROOT / "pages" / "published"
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
    if not creds.valid:
        raise RuntimeError("Blogger credentials are invalid or expired. Refresh the OAuth token and update the GitHub secret.")
    return creds


def selected_file():
    requested = os.environ.get("PAGE_FILE", "").strip()
    if not requested:
        raise RuntimeError("PAGE_FILE is required.")
    path = (ROOT / requested).resolve()
    if not path.is_relative_to(QUEUE.resolve()):
        raise RuntimeError("PAGE_FILE must be inside pages/queue/.")
    if path.suffix.lower() != ".json" or not path.is_file():
        raise FileNotFoundError(f"Page JSON file not found: {requested}")
    return path


def main():
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    if not blog_id:
        raise RuntimeError("Missing BLOGGER_BLOG_ID GitHub Actions secret.")

    path = selected_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    if not title or not content:
        raise ValueError("Page JSON must contain non-empty 'title' and 'content'.")
    if payload.get("status", "queued") != "queued":
        raise RuntimeError("Only pages with status='queued' can be published.")

    body = {
        "kind": "blogger#page",
        "title": title,
        "content": content,
    }
    if payload.get("custom_url"):
        body["customUrl"] = payload["custom_url"]
    if payload.get("labels"):
        print("Note: Blogger Pages do not support post labels; ignoring labels.")

    service = build("blogger", "v3", credentials=load_credentials(), cache_discovery=False)
    result = service.pages().insert(
        blogId=blog_id,
        body=body,
        isDraft=False
    ).execute()

    payload["status"] = "published"
    payload["blogger_page_id"] = result.get("id")
    payload["blogger_url"] = result.get("url")
    payload["published_at"] = datetime.now(timezone.utc).isoformat()

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE / path.name
    archive_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    path.unlink()

    print(f"Published Blogger Page: {title}")
    print(f"Page URL: {result.get('url')}")
    print(f"Page ID: {result.get('id')}")


if __name__ == "__main__":
    main()
