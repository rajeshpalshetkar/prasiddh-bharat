(function () {
  "use strict";

  const root = document.querySelector("[data-pb-section]");
  if (!root) return;

  const dataUrl = root.dataset.dataUrl;
  const pageSize = Number(root.dataset.pageSize || 20);
  const list = root.querySelector("[data-pb-list]");
  const loadMore = root.querySelector("[data-pb-load-more]");
  const status = root.querySelector("[data-pb-status]");
  let items = [];
  let shown = 0;

  function safeText(value) {
    return String(value || "").replace(/[&<>"']/g, function (char) {
      return ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;",
        '"': "&quot;", "'": "&#39;"
      })[char];
    });
  }

  function renderNext() {
    const batch = items.slice(shown, shown + pageSize);
    batch.forEach(function (item) {
      const article = document.createElement("article");
      article.className = "pb-headline-item";

      const title = safeText(item.title);
      const source = safeText(item.source_name || "स्रोत");
      const date = safeText(item.published || item.collected_at || "");
      const url = String(item.url || "");

      const link = document.createElement("a");
      link.className = "pb-headline-link";
      link.textContent = item.title || "शीर्षक उपलब्ध नहीं";
      link.href = /^https:\/\//i.test(url) ? url : "#";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      article.appendChild(link);

      const meta = document.createElement("div");
      meta.className = "pb-headline-meta";
      meta.textContent = [source, date].filter(Boolean).join(" · ");
      article.appendChild(meta);
      list.appendChild(article);
    });

    shown += batch.length;
    loadMore.hidden = shown >= items.length;
    if (status) status.textContent = items.length
      ? "कुल " + items.length + " अपडेट उपलब्ध हैं।"
      : "अभी कोई अपडेट उपलब्ध नहीं है।";
  }

  async function init() {
    if (!dataUrl || !list) return;
    try {
      const response = await fetch(dataUrl, { cache: "no-store" });
      if (!response.ok) throw new Error("डेटा लोड नहीं हो सका (" + response.status + ")");
      const payload = await response.json();
      items = Array.isArray(payload.items) ? payload.items : [];
      items.sort(function (a, b) {
        return String(b.published || b.collected_at || "")
          .localeCompare(String(a.published || a.collected_at || ""));
      });
      renderNext();
    } catch (error) {
      if (status) status.textContent = "अपडेट लोड नहीं हो पाए। कृपया बाद में प्रयास करें।";
      console.error("Prasiddh Bharat section renderer:", error);
    }
  }

  if (loadMore) loadMore.addEventListener("click", renderNext);
  init();
})();