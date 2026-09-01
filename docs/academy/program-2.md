# Program 2 · Build & Own

Program 2 takes a learner from parts and documentation to a checked platform they can maintain. It connects the open hardware, firmware and ROS 2 repositories through one reproducible build path.

| For | Starting point | Verified outcome |
| --- | --- | --- |
| Builders, technicians and makers | Basic workshop and electrical skills | Assemble, bring up, calibrate and document a working platform |

## Learning sequence

<div class="oamr-path"><span>Prepare</span><b>→</b><span>Source</span><b>→</b><span>Assemble</span><b>→</b><span>Bring up</span><b>→</b><span>Calibrate</span><b>→</b><span>Accept</span><b>→</b><span>Maintain</span></div>

The hardware design, BOM and manufacturing source live in `openamr-platform-hw`; embedded control lives in `openamr-platform-fw`; ROS 2 Jazzy integration lives in `openamr-platform-sw`. The current software stack is experimental: simulation, Nav2 and docking run end to end, while real-robot drivers and control remain in progress.

## Continue

- [Prepare to build](../build/prepare/index.md)
- [Assembly](../build/assembly/index.md)
- [Acceptance](../build/acceptance/index.md)
