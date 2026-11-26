---
title: Installation
tags: [developer, integrator]
status: experimental
description: Install the OpenAMRobot 2.0 rc.1 Digital Twin with the manifest bootstrap script, or step by step with the same commands.
---

# Installation

**For:** developers installing the rc.1 Digital Twin on a clean Ubuntu 24.04 machine.

**Canonical source:** `tools/bootstrap_digital_twin.sh` and `releases/v2.0.0-rc.1-digital-twin.repos` in
[openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest). The commands below are copied from that
script; if they differ, the script wins.

**Before you start:** a machine that matches the [tested environment](requirements.md), `sudo` rights and network access.

**When you finish:** a built workspace in `~/oamr_dt_ws` with the six pinned repositories, and a file `exact.repos`
that records the exact commits.

!!! warning "Simulation only"
    The installation contains no hardware driver set-up. Nothing here is hardware, physical acceptance or safety evidence.

## Install with the bootstrap script

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/openAMRobot/openamrobot-manifest.git
bash openamrobot-manifest/tools/bootstrap_digital_twin.sh "$HOME/oamr_dt_ws"
```

!!! note "Valid after publication"
    The script and the profile are not on `main` of openamrobot-manifest yet. Until
    [openamrobot-manifest pull request 23](https://github.com/openAMRobot/openamrobot-manifest/pull/23) merges, they are
    on the branch `release/v2.0.0-rc.1-pins`, at commit `6b50185c3e126cc3830ce05b1da14e74d08cf2b6`. Select that commit
    after cloning:

    ```bash
    git -C openamrobot-manifest checkout 6b50185c3e126cc3830ce05b1da14e74d08cf2b6
    ```

The script takes two optional arguments: the workspace (default `~/oamr_dt_ws`) and the profile file (default
`releases/v2.0.0-rc.1-digital-twin.repos` beside the script). It asks for the `sudo` password for `apt`. Every step
is idempotent, so the script is safe to run again after an interruption.

In CI the first run of the script took between 6 and 9 minutes on a clean hosted runner, and a second run under one
minute (run linked under [What was tested](#what-was-tested)). The colcon build inside it covers 17 packages and took
about 1.5 minutes there. Your times depend on your machine and network.

## What the script does

The six steps below are the manual equivalent. Run them in order if you prefer not to use the script, or read them to
know what the script changes on your machine.

### 1. ROS 2 Jazzy from packages.ros.org

Installs the ROS 2 apt source at a pinned version, then the ROS base packages, the development tools and `vcstool`,
and initialises `rosdep`.

```bash
sudo apt-get update
sudo apt-get install -y curl locales software-properties-common python3-pip
sudo add-apt-repository -y universe
curl --fail --location --retry 5 --retry-delay 5 -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.3.0/ros2-apt-source_1.3.0.noble_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt-get update
sudo apt-get install -y ros-jazzy-ros-base ros-dev-tools python3-vcstool
sudo rosdep init
```

`sudo rosdep init` reports an error when rosdep is already initialised. That is harmless; the script prints
"rosdep init: already initialized" in that case.

### 2. Gazebo Harmonic, pinned vendor builds

Installs three Gazebo vendor packages at the exact builds the acceptance workflow uses, and holds them so that a
later `apt upgrade` does not replace them.

```bash
sudo apt-get install -y --allow-downgrades \
  "ros-jazzy-gz-sim-vendor=0.0.13-1noble.20261031.125555" "ros-jazzy-gz-tools-vendor=0.0.8-1noble.20261025.230735" "ros-jazzy-sdformat-vendor=0.0.14-1noble.20261031.120928"
