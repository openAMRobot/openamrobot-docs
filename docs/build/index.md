---
title: Build
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental build path</span><h1>Build a platform you can verify</h1><p>Move from workspace and parts to assembly, software, calibration and a recorded acceptance baseline.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Build sequence

<div class="oamr-path"><span>Prepare</span><b>→</b><span>Source</span><b>→</b><span>Assemble</span><b>→</b><span>Install</span><b>→</b><span>Bring up</span><b>→</b><span>Calibrate</span><b>→</b><span>Accept</span></div>

| Stage | Outcome | Start here |
| --- | --- | --- |
| Prepare | Safe workspace, tools, skills and realistic plan | [Before you start](prepare/index.md) |
| Source | BOM and revision-matched parts are available | [The kit](kit/index.md) |
| Assemble | Mechanics, electronics and wiring match the design source | [Assembly](assembly/index.md) |
| Install | Firmware and ROS 2 software are installed and identified | [Getting software onto the robot](software/index.md) |
| Bring up | Power, motors, sensors and first motion pass controlled checks | [Bring-up](bringup/index.md) |
| Calibrate | Odometry and sensor geometry have recorded baselines | [Calibration](calibration/index.md) |
| Accept | The configuration passes measurable acceptance tests | [Acceptance](acceptance/index.md) |

The canonical CAD, BOM and manufacturing source is in [`openamr-platform-hw`](https://github.com/openAMRobot/openamr-platform-hw). Embedded control belongs to [`openamr-platform-fw`](https://github.com/openAMRobot/openamr-platform-fw), and ROS 2 integration belongs to [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw).

!!! warning "Current maturity"
    The released source is suitable for study and development. Simulation, Nav2 and docking run end to end; real-robot drivers, control and hardware acceptance documentation remain in progress. Do not treat an unfinished page as a validated safety or manufacturing instruction.
