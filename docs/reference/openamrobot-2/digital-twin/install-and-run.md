---
title: Install and run the digital twin
tags: [developer, integrator]
status: experimental
description: Install the OpenAMRobot 2.0 digital twin on Ubuntu 24.04 at pinned commits, run it headless or with a desktop, and check that it works.
---

# Install and run the digital twin

**For:** engineers who want the whole simulated robot running on their own computer.

**When you finish:** the workspace is built at pinned commits, the model tests pass, the robot runs headless with
every device on virtual CAN, and one driving scenario has passed. With a desktop you also see it in RViz.

**Canonical source:** the Build 1 scene README in
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw/blob/196dd3fe64900ba4a12124c9ee20e0cfaafa1651/ros2/src/openamrobot_build1_scene/README.md)
and the acceptance workflow
[`baseline1-acceptance.yml`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/196dd3fe64900ba4a12124c9ee20e0cfaafa1651/.github/workflows/baseline1-acceptance.yml).
The commands below take every pin from those files, so they build what the acceptance runs build.

!!! warning "Simulation, not hardware validation"
    A twin that runs on your computer is development evidence. It is never real-robot, electrical or safety evidence.

## How these commands are checked

Every block on this page marked **headless, checked in CI** is extracted from this page's source text and run, in
order, as one script by the `digital-twin-quickstart` workflow of openamrobot-docs. The job fails if any command
fails. Blocks marked **desktop** need a screen and are checked by hand with the
[desktop acceptance checklist](#desktop-acceptance-checklist).

## Requirements

| Item | Headless | Desktop |
|---|---|---|
| Operating system | Ubuntu 24.04 (noble), x86_64 | Ubuntu 24.04 with a graphical session |
| CPU and memory | 4 cores, 16 GB RAM | 8 cores, 16 GB RAM or more |
| Disk | about 15 GB for ROS 2, Gazebo and the workspace | the same |
| GPU | not needed | not needed for Gazebo and RViz; Isaac Sim needs an NVIDIA RTX GPU ([Simulators](simulators.md#isaac-sim)) |
| Rights | `sudo` for packages and the virtual CAN interfaces | the same |
| Kernel | the `vcan` module (package `linux-modules-extra-$(uname -r)`) | the same |

On a 4-core machine without a graphics card the whole stack runs at a real-time factor of about 0.25: one simulated
second takes about four seconds. The hosted CI runners reach 0.13 to 0.5.

## Pins

The twin runs from the integration branches, not from `main`. One commit names the whole set:

| Input | Where the pin comes from |
|---|---|
| openamr-upperbody-sw `integration/baseline1` | `UB_SHA` below |
| openamr-platform-sw `integration/baseline1` | `PLATFORM_SW_SHA` in `baseline1-acceptance.yml` at `UB_SHA` |
| openamrobot-interfaces | `INTERFACES_SHA` in the same workflow |
| enactic/openarm_description, openarm_ros2, openarm_can | `config/pins.yaml` of the Build 1 scene at `UB_SHA` |
| Gazebo vendor packages | `GZ_SIM_VENDOR`, `GZ_TOOLS_VENDOR`, `SDFORMAT_VENDOR` in the same workflow |

The final pins of the Digital Twin release candidate are listed in the release candidate report; see
[Evidence and limits](evidence-and-limits.md#release-and-versioning).

## Quick start (headless)

### 1. ROS 2 Jazzy and tools

**Headless, checked in CI.** Installs ROS 2 Jazzy from packages.ros.org through a pinned apt source release, as the
acceptance workflow does.

<!-- quickstart:headless -->
```bash
sudo apt-get update
sudo apt-get install -y curl git locales software-properties-common python3-yaml python3-can iproute2 can-utils
sudo add-apt-repository -y universe
curl --fail --location --retry 5 --retry-delay 5 -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.3.0/ros2-apt-source_1.3.0.noble_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt-get update
sudo apt-get install -y ros-jazzy-ros-base ros-dev-tools
sudo rosdep init || echo "rosdep is already initialised"
rosdep update --rosdistro jazzy
```

### 2. Workspace at the pinned commits

**Headless, checked in CI.** Fetches exactly one commit of each repository.

<!-- quickstart:headless -->
```bash
export TWIN_WS="$HOME/openamr_twin_ws"
export UB_SHA=196dd3fe64900ba4a12124c9ee20e0cfaafa1651
fetch_at() {
  git init -q "${2}"
  git -C "${2}" fetch -q --depth 1 "${1}" "${3}"
  git -C "${2}" -c advice.detachedHead=false checkout -q FETCH_HEAD
}
mkdir -p "$TWIN_WS/src/upstream"
cd "$TWIN_WS/src"
fetch_at https://github.com/openAMRobot/openamr-upperbody-sw.git openamr-upperbody-sw "$UB_SHA"
export ACCEPTANCE="$TWIN_WS/src/openamr-upperbody-sw/.github/workflows/baseline1-acceptance.yml"
export SCENE_PINS="$TWIN_WS/src/openamr-upperbody-sw/ros2/src/openamrobot_build1_scene/config/pins.yaml"
workflow_pin() { sed -n "s/^  ${1}: *//p" "$ACCEPTANCE" | tr -d "'\""; }
scene_pin() { python3 -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["pins"][sys.argv[2]]["sha"])' "$SCENE_PINS" "${1}"; }
fetch_at https://github.com/openAMRobot/openamr-platform-sw.git openamr-platform-sw "$(workflow_pin PLATFORM_SW_SHA)"
fetch_at https://github.com/openAMRobot/openamrobot-interfaces.git openamrobot-interfaces "$(workflow_pin INTERFACES_SHA)"
fetch_at https://github.com/enactic/openarm_description.git upstream/openarm_description "$(scene_pin openarm_description)"
fetch_at https://github.com/enactic/openarm_ros2.git upstream/openarm_ros2 "$(scene_pin openarm_ros2)"
fetch_at https://github.com/enactic/openarm_can.git upstream/openarm_can "$(scene_pin openarm_can)"
for d in openamr-upperbody-sw openamr-platform-sw openamrobot-interfaces upstream/*; do
  echo "$d $(git -C "$d" rev-parse HEAD)"
done | tee "$TWIN_WS/pins.txt"
```

`pins.txt` lists the six commits. A result you report names them.

### 3. Dependencies and build

**Headless, checked in CI.** Holds the Gazebo vendor packages at the versions the acceptance runs use, installs the
dependencies and builds the scene with everything it needs.

<!-- quickstart:headless -->
```bash
cd "$TWIN_WS"
sudo apt-get install -y --allow-downgrades \
  "ros-jazzy-gz-sim-vendor=$(workflow_pin GZ_SIM_VENDOR)" \
  "ros-jazzy-gz-tools-vendor=$(workflow_pin GZ_TOOLS_VENDOR)" \
  "ros-jazzy-sdformat-vendor=$(workflow_pin SDFORMAT_VENDOR)"
sudo apt-mark hold ros-jazzy-gz-sim-vendor ros-jazzy-gz-tools-vendor ros-jazzy-sdformat-vendor
rosdep install --rosdistro jazzy -y -r --ignore-src \
  --from-paths $(colcon list --base-paths src --packages-up-to openamrobot_build1_scene openamrobot_station_alignment --paths-only)
sudo apt-get install -y ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-moveit ros-jazzy-joint-state-publisher ros-jazzy-launch-testing-ament-cmake ros-jazzy-ament-cmake-pytest \
  ros-jazzy-rmw-cyclonedds-cpp
source /opt/ros/jazzy/setup.bash
gz sim --versions
colcon build --packages-up-to openamrobot_build1_scene openamrobot_station_alignment --event-handlers console_cohesion+
```

ROS 2 is sourced after the installs, so that the `gz` command of the vendor packages is on the path. `gz sim --versions` prints the Gazebo version; the acceptance runs check for `8.15.0`. If `apt-get` reports that a
pinned vendor version is not found, packages.ros.org has replaced it; see [Troubleshooting](#troubleshooting).

### 4. Model and scene tests that need no simulator

**Headless, checked in CI.** The eight tests the scene README lists as needing neither Gazebo nor virtual CAN.

<!-- quickstart:headless -->
```bash
cd "$TWIN_WS"
source install/setup.bash
colcon test --packages-select openamrobot_build1_scene --return-code-on-test-failure \
  --ctest-args -R "^test_(scene|world_and_map|launch_support|command_map|footprint|odometry|candump|docs_and_pins)$"
colcon test-result --test-result-base build/openamrobot_build1_scene --verbose
```

### 5. Virtual CAN buses

**Headless, checked in CI.** Creates the five buses: `vcan_drive`, `vcan_bms` and `vcan_aux` as classic CAN (MTU 16),
`vcan_arm_l` and `vcan_arm_r` as CAN FD (MTU 72). The script prints `BLOCKED` and exits 3 when the module or the rights
are missing.

<!-- quickstart:headless -->
```bash
sudo apt-get install -y "linux-modules-extra-$(uname -r)" || echo "linux-modules-extra-$(uname -r) is not available; vcan may already be built in"
sudo modprobe vcan
sudo modprobe can_raw
ros2 run openamrobot_build1_scene setup_vcan_all.sh
ip -details link show type vcan | grep -E "vcan_|mtu"
```

### 6. Start the twin headless and see the devices

**Headless, checked in CI.** Starts Gazebo with the whole robot in the device profile `firmware_sil` (every device
emulator on its virtual bus, the real OpenArm driver), without Nav2 and MoveIt, waits until the drive emulator reports
through the host stand-in of the base controller, then stops the launch.

<!-- quickstart:headless -->
```bash
cd "$TWIN_WS"
export QT_QPA_PLATFORM=offscreen
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><Discovery><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
ros2 launch openamrobot_build1_scene build1.launch.py headless:=true rviz:=false nav2:=false moveit:=false create_vcan:=false \
  > "$TWIN_WS/twin_launch.log" 2>&1 &
TWIN_PID=$!
timeout 900 bash -c 'until ros2 topic list | grep -qx /sil/drive/status; do sleep 5; done'
timeout 300 ros2 topic echo --once /sil/drive/status
timeout 300 ros2 topic echo --once /clock
ros2 topic list | grep -E "^/(sil|build1)/" | sort
kill -TERM "$TWIN_PID"
timeout 120 bash -c "while kill -0 $TWIN_PID 2>/dev/null; do sleep 2; done" || kill -KILL "$TWIN_PID" || true
pkill -f "gz sim" || true
pkill -f openamrobot_ || true
ros2 daemon stop || true
```

The launch runs in the background and is stopped with SIGTERM, because a background job of a script ignores Ctrl+C;
in an interactive terminal you can run it in the foreground and press Ctrl+C. `/sil/drive/status` is JSON from the host stand-in: drive configured, CiA 402 statusword, fault code, target and wheel
speeds. `twin_launch.log` holds the launch output, including the engine limit the launch prints.

### 7. First scenario: drive with Nav2

**Headless, checked in CI.** Scenario 14 (`scn14_drive_fast`): Nav2 drives 2 m and turns 90 degrees in the `fast`
profile (no devices, DART physics) and compares odometry with ground truth. It writes its numbers to
`build1_logs/`.

<!-- quickstart:headless -->
```bash
cd "$TWIN_WS"
export BUILD1_LOG_DIR="$TWIN_WS/build1_logs"
mkdir -p "$BUILD1_LOG_DIR"
colcon test --packages-select openamrobot_build1_scene --return-code-on-test-failure \
  --ctest-args -R "^test_scn14_drive_fast$"
colcon test-result --test-result-base build/openamrobot_build1_scene --verbose
ls "$BUILD1_LOG_DIR"
```

Each scenario reports PASS, FAIL or BLOCKED. BLOCKED is never PASS.

## The Baseline 1 mission

The whole mission (eight phases, about 35 to 140 minutes of wall time per leg on a hosted runner) is not part of the
quick start. It is the CTest `test_baseline1_mission`, run by `baseline1-acceptance.yml` with these settings, which
every leg declares:

```bash
cd "$TWIN_WS"
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><Discovery><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
export BUILD1_PLANNING_POSE_SOURCE=ground_truth BASELINE1_STATION_APPROACH=1 BASELINE1_STATION_ALIGNMENT=1
export BASELINE1_SEED=20261117 PYTHONHASHSEED=20261117 BUILD1_CONTACT_SENSORS=1 BASELINE1_CANCEL_CHECK=1
export BUILD1_LOG_DIR="$TWIN_WS/build1_logs" QT_QPA_PLATFORM=offscreen
colcon test --packages-select openamrobot_build1_scene --return-code-on-test-failure --ctest-args -R "^test_baseline1_mission$"
```

Checked by: the acceptance workflow runs this command; see [Evidence and limits](evidence-and-limits.md) for the run
IDs. The values above are copied from `baseline1-acceptance.yml` at `UB_SHA`; if they differ, the workflow wins.
[Scenarios](scenarios.md) explains the phases and checks.

## Desktop

**Desktop.** Not run in CI. Needs a graphical session.

Install the ROS 2 desktop tools (RViz) once:

```bash
sudo apt-get install -y ros-jazzy-desktop
```

Start the scene with RViz, every device on virtual CAN, Nav2 and MoveIt:

```bash
cd "$TWIN_WS"
source install/setup.bash
ros2 launch openamrobot_build1_scene build1.launch.py rviz:=true
```

Without virtual CAN the launch prints `BLOCKED` and stops. The physics-only profile still runs:

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast rviz:=true
```

List the scenarios and run one against the running launch, from a second terminal:

```bash
ros2 run openamrobot_build1_scene run_scenario.py --list
ros2 run openamrobot_build1_scene run_scenario.py scn01_drive
```

The read-only engineering monitor (Control Room) and the browser operator UI are described in
[Operator UI and Control Room](operator-ui.md).

## Container

The repository ships a dev container (`.devcontainer/` of openamr-upperbody-sw) for GitHub Codespaces and local Dev
Containers: ROS 2 Jazzy desktop, RViz in the browser through noVNC on port 6080. It builds the combined model packages
of `main` (model, control, Gazebo, MoveIt, bring-up), not the Build 1 scene, and a container normally cannot create
`vcan` interfaces. Use it for the model and the `fast` profile; use a full Ubuntu 24.04 machine for the device
profiles. Status: not checked for the Digital Twin release candidate.

## Desktop acceptance checklist

A person who did not build the twin follows this page on a clean Ubuntu 24.04 desktop and records each line with the
date, the machine (CPU, RAM, GPU), the six commits of `pins.txt` and PASS, FAIL or BLOCKED. The record goes into the
release candidate pull request thread. One reviewer covers steps 1 to 6, a second repeats steps 1 to 6 on another
machine, a third covers steps 7 and 8 on an NVIDIA GPU machine.

| Step | Do | Expected |
|---|---|---|
| 1 | Quick start steps 1 to 7 | every command exits 0; scenario 14 PASS |
| 2 | `ros2 launch openamrobot_build1_scene build1.launch.py rviz:=true` | Gazebo and RViz open; the robot stands at the origin |
| 3 | RViz checklist of the scene README | one TF tree `map` > `odom` > `base_footprint`, with `base_footprint` > `base_link` and `base_footprint` > lift > arms (the lift hangs from `base_footprint`, not from `base_link`); no flickering frame; scan, costmaps, planning scene shown |
| 4 | `run_scenario.py scn01_drive` | the base drives 2 m and turns; PASS with odometry error in the log |
| 5 | Control Room next to the running scene ([Operator UI and Control Room](operator-ui.md)) | live status, CAN bus rates and decoded signals; nothing published outside `/control_room/` |
| 6 | Operator UI monitoring views, only if the [UI conditions](operator-ui.md#operator-ui) are met | robot state, map and mission status shown; manual driving not used |
| 7 | Isaac Sim run kit ([Simulators](simulators.md#isaac-sim)) | result JSON with one articulation and the expected joint count |
| 8 | MuJoCo viewer of the generated model, when the parity job is green | the model loads and stands |

## Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| `BLOCKED: cannot create vcan_drive` | `vcan` module missing or no sudo rights | install `linux-modules-extra-$(uname -r)`, run `sudo modprobe vcan`; in a container use the `fast` profile |
| The launch prints `BLOCKED` and stops | no virtual CAN for a device profile | run step 5, or start with `profile:=fast` |
| `apt-get`: version of `ros-jazzy-gz-sim-vendor` not found | packages.ros.org replaced the pinned build | report it in openamr-upperbody-sw; the acceptance pins move only through a reviewed change. Do not report results built on other versions as acceptance evidence |
| Lift checks report BLOCKED | real-time factor below about 0.5: the CTL-017 model faults on its Hall rate rule | expected on slow machines; not a FAIL |
| `ros2 topic list` shows nothing from the launch | middleware mismatch between terminals | export the same `RMW_IMPLEMENTATION` and `CYCLONEDDS_URI` in every terminal |
| Late nodes do not discover each other | CycloneDDS participant index cap | keep `MaxAutoParticipantIndex` 120 as above |
| MoveIt refuses the start state | joint 4 reads just below its limit after activation | the scenarios move to the park pose first; see the scene README, Known limits |
| A repeated run gives different numbers | Gazebo has no seed argument; parking varies from run to run | compare runs by their checks, not by exact values |

## Next step

[Scenarios](scenarios.md): what Baseline 1 checks, phase by phase.
