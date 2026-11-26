---
title: Check out and validate a workspace
description: Import the OpenAMRobot repositories into a workspace with vcs, validate the manifest, and build the two source drivers.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Active</span><h1>Check out and validate a workspace</h1><p>Import the repositories, validate the manifest and know what the result shows.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Developers who want a source checkout of the OpenAMRobot repositories, or reviewers who need to check a manifest.

**When you finish:** you will have a workspace imported from a manifest and, if you ran the checks, evidence of what validated and what did not.

**Applies to:** the procedures in the [`openamrobot-manifest` README](https://github.com/openAMRobot/openamrobot-manifest/blob/main/README.md), checked against `main` at `5b782ac`. The commands are summarised from it and have not been run by the documentation team. Read the current README before you run them.

## Before you start

- Ubuntu 24.04 with ROS 2 Jazzy for the ROS 2 packages. The README names this as the platform for the driver build.
- `git`, `vcstool` and `colcon`. To validate a manifest you also need Python 3 with PyYAML and `yamllint`.
- Network access to the repositories.

## Assemble a development workspace

```bash
mkdir -p ~/oamr_ws && cd ~/oamr_ws
vcs import . < /path/to/openamrobot.repos
colcon build
```

ROS 2 packages land in `src/`. The README says additional UI ROS packages are found under `ui/` when `colcon` runs at the workspace root. Firmware, hardware and documentation use their own build procedures. Importing and discovering packages does not establish that the full workspace builds.

## Check out the pinned rc.1 snapshot

Use a **new, empty** workspace. The snapshot is a candidate, not an accepted release.

```bash
mkdir -p ~/oamr_rc1_ws
vcs import ~/oamr_rc1_ws < releases/v2.0.0-rc.1.repos
vcs export --exact ~/oamr_rc1_ws > /tmp/rc1-exact.repos
python3 tools/check_release_manifest.py releases/v2.0.0-rc.1.repos --exact-export /tmp/rc1-exact.repos
cd ~/oamr_rc1_ws
colcon list
```

The comparison with an exact export rejects changed, missing or extra repositories. Run the commands from a clone of `openamrobot-manifest`.

## Validate a manifest

From a clone of the manifest repository:

```bash
python3 -m unittest discover -s tests -v
python3 tools/check_manifest.py openamrobot.repos
```

For the release snapshot, the README also lists an offline check and a release-manifest check:

```bash
python3 tools/check_manifest.py --offline releases/v2.0.0-rc.1.repos
python3 tools/check_release_manifest.py releases/v2.0.0-rc.1.repos --development openamrobot.repos
```

The [reference](reference.md) explains what each stage of `check_manifest.py` reports.

## Build the two source drivers

The manifests include two source-only driver packages. On Ubuntu 24.04 with ROS 2 Jazzy installed, the README prepares the tools and then runs a dedicated check in a new workspace:

```bash
sudo apt-get update
sudo apt-get install build-essential cmake git python3-colcon-common-extensions python3-rosdep python3-vcstool python3-yaml
# Run once if /etc/ros/rosdep/sources.list.d/20-default.list is absent:
sudo rosdep init
rosdep update --rosdistro jazzy
bash tools/verify_jazzy_drivers.sh releases/v2.0.0-rc.1.repos ~/oamr_driver_ws ~/oamr_driver_evidence
```

The script imports the release manifest, records the exact export and package discovery, builds only the two drivers and confirms that their executables are installed. It does not start hardware and does not show that the full workspace builds.

## If it did not work

Read the checker output, because it reports its stages separately. Network failures affect only the remote stage. Known build issues, such as the duplicate `openamr_ui_msgs` package, are tracked in the repository. Report new problems in the [manifest repository issues](https://github.com/openAMRobot/openamrobot-manifest/issues).

## Next step

[Files, checks and drivers](reference.md).
