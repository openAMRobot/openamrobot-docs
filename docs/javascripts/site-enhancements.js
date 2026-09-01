(() => {
  const titleOverrides = {
    api: "API",
    ai: "AI",
    fw: "Firmware",
    hw: "Hardware",
    ros2: "ROS 2",
    tf: "TF",
    ui: "UI",
    urdf: "URDF",
    vla: "VLA",
  };

  const humanize = (value) =>
    value
      .split("-")
      .map((word) => titleOverrides[word.toLowerCase()] || word)
      .join(" ")
      .replace(/^./, (letter) => letter.toUpperCase());

  const configureExternalLinks = () => {
    document.querySelectorAll("a[href]").forEach((link) => {
      if (link.hasAttribute("data-same-tab")) return;

      let destination;
      try {
        destination = new URL(link.href, window.location.href);
      } catch {
        return;
      }

      if (
        !["http:", "https:"].includes(destination.protocol) ||
        destination.origin === window.location.origin
      ) {
        return;
      }

      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.classList.add("oamr-external-link");

      if (!link.title) link.title = "Opens in a new tab";
    });
  };

  const createBreadcrumbs = () => {
    const content = document.querySelector(".md-content__inner");
    if (!content) return;

    content.querySelector(".oamr-breadcrumbs")?.remove();

    const parts = window.location.pathname
      .replace(/^\/+|\/+$/g, "")
      .split("/")
      .filter(Boolean);

    if (!parts.length) return;

    const nav = document.createElement("nav");
    nav.className = "oamr-breadcrumbs";
    nav.setAttribute("aria-label", "Breadcrumb");

    const list = document.createElement("ol");
    const home = document.createElement("li");
    const homeLink = document.createElement("a");
    homeLink.href = `${window.location.origin}/`;
    homeLink.textContent = "Home";
    home.appendChild(homeLink);
    list.appendChild(home);

    let accumulated = "";
    const visibleParts = parts.slice(-2);
    const hiddenDepth = parts.length - visibleParts.length;

    visibleParts.forEach((part, index) => {
      const sourceIndex = index + hiddenDepth;
      accumulated = `/${parts.slice(0, sourceIndex + 1).join("/")}`;
      const item = document.createElement("li");
      const isLast = index === visibleParts.length - 1;
      const label = isLast
        ? document.querySelector("h1")?.textContent?.trim() || humanize(part)
        : humanize(part);

      if (isLast) {
        const current = document.createElement("span");
        current.textContent = label;
        current.setAttribute("aria-current", "page");
        item.appendChild(current);
      } else {
        const anchor = document.createElement("a");
        anchor.href = `${window.location.origin}${accumulated}/`;
        anchor.textContent = label;
        item.appendChild(anchor);
      }

      list.appendChild(item);
    });

    nav.appendChild(list);
    content.prepend(nav);
  };

  const addTrackLabels = () => {
    const content = document.querySelector(".md-content__inner");
    if (!content) return;

    content.querySelector(".oamr-track-labels")?.remove();

    const path = window.location.pathname;
    const rules = [
      [/^\/paths\/domain-expert\//, ["Domain Expert"]],
      [/^\/paths\/beginner\//, ["Beginner"]],
      [/^\/paths\/integrator\//, ["Integrator"]],
      [/^\/paths\/builder\//, ["Builder"]],
      [/^\/paths\/developer\//, ["Developer"]],
      [/^\/paths\/entrepreneur\//, ["Entrepreneur"]],
      [/^\/foundations\//, ["Beginner", "Builder"]],
      [/^\/build\//, ["Builder", "Integrator"]],
      [/^\/use\//, ["Domain Expert"]],
      [/^\/configure\//, ["Integrator"]],
      [/^\/customize\//, ["Developer", "Integrator"]],
      [/^\/maintain\//, ["Domain Expert", "Integrator"]],
      [/^\/reference\//, ["Developer", "Integrator"]],
      [/^\/solutions\//, ["Integrator", "Entrepreneur"]],
      [/^\/business\//, ["Entrepreneur"]],
      [/^\/academy\//, ["Domain Expert", "Beginner", "Builder", "Developer"]],
    ];

    const match = rules.find(([pattern]) => pattern.test(path));
    if (!match) return;

    const wrapper = document.createElement("div");
    wrapper.className = "oamr-track-labels";
    wrapper.setAttribute("aria-label", "Recommended paths");

    match[1].forEach((label) => {
      const chip = document.createElement("span");
      chip.textContent = label;
      wrapper.appendChild(chip);
    });

    const breadcrumbs = content.querySelector(".oamr-breadcrumbs");
    breadcrumbs?.insertAdjacentElement("afterend", wrapper);
  };

  const enhancePage = () => {
    configureExternalLinks();
    createBreadcrumbs();
    addTrackLabels();
  };

  if (typeof document$ !== "undefined") {
    document$.subscribe(enhancePage);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhancePage);
  } else {
    enhancePage();
  }
})();
