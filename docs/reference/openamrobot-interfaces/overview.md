---
title: openamrobot-interfaces overview
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Shared interface contracts</h1><p>One source for reusable ROS 2 messages, services, actions and cross-repository schemas.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamrobot-interfaces`](https://github.com/openAMRobot/openamrobot-interfaces) separates shared contracts from application logic so the platform software, UI, simulation and future integrations do not redefine the same interface.

| Belongs here | Belongs elsewhere |
| --- | --- |
| Shared ROS 2 messages, services and actions | Navigation, docking or application behaviour |
| Reusable JSON/YAML schemas | Hardware drivers and embedded implementation |
| Versioning and interoperability rules | UI components and presentation logic |
| Transport-independent contracts where practical | Middleware bridges and deployment configuration |

Consumers should depend on the shared package and treat incompatible contract changes as versioned migrations. Concrete behaviour remains in the repository that implements it.
