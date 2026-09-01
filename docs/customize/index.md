---
title: Customize
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Mixed maturity</span><h1>Extend the platform through owned contracts</h1><p>Add devices, code, firmware, hardware, simulations or policies without duplicating another repository's responsibility.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Choose the owning layer

| Extension | Owning source | Start here |
| --- | --- | --- |
| ROS 2 behaviour and platform integration | `openamr-platform-sw` | [Software](software/index.md) |
| Embedded control and bridges | `openamr-platform-fw` | [Firmware](firmware/index.md) |
| Chassis, power and electronics | `openamr-platform-hw` | [Hardware](hardware/index.md) |
| Shared messages, services and actions | `openamrobot-interfaces` | [Working with interfaces](software/working-with-interfaces.md) |
| UI panels and Blockly blocks | `openamrobot-ui` | [Extending the UI](software/extending-the-ui.md) |
| Reusable arms and devices | `openamrobot-manipulation` | [Device packages](device-packages/index.md) |
| Worlds and scenario validation | Owning software repository | [Simulation](simulation/index.md) |
| Datasets and policies | Developing manipulation/AI layer | [AI and policies](ai/index.md) |

<div class="oamr-path"><span>Choose contract</span><b>→</b><span>Check maturity</span><b>→</b><span>Implement</span><b>→</b><span>Test</span><b>→</b><span>Document</span><b>→</b><span>Contribute</span></div>

The mobile simulation, navigation and docking stack is active but experimental. The shared manipulation framework and upper-body repositories are planned for the v0.2 cycle and simulation-first; their current contracts are design direction, not released implementation.

Use the [repository map](../reference/repositories.md) before changing a contract and follow the [contribution workflow](../community/contributing.md) for DCO, contributor agreement, review and testing requirements.
