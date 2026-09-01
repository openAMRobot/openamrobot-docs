---
title: openamrobot-release overview
description: Understand how OpenAMRobot releases package compatible software, firmware, hardware and documentation evidence.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Released · v0.0.1</span><h1>Frozen product-level source snapshot</h1><p>A versioned archive of the hardware, software, firmware, UI, interfaces, communication, documentation and governance repositories.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamrobot-release`](https://github.com/openAMRobot/openamrobot-release) exists because GitHub's automatic archive for one repository cannot represent the multi-repository platform.

| Verify before use | Purpose |
| --- | --- |
| `RELEASE_NOTES.md` | Included capability and release context |
| `KNOWN_LIMITATIONS.md` | Unsupported or incomplete behaviour |
| `VERSION` | Product-level version identity |
| `MANIFEST.json` | Participating repositories and source revisions |
| `checksums.sha256` | Archive integrity |

The current public snapshot is [`OpenAMRobot-v0.0.1-source.zip`](https://github.com/openAMRobot/openamrobot-release/releases/tag/v0.0.1). Live repositories may be newer; use the release archive when reproducibility matters.
