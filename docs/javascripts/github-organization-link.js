(() => {
  const organizationUrl = "https://github.com/openAMRobot";
  const metricsRepository = "openAMRobot/openamr-platform-sw";

  const configureSourceLink = () => {
    const source = document.querySelector("a.md-source");

    if (!source) return;

    source.href = organizationUrl;
    source.title = "Visit the OpenAMRobot GitHub organization";
    source.setAttribute("aria-label", "Visit the OpenAMRobot GitHub organization");

    const facts = source.querySelector(".md-source__facts");

    if (facts) {
      facts.title = `Stars and forks for the representative ${metricsRepository} repository`;
      facts.setAttribute(
        "aria-label",
        `Stars and forks for the representative ${metricsRepository} repository`
      );
    }
  };

  if (typeof document$ !== "undefined") {
    document$.subscribe(configureSourceLink);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", configureSourceLink);
  } else {
    configureSourceLink();
  }
})();
