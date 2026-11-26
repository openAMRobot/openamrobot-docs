---
title: Manifest reference
description: The files, validation stages and source drivers of the OpenAMRobot manifest repository.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Active</span><h1>Manifest reference</h1><p>Where each manifest fact is recorded, what the checks report and which drivers are included.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Readers who need to find a manifest file, a check or a driver pin.

**Applies to:** [`openamrobot-manifest`](https://github.com/openAMRobot/openamrobot-manifest), checked against `main` at `5b782ac` on 22 November 2026. The repository is authoritative. Pinned commits are not copied here because they change.

## Repository files

| File or directory | Purpose |
| --- | --- |
| `openamrobot.repos` | The development manifest. It may track branches. |
| `releases/v2.0.0-rc.1.repos` | The pinned rc.1 candidate snapshot, with full commit SHAs. |
| `tools/check_manifest.py` | Validates a manifest in separate stages. |
| `tools/check_release_manifest.py` | Checks a release snapshot against the development manifest or an exact export. |
| `tools/verify_jazzy_drivers.sh` | Imports a manifest and builds the two source drivers in a new workspace. |
| `ci/ros2-image.txt` | The candidate ROS 2 Jazzy CI image, pinned by its immutable OCI digest. |
| `tests/` | Unit tests for the checkers. |
| `STATE.md` | The working state of the repository, for maintainers. |

## What `check_manifest.py` reports

It reports three stages separately:

| Stage | What it checks |
| --- | --- |
| `yamllint` | Syntax and duplicate keys. |
| `strict` | A duplicate-key-rejecting loader and the manifest structure. |
| `remote` | Branches and tags with `vcs validate`, and full SHAs with an exact Git fetch and commit verification. Needs network. `--offline` reports this stage as SKIPPED. |

None of these stages imports a workspace, discovers packages or builds. Run `vcs import`, `colcon list` and `colcon build` for that. SKIPPED is not a pass.

The strict release checker rejects branches, tags and abbreviated hashes. The README notes that the full-SHA check avoids a `vcstool` 0.3.0 bug with advertised commit hashes, tracked in the repository as issue #12.

## Source drivers

Both manifests include two source-only drivers. Importing them from source replaces trying to install the driver itself with apt or a rosdep rule. `rosdep` still installs their declared dependencies.

| Package | Checkout path | Upstream | What the README says it does |
| --- | --- | --- | --- |
| `sllidar_ros2` | `src/sllidar_ros2` | [SLAMTEC](https://github.com/Slamtec/sllidar_ros2) | Drives the 2.0 navigation LiDAR, a SLAMTEC RPLIDAR S3 (S3M1-R2), over USB through a USB to UART adapter at 1,000,000 baud, and publishes `/scan` in `lidar_link`. |
| `micro_ros_agent` | `src/micro_ros_agent` | [micro-ROS Jazzy](https://github.com/micro-ROS/micro-ROS-Agent/tree/jazzy) | Connects the base controller. micro-ROS runs over UDP on Ethernet between the microcontroller and the Jetson. USB is for the bench only. |

The pinned commits are in the manifests. The SLAMTEC package declares a BSD licence and the micro-ROS agent is Apache-2.0. Keep their original licence files and notices.

## Limits

- A manifest checkout does not show that a build passes, that robot hardware works or that a release is accepted.
- The duplicate `openamr_ui_msgs` package (OA-08) and the UI dependency declarations are separate open issues.
- A source pin is not a hermetic build. The micro-ROS superbuild downloads further dependencies while it compiles.

## See also

[Concepts](concepts.md), [Check out and validate](setup.md), and [release concepts](../openamrobot-release/concepts.md).
