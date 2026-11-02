# Blogger Draft Queue

ChatGPT-created standalone articles can be saved here as JSON files. The manual GitHub Actions workflow sends queued articles to Blogger with `isDraft=true`. It never publishes them live.

Example JSON:

```json
{
  "title": "लेख का शीर्षक",
  "content": "<p>लेख का HTML...</p>",
  "labels": ["समाचार", "विशेष लेख"],
  "status": "queued"
}
```

After successful Blogger draft creation, the JSON file is moved to `drafts/submitted/` with the Blogger post ID.

Never put OAuth tokens or client secrets in this folder.
