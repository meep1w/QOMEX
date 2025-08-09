document.addEventListener("DOMContentLoaded", () => {
  const lang = localStorage.getItem("language") || "ru";
  const all = document.querySelectorAll("[data-i18n]");

  all.forEach(el => {
    const key = el.dataset.i18n;
    const tr = window.translations?.[lang]?.[key];
    if (tr) el.innerHTML = tr;
  });
});
