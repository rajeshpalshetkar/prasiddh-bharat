# Blogger Page Publishing Queue\n\nCreate one JSON file per page in this folder. Required fields: `title`, `content`. Optional: `custom_url`. Keep `status` as `queued`.\n\nRun GitHub Actions → Publish Blogger Pages, enter the JSON file path, and type `PUBLISH` to confirm public publishing. Published requests are moved to `pages/published/`.\n\nExample JSON structure:\n\n```json\n{
  "title": "छात्रवृत्ति एवं शिक्षा सहायता",
  "content": "<h1>छात्रवृत्ति एवं शिक्षा सहायता</h1><p>यहाँ अपना पूरा Blogger HTML content रखें।</p>",
  "custom_url": "scholarship-assistance",
  "status": "queued"
}\n```\n\nOnly run this workflow for reviewed HTML. It publishes immediately to the public Blogger site.