(function () {
  "use strict";

  function field(id) {
    return document.getElementById(id);
  }

  function attachCounter(input, limit) {
    if (!input || input.dataset.seoCounter) return;
    const counter = document.createElement("small");
    counter.className = "editorial-seo-counter";
    input.insertAdjacentElement("afterend", counter);
    input.dataset.seoCounter = "true";
    function update() {
      const length = Array.from(input.value).length;
      counter.textContent = `${length} / ${limit}`;
      counter.classList.toggle("editorial-seo-counter--over", length > limit);
    }
    input.addEventListener("input", update);
    update();
  }

  function init() {
    const preview = document.querySelector(".editorial-seo-preview");
    if (!preview) return;
    const category = preview.dataset.seoKind === "category";
    const title = field(category ? "id_name" : "id_title");
    const summary = field("id_summary");
    const slug = field("id_slug");
    const seoTitle = field("id_seo_title");
    const seoDescription = field("id_seo_description");
    const canonical = field("id_seo_canonical_url");
    const titleText = preview.querySelector(".editorial-seo-preview__title");
    const descriptionText = preview.querySelector(".editorial-seo-preview__description");
    const urlText = preview.querySelector(".editorial-seo-preview__url");
    attachCounter(seoTitle, 60);
    attachCounter(seoDescription, 160);
    function update() {
      titleText.textContent = seoTitle?.value.trim() || title?.value.trim() || "عنوان صفحه";
      descriptionText.textContent =
        seoDescription?.value.trim() || summary?.value.trim() || "توضیح صفحه";
      const prefix = category ? "/editorial/category/" : "/editorial/";
      urlText.textContent =
        canonical?.value.trim() || `${preview.dataset.seoSite}${prefix}${slug?.value.trim() || ""}`;
    }
    [title, summary, slug, seoTitle, seoDescription, canonical].forEach((input) => {
      input?.addEventListener("input", update);
    });
    update();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