sudo apt-mark hold ros-jazzy-gz-sim-vendor ros-jazzy-gz-tools-vendor ros-jazzy-sdformat-vendor
```

The ROS package server keeps only the newest build of a package. If the tested builds are no longer in the apt
index, the script installs the current ones and prints a warning that rc.1 was not qualified on them. Set
`OAMR_GZ_PIN=strict` to make that case an error instead, as the CI job does.

### 3. Import the pinned sources

Imports six repositories at full commit hashes into the workspace, writes the exact result to `exact.repos`, and
checks it. `check_release_manifest.py` compares the checkout with the profile. `check_profile.py` fails when a pin
differs from the release manifest or from the pins of the imported upper-body commit, or when two packages in the
workspace provide the same ROS package name.

Run these from the root of the openamrobot-manifest checkout:

```bash
mkdir -p "$HOME/oamr_dt_ws"
vcs import "$HOME/oamr_dt_ws" < releases/v2.0.0-rc.1-digital-twin.repos
vcs export --exact "$HOME/oamr_dt_ws" > "$HOME/oamr_dt_ws/exact.repos"
python3 tools/check_release_manifest.py releases/v2.0.0-rc.1-digital-twin.repos --exact-export "$HOME/oamr_dt_ws/exact.repos"
python3 tools/check_profile.py releases/v2.0.0-rc.1-digital-twin.repos --release releases/v2.0.0-rc.1.repos --workspace "$HOME/oamr_dt_ws"
```

The profile holds these repositories and paths:

| Path in the workspace | Repository | Commit |
|---|---|---|
| `src/openamr-upperbody-sw` | [openAMRobot/openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) | `1ab45a62957d238fc293eee08a8fd9158acebb01` |
| `src/openamr-platform-sw` | [openAMRobot/openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) | `ddd20ab3a85d98bb78c4c5f014952c4a0717ef92` |
| `src/openamrobot-interfaces` | [openAMRobot/openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) | `50ed777be7990edbd3465f33fd97a158e7e3b88b` |
| `src/upstream/openarm_description` | [enactic/openarm_description](https://github.com/enactic/openarm_description) | `14ff67b638ff1c738a1b9a6be8aaa5ce5ed2c831` |
| `src/upstream/openarm_ros2` | [enactic/openarm_ros2](https://github.com/enactic/openarm_ros2) | `4e837e1d0dae692ff67b560b69d8d281d7a8d4ed` |
| `src/upstream/openarm_can` | [enactic/openarm_can](https://github.com/enactic/openarm_can) | `bfd4e52194aefe38389fa6e670be3738136facb9` |

The file `releases/v2.0.0-rc.1.repos` beside it is the full source inventory of the release archive. It is not a
buildable workspace; do not import it for the Digital Twin.

### 4. Dependencies

Resolves the dependencies of the two top packages with `rosdep`, then installs the simulation, navigation, motion
planning, middleware and CAN packages by name. The last line installs the kernel module package for virtual CAN; if
it is not available for your kernel, the `fast` and `fine` profiles still work.

```bash
source /opt/ros/jazzy/setup.bash
cd "$HOME/oamr_dt_ws"
rosdep update --rosdistro jazzy
paths=$(colcon list --base-paths src --packages-up-to openamrobot_build1_scene openamrobot_station_alignment --paths-only)
rosdep install --rosdistro jazzy --from-paths $paths --ignore-src -y -r
sudo apt-get install -y python3-can ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-moveit ros-jazzy-joint-state-publisher ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-rviz2 iproute2 can-utils
sudo apt-get install -y "linux-modules-extra-$(uname -r)"
```

### 5. Build

Builds `openamrobot_build1_scene`, `openamrobot_station_alignment` and everything they depend on.

```bash
colcon build --base-paths src --packages-up-to openamrobot_build1_scene openamrobot_station_alignment --event-handlers console_cohesion+
```

### 6. Environment of every new terminal

The script ends by printing these four lines. Run them in every terminal that starts or talks to the twin.

```bash
source /opt/ros/jazzy/setup.bash
source $HOME/oamr_dt_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><Discovery><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
```

The last line raises a CycloneDDS discovery limit. The Build 1 launch starts many ROS nodes, and at the default
limit late participants did not match in the project's DDS benchmark. All Build 1 CI workflows set the same value.

## Verify the installation

A build that finishes is not yet a working installation. Start the twin and check it as in the
[quick start](quick-start.md#4-check-that-it-is-ready).

## What was tested

The [Digital Twin clean install workflow](https://github.com/openAMRobot/openamrobot-manifest/actions/runs/45738318716)
ran the script twice on each of two fresh hosted runners, then started the `fast` profile headless and checked the
clock, the robot description, TF and the drive demonstration. Both environments passed. That run used the profile
with openamr-upperbody-sw at `729be2a`, whose source tree is identical to the candidate commit `1ab45a6`; the repeat on
the final profile, [run 45747748555](https://github.com/openAMRobot/openamrobot-manifest/actions/runs/45747748555),
passed in both environments. Simulation evidence only.

The check was extended on 26 November ([run 45824534544](https://github.com/openAMRobot/openamrobot-manifest/actions/runs/45824534544),
both environments passed): after the drive demonstration it runs the lift demonstration, ends the launch with one
interrupt (4 and 9 s, no process left), starts a second launch and runs the grasp demonstration with both arms and
grippers.

Measured on hosted runners in [run 45756061297](https://github.com/openAMRobot/openamrobot-manifest/actions/runs/45756061297),
headless: the script took 5.5 and 7 minutes; from the launch command to a ready twin (advancing clock, robot
description, TF) 24 s and 43 s; the drive demonstration 1.3 and 3.9 minutes. A desktop session with RViz was not
measured.

## If it did not work

See [Troubleshooting](troubleshooting.md), sections "Installation" and "Workspace".

Next: [Quick start](quick-start.md).
