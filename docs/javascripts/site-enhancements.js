(() => {
  const configureExternalLinks = () => {
    document.querySelectorAll("a[href]").forEach((link) => {
      if (link.hasAttribute("data-same-tab")) return;
      let destination;
      try {
        destination = new URL(link.href, window.location.href);
      } catch {
        return;
      }
      if (!["http:", "https:"].includes(destination.protocol) || destination.origin === window.location.origin) return;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.classList.add("oamr-external-link");
      if (!link.title) link.title = "Opens in a new tab";
    });
  };

  if (typeof document$ !== "undefined") document$.subscribe(configureExternalLinks);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", configureExternalLinks);
  else configureExternalLinks();
})();
