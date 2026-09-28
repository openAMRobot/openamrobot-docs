/* Collapsible table of contents (right sidebar).
   Adds a small arrow button to the "Table of contents" sidebar. Pressing it
   slides the sidebar out to the right and widens the content; a tab on the
   right edge brings it back. The choice is remembered per browser. */
(() => {
  const KEY = "oamr-toc-collapsed";
  const isCollapsed = () => {
    try { return localStorage.getItem(KEY) === "1"; } catch { return false; }
  };
  const remember = (value) => {
    try { localStorage.setItem(KEY, value ? "1" : "0"); } catch { /* storage unavailable */ }
  };

  const apply = (collapsed) => {
    document.documentElement.classList.toggle("oamr-toc-collapsed", collapsed);
    document.querySelectorAll(".oamr-toc-toggle").forEach((button) => {
      button.setAttribute("aria-expanded", collapsed ? "false" : "true");
      button.setAttribute("aria-label", collapsed ? "Show table of contents" : "Hide table of contents");
      button.title = collapsed ? "Show table of contents" : "Hide table of contents";
    });
  };

  const setup = () => {
    const sidebar = document.querySelector(".md-sidebar--secondary");
    if (!sidebar) return;
    const scrollwrap = sidebar.querySelector(".md-sidebar__scrollwrap");
    if (!scrollwrap || scrollwrap.querySelector(".oamr-toc-toggle")) return;

    const hide = document.createElement("button");
    hide.type = "button";
    hide.className = "oamr-toc-toggle oamr-toc-toggle--hide";
    hide.innerHTML = '<span aria-hidden="true">&#8250;</span>';
    hide.addEventListener("click", () => { remember(true); apply(true); });
    scrollwrap.prepend(hide);

    let show = document.querySelector(".oamr-toc-toggle--show");
    if (!show) {
      show = document.createElement("button");
      show.type = "button";
      show.className = "oamr-toc-toggle oamr-toc-toggle--show";
      show.innerHTML = '<span aria-hidden="true">&#8249;</span><span class="oamr-toc-toggle__label">Contents</span>';
      show.addEventListener("click", () => { remember(false); apply(false); });
      document.body.appendChild(show);
    }
    apply(isCollapsed());
  };

  if (typeof document$ !== "undefined") document$.subscribe(setup);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", setup);
  else setup();
})();
