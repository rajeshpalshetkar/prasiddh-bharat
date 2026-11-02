import json, os
from pathlib import Path
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "pages" / "queue"

def main():
    requested = os.environ.get("PAGE_FILE", "").strip()
    path = (ROOT / requested).resolve()
    if not path.is_relative_to(QUEUE.resolve()) or path.suffix != ".json" or not path.is_file():
        raise RuntimeError("PAGE_FILE must point to an existing JSON file inside pages/queue/.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "queued" or not data.get("title") or not data.get("content"):
        raise RuntimeError("Queue JSON requires title, content and status=queued.")
    info = json.loads(os.environ["BLOGGER_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(info, ["https://www.googleapis.com/auth/blogger"])
    if not creds.valid and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    if not creds.valid:
        raise RuntimeError("Blogger OAuth token is invalid or expired.")
    service = build("blogger", "v3", credentials=creds, cache_discovery=False)
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    pages = service.pages().list(blogId=blog_id, fetchBodies=True, maxResults=500).execute().get("items", [])
    matches = [p for p in pages if p.get("title", "").strip() == data["title"].strip()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one existing Blogger page titled '{data['title']}', found {len(matches)}. No page changed.")
    page_id = matches[0]["id"]
    body = {"id": page_id, "title": data["title"], "content": data["content"]}
    result = service.pages().update(blogId=blog_id, pageId=page_id, body=body).execute()
    data.update({"status":"updated","blogger_page_id":page_id,"blogger_url":result.get("url"),"updated_at":datetime.now(timezone.utc).isoformat()})
    archive = ROOT / "pages" / "published"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "update-all-sections.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    path.unlink()
    print("Updated Blogger page:", result.get("title"))
    print("Page URL:", result.get("url"))

if __name__ == "__main__":
    main()
